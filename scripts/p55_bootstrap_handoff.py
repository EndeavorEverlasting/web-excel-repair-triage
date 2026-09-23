#!/usr/bin/env python3
"""Validate the typed P143 -> P55/integration bootstrap handoff."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
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


def _instant(value: Any, label: str) -> datetime:
    raw = _text(value, label)
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HandoffError(f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise HandoffError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _git_commit(ref: str) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    value = proc.stdout.strip()
    if proc.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise HandoffError(f"plan_artifact.ref does not resolve to a commit: {ref}")
    return value


def _git_blob(commit: str, relative: str) -> bytes:
    proc = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise HandoffError(
            f"plan_artifact.path is not recoverable from declared ref: {relative}@{commit}"
        )
    return proc.stdout


def _validate_destination_binding(
    evidence: dict[str, Any],
    destination: dict[str, Any],
    *,
    label: str,
    route: str | None = None,
) -> None:
    for field in ("owner", "name"):
        if _text(evidence.get(field), f"{label}.{field}") != destination[field]:
            raise HandoffError(f"{label}.{field} does not match destination.{field}")
    if "visibility" in evidence:
        if _text(evidence.get("visibility"), f"{label}.visibility") != destination["visibility"]:
            raise HandoffError(f"{label}.visibility does not match destination.visibility")
    if route is not None:
        if _text(evidence.get("route"), f"{label}.route") != route:
            raise HandoffError(f"{label}.route does not match manifest route")


def _validate_provider_evidence(destination: dict[str, Any], contract: dict[str, Any]) -> None:
    state = destination["provider_state"]
    evidence = destination.get("provider_evidence")
    actionable = set(contract["provider_evidence"]["actionable_states"])
    if state not in actionable:
        if evidence is not None:
            if not isinstance(evidence, dict):
                raise HandoffError("destination.provider_evidence must be null or an object")
            _validate_destination_binding(
                evidence, destination, label="destination.provider_evidence"
            )
            if _text(
                evidence.get("provider_state"),
                "destination.provider_evidence.provider_state",
            ) != state:
                raise HandoffError(
                    "destination.provider_evidence.provider_state does not match destination.provider_state"
                )
        return
    if not isinstance(evidence, dict):
        raise HandoffError(f"{state} requires destination-bound provider evidence")
    for field in contract["provider_evidence"]["required_fields"]:
        _text(evidence.get(field), f"destination.provider_evidence.{field}")
    _validate_destination_binding(
        evidence, destination, label="destination.provider_evidence"
    )
    if evidence["provider_state"] != state:
        raise HandoffError(
            "destination.provider_evidence.provider_state does not match destination.provider_state"
        )
    observed = _instant(
        evidence["observed_at"], "destination.provider_evidence.observed_at"
    )
    age = (datetime.now(timezone.utc) - observed).total_seconds()
    maximum_age = int(contract["provider_evidence"]["maximum_age_seconds"])
    if age < -300 or age > maximum_age:
        raise HandoffError(
            f"destination.provider_evidence is stale or future-dated: age_seconds={int(age)}"
        )


def _validate_authority_evidence(
    authority: dict[str, Any],
    destination: dict[str, Any],
    route: str,
    contract: dict[str, Any],
) -> tuple[bool, bool]:
    approved = _bool(
        authority.get("operator_approved"), "authority.operator_approved"
    )
    authorized = _bool(
        authority.get("execution_authorization"), "authority.execution_authorization"
    )
    evidence = authority.get("evidence")
    if not isinstance(evidence, dict):
        raise HandoffError("authority.evidence must be an object")
    for decision, asserted in (
        ("operator_approved", approved),
        ("execution_authorization", authorized),
    ):
        record = evidence.get(decision)
        if not asserted:
            if record is not None:
                raise HandoffError(
                    f"authority.evidence.{decision} must be null when {decision}=false"
                )
            continue
        if not isinstance(record, dict):
            raise HandoffError(
                f"{decision}=true requires authority.evidence.{decision}"
            )
        for field in contract["authority_evidence"]["required_fields"]:
            _text(record.get(field), f"authority.evidence.{decision}.{field}")
        if record["decision"] != decision:
            raise HandoffError(
                f"authority.evidence.{decision}.decision must equal {decision}"
            )
        _validate_destination_binding(
            record,
            destination,
            label=f"authority.evidence.{decision}",
            route=route,
        )
        _instant(
            record["recorded_at"],
            f"authority.evidence.{decision}.recorded_at",
        )
    return approved, authorized


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
        resolved_commit = _git_commit(plan["ref"])
        committed = _git_blob(resolved_commit, path_relative)
        if committed != path_full.read_bytes():
            raise HandoffError(
                "LOCAL_TRACKED_FILE plan artifact does not match the blob at plan_artifact.ref"
            )
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

    _validate_provider_evidence(destination, contract)

    authority = manifest["authority"]
    if not isinstance(authority, dict):
        raise HandoffError("authority must be an object")

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

    approved, authorized = _validate_authority_evidence(
        authority, destination, route, contract
    )

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
        "authority_evidence_complete": approved and authorized,
        "mutation_authorized": False,
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
