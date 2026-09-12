"""triage/harness/cli.py
-----------------------
Minimal harness CLI providing: doctor, workflows, explain, run, validate.

Usage:
    python -m triage.harness.cli doctor
    python -m triage.harness.cli workflows
    python -m triage.harness.cli explain <workflow_id>
    python -m triage.harness.cli run <workflow_id> [--months M M] [--input PATH ...]
    python -m triage.harness.cli validate <run_id>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.harness.doctor import run_doctor
from triage.harness.context import (
    create_run_context,
    complete_run_context,
    load_run_context,
)
from triage.harness.validate import run_validation
from triage.harness.output_policy import validate_output_allocation
from triage.harness.registry import (
    get_workflow,
    list_workflows,
    list_artifacts,
)
from triage.path_policy import repo_root


def _emit(data: Any) -> None:
    print(json.dumps(data, indent=2, default=str))


def cmd_doctor(args: argparse.Namespace) -> int:
    result = run_doctor()
    _emit(result)
    return 0 if result["status"] == "OK" else 1


def cmd_workflows(args: argparse.Namespace) -> int:
    wfs = list_workflows()
    output: Dict[str, Any] = {}
    for wf_id, wf in wfs.items():
        output[wf_id] = {
            "name": wf.get("name", ""),
            "description": wf.get("description", ""),
            "direction": wf.get("direction", ""),
            "proof_ceiling": wf.get("proof_ceiling", ""),
        }
    _emit(output)
    return 0


def cmd_explain(args: argparse.Namespace) -> int:
    wf = get_workflow(args.workflow_id)
    if wf is None:
        print(f"Unknown workflow: {args.workflow_id!r}", file=sys.stderr)
        return 1
    artifact_id = wf.get("artifact_id", "")
    artifacts = list_artifacts()
    artifact_info = artifacts.get(artifact_id, {}) if artifact_id else {}

    output = {
        "workflow_id": args.workflow_id,
        "name": wf.get("name", ""),
        "description": wf.get("description", ""),
        "direction": wf.get("direction", ""),
        "inputs": wf.get("inputs", {}),
        "outputs": wf.get("outputs", []),
        "artifact_id": artifact_id,
        "engine": wf.get("engine", ""),
        "minimum_proof_level": wf.get("minimum_proof_level", ""),
        "proof_ceiling": wf.get("proof_ceiling", ""),
        "validation_profile": wf.get("validation_profile", ""),
    }
    if artifact_info:
        output["artifact"] = {
            "type": artifact_info.get("type", ""),
            "delivery": artifact_info.get("delivery", False),
            "privacy_class": artifact_info.get("privacy_class", ""),
            "required_sidecars": artifact_info.get("required_sidecars", []),
        }
    _emit(output)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    wf = get_workflow(args.workflow_id)
    if wf is None:
        print(f"Unknown workflow: {args.workflow_id!r}", file=sys.stderr)
        return 1

    months = args.months or ["2026-04", "2026-05"]
    input_paths = args.input or []

    # Validate output allocation
    out_dir = repo_root() / "Outputs" / "runs" / "preview"
    violations = validate_output_allocation(str(out_dir), input_paths)
    if violations:
        _emit({"status": "FAIL", "violations": violations})
        return 1

    # Create run context (allocates run dir internally)
    ctx = create_run_context(
        workflow_id=args.workflow_id,
        input_paths=input_paths,
        requested_proof_level=wf.get("minimum_proof_level", "harness"),
        metadata={"months": months},
    )
    run_dir = repo_root() / ctx["output_dir"]

    # Write synthetic manifest into the same run dir
    import datetime as _dt
    manifest = {
        "engine": wf.get("engine", "triage.harness.cli"),
        "workflow_id": args.workflow_id,
        "run_id": ctx["run_id"],
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "months": months,
        "synthetic": True,
        "outputs": {"run_dir": ctx["output_dir"]},
    }
    manifest_path = run_dir / "synthetic-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")

    # Complete with build proof for synthetic
    ctx = complete_run_context(ctx, "build")

    _emit(ctx)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    report = run_validation(args.run_id)
    _emit(report)
    return 0 if report["overall_status"] == "PASS" else 1


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="triage.harness.cli",
        description="Harness spine CLI — workflow orchestration and validation.",
    )
    sub = ap.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Check harness health")
    sub.add_parser("workflows", help="List registered workflows")

    p_explain = sub.add_parser("explain", help="Explain a workflow")
    p_explain.add_argument("workflow_id")

    p_run = sub.add_parser("run", help="Execute a workflow (synthetic mode)")
    p_run.add_argument("workflow_id")
    p_run.add_argument("--months", nargs="+", default=["2026-04", "2026-05"])
    p_run.add_argument("--input", nargs="*", default=[])

    p_validate = sub.add_parser("validate", help="Validate a run directory")
    p_validate.add_argument("run_id")

    args = ap.parse_args(argv)

    dispatch = {
        "doctor": cmd_doctor,
        "workflows": cmd_workflows,
        "explain": cmd_explain,
        "run": cmd_run,
        "validate": cmd_validate,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
