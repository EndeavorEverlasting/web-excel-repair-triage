#!/usr/bin/env python3
"""Deterministic AFK Agent Flow prompt-routing control plane.

A prompt route is a backend state transition. Human-facing presentation is optional
metadata over the same canonical transition used by agents, classifiers, scripts,
and workflows.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "harness/contracts/operant-prompt-routing.v1.json"
SCHEMA_VERSION = "prompt-route-receipt/v1"

ROUTED = "ROUTED"
NON_MUTATING_STATUSES = {
    "IDEMPOTENT_NOOP",
    "ALREADY_AT_TARGET",
    "BLOCKED",
    "HUMAN_GATE_REQUIRED",
    "AUTONOMY_GAP",
    "PROMPT_NOT_FOUND",
    "PROMPT_INACTIVE",
    "STALE_REJECTED",
    "PRECEDENCE_REJECTED",
    "SUPERSEDED",
    "POLICY_REJECTED",
    "PARTIAL_TRUTH",
    "ERROR",
}


class RouteError(ValueError):
    """Fail-closed prompt routing contract error."""


@dataclass(frozen=True)
class RouteState:
    current_prompt_id: str | None
    version: int

    def __post_init__(self) -> None:
        if self.version < 0:
            raise RouteError("route state version cannot be negative")


class RouteLedger:
    """In-memory idempotency ledger used by the deterministic router.

    Durable callers may persist these records elsewhere, but the semantic key stays
    `(scope, idempotency_key)` and the stored fingerprint remains authoritative.
    """

    def __init__(self) -> None:
        self._by_key: dict[tuple[str, str], dict[str, Any]] = {}

    @staticmethod
    def key(receipt: dict[str, Any]) -> tuple[str, str]:
        return (
            str(receipt["idempotency"]["scope"]),
            str(receipt["request"]["idempotency_key"]),
        )

    def get(self, receipt: dict[str, Any]) -> dict[str, Any] | None:
        value = self._by_key.get(self.key(receipt))
        return copy.deepcopy(value) if value is not None else None

    def record(self, receipt: dict[str, Any]) -> None:
        key = self.key(receipt)
        self._by_key[key] = {
            "receipt_id": receipt["receipt_id"],
            "request_fingerprint": receipt["request"]["request_fingerprint"],
            "route_status": receipt["route"]["status"],
            "resolved_prompt_id": receipt["target"].get("resolved_prompt_id"),
        }


def _canonical_json_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def resolve_canonical_target(prompt_id: str) -> tuple[dict[str, Any], str]:
    """Resolve one prompt through the same combined registry used by the generated product.

    Returns `(target_binding, registry_digest)`. Missing IDs fail closed as an
    unresolved binding rather than guessing a neighboring prompt.
    """
    normalized = str(prompt_id or "").strip().upper()
    if not normalized:
        raise RouteError("prompt ID is required for canonical resolution")
    try:
        builder = importlib.import_module("scripts.build_prompt_kit_registry")
        prompts = builder.load_prompt_kit_registry()
    except (ImportError, SystemExit, OSError, ValueError) as exc:
        raise RouteError(f"cannot load canonical Prompt Kit registry: {exc}") from exc
    if not isinstance(prompts, list) or not prompts:
        raise RouteError("canonical Prompt Kit registry is empty")
    registry_projection = [
        {"id": str(item.get("id", "")), "seq": str(item.get("seq", "")), "copyContent": str(item.get("copyContent", ""))}
        for item in prompts
    ]
    registry_digest = _canonical_json_digest(registry_projection)
    found = next((item for item in prompts if str(item.get("id", "")).upper() == normalized), None)
    if found is None:
        return ({
            "requested_prompt_id": normalized,
            "resolved_prompt_id": None,
            "canonical": False,
            "active": False,
            "resolution": "unresolved",
            "prompt_digest": None,
        }, registry_digest)
    canonical_id = str(found["id"])
    return ({
        "requested_prompt_id": str(prompt_id).strip(),
        "resolved_prompt_id": canonical_id,
        "canonical": True,
        "active": True,
        "resolution": "exact_id" if str(prompt_id).strip() == canonical_id else "normalized_id",
        "prompt_digest": _canonical_json_digest(found),
    }, registry_digest)


def validate_repository_binding(receipt: dict[str, Any]) -> None:
    """Verify target and registry digests against current canonical repository truth."""
    target = receipt.get("target") or {}
    requested = target.get("requested_prompt_id")
    resolved, registry_digest = resolve_canonical_target(str(requested or ""))
    if receipt.get("repository", {}).get("registry_digest") != registry_digest:
        raise RouteError("route receipt registry digest does not match canonical registry")
    for field in ("resolved_prompt_id", "canonical", "active", "resolution", "prompt_digest"):
        if target.get(field) != resolved.get(field):
            raise RouteError(f"route receipt target binding drifted from canonical registry: {field}")


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RouteError(f"cannot load prompt routing policy: {exc}") from exc
    if payload.get("schema_version") != "operant-prompt-routing/v1":
        raise RouteError("unsupported prompt routing policy schema")
    return payload


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RouteError(f"{label} must be an object")
    return value


def _require_keys(value: dict[str, Any], keys: Iterable[str], label: str) -> None:
    missing = [key for key in keys if key not in value]
    if missing:
        raise RouteError(f"{label} missing required fields: {', '.join(missing)}")


def validate_receipt(
    receipt: dict[str, Any],
    policy: dict[str, Any] | None = None,
    *,
    final: bool = True,
) -> None:
    """Validate v1 structure; enforce terminal outcome invariants only for final receipts."""
    policy = policy or load_policy()
    if not isinstance(receipt, dict):
        raise RouteError("route receipt must be an object")
    if receipt.get("schema_version") != SCHEMA_VERSION:
        raise RouteError("unsupported prompt route receipt schema")

    required_top = (
        "receipt_id", "created_at", "repository", "request", "actor", "source",
        "target", "decision", "precedence", "gates", "route", "presentation",
        "idempotency", "autonomy", "evidence", "outcome",
    )
    _require_keys(receipt, required_top, "route receipt")

    for key in ("repository", "request", "actor", "source", "target", "decision",
                "precedence", "gates", "route", "presentation", "idempotency",
                "autonomy", "evidence", "outcome"):
        _require_mapping(receipt[key], key)

    actor = receipt["actor"]
    if actor.get("type") not in {"human", "agent", "classifier", "script", "workflow"}:
        raise RouteError(f"unsupported actor type: {actor.get('type')!r}")
    allowed_classes = policy.get("authority_classes", {})
    authority_class = actor.get("authority_class")
    if authority_class not in allowed_classes:
        raise RouteError(f"unknown authority class: {authority_class!r}")
    expected_rank = int(allowed_classes[authority_class]["rank"])
    if receipt["precedence"].get("authority_rank") != expected_rank:
        raise RouteError(
            f"authority rank drift for {authority_class}: "
            f"expected={expected_rank} actual={receipt['precedence'].get('authority_rank')}"
        )

    if actor["type"] == "human" and actor.get("human_present") is not True:
        raise RouteError("human actor must record human_present=true")
    if actor["type"] != "human" and actor.get("human_present") not in {False, True}:
        raise RouteError("human_present must be boolean")

    decision = receipt["decision"]
    priority = decision.get("priority")
    if not isinstance(priority, int) or not 0 <= priority <= 1000:
        raise RouteError("decision.priority must be integer 0..1000")
    if decision.get("decision_source") == "classifier" or actor["type"] == "classifier":
        classifier = decision.get("classifier")
        if not isinstance(classifier, dict):
            raise RouteError("classifier route requires classifier provenance")
        candidates = classifier.get("candidate_prompt_ids")
        if not isinstance(candidates, list) or not candidates:
            raise RouteError("classifier provenance requires candidate_prompt_ids")

    target = receipt["target"]
    requested = target.get("requested_prompt_id")
    if not isinstance(requested, str) or not requested.startswith("P"):
        raise RouteError("requested_prompt_id must be a prompt ID")

    route = receipt["route"]
    status = route.get("status")
    allowed_statuses = set(policy.get("route_statuses", []))
    if status not in allowed_statuses:
        raise RouteError(f"unsupported route status: {status!r}")
    if not isinstance(route.get("changed"), bool):
        raise RouteError("route.changed must be boolean")

    gates = receipt["gates"]
    if gates.get("aggregate") not in set(policy.get("gate_aggregates", [])):
        raise RouteError(f"unsupported gate aggregate: {gates.get('aggregate')!r}")
    if not isinstance(gates.get("mutation_allowed"), bool):
        raise RouteError("gates.mutation_allowed must be boolean")
    if not isinstance(gates.get("results"), list):
        raise RouteError("gates.results must be a list")

    required_gate_outcomes = set(policy.get("required_gate_blocking_outcomes", []))
    for gate in gates["results"]:
        _require_mapping(gate, "gate result")
        if gate.get("classification") == "REQUIRED" and gate.get("outcome") in required_gate_outcomes:
            if gates["mutation_allowed"]:
                raise RouteError("required non-PASS gate cannot allow mutation")

    presentation = receipt["presentation"]
    if presentation.get("applied_mode") == "none":
        for flag in ("prompt_visible", "prompt_opened", "prompt_snapped", "focus_applied"):
            if presentation.get(flag) is not False:
                raise RouteError(f"presentation {flag} must be false when applied_mode=none")
    if presentation.get("surface") == "headless":
        if presentation.get("requested_mode") != "none" or presentation.get("applied_mode") != "none":
            raise RouteError("headless routes cannot request or apply UI presentation")

    idempotency = receipt["idempotency"]
    if idempotency.get("scope") not in {"request", "session", "run", "candidate", "global"}:
        raise RouteError("unsupported idempotency scope")
    if not isinstance(idempotency.get("duplicate"), bool):
        raise RouteError("idempotency.duplicate must be boolean")

    autonomy = receipt["autonomy"]
    if autonomy.get("status") not in {"PASS", "DEGRADED", "FAIL"}:
        raise RouteError("unsupported autonomy status")
    if not isinstance(autonomy.get("human_dependency"), bool):
        raise RouteError("autonomy.human_dependency must be boolean")
    if autonomy.get("human_dependency") and autonomy.get("status") == "PASS":
        raise RouteError("human-dependent route cannot claim autonomy PASS")

    evidence = receipt["evidence"]
    if evidence.get("gold_eval_authority") is not False:
        raise RouteError("routing receipts never have gold eval authority")
    if evidence.get("raw_user_content_stored") is not False:
        raise RouteError("durable route receipts cannot store raw user content")

    if final:
        if status == ROUTED:
            if target.get("canonical") is not True or target.get("active") is not True:
                raise RouteError("ROUTED requires active canonical target")
            if target.get("resolved_prompt_id") is None:
                raise RouteError("ROUTED requires resolved prompt ID")
            if gates.get("aggregate") != "PASS" or gates.get("mutation_allowed") is not True:
                raise RouteError("ROUTED requires passing mutation gate")
            before = route.get("route_version_before")
            after = route.get("route_version_after")
            if not isinstance(before, int) or not isinstance(after, int) or after != before + 1:
                raise RouteError("ROUTED must advance route version by exactly one")
            if route.get("changed") is not True:
                raise RouteError("ROUTED must record changed=true")
        elif status in NON_MUTATING_STATUSES:
            if route.get("changed") is not False:
                raise RouteError(f"{status} must record changed=false")
            before = route.get("route_version_before")
            after = route.get("route_version_after")
            if isinstance(before, int) and isinstance(after, int) and after != before:
                raise RouteError(f"{status} cannot advance route version")

        if status == "STALE_REJECTED" and receipt["precedence"].get("compare_and_set") != "STALE":
            raise RouteError("STALE_REJECTED requires compare_and_set=STALE")
        if status == "IDEMPOTENT_NOOP":
            if idempotency.get("duplicate") is not True or not idempotency.get("original_receipt_id"):
                raise RouteError("IDEMPOTENT_NOOP requires original duplicate receipt")
        if status in {"HUMAN_GATE_REQUIRED", "AUTONOMY_GAP"}:
            if autonomy.get("human_dependency") is not True or autonomy.get("status") != "FAIL":
                raise RouteError("human dependency must be represented as autonomy failure")


def _nonmutating(
    receipt: dict[str, Any],
    state: RouteState,
    *,
    status: str,
    reason_code: str,
    message: str,
    blocking: bool,
    next_action: str | None = None,
) -> tuple[dict[str, Any], RouteState]:
    result = copy.deepcopy(receipt)
    result["decision"]["reason_code"] = reason_code
    result["route"].update(
        {
            "status": status,
            "route_version_before": state.version,
            "route_version_after": state.version,
            "changed": False,
        }
    )
    result["gates"]["mutation_allowed"] = False
    result["outcome"].update(
        {
            "code": status,
            "message": message,
            "blocking": blocking,
            "next_action": next_action,
        }
    )
    return result, state


def _replay_result(original_status: str) -> tuple[str, bool]:
    if original_status in {"ROUTED", "ALREADY_AT_TARGET", "IDEMPOTENT_NOOP"}:
        return "NOOP_ALREADY_APPLIED", False
    if original_status in {"BLOCKED", "HUMAN_GATE_REQUIRED", "AUTONOMY_GAP"}:
        return "ORIGINAL_BLOCKED", True
    return "ORIGINAL_FAILED", True


def _human_required_gate(receipt: dict[str, Any]) -> dict[str, Any] | None:
    for gate in receipt["gates"].get("results", []):
        if gate.get("classification") == "REQUIRED" and gate.get("outcome") == "HUMAN_REQUIRED":
            return gate
    return None


def _finalize(
    result: dict[str, Any],
    state: RouteState,
    ledger: RouteLedger,
    policy: dict[str, Any],
    *,
    record: bool = True,
) -> tuple[dict[str, Any], RouteState]:
    validate_receipt(result, policy, final=True)
    if record:
        ledger.record(result)
    return result, state


def evaluate_route(
    receipt: dict[str, Any],
    *,
    state: RouteState,
    ledger: RouteLedger,
    policy: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], RouteState]:
    policy = policy or load_policy()
    candidate = copy.deepcopy(receipt)
    validate_receipt(candidate, policy, final=False)

    existing = ledger.get(candidate)
    if existing is not None:
        if existing["request_fingerprint"] != candidate["request"]["request_fingerprint"]:
            result, unchanged = _nonmutating(
                candidate,
                state,
                status="POLICY_REJECTED",
                reason_code="IDEMPOTENCY_KEY_REUSE_MISMATCH",
                message="Idempotency key was reused for a materially different route request.",
                blocking=True,
                next_action="ISSUE_NEW_IDEMPOTENCY_KEY",
            )
            result["idempotency"].update(
                {"duplicate": True, "original_receipt_id": existing["receipt_id"], "replay_result": "ORIGINAL_FAILED"}
            )
            result["autonomy"].update({"status": "FAIL", "failure_class": "ROUTING_CONTRACT_VIOLATION"})
            return _finalize(result, unchanged, ledger, policy)

        replay_result, blocking = _replay_result(existing["route_status"])
        result, unchanged = _nonmutating(
            candidate,
            state,
            status="IDEMPOTENT_NOOP",
            reason_code="IDEMPOTENT_REPLAY",
            message="Logical route request was already processed; no second mutation was applied.",
            blocking=blocking,
            next_action=None if not blocking else "ISSUE_NEW_ROUTE_REQUEST_AFTER_REMEDIATION",
        )
        result["idempotency"].update(
            {"duplicate": True, "original_receipt_id": existing["receipt_id"], "replay_result": replay_result}
        )
        result["autonomy"].update({"status": "PASS" if not blocking else "FAIL", "failure_class": None if not blocking else "PRIOR_ROUTE_BLOCKED"})
        return _finalize(result, unchanged, ledger, policy)

    human_gate = _human_required_gate(candidate)
    if human_gate is not None:
        dependency_class = human_gate.get("dependency_class", "UNIMPLEMENTED_AUTOMATION")
        remediation = human_gate.get("remediation_prompt_id") or policy["autonomy_policy"]["default_prototype_prompt_id"]
        status = (
            "HUMAN_GATE_REQUIRED"
            if dependency_class == "IRREDUCIBLE_EXTERNAL_AUTHORITY"
            else "AUTONOMY_GAP"
        )
        next_action = (
            f"AUTOMATE_OR_PROTOTYPE_GATE:{human_gate.get('gate_id')}:{remediation}"
            if status == "AUTONOMY_GAP"
            else f"PROVE_EXTERNAL_AUTHORITY_OR_AUTOMATE:{human_gate.get('gate_id')}:{remediation}"
        )
        result, unchanged = _nonmutating(
            candidate,
            state,
            status=status,
            reason_code="HUMAN_DEPENDENCY_DETECTED",
            message="Required human involvement is an autonomy failure and cannot be satisfied by mere human presence.",
            blocking=True,
            next_action=next_action,
        )
        result["gates"]["aggregate"] = "HUMAN_REQUIRED"
        result["autonomy"].update(
            {
                "status": "FAIL",
                "human_dependency": True,
                "failure_class": dependency_class,
                "remediation_prompt_id": remediation,
            }
        )
        return _finalize(result, unchanged, ledger, policy)

    required_bad = [
        gate
        for gate in candidate["gates"].get("results", [])
        if gate.get("classification") == "REQUIRED" and gate.get("outcome") != "PASS"
    ]
    if required_bad:
        result, unchanged = _nonmutating(
            candidate,
            state,
            status="BLOCKED",
            reason_code="REQUIRED_GATE_FAILED",
            message=f"Required gate did not pass: {required_bad[0].get('gate_id')}",
            blocking=True,
            next_action=(
                f"ROUTE_REMEDIATION:{required_bad[0].get('remediation_prompt_id')}"
                if required_bad[0].get("remediation_prompt_id")
                else "DERIVE_REPAIR_FROM_VALIDATION_EVIDENCE"
            ),
        )
        result["autonomy"].update({"status": "DEGRADED", "failure_class": "VALIDATION_REPAIR_REQUIRED"})
        return _finalize(result, unchanged, ledger, policy)

    expected = candidate["precedence"].get("expected_state_version")
    if expected is not None and expected != state.version:
        result, unchanged = _nonmutating(
            candidate,
            state,
            status="STALE_REJECTED",
            reason_code="STALE_ROUTE_STATE",
            message=f"Expected route state {expected}, observed {state.version}.",
            blocking=True,
            next_action="REREAD_ROUTE_STATE_AND_RECOMPUTE",
        )
        result["precedence"].update(
            {"observed_state_version": state.version, "compare_and_set": "STALE"}
        )
        result["autonomy"].update({"status": "PASS", "failure_class": None})
        return _finalize(result, unchanged, ledger, policy)

    target = candidate["target"]
    if target.get("resolved_prompt_id") is None or target.get("resolution") == "unresolved":
        result, unchanged = _nonmutating(
            candidate,
            state,
            status="PROMPT_NOT_FOUND",
            reason_code="PROMPT_NOT_FOUND",
            message="Requested prompt could not be resolved in the bound registry.",
            blocking=True,
            next_action="REFRESH_REGISTRY_AND_RECOMPUTE",
        )
        result["autonomy"].update({"status": "FAIL", "failure_class": "REGISTRY_RESOLUTION_FAILURE"})
        return _finalize(result, unchanged, ledger, policy)
    if target.get("active") is not True:
        result, unchanged = _nonmutating(
            candidate,
            state,
            status="PROMPT_INACTIVE",
            reason_code="PROMPT_INACTIVE",
            message="Requested prompt is not active in the bound registry.",
            blocking=True,
            next_action="DERIVE_ACTIVE_OWNER",
        )
        result["autonomy"].update({"status": "FAIL", "failure_class": "INACTIVE_ROUTE_TARGET"})
        return _finalize(result, unchanged, ledger, policy)

    if target["resolved_prompt_id"] == state.current_prompt_id:
        result, unchanged = _nonmutating(
            candidate,
            state,
            status="ALREADY_AT_TARGET",
            reason_code="ALREADY_AT_TARGET",
            message="Canonical route state already points at the requested prompt.",
            blocking=False,
        )
        result["autonomy"].update({"status": "PASS", "failure_class": None})
        return _finalize(result, unchanged, ledger, policy)

    # An authority class may recommend a route without being allowed to mutate route state.
    authority_class = candidate["actor"]["authority_class"]
    if policy["authority_classes"][authority_class].get("mutating") is not True:
        result, unchanged = _nonmutating(
            candidate,
            state,
            status="POLICY_REJECTED",
            reason_code="AUTHORITY_NOT_MUTATING",
            message=f"Authority class {authority_class} may recommend but cannot mutate canonical route state.",
            blocking=False,
            next_action="ESCALATE_TO_AUTHORIZED_AUTONOMOUS_ROUTER",
        )
        result["autonomy"].update({"status": "PASS", "failure_class": None})
        return _finalize(result, unchanged, ledger, policy)

    result = copy.deepcopy(candidate)
    result["precedence"].update(
        {"observed_state_version": state.version, "compare_and_set": "MATCH" if expected is not None else "NOT_REQUIRED"}
    )
    result["route"].update(
        {
            "status": "ROUTED",
            "route_version_before": state.version,
            "route_version_after": state.version + 1,
            "changed": True,
        }
    )
    result["gates"].update({"aggregate": "PASS", "mutation_allowed": True})
    result["idempotency"].update({"duplicate": False, "original_receipt_id": None, "replay_result": None})
    result["autonomy"].update({"status": "PASS", "human_dependency": False, "failure_class": None, "remediation_prompt_id": None})
    result["outcome"].update(
        {
            "code": "ROUTED",
            "message": f"Canonical route advanced to {target['resolved_prompt_id']}.",
            "blocking": False,
            "next_action": None,
        }
    )
    new_state = RouteState(target["resolved_prompt_id"], state.version + 1)
    return _finalize(result, new_state, ledger, policy)


def _precedence_key(receipt: dict[str, Any]) -> tuple[int, int, str, str]:
    """Stable winner key. Lower tuple wins after negating descending fields."""
    return (
        -int(receipt["precedence"]["authority_rank"]),
        -int(receipt["decision"]["priority"]),
        str(receipt["request"]["request_fingerprint"]),
        str(receipt["receipt_id"]),
    )


def resolve_competing_routes(
    receipts: list[dict[str, Any]],
    *,
    state: RouteState,
    ledger: RouteLedger,
    policy: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], RouteState]:
    """Resolve concurrent route requests without arrival-order authority.

    Winner order is policy authority rank, decision priority, request fingerprint,
    then receipt ID. The fingerprint/ID steps are deterministic tie-breaks only;
    semantic priority should be expressed through authority and decision priority.
    """
    policy = policy or load_policy()
    if not receipts:
        return [], state
    candidates = [copy.deepcopy(value) for value in receipts]
    for candidate in candidates:
        validate_receipt(candidate, policy, final=False)

    winner = min(candidates, key=_precedence_key)
    winner_id = winner["receipt_id"]
    winner_result, new_state = evaluate_route(winner, state=state, ledger=ledger, policy=policy)

    results: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate["receipt_id"] == winner_id:
            results.append(winner_result)
            continue
        result, _ = _nonmutating(
            candidate,
            state,
            status="PRECEDENCE_REJECTED",
            reason_code="LOWER_PRECEDENCE_COMPETING_ROUTE",
            message=f"Competing route lost deterministic precedence to {winner_id}.",
            blocking=True,
            next_action=f"RECOMPUTE_AFTER:{winner_id}",
        )
        result["precedence"]["superseded_by_receipt_id"] = winner_id
        result["autonomy"].update({"status": "PASS", "failure_class": None})
        validate_receipt(result, policy)
        ledger.record(result)
        results.append(result)
    return results, new_state
