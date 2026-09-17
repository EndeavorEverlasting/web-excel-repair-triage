#!/usr/bin/env python3
"""Plan and optionally execute the paired 16-run compute-authority pilot."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EVAL = ROOT / "harness" / "evals" / "compute-authority"
SCRIPTS = EVAL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from conditions import validate_conditions  # noqa: E402
from grade_run import grade_run  # noqa: E402
from init_run import initialize_run  # noqa: E402
from runtime_adapter import invoke_or_mark_invalid  # noqa: E402

DEFAULT_OUTPUT = ROOT / "Outputs" / "repository-ai-evals" / "compute-authority"


def _rng(seed: str) -> random.Random:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_plan(*, seed: str | None = None, cases: list[str] | None = None) -> dict[str, Any]:
    contract = validate_conditions()
    pilot = contract["pilot"]
    selected = [case.upper() for case in (cases or pilot["cases"])]
    expected = set(pilot["cases"])
    if not selected or any(case not in expected for case in selected) or len(set(selected)) != len(selected):
        raise ValueError("pilot cases must be unique members of the frozen TC01..TC08 set")
    seed = seed or pilot["pair_order_seed"]
    rng = _rng(seed)
    shuffled = list(selected)
    rng.shuffle(shuffled)
    control_first_count = len(shuffled) // 2
    assignments: list[dict[str, Any]] = []
    pair_orders: list[dict[str, Any]] = []
    for pair_index, case_id in enumerate(shuffled, start=1):
        order = ["control", "treatment"] if pair_index <= control_first_count else ["treatment", "control"]
        pair_orders.append({"case": case_id, "order": order})
        for order_index, condition in enumerate(order, start=1):
            assignments.append({
                "pair_index": pair_index,
                "order_index": order_index,
                "case": case_id,
                "condition": condition,
                "repetition": 1,
            })
    return {
        "schema_version": "compute-authority-pilot-plan/v1",
        "study_id": contract["study_id"],
        "seed": seed,
        "pair_orders": pair_orders,
        "runs": assignments,
        "planned_runs": len(assignments),
        "control_first_pairs": sum(1 for item in pair_orders if item["order"][0] == "control"),
        "treatment_first_pairs": sum(1 for item in pair_orders if item["order"][0] == "treatment"),
    }


def _load_adapter(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("adapter config must be a JSON object")
    return payload


def execute_pilot(plan: dict[str, Any], *, pilot_id: str, adapter_config: dict[str, Any] | None) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    valid_runs = invalid_runs = 0
    for spec in plan["runs"]:
        run_id = f"{pilot_id}-{spec['pair_index']:02d}-{spec['order_index']}-{spec['case']}-{spec['condition']}"
        run_dir = initialize_run(
            case_id=spec["case"],
            condition=spec["condition"],
            repetition=spec["repetition"],
            run_id=run_id,
        )
        outcome = invoke_or_mark_invalid(adapter_config, run_dir)
        record = {"run_id": run_id, "case": spec["case"], "condition": spec["condition"]}
        if outcome["valid"]:
            grade = grade_run(run_dir)
            record.update({"disposition": "VALID", "grade_result": grade["result"]})
            valid_runs += 1
        else:
            record.update({"disposition": "INVALID", "invalid_code": outcome["invalid"]["code"]})
            invalid_runs += 1
        records.append(record)
    runtime_state = "OBSERVED_RUNTIME" if valid_runs else "UNPROVEN_RUNTIME"
    return {
        "schema_version": "compute-authority-pilot-receipt/v1",
        "pilot_id": pilot_id,
        "runtime_state": runtime_state,
        "planned_runs": plan["planned_runs"],
        "valid_runs": valid_runs,
        "invalid_runs": invalid_runs,
        "blocker": None if adapter_config is not None else "RUNTIME_UNAVAILABLE",
        "runs": records,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "effectiveness_promoted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter-config", type=Path)
    parser.add_argument("--pilot-id", default="pilot")
    parser.add_argument("--seed")
    parser.add_argument("--case", action="append", dest="cases")
    parser.add_argument("--plan-output", type=Path, default=DEFAULT_OUTPUT / "pilot-plan.json")
    parser.add_argument("--receipt-output", type=Path, default=DEFAULT_OUTPUT / "pilot-receipt.json")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    plan = build_plan(seed=args.seed, cases=args.cases)
    args.plan_output.parent.mkdir(parents=True, exist_ok=True)
    args.plan_output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.plan_only:
        receipt = {
            "schema_version": "compute-authority-pilot-receipt/v1",
            "pilot_id": args.pilot_id,
            "runtime_state": "UNPROVEN_RUNTIME",
            "planned_runs": plan["planned_runs"],
            "valid_runs": 0,
            "invalid_runs": 0,
            "blocker": "RUNTIME_UNAVAILABLE",
            "runs": [],
            "effectiveness_promoted": False,
        }
    else:
        receipt = execute_pilot(plan, pilot_id=args.pilot_id, adapter_config=_load_adapter(args.adapter_config))

    args.receipt_output.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.summary:
        print(json.dumps({
            "pilot_id": receipt["pilot_id"],
            "runtime_state": receipt["runtime_state"],
            "planned_runs": receipt["planned_runs"],
            "valid_runs": receipt["valid_runs"],
            "invalid_runs": receipt["invalid_runs"],
            "blocker": receipt["blocker"],
            "effectiveness_promoted": receipt["effectiveness_promoted"],
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
