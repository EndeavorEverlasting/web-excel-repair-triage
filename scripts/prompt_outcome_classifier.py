"""Deterministic symptom classification for Prompt Kit outcome receipts."""
from __future__ import annotations

from typing import Any

try:
    from scripts.prompt_outcome_contract import ContractError, load, require_nonnegative_int
except ModuleNotFoundError:
    from prompt_outcome_contract import ContractError, load, require_nonnegative_int

CONTRACT = __import__("pathlib").Path(__file__).resolve().parents[1] / "harness/contracts/prompt-outcome-classification.v1.json"


def decision(
    primary: str,
    result: str,
    confidence: str,
    attribution: str,
    actionability: str,
    rationale: str,
    secondary: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "primary": primary,
        "secondary": secondary or [],
        "result": result,
        "confidence": confidence,
        "attribution": attribution,
        "actionability": actionability,
        "rationale": rationale,
    }


def classify_signals(
    signals: list[dict[str, Any]],
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    contract = contract or load(CONTRACT)
    if not isinstance(signals, list) or any(
        not isinstance(signal, dict) or not signal.get("type") for signal in signals
    ):
        raise ContractError("signals must be objects with non-empty type")

    types = {signal["type"] for signal in signals}
    first = lambda kind: next((s for s in signals if s["type"] == kind), None)

    claim, observed = first("state_claim"), first("state_observation")
    if claim and observed:
        order = contract["evidence_state_order"]
        try:
            over = order.index(claim["state"]) > order.index(observed["state"])
        except ValueError as exc:
            raise ContractError("unknown evidence state") from exc
        if over:
            secondary = ["environment"] if "environment_failure" in types else []
            return decision(
                "evidence-promotion", "FAILURE", "HIGH", "PROVEN", "ACTIONABLE_REPAIR",
                f"claimed state {claim['state']} exceeds observed state {observed['state']}",
                secondary,
            )

    if "success_claim_with_unresolved_blocker" in types:
        secondary = ["environment"] if "environment_failure" in types else []
        return decision(
            "evidence-promotion", "FAILURE", "HIGH", "PROVEN", "ACTIONABLE_REPAIR",
            "success was claimed across an independently observed unresolved blocker",
            secondary,
        )

    if {"terminal_claim", "safe_successor_observed"} <= types:
        return decision(
            "premature-terminal", "FAILURE", "HIGH", "PROVEN", "ACTIONABLE_REPAIR",
            "terminality was claimed while a safe actionable successor remained",
        )

    if "expected_durable_artifact_missing" in types:
        return decision(
            "durability", "FAILURE", "HIGH", "PROVEN", "ACTIONABLE_REPAIR",
            "a required durable owner/artifact was deterministically absent",
        )

    transfer = first("manual_context_transfer")
    transfer_threshold = require_nonnegative_int(
        contract["signal_policy"]["manual_context_transfer_minimum_occurrences"],
        "manual_context_transfer_minimum_occurrences",
    )
    if transfer:
        count = require_nonnegative_int(
            transfer.get("occurrence_count", 0),
            "manual_context_transfer.occurrence_count",
        )
        if count >= transfer_threshold:
            return decision(
                "durability", "FAILURE", "HIGH", "PROVEN", "ACTIONABLE_REPAIR",
                "repeated manual context transfer proves the durable continuity owner was bypassed",
            )

    if {"prior_validated_state", "same_requirement_broken"} <= types or "provider_revert_for_behavior" in types:
        return decision(
            "regression", "FAILURE", "HIGH", "PROVEN", "ACTIONABLE_REPAIR",
            "behavior proven for the same requirement later became broken or was reverted",
        )

    route = first("prompt_replaced_by_canonical_owner")
    if "wrong_owner_or_route" in types:
        return decision(
            "routing", "FAILURE", "HIGH", "PROVEN", "ACTIONABLE_REPAIR",
            "repository/review evidence proves the selected owner or route was wrong",
        )
    if route and route.get("replacement_advanced_task") is True:
        return decision(
            "routing", "FAILURE", "MEDIUM", "CORRELATED", "CONDITIONAL_ACTIONABLE_REPAIR",
            "a canonical replacement owner advanced the same task after the original route did not",
        )

    if "explicit_invariant_violation" in types or "review_requirement_miss" in types:
        return decision(
            "interpretation", "FAILURE", "HIGH", "PROVEN", "ACTIONABLE_REPAIR",
            "the selected owner violated an explicit invariant or requirement",
        )

    if (
        {"deterministic_action_failure", "false_unavailable_claim", "available_capability_ignored"} & types
        and "environment_failure" not in types
    ):
        return decision(
            "execution", "FAILURE", "HIGH", "PROVEN", "ACTIONABLE_REPAIR",
            "the intended action failed under available conditions or an available capability was incorrectly excluded",
        )

    correction = first("correction_not_integrated")
    correction_threshold = require_nonnegative_int(
        contract["signal_policy"]["correction_not_integrated_minimum_occurrences"],
        "correction_not_integrated_minimum_occurrences",
    )
    if correction:
        count = require_nonnegative_int(
            correction.get("occurrence_count", 0),
            "correction_not_integrated.occurrence_count",
        )
        if count >= correction_threshold:
            return decision(
                "progression", "FAILURE", "HIGH", "CORRELATED", "CONDITIONAL_ACTIONABLE_REPAIR",
                "operator correction repeated without being integrated into the task model",
            )

    repeat = first("same_prompt_same_mission_repeat")
    threshold = require_nonnegative_int(
        contract["signal_policy"]["repeated_local_pattern_minimum_occurrences"],
        "repeated_local_pattern_minimum_occurrences",
    )
    if repeat:
        count = require_nonnegative_int(
            repeat.get("occurrence_count", 0),
            "same_prompt_same_mission_repeat.occurrence_count",
        )
        if count >= threshold and "durable_state_advance" not in types:
            return decision(
                "progression", "FAILURE", "HIGH", "CORRELATED", "CONDITIONAL_ACTIONABLE_REPAIR",
                f"same prompt/mission repeated {count} times without durable state advance",
            )

    if "environment_failure" in types:
        return decision(
            "environment", "BLOCKED", "HIGH", "PROVEN", "INFORMATION_ONLY",
            "an external provider/access/runtime/tooling condition blocked execution",
        )

    return decision(
        "unknown", "UNKNOWN", "NONE", "UNOBSERVED", "INFORMATION_ONLY",
        "available signals do not safely prove a prompt failure class",
    )
