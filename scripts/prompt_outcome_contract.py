"""Shared deterministic primitives for Prompt Kit outcome receipts."""
from __future__ import annotations

import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any

FAILURE_CLASSES = (
    "routing", "interpretation", "execution", "progression", "durability",
    "premature-terminal", "evidence-promotion", "regression", "environment", "unknown",
)
CAUSE_FAMILIES = (
    "grounding", "intent-fidelity", "decomposition", "contract-fidelity",
    "action-space", "recovery", "unknown",
)
INTERVENTIONS = ("CONTINUE", "CRITIQUE", "REGROUND", "REBOOTSTRAP")
RESULTS = ("SUCCESS", "PARTIAL", "FAILURE", "BLOCKED", "UNKNOWN")
CONFIDENCE = ("HIGH", "MEDIUM", "LOW", "NONE")
ATTRIBUTION = ("PROVEN", "CORRELATED", "UNOBSERVED")
ACTIONABILITY = (
    "INFORMATION_ONLY", "REVIEW_CANDIDATE",
    "CONDITIONAL_ACTIONABLE_REPAIR", "ACTIONABLE_REPAIR",
)
CONTRACT = Path(__file__).resolve().parents[1] / "harness/contracts/prompt-outcome-classification.v1.json"


class ContractError(ValueError):
    pass


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ContractError(f"{path} must be a JSON object")
    return value


def _type_matches(value: object, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ContractError(f"unsupported schema type: {expected}")


def _resolve_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ContractError(f"unsupported external schema ref: {ref}")
    node: Any = root
    for raw in ref[2:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or key not in node:
            raise ContractError(f"unresolved schema ref: {ref}")
        node = node[key]
    if not isinstance(node, dict):
        raise ContractError(f"schema ref does not resolve to object: {ref}")
    return node


def validate_schema_instance(
    value: object,
    schema: dict[str, Any],
    *,
    root: dict[str, Any] | None = None,
    path: str = "$",
) -> None:
    """Validate the JSON-Schema subset used by prompt-outcome-receipt/v1."""
    root = root or schema
    if "$ref" in schema:
        validate_schema_instance(value, _resolve_ref(root, schema["$ref"]), root=root, path=path)
        return
    if "oneOf" in schema:
        matches = 0
        for option in schema["oneOf"]:
            try:
                validate_schema_instance(value, option, root=root, path=path)
                matches += 1
            except ContractError:
                pass
        if matches != 1:
            raise ContractError(f"{path}: oneOf matched {matches} branches")
        return
    if "const" in schema and value != schema["const"]:
        raise ContractError(f"{path}: expected const {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise ContractError(f"{path}: value {value!r} not in enum")

    expected = schema.get("type")
    if expected is not None:
        allowed = [expected] if isinstance(expected, str) else list(expected)
        if not any(_type_matches(value, item) for item in allowed):
            raise ContractError(f"{path}: expected type {allowed}, observed {type(value).__name__}")

    if isinstance(value, str):
        if len(value) < int(schema.get("minLength", 0)):
            raise ContractError(f"{path}: string shorter than minLength")
        if "maxLength" in schema and len(value) > int(schema["maxLength"]):
            raise ContractError(f"{path}: string exceeds maxLength {schema['maxLength']}")
        pattern = schema.get("pattern")
        if pattern and re.search(pattern, value) is None:
            raise ContractError(f"{path}: string does not match pattern")
        if schema.get("format") == "date-time":
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ContractError(f"{path}: invalid date-time") from exc
            if parsed.tzinfo is None:
                raise ContractError(f"{path}: date-time requires timezone")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        numeric = float(value)
        if "minimum" in schema and numeric < float(schema["minimum"]):
            raise ContractError(f"{path}: number below minimum")
        if "maximum" in schema and numeric > float(schema["maximum"]):
            raise ContractError(f"{path}: number above maximum")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < int(schema["minItems"]):
            raise ContractError(f"{path}: fewer than minItems")
        if "maxItems" in schema and len(value) > int(schema["maxItems"]):
            raise ContractError(f"{path}: more than maxItems")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in value]
            if len(encoded) != len(set(encoded)):
                raise ContractError(f"{path}: array items must be unique")
        if "items" in schema:
            for index, item in enumerate(value):
                validate_schema_instance(item, schema["items"], root=root, path=f"{path}[{index}]")

    if isinstance(value, dict):
        missing = [key for key in schema.get("required", []) if key not in value]
        if missing:
            raise ContractError(f"{path}: missing required fields: {', '.join(missing)}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                raise ContractError(f"{path}: unsupported fields: {', '.join(extra)}")
        for key, child in value.items():
            if key in properties:
                validate_schema_instance(child, properties[key], root=root, path=f"{path}.{key}")


def require_nonnegative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractError(f"{field} must be an integer")
    if value < 0:
        raise ContractError(f"{field} must be non-negative")
    return value


def _intervention_rank(name: str) -> int:
    try:
        return INTERVENTIONS.index(name)
    except ValueError as exc:
        raise ContractError(f"unknown intervention: {name}") from exc


def derive_interaction_metrics(
    grounding_episode_id: object,
    response_relevance: object,
    correction_events: object,
    signals: list[dict[str, Any]],
    primary: str,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive episode-scoped correction burden; ordinary usage never contributes."""
    contract = contract or load(CONTRACT)
    policy = contract["interaction_divergence_policy"]

    if not isinstance(grounding_episode_id, str) or not grounding_episode_id.strip():
        raise ContractError("grounding_episode_id must be a non-empty string")
    episode_id = grounding_episode_id.strip()

    if (
        isinstance(response_relevance, bool)
        or not isinstance(response_relevance, (int, float))
        or not math.isfinite(float(response_relevance))
    ):
        raise ContractError("response_relevance must be a finite number")
    relevance = float(response_relevance)
    if not 0.0 <= relevance <= 1.0:
        raise ContractError("response_relevance must be between 0 and 1")

    if not isinstance(correction_events, list):
        raise ContractError("correction_events must be a list")

    weights = policy["correction_action_weights"]
    action_causes = policy["correction_action_causes"]
    causes: set[str] = set(contract["symptom_to_cause_candidates"].get(primary, []))
    seen_event_ids: set[str] = set()
    action_kinds: set[str] = set()
    burden = 0.0

    for index, event in enumerate(correction_events):
        if not isinstance(event, dict):
            raise ContractError(f"correction_events[{index}] must be an object")
        required = {"event_id", "grounding_episode_id", "kind", "corrective"}
        optional = {"signal_id", "occurred_at"}
        if not required.issubset(event) or set(event) - required - optional:
            raise ContractError(
                f"correction_events[{index}] must contain event_id, grounding_episode_id, kind, corrective and only bounded optional fields"
            )
        event_id = event["event_id"]
        if not isinstance(event_id, str) or not event_id:
            raise ContractError(f"correction_events[{index}].event_id must be non-empty")
        if event_id in seen_event_ids:
            raise ContractError(f"duplicate correction event id: {event_id}")
        seen_event_ids.add(event_id)

        if event["grounding_episode_id"] != episode_id:
            raise ContractError(
                f"correction_events[{index}] belongs to {event['grounding_episode_id']!r}, not grounding episode {episode_id!r}"
            )
        if event["corrective"] is not True:
            raise ContractError(f"correction_events[{index}].corrective must be true")

        kind = event["kind"]
        if kind not in weights:
            raise ContractError(f"unsupported correction action: {kind}")
        action_kinds.add(kind)
        burden += float(weights[kind])
        causes.update(action_causes.get(kind, []))

    for signal in signals:
        causes.update(policy["signal_cause_candidates"].get(signal.get("type"), []))
    if not causes:
        causes.add("unknown")
    if any(cause not in CAUSE_FAMILIES for cause in causes):
        raise ContractError("contract emitted unknown cause family")

    decimals = int(policy["formula"]["rounding_decimals"])
    burden = round(burden, decimals)
    interaction_yield = round(relevance / (1.0 + burden), decimals)
    pressure = round(1.0 - interaction_yield, decimals)

    intervention = None
    for threshold in policy["thresholds"]:
        if float(threshold["minimum"]) <= pressure < float(threshold["maximum_exclusive"]):
            intervention = threshold["intervention"]
            break
    if intervention is None:
        raise ContractError(f"no intervention threshold covers divergence pressure {pressure}")

    minimum = policy["minimum_intervention_by_symptom"].get(primary, "CONTINUE")
    if _intervention_rank(minimum) > _intervention_rank(intervention):
        intervention = minimum
    if action_kinds.intersection(policy["force_rebootstrap_actions"]):
        intervention = "REBOOTSTRAP"

    return {
        "grounding_episode_id": episode_id,
        "response_relevance": round(relevance, decimals),
        "correction_events": correction_events,
        "correction_burden": burden,
        "interaction_yield": interaction_yield,
        "divergence_pressure": pressure,
        "cause_candidates": sorted(causes, key=lambda item: CAUSE_FAMILIES.index(item)),
        "intervention": intervention,
    }
