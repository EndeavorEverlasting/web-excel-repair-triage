#!/usr/bin/env python3
"""Validate commitment-boundary packets and their cross-record semantics."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness" / "contracts" / "commitment-boundary.v1.json"

ALLOWED_ASSERTIONS = {
    "INTERNAL_TARGET": {"INTERNAL_TARGET", "NONCOMMITTAL_STATUS"},
    "ESTIMATE": {"ESTIMATE", "NONCOMMITTAL_STATUS"},
    "EXTERNAL_CONSTRAINT": {"EXTERNAL_CONSTRAINT", "NONCOMMITTAL_STATUS"},
    "EXTERNAL_COMMITMENT": {"EXTERNAL_COMMITMENT", "NONCOMMITTAL_STATUS"},
}


class CommitmentBoundaryError(ValueError):
    """Raised when a packet violates the commitment boundary."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CommitmentBoundaryError(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise CommitmentBoundaryError(f"JSON root must be an object: {path}")
    return payload


def validate_contract_schema(contract: dict[str, Any]) -> None:
    try:
        Draft202012Validator.check_schema(contract)
    except SchemaError as exc:
        raise CommitmentBoundaryError(
            f"invalid contract schema: {exc.message}"
        ) from exc


def load_contract() -> dict[str, Any]:
    contract = load_json(CONTRACT)
    validate_contract_schema(contract)
    if contract.get("$id") != "commitment-boundary/v1":
        raise CommitmentBoundaryError("commitment boundary schema identity drift")
    if contract.get("schema_version") != "commitment-boundary/v1":
        raise CommitmentBoundaryError("commitment boundary schema version drift")
    return contract


def canonical_packet() -> dict[str, Any]:
    return {
        "schema_version": "commitment-boundary/v1",
        "communication_scope": "EXTERNAL",
        "facts": [
            {
                "fact_id": "internal-arrival-target",
                "kind": "INTERNAL_TARGET",
                "value": "11:00 AM",
                "authority_class": "INTERNAL_PLANNING",
                "evidence_ref": "internal-plan:south-brooklyn-buffer",
                "externally_material": False,
            },
            {
                "fact_id": "delivery-window",
                "kind": "EXTERNAL_COMMITMENT",
                "value": "11:30 AM-12:00 PM",
                "authority_class": "RECIPIENT_CONFIRMED",
                "evidence_ref": "recipient-confirmation:south-brooklyn-delivery-window",
                "externally_material": True,
            },
        ],
        "claims": [
            {
                "claim_id": "assembly-during-delivery",
                "source_ref": "delivery-window",
                "asserted_kind": "EXTERNAL_COMMITMENT",
                "text": "Our technicians will assemble on-site during delivery.",
            }
        ],
    }


def validate_packet(
    packet: dict[str, Any],
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    contract = load_contract() if contract is None else contract
    validator = Draft202012Validator(contract)
    schema_errors = sorted(
        validator.iter_errors(packet),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if schema_errors:
        rendered = "; ".join(error.message for error in schema_errors[:5])
        raise CommitmentBoundaryError(f"schema validation failed: {rendered}")

    facts = packet["facts"]
    facts_by_id: dict[str, dict[str, Any]] = {}
    for fact in facts:
        fact_id = fact["fact_id"]
        if fact_id in facts_by_id:
            raise CommitmentBoundaryError(
                f"duplicate fact_id makes source resolution ambiguous: {fact_id}"
            )
        facts_by_id[fact_id] = fact

    claim_ids: set[str] = set()
    for claim in packet["claims"]:
        claim_id = claim["claim_id"]
        if claim_id in claim_ids:
            raise CommitmentBoundaryError(f"duplicate claim_id: {claim_id}")
        claim_ids.add(claim_id)

        source_ref = claim["source_ref"]
        source = facts_by_id.get(source_ref)
        if source is None:
            raise CommitmentBoundaryError(
                f"claim {claim_id} references missing fact: {source_ref}"
            )

        source_kind = source["kind"]
        asserted_kind = claim["asserted_kind"]
        allowed = ALLOWED_ASSERTIONS[source_kind]
        if asserted_kind not in allowed:
            raise CommitmentBoundaryError(
                f"claim {claim_id} promotes {source_kind} to {asserted_kind}"
            )

        if (
            packet["communication_scope"] == "EXTERNAL"
            and asserted_kind == "INTERNAL_TARGET"
            and not source["externally_material"]
        ):
            raise CommitmentBoundaryError(
                f"claim {claim_id} exposes a non-material internal target externally"
            )

    return {
        "status": "PASS",
        "schema_version": contract["schema_version"],
        "facts": len(facts),
        "claims": len(packet["claims"]),
        "semantic_validator": "scripts/validate_commitment_boundary.py",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    try:
        contract = load_contract()
        packet = load_json(args.input) if args.input else canonical_packet()
        result = validate_packet(packet, contract)
    except CommitmentBoundaryError as exc:
        print(f"commitment-boundary: FAIL: {exc}", file=sys.stderr)
        return 1

    if args.summary:
        print(
            "commitment-boundary: PASS "
            f"facts={result['facts']} claims={result['claims']} "
            "referential_integrity=PASS authority_typing=PASS non_promotion=PASS"
        )
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
