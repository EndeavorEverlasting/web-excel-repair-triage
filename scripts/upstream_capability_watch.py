#!/usr/bin/env python3
"""Deterministic state transitions for Operant upstream capability watches."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any


class CapabilityWatchError(ValueError):
    """Raised when capability-watch state or events violate the contract."""


REQUIRED_STATE_FIELDS = (
    "last_observed_identity",
    "last_processed_identity",
    "last_observed_repository_revision",
    "status",
)
VALID_STATUSES = {
    "UNSEEN",
    "CURRENT",
    "UPSTREAM_CHANGED",
    "EVALUATING",
    "CANDIDATE",
    "DECLINED",
    "INTEGRATED",
}
CHANGE_SOURCE_STATUSES = VALID_STATUSES - {"UNSEEN"}


def _required_text(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise CapabilityWatchError(f"{field} must be a non-empty string")
    return text


def _copy_state(state: Mapping[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_STATE_FIELDS if field not in state]
    if missing:
        raise CapabilityWatchError("watch state missing required field(s): " + ", ".join(missing))
    status = str(state.get("status", ""))
    if status not in VALID_STATUSES:
        raise CapabilityWatchError(f"unsupported watch status: {status or '<missing>'}")
    return dict(state)


def _impact_edge_ids(values: Iterable[str]) -> list[str]:
    normalized = {_required_text(value, "impact_edge_id") for value in values}
    return sorted(normalized)


def new_watch_state() -> dict[str, Any]:
    """Return the canonical pre-observation state."""
    return {
        "last_observed_identity": None,
        "last_processed_identity": None,
        "last_observed_repository_revision": None,
        "status": "UNSEEN",
    }


def transition_event_id(
    source_id: str,
    resource_id: str,
    previous_processed_identity: str,
    observed_identity: str,
) -> str:
    """Return the stable event identity for one source/capability transition."""
    key = [
        _required_text(source_id, "source_id"),
        _required_text(resource_id, "resource_id"),
        _required_text(previous_processed_identity, "previous_processed_identity"),
        _required_text(observed_identity, "observed_identity"),
    ]
    canonical = json.dumps(key, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def observe_capability(
    state: Mapping[str, Any],
    *,
    source_id: str,
    resource_id: str,
    observed_identity: str,
    repository_revision: str,
    impact_edge_ids: Iterable[str] = (),
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Observe one capability identity without consuming an un-routed change."""
    next_state = _copy_state(state)
    source_id = _required_text(source_id, "source_id")
    resource_id = _required_text(resource_id, "resource_id")
    observed_identity = _required_text(observed_identity, "observed_identity")
    repository_revision = _required_text(repository_revision, "repository_revision")

    if next_state["status"] == "UNSEEN":
        if next_state["last_observed_identity"] is not None or next_state["last_processed_identity"] is not None:
            raise CapabilityWatchError("UNSEEN state must not contain observed or processed identity")
        next_state.update(
            last_observed_identity=observed_identity,
            last_processed_identity=observed_identity,
            last_observed_repository_revision=repository_revision,
            status="CURRENT",
        )
        return next_state, None

    previous_processed = _required_text(
        next_state["last_processed_identity"],
        "last_processed_identity",
    )
    next_state["last_observed_identity"] = observed_identity
    next_state["last_observed_repository_revision"] = repository_revision

    if observed_identity == previous_processed:
        return next_state, None

    if str(state["status"]) not in CHANGE_SOURCE_STATUSES:
        raise CapabilityWatchError(f"status cannot observe a change: {state['status']}")
    next_state["status"] = "UPSTREAM_CHANGED"
    edge_ids = _impact_edge_ids(impact_edge_ids)
    event = {
        "event_id": transition_event_id(
            source_id,
            resource_id,
            previous_processed,
            observed_identity,
        ),
        "source_id": source_id,
        "resource_id": resource_id,
        "previous_processed_identity": previous_processed,
        "observed_identity": observed_identity,
        "repository_revision": repository_revision,
        "impact_edge_ids": edge_ids,
        "status": "UPSTREAM_CHANGED" if edge_ids else "NO_IMPACT_EDGE",
    }
    return next_state, event


def record_routing_result(
    state: Mapping[str, Any],
    event: Mapping[str, Any],
    *,
    event_persisted: bool,
    impact_resolution_persisted: bool,
    routing_checkpoint_persisted: bool,
) -> dict[str, Any]:
    """Advance processed identity only after every durable routing checkpoint."""
    next_state = _copy_state(state)
    expected_event_id = transition_event_id(
        _required_text(event.get("source_id"), "event.source_id"),
        _required_text(event.get("resource_id"), "event.resource_id"),
        _required_text(event.get("previous_processed_identity"), "event.previous_processed_identity"),
        _required_text(event.get("observed_identity"), "event.observed_identity"),
    )
    if event.get("event_id") != expected_event_id:
        raise CapabilityWatchError("event_id does not match the canonical transition key")
    if next_state["status"] != "UPSTREAM_CHANGED":
        raise CapabilityWatchError("routing result requires UPSTREAM_CHANGED state")
    if next_state["last_processed_identity"] != event["previous_processed_identity"]:
        raise CapabilityWatchError("event previous identity is stale for current watch state")
    if next_state["last_observed_identity"] != event["observed_identity"]:
        raise CapabilityWatchError("event observed identity was superseded by a later observation")

    if event_persisted and impact_resolution_persisted and routing_checkpoint_persisted:
        next_state["last_processed_identity"] = event["observed_identity"]
        next_state["status"] = "EVALUATING"
    return next_state
