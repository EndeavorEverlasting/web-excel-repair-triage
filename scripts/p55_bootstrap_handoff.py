#!/usr/bin/env python3
"""Validate the typed P143 -> P55/integration bootstrap handoff."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness" / "contracts" / "p55-bootstrap-handoff.v1.json"


class HandoffError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HandoffError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HandoffError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise HandoffError(f"expected JSON object: {path}")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HandoffError(f"{label} must be a non-empty string")
    return value.strip()


def _bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise HandoffError(f"{label} must be boolean")
    return value


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    contract = _load(CONTRACT_PATH)
    if manifest.get("schema_version") != contract["manifest_schema"]:
        raise HandoffError("unsupported bootstrap handoff schema")
    for field in contract["required_manifest_fields"]:
        if field not in manifest:
            raise HandoffError(f"manifest missing field: {field}")

    _text(manifest["handoff_id"], "handoff_id")
    _text(manifest["proof_ceiling"], "proof_ceiling")

    plan = manifest["plan_artifact"]
    if not isinstance(plan, dict):
        raise HandoffError("plan_artifact must be an object")
    for field in ("repository", "ref", "path"):
        _text(plan.get(field), f"plan_artifact.{field}")

    donors = manifest["donors"]
    if not isinstance(donors, list) or len(donors) < 2:
        raise HandoffError("donors must contain at least two pinned repositories")
    for index, donor in enumerate(donors):
        if not isinstance(donor, dict):
            raise HandoffError(f"donors[{index}] must be an object")
        for field in ("repository", "ref", "sha"):
            _text(donor.get(field), f"donors[{index}].{field}")

    destination = manifest["destination"]
    if not isinstance(destination, dict):
        raise HandoffError("destination must be an object")
    for field in ("name", "owner", "visibility", "proposal_state", "provider_state"):
        _text(destination.get(field), f"destination.{field}")
    if destination["visibility"] not in contract["visibility_states"]:
        raise HandoffError(f"invalid destination.visibility: {destination['visibility']!r}")
    if destination["proposal_state"] not in contract["proposal_states"]:
        raise HandoffError(f"invalid destination.proposal_state: {destination['proposal_state']!r}")
    provider_state = destination["provider_state"]
    if provider_state not in contract["provider_states"]:
        raise HandoffError(f"invalid destination.provider_state: {provider_state!r}")

    authority = manifest["authority"]
    if not isinstance(authority, dict):
        raise HandoffError("authority must be an object")
    approved = _bool(authority.get("operator_approved"), "authority.operator_approved")
    authorized = _bool(authority.get("execution_authorization"), "authority.execution_authorization")
    provenance = authority.get("provenance")
    if not isinstance(provenance, list) or any(not isinstance(item, str) or not item.strip() for item in provenance):
        raise HandoffError("authority.provenance must be an array of non-empty strings")

    dispositions = manifest["capability_dispositions"]
    if not isinstance(dispositions, list) or not dispositions:
        raise HandoffError("capability_dispositions must be a non-empty array")
    for index, item in enumerate(dispositions):
        if not isinstance(item, dict):
            raise HandoffError(f"capability_dispositions[{index}] must be an object")
        _text(item.get("capability"), f"capability_dispositions[{index}].capability")
        _text(item.get("disposition"), f"capability_dispositions[{index}].disposition")

    route = _text(manifest["route"], "route")
    next_owner = _text(manifest["next_owner"], "next_owner")
    if route not in contract["routes"]:
        raise HandoffError(f"invalid route: {route!r}")

    if route == "P55_CREATE":
        if provider_state != "AVAILABLE":
            raise HandoffError("P55_CREATE requires destination.provider_state AVAILABLE")
        if next_owner != "P55":
            raise HandoffError("P55_CREATE requires next_owner P55")
    elif route == "INTEGRATE_EXISTING":
        if provider_state != "EXISTS_OWNED":
            raise HandoffError("INTEGRATE_EXISTING requires destination.provider_state EXISTS_OWNED")
        if next_owner not in contract["integration_owners"]:
            raise HandoffError("INTEGRATE_EXISTING requires an integration owner")
    else:
        if provider_state in {"AVAILABLE", "EXISTS_OWNED"}:
            raise HandoffError("BLOCKED may not hide an actionable AVAILABLE or EXISTS_OWNED destination")
        if next_owner != "BLOCKED":
            raise HandoffError("BLOCKED requires next_owner BLOCKED")

    return {
        "status": "PASS",
        "route": route,
        "next_owner": next_owner,
        "provider_state": provider_state,
        "operator_approved": approved,
        "execution_authorization": authorized,
        "mutation_authorized": approved and authorized,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    try:
        receipt = validate_manifest(_load(args.manifest))
    except HandoffError as exc:
        print(f"P55_BOOTSTRAP_HANDOFF=FAIL: {exc}")
        return 1
    if args.summary:
        print(
            "P55_BOOTSTRAP_HANDOFF=PASS "
            f"route={receipt['route']} next_owner={receipt['next_owner']} "
            f"provider_state={receipt['provider_state']} "
            f"mutation_authorized={str(receipt['mutation_authorized']).lower()}"
        )
    else:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
