#!/usr/bin/env python3
"""Plan and execute the five-scenario Prompt Kit runtime-compliance pilot."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EVAL = ROOT / "harness" / "evals" / "runtime-compliance"
FIXTURES = EVAL / "fixtures"
SCRIPTS = EVAL / "scripts"
DEFAULT_OUTPUT = ROOT / "Outputs" / "repository-ai-evals" / "runtime-compliance"
INDEX_PATH = FIXTURES / "index.v1.json"
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime_adapter import invoke_or_mark_invalid  # noqa: E402
from scripts.validate_prompt_runtime_compliance_receipt import validate_receipt  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def repository_sha() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def validate_run_id(run_id: str) -> str:
    if not isinstance(run_id, str) or not RUN_ID_RE.fullmatch(run_id):
        raise ValueError("run_id must be a safe 1..128 character path component")
    if run_id in {".", ".."}:
        raise ValueError("run_id cannot be a traversal component")
    return run_id


def _scenario_rows() -> list[dict[str, Any]]:
    index = load_json(INDEX_PATH)
    if index.get("schema_version") != "prompt-runtime-compliance-scenario-index/v1":
        raise ValueError("runtime-compliance scenario index identity drift")
    rows = index.get("scenarios")
    if not isinstance(rows, list) or len(rows) != 5:
        raise ValueError("runtime-compliance pilot requires exactly five indexed scenarios")
    expected = {f"RTC{i:02d}" for i in range(1, 6)}
    ids = [row.get("scenario_id") for row in rows]
    if set(ids) != expected or len(ids) != len(set(ids)):
        raise ValueError("scenario index must contain RTC01..RTC05 exactly once")
    return rows


def build_plan(selected: list[str] | None = None) -> dict[str, Any]:
    rows = _scenario_rows()
    wanted = [item.upper() for item in selected] if selected else [row["scenario_id"] for row in rows]
    if len(wanted) != len(set(wanted)):
        raise ValueError("selected scenario ids must be unique")
    by_id = {row["scenario_id"]: row for row in rows}
    if any(item not in by_id for item in wanted):
        raise ValueError("selected scenarios must be members of RTC01..RTC05")
    runs = [
        {
            "scenario_id": scenario_id,
            "fixture_path": by_id[scenario_id]["path"],
            "protected_rule_ids": by_id[scenario_id]["protected_rule_ids"],
        }
        for scenario_id in wanted
    ]
    return {
        "schema_version": "prompt-runtime-compliance-pilot-plan/v1",
        "pilot_id": "P07-runtime-compliance-pilot",
        "runs": runs,
        "planned_runs": len(runs),
        "proof_ceiling": "Plan only until a runtime adapter executes each scenario and emits validated receipts.",
    }


def initialize_run(
    scenario_id: str,
    *,
    run_id: str,
    output_root: Path = DEFAULT_OUTPUT,
) -> Path:
    run_id = validate_run_id(run_id)
    row = next(row for row in _scenario_rows() if row["scenario_id"] == scenario_id)
    fixture = ROOT / row["path"]
    if not fixture.is_file():
        raise FileNotFoundError(f"scenario fixture missing: {fixture}")
    run_dir = output_root / "runs" / run_id
    if run_dir.exists():
        raise FileExistsError(f"run directory already exists: {run_dir}")
    run_dir.mkdir(parents=True)
    shutil.copy2(fixture, run_dir / "scenario.json")
    workspace = run_dir / "workspace"
    workspace.mkdir()
    scenario = load_json(fixture)
    if scenario_id == "RTC04":
        protocol = scenario["mutation_protocol"]
        (workspace / "target-state.json").write_text(
            json.dumps(
                {
                    "target_identity": protocol["target_identity"],
                    "state_fingerprint": protocol["pre_state_fingerprint"],
                    "mutation_applied": False,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    now = datetime.now(timezone.utc).isoformat()
    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "schema_version": "prompt-runtime-compliance-run/v1",
                "run_id": run_id,
                "scenario_id": scenario_id,
                "repository_sha": repository_sha(),
                "started_at": now,
                "completed_at": None,
                "result": "UNPROVEN_RUNTIME",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return run_dir


def _claimed_compliance_result(capture: dict[str, Any]) -> str:
    serious_fail = any(
        row["result"] == "FAIL"
        and row["severity"] in {"CRITICAL", "HIGH"}
        and row["status"] != "INFORMATIONAL"
        for row in capture["reported_violations"]
    )
    if serious_fail:
        return "FAIL"
    if any(check["status"] == "UNKNOWN" for check in capture["proof"]["checks"]):
        return "INCONCLUSIVE"
    return "PASS"


def capture_to_receipt(capture: dict[str, Any]) -> dict[str, Any]:
    run_id = capture["run"]["run_id"]
    return {
        "schema_version": "prompt-runtime-compliance-receipt/v1",
        "receipt_id": f"prcr/{run_id}",
        "supersedes_receipt_id": None,
        "related_receipt_ids": [],
        "run": capture["run"],
        "model_config": capture["model_config"],
        "effective_prompt": capture["effective_prompt"],
        "scenario": capture["scenario"],
        "boundary_events": capture["boundary_events"],
        "actions": capture["actions"],
        "terminal": capture["terminal"],
        "violations": capture["reported_violations"],
        "proof": capture["proof"],
        "regression_linkage": capture["regression_linkage"],
        "evidence": capture["evidence"],
        "privacy": capture["privacy"],
        "compliance_result": _claimed_compliance_result(capture),
        "occurred_at": capture["run"]["ended_at"],
    }


def build_observed_behavior_proof(
    receipt: dict[str, Any],
    subject: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not receipt["proof"]["runtime_observed"]:
        return None
    if not any(row["kind"] == "runtime" for row in receipt["evidence"]):
        raise ValueError("observed runtime proof requires direct runtime evidence")
    if subject is None:
        raise ValueError("observed runtime proof requires an exact observed-behavior subject")
    passed = receipt["compliance_result"] == "PASS"
    return {
        "schema_version": "observed-behavior-proof/v1",
        "subject": subject,
        "evidence_class": "target_runtime_observed",
        "observations": [
            {
                "id": "runtime-compliance-receipt",
                "occurred": True,
                "passed": passed,
            }
        ],
        "claims": [
            {
                "id": "prompt-runtime-compliance",
                "status": "PASS" if passed else "FAIL",
                "required_evidence_class": "target_runtime_observed",
                "observation_ids": ["runtime-compliance-receipt"],
            }
        ],
        "verdict": "PASS" if passed else "FAIL",
    }


def execute_case(
    spec: dict[str, Any],
    *,
    pilot_id: str,
    adapter_config: dict[str, Any] | None,
    output_root: Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    scenario_id = spec["scenario_id"]
    run_id = validate_run_id(f"{pilot_id}-{scenario_id.lower()}")
    run_dir = initialize_run(scenario_id, run_id=run_id, output_root=output_root)
    outcome = invoke_or_mark_invalid(adapter_config, run_dir)
    if not outcome["valid"]:
        return {
            "run_id": run_id,
            "scenario_id": scenario_id,
            "disposition": "INVALID",
            "invalid_code": outcome["invalid"]["code"],
        }

    capture = outcome["capture"]
    receipt = capture_to_receipt(capture)
    validation = validate_receipt(receipt)
    (run_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (run_dir / "validation.json").write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    meta = load_json(run_dir / "run.json")
    meta.update(
        {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "result": validation["overall_result"],
        }
    )
    (run_dir / "run.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "disposition": "VALID",
        "compliance_result": receipt["compliance_result"],
        "validation_result": validation["overall_result"],
        "runtime_observed": capture["observed_runtime"],
        "receipt_path": str((run_dir / "receipt.json").relative_to(output_root)),
        "validation_path": str((run_dir / "validation.json").relative_to(output_root)),
    }


def execute_pilot(
    plan: dict[str, Any],
    *,
    pilot_id: str,
    adapter_config: dict[str, Any] | None,
    output_root: Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    records = [
        execute_case(
            spec,
            pilot_id=pilot_id,
            adapter_config=adapter_config,
            output_root=output_root,
        )
        for spec in plan["runs"]
    ]
    valid = [row for row in records if row["disposition"] == "VALID"]
    invalid = [row for row in records if row["disposition"] == "INVALID"]
    observed = [row for row in valid if row["runtime_observed"]]
    runtime_state = "OBSERVED_RUNTIME" if len(observed) == len(records) and records else "UNPROVEN_RUNTIME"
    if adapter_config is None:
        blocker: str | None = "RUNTIME_UNAVAILABLE"
    elif invalid:
        blocker = "INVALID_RUNS"
    elif len(observed) != len(records):
        blocker = "FAKE_OR_NONOBSERVED_ADAPTER"
    else:
        blocker = None
    return {
        "schema_version": "prompt-runtime-compliance-pilot-receipt/v1",
        "pilot_id": pilot_id,
        "runtime_state": runtime_state,
        "planned_runs": plan["planned_runs"],
        "valid_runs": len(valid),
        "invalid_runs": len(invalid),
        "observed_runs": len(observed),
        "blocker": blocker,
        "runs": records,
        "proof_ceiling": (
            "Exact observed model/config runtime only."
            if runtime_state == "OBSERVED_RUNTIME"
            else "Repository harness evidence only; target runtime remains unobserved."
        ),
    }


def _load_adapter(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("adapter config must be a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter-config", type=Path)
    parser.add_argument("--pilot-id", default="pilot")
    parser.add_argument("--scenario", action="append", dest="scenarios")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--plan-output", type=Path)
    parser.add_argument("--receipt-output", type=Path)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    plan = build_plan(args.scenarios)
    plan_path = args.plan_output or (args.output_root / "pilot-plan.json")
    receipt_path = args.receipt_output or (args.output_root / "pilot-receipt.json")
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.plan_only:
        receipt = {
            "schema_version": "prompt-runtime-compliance-pilot-receipt/v1",
            "pilot_id": args.pilot_id,
            "runtime_state": "UNPROVEN_RUNTIME",
            "planned_runs": plan["planned_runs"],
            "valid_runs": 0,
            "invalid_runs": 0,
            "observed_runs": 0,
            "blocker": "RUNTIME_UNAVAILABLE",
            "runs": [],
            "proof_ceiling": "Plan-only evidence; no runtime adapter executed.",
        }
    else:
        receipt = execute_pilot(
            plan,
            pilot_id=args.pilot_id,
            adapter_config=_load_adapter(args.adapter_config),
            output_root=args.output_root,
        )

    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.summary:
        print(
            json.dumps(
                {
                    "pilot_id": receipt["pilot_id"],
                    "runtime_state": receipt["runtime_state"],
                    "planned_runs": receipt["planned_runs"],
                    "valid_runs": receipt["valid_runs"],
                    "invalid_runs": receipt["invalid_runs"],
                    "observed_runs": receipt["observed_runs"],
                    "blocker": receipt["blocker"],
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
