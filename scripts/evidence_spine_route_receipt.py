#!/usr/bin/env python3
"""Thin actor-neutral Prompt Route Receipt adapter for Evidence Spine Lane A.

This module salvages only P95-approved concepts from stale PR #450:
authoritative-vs-inferred destination semantics and deterministic idempotency.
It does not own route state, compare-and-set mutation, prompt selection,
outcome classification, recovery, or dispatch.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from scripts.evidence_spine_runtime import ContinuationError, classify_route_destination

SCHEMA_VERSION = "prompt-route-receipt/v1"
IDEMPOTENCY_PREFIX = "idem_"
RECEIPT_PREFIX = "route_"
PROMPT_ID_RE = re.compile(r"^P[0-9]{2,3}$")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
PROVENANCE = {"observed", "declared", "inferred", "unknown"}

TOP_LEVEL_FIELDS = {
    "schema_version",
    "receipt_id",
    "route_id",
    "prompt_id",
    "prompt_revision",
    "source_surface",
    "destination",
    "idempotency",
}
DESTINATION_FIELDS = {
    "destination",
    "provenance",
    "authoritative",
    "effective_destination",
}
IDEMPOTENCY_FIELDS = {"key", "semantic_sha256"}


class RouteReceiptError(ValueError):
    pass


def _canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _required_text(value: Any, field: str, *, max_length: int) -> str:
    if not isinstance(value, str):
        raise RouteReceiptError(f"{field} must be a string")
    text = value.strip()
    if not text or len(text) > max_length:
        raise RouteReceiptError(f"{field} must be 1..{max_length} characters")
    return text


def _safe_id(value: Any, field: str) -> str:
    text = _required_text(value, field, max_length=160)
    if not SAFE_ID_RE.fullmatch(text):
        raise RouteReceiptError(f"{field} contains unsupported characters")
    return text


def _prompt_id(value: Any) -> str:
    text = _required_text(value, "prompt_id", max_length=5)
    if not PROMPT_ID_RE.fullmatch(text):
        raise RouteReceiptError("prompt_id must match PNN or PNNN")
    return text


def _semantic_projection(
    *,
    route_id: str,
    prompt_id: str,
    prompt_revision: str,
    source_surface: str,
    destination: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": route_id,
        "prompt_id": prompt_id,
        "prompt_revision": prompt_revision,
        "source_surface": source_surface,
        "destination": destination,
    }


def build_route_receipt(
    *,
    route_id: str,
    prompt_id: str,
    prompt_revision: str,
    source_surface: str,
    destination: str | None,
    provenance: str,
) -> dict[str, Any]:
    """Build one deterministic actor-neutral route receipt.

    route_id is the stable route-attempt identity. Reusing it with changed
    semantic material intentionally produces the same idempotency key but a
    different semantic hash, allowing conflict detection without mutable state.
    """
    route_id = _safe_id(route_id, "route_id")
    prompt_id = _prompt_id(prompt_id)
    prompt_revision = _required_text(prompt_revision, "prompt_revision", max_length=128)
    source_surface = _safe_id(source_surface, "source_surface")
    if provenance not in PROVENANCE:
        raise RouteReceiptError(f"unsupported destination provenance: {provenance!r}")
    if destination is not None and not isinstance(destination, str):
        raise RouteReceiptError("destination must be a string or null")

    try:
        destination_record = classify_route_destination(
            destination=destination,
            provenance=provenance,
        )
    except ContinuationError as exc:
        raise RouteReceiptError(str(exc)) from exc

    projection = _semantic_projection(
        route_id=route_id,
        prompt_id=prompt_id,
        prompt_revision=prompt_revision,
        source_surface=source_surface,
        destination=destination_record,
    )
    semantic_sha256 = _canonical_sha256(projection)
    idempotency_key = IDEMPOTENCY_PREFIX + hashlib.sha256(
        f"{SCHEMA_VERSION}|{route_id}".encode("utf-8")
    ).hexdigest()

    receipt = {
        **projection,
        "receipt_id": RECEIPT_PREFIX + semantic_sha256[:24],
        "idempotency": {
            "key": idempotency_key,
            "semantic_sha256": semantic_sha256,
        },
    }
    validate_route_receipt(receipt)
    return receipt


def validate_route_receipt(receipt: Any) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise RouteReceiptError("route receipt must be an object")
    if set(receipt) != TOP_LEVEL_FIELDS:
        missing = sorted(TOP_LEVEL_FIELDS - set(receipt))
        extras = sorted(set(receipt) - TOP_LEVEL_FIELDS)
        raise RouteReceiptError(f"route receipt fields mismatch: missing={missing} extras={extras}")
    if receipt.get("schema_version") != SCHEMA_VERSION:
        raise RouteReceiptError("unsupported route receipt schema")

    route_id = _safe_id(receipt.get("route_id"), "route_id")
    prompt_id = _prompt_id(receipt.get("prompt_id"))
    prompt_revision = _required_text(receipt.get("prompt_revision"), "prompt_revision", max_length=128)
    source_surface = _safe_id(receipt.get("source_surface"), "source_surface")

    destination_record = receipt.get("destination")
    if not isinstance(destination_record, dict) or set(destination_record) != DESTINATION_FIELDS:
        raise RouteReceiptError("destination must match the thin destination record")
    provenance = destination_record.get("provenance")
    if provenance not in PROVENANCE:
        raise RouteReceiptError("destination.provenance is invalid")
    raw_destination = destination_record.get("destination")
    if raw_destination is not None and not isinstance(raw_destination, str):
        raise RouteReceiptError("destination.destination must be string or null")
    try:
        expected_destination = classify_route_destination(
            destination=raw_destination,
            provenance=provenance,
        )
    except ContinuationError as exc:
        raise RouteReceiptError(str(exc)) from exc
    if destination_record != expected_destination:
        raise RouteReceiptError("destination record does not match provenance semantics")

    idempotency = receipt.get("idempotency")
    if not isinstance(idempotency, dict) or set(idempotency) != IDEMPOTENCY_FIELDS:
        raise RouteReceiptError("idempotency must contain key and semantic_sha256")
    key = idempotency.get("key")
    digest = idempotency.get("semantic_sha256")
    if not isinstance(key, str) or not re.fullmatch(r"^idem_[a-f0-9]{64}$", key):
        raise RouteReceiptError("idempotency.key is invalid")
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        raise RouteReceiptError("idempotency.semantic_sha256 is invalid")

    projection = _semantic_projection(
        route_id=route_id,
        prompt_id=prompt_id,
        prompt_revision=prompt_revision,
        source_surface=source_surface,
        destination=destination_record,
    )
    expected_digest = _canonical_sha256(projection)
    expected_key = IDEMPOTENCY_PREFIX + hashlib.sha256(
        f"{SCHEMA_VERSION}|{route_id}".encode("utf-8")
    ).hexdigest()
    expected_receipt_id = RECEIPT_PREFIX + expected_digest[:24]
    if digest != expected_digest:
        raise RouteReceiptError("idempotency.semantic_sha256 mismatch")
    if key != expected_key:
        raise RouteReceiptError("idempotency.key mismatch")
    if receipt.get("receipt_id") != expected_receipt_id:
        raise RouteReceiptError("receipt_id mismatch")
    return receipt


def compare_idempotency(existing: Any, candidate: Any) -> str:
    """Compare two validated receipts without mutating route state."""
    left = validate_route_receipt(existing)
    right = validate_route_receipt(candidate)
    left_idem = left["idempotency"]
    right_idem = right["idempotency"]
    if left_idem["key"] != right_idem["key"]:
        return "DISTINCT"
    if left_idem["semantic_sha256"] == right_idem["semantic_sha256"]:
        return "IDEMPOTENT_NOOP"
    return "IDEMPOTENCY_CONFLICT"
