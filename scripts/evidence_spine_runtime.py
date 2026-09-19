#!/usr/bin/env python3
"""Deterministic Evidence Spine continuation resolver (P95 adapter-only seam)."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness/contracts/evidence-spine-continuation.v1.json"
DISPOSITIONS = ("continue", "recover", "complete", "blocked")
ROUTE_RECEIPT_SCHEMA = "evidence-spine-route-receipt/v1"
PROMPT_ID_RE = re.compile(r"^P[0-9]{2,3}$")
ROUTE_PROVENANCE = {"observed", "declared", "inferred", "unknown"}
ROUTE_FIELDS = {
    "prompt_id",
    "prompt_revision",
    "destination",
    "provenance",
    "surface_id",
    "invocation_id",
    "run_id",
}


class ContinuationError(ValueError):
    pass


def load_contract() -> dict[str, Any]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if contract.get("schema_version") != "evidence-spine-continuation-disposition/v1":
        raise ContinuationError("unsupported continuation contract")
    return contract


def _fingerprint(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def resolve_continuation(evidence: dict[str, Any]) -> dict[str, Any]:
    """Resolve next_action disposition from correlated evidence.

    Expected keys (all optional except that recovery/required gates win):
    - open_recovery: bool
    - required_work_remaining: bool
    - agent_completion_candidate: bool
    - user_only_blocker: str | None
    - outcome_receipts: list (opaque; presence only)
    """
    load_contract()
    if not isinstance(evidence, dict):
        raise ContinuationError("evidence must be an object")

    user_blocker = evidence.get("user_only_blocker")
    if isinstance(user_blocker, str) and user_blocker.strip():
        disposition = "blocked"
        rationale = f"user-only gate: {user_blocker.strip()}"
    elif evidence.get("open_recovery") is True:
        disposition = "recover"
        rationale = "open recovery/required gate supersedes completion candidate"
    elif evidence.get("required_work_remaining") is True:
        disposition = "continue"
        rationale = "required owned work remains"
    elif evidence.get("agent_completion_candidate") is True:
        disposition = "complete"
        rationale = "required gates clear; agent completion candidate accepted"
    else:
        disposition = "continue"
        rationale = "no terminal claim; continue safe owned work"

    if disposition not in DISPOSITIONS:
        raise ContinuationError(f"invalid disposition: {disposition}")

    body = {
        "schema_version": "evidence-spine-continuation-disposition/v1",
        "disposition": disposition,
        "rationale": rationale,
        "completion_candidate_honored": bool(
            evidence.get("agent_completion_candidate") is True and disposition == "complete"
        ),
        "evidence": {
            "open_recovery": bool(evidence.get("open_recovery")),
            "required_work_remaining": bool(evidence.get("required_work_remaining")),
            "agent_completion_candidate": bool(evidence.get("agent_completion_candidate")),
            "outcome_receipt_count": len(evidence.get("outcome_receipts") or []),
        },
    }
    body["input_fingerprint"] = _fingerprint(body["evidence"])
    return body


def classify_route_destination(
    *,
    destination: str | None,
    provenance: str,
) -> dict[str, Any]:
    """Lane A helper: never promote inferred destination to authoritative."""
    allowed = {"observed", "declared", "inferred", "unknown"}
    if provenance not in allowed:
        raise ContinuationError(f"invalid destination provenance: {provenance}")
    dest = (destination or "").strip()
    if provenance == "inferred":
        return {
            "destination": dest or None,
            "provenance": "inferred",
            "authoritative": False,
            "effective_destination": "unknown",
        }
    if provenance == "unknown" or not dest:
        return {
            "destination": dest or None,
            "provenance": "unknown",
            "authoritative": False,
            "effective_destination": "unknown",
        }
    return {
        "destination": dest,
        "provenance": provenance,
        "authoritative": provenance == "observed",
        "effective_destination": dest if provenance == "observed" else dest,
    }


def build_route_receipt(route: dict[str, Any]) -> dict[str, Any]:
    """Build one actor-neutral, deterministic route receipt.

    This is the P95-admitted Lane A seam. It records route provenance without
    mutating route state, consulting outcome/recovery owners, or trusting a
    caller-provided idempotency key/fingerprint.
    """
    if not isinstance(route, dict):
        raise ContinuationError("route must be an object")

    extras = sorted(set(route) - ROUTE_FIELDS)
    if extras:
        raise ContinuationError(f"route contains unsupported fields: {extras}")

    prompt_id = route.get("prompt_id")
    if not isinstance(prompt_id, str) or not PROMPT_ID_RE.fullmatch(prompt_id):
        raise ContinuationError("prompt_id must match P[0-9]{2,3}")

    prompt_revision = route.get("prompt_revision")
    if not isinstance(prompt_revision, str) or not prompt_revision.strip():
        raise ContinuationError("prompt_revision must be a non-empty string")

    surface_id = route.get("surface_id")
    if not isinstance(surface_id, str) or not surface_id.strip():
        raise ContinuationError("surface_id must be a non-empty string")

    provenance = route.get("provenance")
    if provenance not in ROUTE_PROVENANCE:
        raise ContinuationError(f"invalid destination provenance: {provenance}")

    destination = route.get("destination")
    if destination is not None and not isinstance(destination, str):
        raise ContinuationError("destination must be null or a string")
    normalized_destination = (destination or "").strip() or None

    if provenance in {"observed", "declared"} and normalized_destination is None:
        raise ContinuationError(f"{provenance} route requires destination")
    if provenance == "unknown" and normalized_destination is not None:
        raise ContinuationError("unknown route must not carry destination")

    for field in ("invocation_id", "run_id"):
        value = route.get(field)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ContinuationError(f"{field} must be null or a non-empty string")

    classified = classify_route_destination(
        destination=normalized_destination,
        provenance=provenance,
    )
    confidence = {
        "observed": "authoritative",
        "declared": "declared",
        "inferred": "inferred",
        "unknown": "unknown",
    }[provenance]

    semantic = {
        "prompt_id": prompt_id,
        "prompt_revision": prompt_revision.strip(),
        "surface_id": surface_id.strip(),
        "destination": classified["destination"],
        "provenance": classified["provenance"],
        "destination_confidence": confidence,
        "authoritative": classified["authoritative"],
        "effective_destination": (
            classified["effective_destination"] if classified["authoritative"] else "unknown"
        ),
        "invocation_id": route.get("invocation_id"),
        "run_id": route.get("run_id"),
    }
    semantic_sha256 = _fingerprint(semantic)
    return {
        "schema_version": ROUTE_RECEIPT_SCHEMA,
        "route_id": f"route_{semantic_sha256}",
        "semantic_sha256": semantic_sha256,
        **semantic,
    }


def accept_observation_event(event: dict[str, Any]) -> dict[str, Any]:
    """Lane B helper: reject raw content fields; ordinary usage is not failure."""
    if not isinstance(event, dict):
        raise ContinuationError("observation event must be an object")
    forbidden = (
        "raw_prompt",
        "raw_response",
        "clipboard",
        "transcript",
        "query_text",
        "session_identity",
    )
    present = [key for key in forbidden if key in event and event[key] not in (None, "", [])]
    if present:
        return {"accepted": False, "reason": "privacy_rejected", "rejected_fields": present}
    kind = str(event.get("kind") or "usage")
    return {
        "accepted": True,
        "kind": kind,
        "is_failure": False,
        "prompt_id": event.get("prompt_id"),
        "provenance": event.get("provenance") or "observed",
    }


# Owner-specific recurrence thresholds from architecture §8 / Panel 3 brief.
OWNER_THRESHOLDS = {
    "deterministic_contradiction": 1,
    "repeated_local_pattern": 3,
    "manual_context_transfer": 2,
    "correction_not_integrated": 2,
    "premature_terminal": 1,  # plus successor observed separately
    "generic": 3,
}


def aggregate_recurrence(occurrences: list[dict[str, Any]]) -> dict[str, Any]:
    """Lane C helper: group by contract_failure_id; apply thresholds."""
    if not isinstance(occurrences, list):
        raise ContinuationError("occurrences must be a list")
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in occurrences:
        if not isinstance(item, dict):
            raise ContinuationError("occurrence must be an object")
        key = str(item.get("contract_failure_id") or "").strip()
        if not key:
            raise ContinuationError("contract_failure_id required")
        groups.setdefault(key, []).append(item)

    findings = []
    for failure_id, items in sorted(groups.items()):
        kind = str(items[0].get("failure_kind") or "generic")
        threshold = OWNER_THRESHOLDS.get(kind, OWNER_THRESHOLDS["generic"])
        count = len(items)
        if count < 1:
            continue
        if count >= threshold:
            state = "confirmed_recurrence"
        elif count == 1:
            state = "evidence_only"
        else:
            state = "suspected_recurrence"
        if any(bool(i.get("post_fix")) for i in items) and state != "evidence_only":
            state = "monitoring_reopened"
        findings.append(
            {
                "contract_failure_id": failure_id,
                "failure_kind": kind,
                "count": count,
                "threshold": threshold,
                "state": state,
                "receipt_ids": [i.get("receipt_id") for i in items if i.get("receipt_id")],
            }
        )
    return {"findings": findings}


def compile_work_request(finding: dict[str, Any]) -> dict[str, Any] | None:
    """Compile P115-compatible work request only when fully bounded."""
    required = (
        "remediation_owner",
        "observed_behavior",
        "expected_behavior",
        "acceptance_criteria",
        "proof_requirements",
    )
    if finding.get("state") not in {"confirmed_recurrence", "monitoring_reopened"}:
        return None
    missing = [k for k in required if not str(finding.get(k) or "").strip()]
    if missing:
        return {
            "compiled": False,
            "reason": "incomplete_ticket_inputs",
            "missing": missing,
        }
    return {
        "compiled": True,
        "schema_version": "evidence-spine-p115-work-request/v1",
        "remediation_owner": finding["remediation_owner"],
        "contract_failure_id": finding.get("contract_failure_id"),
        "linked_receipt_ids": finding.get("receipt_ids") or [],
        "observed_behavior": finding["observed_behavior"],
        "expected_behavior": finding["expected_behavior"],
        "acceptance_criteria": finding["acceptance_criteria"],
        "proof_requirements": finding["proof_requirements"],
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_res = sub.add_parser("resolve")
    p_res.add_argument("--evidence", required=True, help="Path to evidence JSON")
    args = parser.parse_args(argv)
    if args.cmd == "resolve":
        evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
        print(json.dumps(resolve_continuation(evidence), indent=2, sort_keys=True))
        return 0
    raise ContinuationError(f"unknown command: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
