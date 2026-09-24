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
DEFAULT_GENERATION = "v1"
GENERATIONS = {
    "v1": {
        "conditions": EVAL / "runtime" / "conditions.v1.json",
        "identities": EVAL / "prompts" / "identities.json",
    },
    "v2": {
        "conditions": EVAL / "runtime" / "conditions.v2.json",
        "identities": EVAL / "prompts" / "gen2" / "identities.json",
    },
}
# Backward-compatible default (generation v1) locators.
CONDITIONS = GENERATIONS[DEFAULT_GENERATION]["conditions"]
IDENTITIES = GENERATIONS[DEFAULT_GENERATION]["identities"]
VALID_CONDITIONS = ("control", "treatment")
EXPECTED_CASES = tuple(f"TC{i:02d}" for i in range(1, 9))


def normalize_generation(generation: str | None) -> str:
    token = (generation or DEFAULT_GENERATION).lower().strip()
    token = {"gen1": "v1", "gen2": "v2", "1": "v1", "2": "v2"}.get(token, token)
    if token not in GENERATIONS:
        raise ValueError(f"unknown generation: {generation!r}")
    return token


def _json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object: {path}")
    return payload


def _prompt_digest(path: Path) -> str:
    body = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def validate_conditions(generation: str = DEFAULT_GENERATION) -> dict[str, Any]:
    generation = normalize_generation(generation)
    spec = GENERATIONS[generation]
    contract = _json(spec["conditions"])
    identities = _json(spec["identities"])
    errors: list[str] = []

    if contract.get("schema_version") != "compute-authority-conditions/v1":
        errors.append("unexpected conditions schema_version")
    if contract.get("study_id") != "prompt-kit-compute-authority":
        errors.append("unexpected study_id")
    if contract.get("frozen") is not True:
        errors.append("conditions must be frozen")
    if contract.get("generation", DEFAULT_GENERATION) != generation:
        errors.append("conditions generation mismatch")
    if identities.get("generation", DEFAULT_GENERATION) != generation:
        errors.append("identities generation mismatch")

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


def resolve(condition: str, generation: str = DEFAULT_GENERATION) -> dict[str, Any]:
    normalized = condition.lower().strip()
    if normalized not in VALID_CONDITIONS:
        raise ValueError(f"unknown condition: {condition!r}")
    return dict(validate_conditions(generation)["conditions"][normalized])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", choices=VALID_CONDITIONS)
    parser.add_argument("--generation", choices=sorted(GENERATIONS), default=DEFAULT_GENERATION)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    contract = validate_conditions(args.generation)
    payload: dict[str, Any]
    if args.condition:
        payload = resolve(args.condition, args.generation)
    else:
        payload = {
            "status": "PASS",
            "study_id": contract["study_id"],
            "generation": normalize_generation(args.generation),
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
