#!/usr/bin/env python3
"""Registry-bound Prompt Kit routing-decision compiler for the FM/ASB seam."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_prompt_kit_registry  # noqa: E402
from scripts import evidence_spine_runtime  # noqa: E402
OPERANT_VERSION_PATH = ROOT / "OPERANT_VERSION"

DECISION_SCHEMA = "prompt-kit.routing-decision/v1"
REGISTRY_SCHEMA_VERSION = "ai-harness-prompt-registry/v1"
ROUTE_RECEIPT_SCHEMA = "evidence-spine-route-receipt/v1"
EVENT_RE = re.compile(r"^evt_[A-Za-z0-9][A-Za-z0-9._-]{7,95}$")
CORR_RE = re.compile(r"^corr_[A-Za-z0-9][A-Za-z0-9._-]{7,95}$")
GE_RE = re.compile(r"^ge_[A-Za-z0-9][A-Za-z0-9._-]{7,95}$")
SHA_RE = re.compile(r"^[a-f0-9]{64}$")
PROMPT_ID_RE = re.compile(r"^P[0-9]{2,4}$")
WIRE_PROMPT_ID_RE = re.compile(r"^P[0-9]{2,3}$")
WIRE_DESTINATION_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,67}$")
RFC3339_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
SIGNALS = {
    "routing",
    "interpretation",
    "execution",
    "progression",
    "durability",
    "premature-terminal",
    "evidence-promotion",
    "regression",
    "environment",
    "unknown",
}
PROMPT_REF_FIELDS = {
    "id",
    "kitVersion",
    "registrySha256",
    "promptSha256",
    "executionSurface",
}


class RoutingDecisionError(ValueError):
    pass


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _idem_key(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return f"idem_{digest}"


def _require_rfc3339(value: Any, field: str) -> str:
    if not isinstance(value, str) or not RFC3339_RE.fullmatch(value):
        raise RoutingDecisionError(f"{field} must be an RFC3339 date-time")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as exc:
        raise RoutingDecisionError(f"{field} must be an RFC3339 date-time") from exc
    if parsed.utcoffset() is None:
        raise RoutingDecisionError(f"{field} must include a timezone")
    return value


def _load_kit_version() -> str:
    value = OPERANT_VERSION_PATH.read_text(encoding="utf-8").strip()
    if not value or len(value) > 64:
        raise RoutingDecisionError("OPERANT_VERSION is missing or invalid")
    return value


def _load_registry() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], str, str]:
    try:
        prompts = build_prompt_kit_registry.load_prompt_kit_registry()
    except SystemExit as exc:
        raise RoutingDecisionError(f"canonical Prompt Kit registry failed to load: {exc}") from exc
    if not isinstance(prompts, list) or not prompts:
        raise RoutingDecisionError("canonical Prompt Kit registry is empty")
    by_id: dict[str, dict[str, Any]] = {}
    for record in prompts:
        prompt_id = str(record.get("id") or "").strip().upper()
        if not PROMPT_ID_RE.fullmatch(prompt_id):
            raise RoutingDecisionError(f"invalid canonical prompt id: {prompt_id!r}")
        if prompt_id in by_id:
            raise RoutingDecisionError(f"duplicate canonical prompt id: {prompt_id}")
        by_id[prompt_id] = record
    return prompts, by_id, _canonical_sha256(prompts), _load_kit_version()


def _prompt_ref(
    record: dict[str, Any],
    *,
    registry_sha256: str,
    kit_version: str,
) -> dict[str, str]:
    prompt_id = str(record["id"]).upper()
    if not WIRE_PROMPT_ID_RE.fullmatch(prompt_id):
        raise RoutingDecisionError(
            f"canonical prompt {prompt_id} cannot be represented by the frozen ASB promptRef protocol"
        )
    execution_surface = str(record.get("executionSurface") or "regular_ai_prompt")
    if execution_surface not in {"regular_ai_prompt", "gnhf_launch_artifact"}:
        raise RoutingDecisionError(
            f"canonical prompt {prompt_id} has unsupported execution surface: {execution_surface}"
        )
    return {
        "id": prompt_id,
        "kitVersion": kit_version,
        "registrySha256": registry_sha256,
        "promptSha256": _canonical_sha256(record),
        "executionSurface": execution_surface,
    }


def _validate_prompt_ref(value: Any, field: str) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != PROMPT_REF_FIELDS:
        raise RoutingDecisionError(f"{field} must be a complete promptRef object or null")
    prompt_id = value.get("id")
    if not isinstance(prompt_id, str) or not WIRE_PROMPT_ID_RE.fullmatch(prompt_id):
        raise RoutingDecisionError(f"{field}.id is invalid for the frozen ASB promptRef protocol")
    for digest_field in ("registrySha256", "promptSha256"):
        digest = value.get(digest_field)
        if not isinstance(digest, str) or not SHA_RE.fullmatch(digest):
            raise RoutingDecisionError(f"{field}.{digest_field} must be a sha256 hex string")
    kit_version = value.get("kitVersion")
    if not isinstance(kit_version, str) or not (1 <= len(kit_version) <= 64):
        raise RoutingDecisionError(f"{field}.kitVersion is invalid")
    if value.get("executionSurface") not in {"regular_ai_prompt", "gnhf_launch_artifact"}:
        raise RoutingDecisionError(f"{field}.executionSurface is invalid")
    return dict(value)


def _validate_routing_request(request: Any) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise RoutingDecisionError("routing request must be an object")
    if request.get("schema") != "prompt-kit.routing-request/v1":
        raise RoutingDecisionError("unsupported routing request schema")
    event_id = request.get("eventId")
    correlation_id = request.get("correlationId")
    if not isinstance(event_id, str) or not EVENT_RE.fullmatch(event_id):
        raise RoutingDecisionError("routing request eventId is invalid")
    if not isinstance(correlation_id, str) or not CORR_RE.fullmatch(correlation_id):
        raise RoutingDecisionError("routing request correlationId is invalid")
    _require_rfc3339(request.get("createdAt"), "routing request createdAt")

    observation_event_id = request.get("observationEventId")
    if not isinstance(observation_event_id, str) or not EVENT_RE.fullmatch(observation_event_id):
        raise RoutingDecisionError("routing request observationEventId is invalid")
    if request.get("causationId") != observation_event_id:
        raise RoutingDecisionError("routing request causationId must equal observationEventId")

    mission = request.get("mission")
    if not isinstance(mission, dict):
        raise RoutingDecisionError("routing request mission must be an object")
    grounding_episode_id = mission.get("groundingEpisodeId")
    if not isinstance(grounding_episode_id, str) or not GE_RE.fullmatch(grounding_episode_id):
        raise RoutingDecisionError("routing request groundingEpisodeId is invalid")

    execution_surface = request.get("executionSurface")
    if execution_surface not in {"regular_ai_prompt", "gnhf_launch_artifact"}:
        raise RoutingDecisionError("routing request executionSurface is invalid")

    policy = request.get("routingPolicy")
    if not isinstance(policy, dict):
        raise RoutingDecisionError("routing request routingPolicy must be an object")
    if policy.get("requireCurrentRegistry") is not True:
        raise RoutingDecisionError("routing request must require the current registry")
    if policy.get("crossSurfaceFallbackAllowed") is not False:
        raise RoutingDecisionError("cross-surface fallback is forbidden")
    max_candidates = policy.get("maxCandidates")
    if not isinstance(max_candidates, int) or isinstance(max_candidates, bool) or not (1 <= max_candidates <= 3):
        raise RoutingDecisionError("routing request maxCandidates must be 1..3")

    signals = request.get("signals")
    if not isinstance(signals, list) or len(signals) > 24:
        raise RoutingDecisionError("routing request signals must be an array of <=24 entries")
    if any(signal not in SIGNALS for signal in signals):
        raise RoutingDecisionError("routing request contains an unknown signal")
    if len(set(signals)) != len(signals):
        raise RoutingDecisionError("routing request signals must be unique")

    correction_events = request.get("correctionEvents")
    if not isinstance(correction_events, list) or len(correction_events) > 24:
        raise RoutingDecisionError("routing request correctionEvents must be an array of <=24 entries")

    _validate_prompt_ref(request.get("currentPrompt"), "routing request currentPrompt")

    idempotency = request.get("idempotency")
    if not isinstance(idempotency, dict):
        raise RoutingDecisionError("routing request idempotency must be an object")
    supplied_semantic = idempotency.get("semanticSha256")
    if not isinstance(supplied_semantic, str) or not SHA_RE.fullmatch(supplied_semantic):
        raise RoutingDecisionError("routing request idempotency.semanticSha256 is invalid")
    semantic_payload = {
        key: value
        for key, value in request.items()
        if key not in {"eventId", "createdAt", "idempotency"}
    }
    expected_semantic = _canonical_sha256(semantic_payload)
    if supplied_semantic != expected_semantic:
        raise RoutingDecisionError("routing request semanticSha256 does not verify")
    expected_key = _idem_key(
        "prompt-kit.routing-request/v1",
        observation_event_id,
        grounding_episode_id,
        execution_surface,
    )
    if idempotency.get("key") != expected_key:
        raise RoutingDecisionError("routing request idempotency key does not verify")
    return request


def _verify_route_receipt(
    receipt: Any,
    *,
    by_id: dict[str, dict[str, Any]],
    registry_sha256: str,
    kit_version: str,
    routing_request_event_id: str,
    correlation_id: str,
) -> tuple[dict[str, Any], dict[str, str], dict[str, Any]]:
    if not isinstance(receipt, dict) or receipt.get("schema_version") != ROUTE_RECEIPT_SCHEMA:
        raise RoutingDecisionError("unsupported route receipt schema")
    route_input = {
        "prompt_id": receipt.get("prompt_id"),
        "prompt_revision": receipt.get("prompt_revision"),
        "destination": receipt.get("destination"),
        "provenance": receipt.get("provenance"),
        "surface_id": receipt.get("surface_id"),
        "invocation_id": receipt.get("invocation_id"),
        "run_id": receipt.get("run_id"),
        "routing_request_event_id": receipt.get("routing_request_event_id"),
        "correlation_id": receipt.get("correlation_id"),
    }
    try:
        rebuilt = evidence_spine_runtime.build_route_receipt(route_input)
    except evidence_spine_runtime.ContinuationError as exc:
        raise RoutingDecisionError(f"invalid route receipt: {exc}") from exc
    if receipt != rebuilt:
        raise RoutingDecisionError("route receipt identity or derived fields do not verify")
    if rebuilt.get("authoritative") is not True or rebuilt.get("provenance") != "observed":
        raise RoutingDecisionError(
            "routing decision requires an observed authoritative route receipt"
        )
    if rebuilt.get("effective_destination") in {None, "", "unknown"}:
        raise RoutingDecisionError(
            "routing decision requires an authoritative effective destination"
        )
    if rebuilt.get("routing_request_event_id") != routing_request_event_id:
        raise RoutingDecisionError(
            "route receipt routing_request_event_id does not match routing request"
        )
    if rebuilt.get("correlation_id") != correlation_id:
        raise RoutingDecisionError(
            "route receipt correlation_id does not match routing request"
        )

    prompt_id = str(receipt.get("prompt_id") or "").upper()
    record = by_id.get(prompt_id)
    if record is None:
        raise RoutingDecisionError(f"route receipt prompt is not in the current registry: {prompt_id}")
    current_ref = _prompt_ref(
        record,
        registry_sha256=registry_sha256,
        kit_version=kit_version,
    )
    if receipt.get("prompt_revision") != current_ref["promptSha256"]:
        raise RoutingDecisionError(
            f"route receipt prompt revision is stale for current registry: {prompt_id}"
        )
    return rebuilt, current_ref, record


def _intervention(request: dict[str, Any]) -> str:
    signals = set(request.get("signals") or [])
    if signals & {"premature-terminal", "evidence-promotion", "regression", "durability"}:
        return "REGROUND"
    if request.get("correctionEvents"):
        return "CRITIQUE"
    return "CONTINUE"


def _classification(request: dict[str, Any]) -> dict[str, Any]:
    signals = request.get("signals") or []
    return {
        "outcomeClass": signals[0] if signals else "unknown",
        "causeCandidates": ["unknown"],
    }


def build_routing_decision(
    request: dict[str, Any],
    route_receipt: dict[str, Any],
    *,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Compile one current-registry-bound routing decision from a verified route receipt."""
    request = _validate_routing_request(request)
    prompts, by_id, registry_sha256, kit_version = _load_registry()
    del prompts
    verified_receipt, selected_ref, selected_record = _verify_route_receipt(
        route_receipt,
        by_id=by_id,
        registry_sha256=registry_sha256,
        kit_version=kit_version,
        routing_request_event_id=request["eventId"],
        correlation_id=request["correlationId"],
    )

    if selected_ref["executionSurface"] != request["executionSurface"]:
        raise RoutingDecisionError(
            "selected prompt execution surface does not match routing request; cross-surface fallback is forbidden"
        )

    current_ref = _validate_prompt_ref(request.get("currentPrompt"), "routing request currentPrompt")
    route_action = "KEEP_CURRENT_PROMPT" if current_ref == selected_ref else "SWITCH_PROMPT"
    destination = str(verified_receipt["effective_destination"])
    if not WIRE_DESTINATION_RE.fullmatch(destination):
        raise RoutingDecisionError(
            "authoritative route destination cannot be represented by frozen decision reasonCodes"
        )
    reason_codes = [
        "current-registry-bound",
        "route-receipt-verified",
        str(verified_receipt["route_id"]),
        f"destination-{destination}",
        "current-prompt-kept" if route_action == "KEEP_CURRENT_PROMPT" else "current-prompt-switched",
    ]

    decision_body: dict[str, Any] = {
        "schema": DECISION_SCHEMA,
        "correlationId": request["correlationId"],
        "causationId": request["eventId"],
        "createdAt": _require_rfc3339(
            created_at if created_at is not None else request["createdAt"],
            "routing decision createdAt",
        ),
        "producer": {
            "system": "prompt-kit",
            "component": "routing-engine",
            "version": kit_version,
        },
        "routingRequestEventId": request["eventId"],
        "registry": {
            "schemaVersion": REGISTRY_SCHEMA_VERSION,
            "kitVersion": kit_version,
            "registrySha256": registry_sha256,
        },
        "decision": {
            "intervention": _intervention(request),
            "routeAction": route_action,
            "primaryPrompt": selected_ref,
            "alternates": [],
            "reasonCodes": reason_codes,
        },
        "classification": _classification(request),
        "requiredVariables": [],
        "proofGate": str(selected_record.get("proofGate") or "").strip(),
        "nextStep": str(selected_record.get("nextStep") or "").strip(),
        "confidence": "MEDIUM",
    }
    if not decision_body["proofGate"] or not decision_body["nextStep"]:
        raise RoutingDecisionError(
            f"canonical prompt {selected_ref['id']} must define proofGate and nextStep"
        )

    semantic_payload = {
        key: value
        for key, value in decision_body.items()
        if key not in {"eventId", "createdAt", "idempotency"}
    }
    semantic_sha256 = _canonical_sha256(semantic_payload)
    decision_body["eventId"] = f"evt_route_dec_{semantic_sha256[:40]}"
    decision_body["idempotency"] = {
        "key": _idem_key(
            DECISION_SCHEMA,
            request["eventId"],
            registry_sha256,
        ),
        "semanticSha256": semantic_sha256,
    }

    if verified_receipt["prompt_id"] != selected_ref["id"]:
        raise RoutingDecisionError("verified route receipt prompt binding changed unexpectedly")
    return decision_body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--route-receipt", required=True, type=Path)
    parser.add_argument("--created-at")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    output_path = args.output.resolve() if args.output else None
    request_path = args.request.resolve()
    receipt_path = args.route_receipt.resolve()
    if output_path is not None and output_path in {request_path, receipt_path}:
        print("routing decision output must not overwrite an input file", file=sys.stderr)
        return 2

    temp_output: Path | None = None
    try:
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if output_path.exists():
                output_path.unlink()
            temp_output = output_path.with_name(output_path.name + ".tmp")
            if temp_output.exists():
                temp_output.unlink()

        request = json.loads(request_path.read_text(encoding="utf-8"))
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        decision = build_routing_decision(request, receipt, created_at=args.created_at)
        payload = json.dumps(decision, indent=2, sort_keys=True) + "\n"
        if output_path is not None:
            assert temp_output is not None
            temp_output.write_text(payload, encoding="utf-8")
            temp_output.replace(output_path)
        else:
            print(payload, end="")
        return 0
    except (OSError, json.JSONDecodeError, RoutingDecisionError) as exc:
        if temp_output is not None:
            try:
                temp_output.unlink(missing_ok=True)
            except OSError:
                pass
        print(f"routing decision failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
