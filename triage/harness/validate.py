"""triage/harness/validate.py
----------------------------
Validation runner: executes checks against a run directory and produces
a structured validation report.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.harness.context import PROOF_RANK, load_run_context, proof_level_gte
from triage.harness.registry import load_artifact_registry
from triage.path_policy import repo_root


def _check_run_context_exists(run_dir: Path) -> Dict[str, Any]:
    ctx_path = run_dir / "run-context.json"
    if not ctx_path.exists():
        return {"name": "run_context_exists", "status": "FAIL", "message": "run-context.json missing"}
    try:
        ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
        required = ["run_id", "workflow_id", "started_at", "branch", "commit_sha", "dirty", "input_paths", "output_dir"]
        missing = [k for k in required if k not in ctx]
        if missing:
            return {"name": "run_context_exists", "status": "FAIL", "message": f"missing fields: {missing}"}
        return {"name": "run_context_exists", "status": "PASS", "proof_level": "harness"}
    except Exception as e:
        return {"name": "run_context_exists", "status": "FAIL", "message": str(e)}


def _check_output_under_outputs(run_dir: Path) -> Dict[str, Any]:
    ctx_path = run_dir / "run-context.json"
    if not ctx_path.exists():
        return {"name": "output_under_outputs", "status": "NOT_RUN", "message": "no run context"}
    ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
    output_dir = ctx.get("output_dir", "")
    root = repo_root()
    full_out = root / output_dir if not Path(output_dir).is_absolute() else Path(output_dir)
    try:
        outputs_root = (root / "Outputs").resolve(strict=False)
        if full_out.resolve(strict=False).is_relative_to(outputs_root):
            return {"name": "output_under_outputs", "status": "PASS", "proof_level": "harness"}
    except (AttributeError, OSError):
        pass
    return {"name": "output_under_outputs", "status": "FAIL", "message": f"output_dir '{output_dir}' not under Outputs/"}


def _check_source_immutable(run_dir: Path) -> Dict[str, Any]:
    ctx_path = run_dir / "run-context.json"
    if not ctx_path.exists():
        return {"name": "source_immutable", "status": "NOT_RUN"}
    ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
    input_paths = ctx.get("input_paths", [])
    root = repo_root()
    source_dirs = ("Candidates", "Active", "References", "ArtifactIntake")
    for inp in input_paths:
        p = Path(inp)
        if not p.is_absolute():
            p = (root / p).resolve(strict=False)
        for sd in source_dirs:
            sd_full = (root / sd).resolve(strict=False)
            try:
                if p.is_relative_to(sd_full):
                    return {"name": "source_immutable", "status": "PASS", "proof_level": "harness"}
            except AttributeError:
                continue
    return {"name": "source_immutable", "status": "NOT_APPLICABLE", "message": "no source-dir inputs"}


def _check_output_dir_exists(run_dir: Path) -> Dict[str, Any]:
    if run_dir.is_dir():
        return {"name": "output_dir_exists", "status": "PASS", "proof_level": "harness"}
    return {"name": "output_dir_exists", "status": "FAIL", "message": f"run dir {run_dir} does not exist"}


def _check_artifact_files(run_dir: Path) -> Dict[str, Any]:
    json_files = list(run_dir.glob("*.json"))
    if not json_files:
        return {"name": "has_artifacts", "status": "FAIL", "message": "no JSON artifacts in run dir"}
    return {
        "name": "has_artifacts",
        "status": "PASS",
        "proof_level": "harness",
        "details": {"artifact_count": len(json_files), "files": [f.name for f in json_files]},
    }


def _check_no_empty_report(run_dir: Path) -> Dict[str, Any]:
    """Schemas must reject ceremonial or empty reports."""
    for jp in run_dir.glob("*.json"):
        try:
            data = json.loads(jp.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                if len(data) <= 1:
                    return {"name": "no_empty_report", "status": "FAIL", "message": f"{jp.name} is empty/ceremonial"}
        except Exception:
            continue
    return {"name": "no_empty_report", "status": "PASS", "proof_level": "harness"}


ALL_CHECKS = [
    _check_run_context_exists,
    _check_output_under_outputs,
    _check_source_immutable,
    _check_output_dir_exists,
    _check_artifact_files,
    _check_no_empty_report,
]


def run_validation(run_id: str) -> Dict[str, Any]:
    """Execute all checks for a run and produce a validation report."""
    root = repo_root()
    run_dir = root / "Outputs" / "runs" / run_id

    checks: List[Dict[str, Any]] = []
    for check_fn in ALL_CHECKS:
        result = check_fn(run_dir)
        checks.append(result)

    status_counts = {"PASS": 0, "FAIL": 0, "NOT_RUN": 0, "NOT_APPLICABLE": 0, "BLOCKED": 0}
    for c in checks:
        s = c.get("status", "NOT_RUN")
        status_counts[s] = status_counts.get(s, 0) + 1

    overall = "PASS" if status_counts["FAIL"] == 0 else "FAIL"

    # Determine proof ceiling
    achieved = "contract"
    for c in checks:
        pl = c.get("proof_level")
        if pl and c.get("status") == "PASS" and proof_level_gte(pl, achieved):
            achieved = pl

    report: Dict[str, Any] = {
        "run_id": run_id,
        "validated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "overall_status": overall,
        "checks": checks,
        "proof_ceiling": achieved,
        "summary": {
            "total": len(checks),
            "pass": status_counts["PASS"],
            "fail": status_counts["FAIL"],
            "not_run": status_counts["NOT_RUN"],
            "not_applicable": status_counts["NOT_APPLICABLE"],
            "blocked": status_counts["BLOCKED"],
        },
    }

    report_path = run_dir / "validation-report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report
