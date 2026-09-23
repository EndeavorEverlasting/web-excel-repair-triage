#!/usr/bin/env python3
"""Validate the typed P143 -> P55/integration bootstrap handoff."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
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


def _repo_path(value: Any, label: str) -> tuple[str, Path]:
    relative = _text(value, label).replace("\\", "/")
    if relative.startswith("/") or relative.startswith("../") or "/../" in f"/{relative}/":
        raise HandoffError(f"{label} must stay inside the repository")
    full = (ROOT / relative).resolve()
    try:
        full.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise HandoffError(f"{label} escapes the repository") from exc
    return relative, full


def _tracked(relative: str) -> bool:
    proc = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=ROOT,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.returncode == 0


def _validate_plan_artifact(plan: dict[str, Any], contract: dict[str, Any]) -> None:
    for field in ("repository", "ref", "path", "write_authority"):
        _text(plan.get(field), f"plan_artifact.{field}")
    if plan["write_authority"] not in contract["plan_write_authorities"]:
        raise HandoffError(f"invalid plan_artifact.write_authority: {plan['write_authority']!r}")
    proof = plan.get("proof")
    if not isinstance(proof, dict):
        raise HandoffError("plan_artifact.proof must be an object")
    kind = _text(proof.get("kind"), "plan_artifact.proof.kind")
    evidence_relative, evidence_full = _repo_path(
        proof.get("evidence_path"), "plan_artifact.proof.evidence_path"
    )
    if not evidence_full.is_file() or not _tracked(evidence_relative):
        raise HandoffError("plan_artifact proof evidence must exist and be tracked")

    if kind == "LOCAL_TRACKED_FILE":
        if plan["repository"] != ".":
            raise HandoffError("LOCAL_TRACKED_FILE requires plan_artifact.repository '.'")
        path_relative, path_full = _repo_path(plan["path"], "plan_artifact.path")
        if evidence_relative != path_relative:
            raise HandoffError("LOCAL_TRACKED_FILE evidence_path must equal plan_artifact.path")
        if not path_full.is_file() or not _tracked(path_relative):
            raise HandoffError("LOCAL_TRACKED_FILE plan artifact must exist and be tracked")
        if not os.access(path_full, os.W_OK):
            raise HandoffError("LOCAL_TRACKED_FILE plan artifact is not writable")
        return

    if kind == "PROVIDER_RECEIPT":
        receipt = _load(evidence_full)
        if receipt.get("schema_version") != contract["provider_receipt_schema"]:
            raise HandoffError("unsupported repository write receipt schema")
        for field in ("repository", "ref", "path", "observed_revision"):
            _text(receipt.get(field), f"provider_receipt.{field}")
        if not re.fullmatch(r"[0-9a-f]{40}", receipt["observed_revision"]):
            raise HandoffError("provider_receipt.observed_revision must be a 40-hex commit")
        if receipt.get("writable") is not True:
            raise HandoffError("provider receipt does not prove writable=true")
        for field in ("repository", "ref", "path"):
            if receipt[field] != plan[field]:
                raise HandoffError(f"provider receipt {field} does not match plan_artifact")
        return

    raise HandoffError(f"unsupported plan_artifact.proof.kind: {kind!r}")


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
    _validate_plan_artifact(plan, contract)

    donors = manifest["donors"]
    if not isinstance(donors, list) or len(donors) < 2:
        raise HandoffError("donors must contain at least two pinned repositories")
    for index, donor in enumerate(donors):
        if not isinstance(donor, dict):
            raise HandoffError(f"donors[{index}] must be an object")
        for field in ("repository", "ref", "sha"):
            _text(donor.get(field), f"donors[{index}].{field}")
        if not re.fullmatch(r"[0-9a-f]{40}", donor["sha"]):
            raise HandoffError(f"donors[{index}].sha must be a pinned 40-hex commit")

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
    if (approved or authorized) and not provenance:
        raise HandoffError("asserted authority requires non-empty provenance")

    dispositions = manifest["capability_dispositions"]
    if not isinstance(dispositions, list) or not dispositions:
        raise HandoffError("capability_dispositions must be a non-empty array")
    seen_capabilities: set[str] = set()
    for index, item in enumerate(dispositions):
        if not isinstance(item, dict):
            raise HandoffError(f"capability_dispositions[{index}] must be an object")
        capability = _text(item.get("capability"), f"capability_dispositions[{index}].capability")
        disposition = _text(item.get("disposition"), f"capability_dispositions[{index}].disposition")
        if disposition not in contract["capability_disposition_values"]:
            raise HandoffError(f"invalid capability disposition: {disposition!r}")
        if capability in seen_capabilities:
            raise HandoffError(f"duplicate capability disposition: {capability}")
        seen_capabilities.add(capability)

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
        "mutation_authorized": route != "BLOCKED" and approved and authorized,
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
