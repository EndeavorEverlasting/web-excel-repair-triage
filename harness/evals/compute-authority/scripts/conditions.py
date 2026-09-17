#!/usr/bin/env python3
"""Resolve and verify immutable Control/Treatment prompt snapshots."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EVAL = ROOT / "harness" / "evals" / "compute-authority"
CONDITIONS = EVAL / "runtime" / "conditions.v1.json"
IDENTITIES = EVAL / "prompts" / "identities.json"
VALID_CONDITIONS = ("control", "treatment")
EXPECTED_CASES = tuple(f"TC{i:02d}" for i in range(1, 9))


def _json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object: {path}")
    return payload


def _prompt_digest(path: Path) -> str:
    body = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def validate_conditions() -> dict[str, Any]:
    contract = _json(CONDITIONS)
    identities = _json(IDENTITIES)
    errors: list[str] = []

    if contract.get("schema_version") != "compute-authority-conditions/v1":
        errors.append("unexpected conditions schema_version")
    if contract.get("study_id") != "prompt-kit-compute-authority":
        errors.append("unexpected study_id")
    if contract.get("frozen") is not True:
        errors.append("conditions must be frozen")

    configured = contract.get("conditions")
    if not isinstance(configured, dict) or set(configured) != set(VALID_CONDITIONS):
        errors.append("conditions must contain exactly control and treatment")
        configured = {}

    for condition in VALID_CONDITIONS:
        expected = identities.get(condition)
        actual = configured.get(condition)
        if not isinstance(expected, dict) or not isinstance(actual, dict):
            errors.append(f"{condition}: missing identity or frozen condition")
            continue
        for field in ("condition", "source_commit", "prompt_path", "prompt_contract_sha"):
            if actual.get(field) != expected.get(field):
                errors.append(f"{condition}: {field} drifted from identities.json")
        prompt_path = ROOT / str(actual.get("prompt_path") or "")
        if not prompt_path.is_file():
            errors.append(f"{condition}: prompt snapshot missing: {prompt_path}")
        elif _prompt_digest(prompt_path) != actual.get("prompt_contract_sha"):
            errors.append(f"{condition}: prompt snapshot hash mismatch")

    pilot = contract.get("pilot")
    if not isinstance(pilot, dict):
        errors.append("missing pilot contract")
        pilot = {}
    if tuple(pilot.get("cases") or ()) != EXPECTED_CASES:
        errors.append("pilot cases must be exactly TC01..TC08")
    if pilot.get("repetitions") != 1:
        errors.append("pilot repetitions must equal 1")
    if pilot.get("conditions") != list(VALID_CONDITIONS):
        errors.append("pilot conditions must be control,treatment")
    if pilot.get("expected_runs") != 16:
        errors.append("pilot expected_runs must equal 16")
    if not str(pilot.get("pair_order_seed") or "").strip():
        errors.append("pilot pair_order_seed must be non-empty")
    if contract.get("runtime_absence_state") != "UNPROVEN_RUNTIME":
        errors.append("runtime absence must remain UNPROVEN_RUNTIME")

    if errors:
        raise ValueError("; ".join(errors))
    return contract


def resolve(condition: str) -> dict[str, Any]:
    normalized = condition.lower().strip()
    if normalized not in VALID_CONDITIONS:
        raise ValueError(f"unknown condition: {condition!r}")
    return dict(validate_conditions()["conditions"][normalized])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", choices=VALID_CONDITIONS)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    contract = validate_conditions()
    payload: dict[str, Any]
    if args.condition:
        payload = resolve(args.condition)
    else:
        payload = {
            "status": "PASS",
            "study_id": contract["study_id"],
            "conditions": list(VALID_CONDITIONS),
            "pilot_runs": contract["pilot"]["expected_runs"],
            "runtime_absence_state": contract["runtime_absence_state"],
        }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.summary or not args.output:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
