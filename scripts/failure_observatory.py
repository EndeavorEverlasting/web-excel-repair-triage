#!/usr/bin/env python3
"""Local, zero-content prototype for privacy-preserving prompt failure observability."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from scripts.execution_boundary_engine import evaluate_boundary

STATE_SCHEMA = "failure-observatory-state/v1"
CAPSULE_SCHEMA = "failure-contribution-capsule/v1"
HOST_FAMILY = "CURSOR"
MARKER_RE = re.compile(r"\[\[AFK_PROMPT:(?P<prompt_id>P\d{2,3}|[A-Z][A-Z0-9_-]{1,31})@(?P<release>[A-Za-z0-9._-]{1,16})\]\]")
SUPPORTED_CURSOR_HOOKS = {
    "beforeSubmitPrompt",
    "postToolUseFailure",
    "afterFileEdit",
    "stop",
    "sessionEnd",
}
CONTENT_BEARING_HOOKS = {"afterAgentThought", "afterAgentResponse"}
FAILURE_TYPES = {"error", "timeout", "permission_denied"}
STOP_STATUSES = {"completed", "aborted", "error"}
SESSION_REASONS = {"completed", "aborted", "error", "window_close", "user_close"}
TOOL_CATEGORIES = {"Shell", "Read", "Write", "Grep", "Delete", "Task", "WebFetch", "WebSearch"}
CAPSULE_KEYS = {
    "schema_version",
    "prompt_id",
    "prompt_release",
    "host_family",
    "outcome",
    "boundary_class",
    "contract_clause",
    "failure_type",
    "mutation_bucket",
    "recovery_disposition",
    "terminal_state",
    "receipt_present",
}
CLAUSE_BY_BOUNDARY = {
    "EC_SEMANTIC_ABANDONMENT": "EBE.NO_SILENT_STOP",
    "EC_PREMATURE_COMPLETION": "EBE.FINALIZATION_GATE",
    "MT_PARTIAL_SIDE_EFFECT_POSSIBLE": "EBE.READ_AFTER_WRITE",
    "MT_WRITE_OUTCOME_UNKNOWN": "EBE.READ_AFTER_WRITE",
    "MT_DUPLICATE_OR_REPLAY_RISK": "EBE.READ_AFTER_WRITE",
    "HT_HOST_FORCED_TERMINATION": "EBE.NO_SILENT_STOP",
    "HT_PROCESS_CRASH": "EBE.NO_SILENT_STOP",
    "HT_LOST_EXECUTION_LEASE": "EBE.NO_SILENT_STOP",
    "UE_UNCLASSIFIED_MATERIAL_BOUNDARY": "EBE.PUBLIC_TRANSITION",
}


class ObservatoryError(ValueError):
    pass


def new_state() -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA,
        "prompt_id": "UNKNOWN",
        "prompt_release": "UNKNOWN",
        "host_family": HOST_FAMILY,
        "objective_active": False,
        "mutation_count_bucket": 0,
        "last_failure_type": "none",
        "explicit_interrupt": False,
        "receipt": None,
        "boundary": None,
        "outcome": "ACTIVE",
    }


def _public_marker(prompt: Any) -> tuple[str, str]:
    if not isinstance(prompt, str):
        return "UNKNOWN", "UNKNOWN"
    match = MARKER_RE.search(prompt[:512])
    if not match:
        return "UNKNOWN", "UNKNOWN"
    return match.group("prompt_id"), match.group("release")


def adapt_cursor_hook(hook_name: str, raw_payload: dict[str, Any]) -> dict[str, Any]:
    if hook_name in CONTENT_BEARING_HOOKS:
        raise ObservatoryError(f"content-bearing Cursor hook forbidden: {hook_name}")
    if hook_name not in SUPPORTED_CURSOR_HOOKS:
        raise ObservatoryError(f"unsupported Cursor hook: {hook_name}")
    if not isinstance(raw_payload, dict):
        raise ObservatoryError("Cursor hook payload must be an object")

    if hook_name == "beforeSubmitPrompt":
        prompt_id, release = _public_marker(raw_payload.get("prompt"))
        return {"kind": "RUN_STARTED", "prompt_id": prompt_id, "prompt_release": release}
    if hook_name == "postToolUseFailure":
        failure_type = raw_payload.get("failure_type")
        if failure_type not in FAILURE_TYPES:
            failure_type = "other"
        tool_name = raw_payload.get("tool_name")
        tool_category = tool_name if tool_name in TOOL_CATEGORIES else "Other"
        return {
            "kind": "TOOL_FAILURE",
            "failure_type": failure_type,
            "is_interrupt": bool(raw_payload.get("is_interrupt")),
            "tool_category": tool_category,
        }
    if hook_name == "afterFileEdit":
        return {"kind": "MUTATION_OBSERVED"}
    if hook_name == "stop":
        status = raw_payload.get("status")
        if status not in STOP_STATUSES:
            status = "other"
        loop_count = raw_payload.get("loop_count")
        return {
            "kind": "STOP",
            "status": status,
            "loop_count_bucket": "ZERO" if loop_count == 0 else "NONZERO",
        }

    reason = raw_payload.get("reason")
    if reason not in SESSION_REASONS:
        reason = "other"
    return {"kind": "SESSION_END", "reason": reason}


def receipt_signal(prompt_id: str, prompt_release: str, proof_state: str) -> dict[str, Any]:
    marker = f"[[AFK_PROMPT:{prompt_id}@{prompt_release}]]"
    if not MARKER_RE.fullmatch(marker):
        raise ObservatoryError("receipt provenance must match bounded public marker grammar")
    if proof_state not in {"IMPLEMENTED", "VALIDATED", "INTEGRATED", "OBSERVED"}:
        raise ObservatoryError("invalid receipt proof state")
    return {
        "kind": "FINALIZATION_RECEIPT",
        "prompt_id": prompt_id,
        "prompt_release": prompt_release,
        "proof_state": proof_state,
    }


def _classify_stop(state: dict[str, Any], signal: dict[str, Any]) -> tuple[str | None, bool]:
    status = signal["status"]
    if state.get("receipt") and status == "completed":
        return None, True
    if status == "aborted" or state.get("explicit_interrupt"):
        return "UC_CANCELLED", True
    if status == "completed":
        return "EC_SEMANTIC_ABANDONMENT", True
    return "UE_UNCLASSIFIED_MATERIAL_BOUNDARY", True


def _classify_session_end(state: dict[str, Any], signal: dict[str, Any]) -> tuple[str | None, bool]:
    reason = signal["reason"]
    if state.get("receipt") and reason == "completed":
        return None, True
    if reason in {"aborted", "user_close", "window_close"}:
        return "UC_CANCELLED", True
    if reason == "error":
        return "UE_UNCLASSIFIED_MATERIAL_BOUNDARY", False
    return "EC_SEMANTIC_ABANDONMENT", True


def apply_signal(
    state: dict[str, Any],
    signal: dict[str, Any],
    architecture: dict[str, Any],
    taxonomy: dict[str, Any],
) -> dict[str, Any]:
    state = json.loads(json.dumps(state))
    kind = signal.get("kind")
    if kind == "RUN_STARTED":
        state.update(
            prompt_id=signal["prompt_id"],
            prompt_release=signal["prompt_release"],
            objective_active=True,
            receipt=None,
            boundary=None,
            outcome="ACTIVE",
        )
        return state
    if kind == "TOOL_FAILURE":
        state["last_failure_type"] = signal["failure_type"]
        state["explicit_interrupt"] = bool(signal["is_interrupt"])
        return state
    if kind == "MUTATION_OBSERVED":
        state["mutation_count_bucket"] = min(2, int(state.get("mutation_count_bucket", 0)) + 1)
        return state
    if kind == "FINALIZATION_RECEIPT":
        state["prompt_id"] = signal["prompt_id"]
        state["prompt_release"] = signal["prompt_release"]
        state["receipt"] = {"proof_state": signal["proof_state"]}
        return state
    if kind not in {"STOP", "SESSION_END"}:
        raise ObservatoryError(f"unsupported HostSignal kind: {kind}")

    classification, process_alive = (
        _classify_stop(state, signal)
        if kind == "STOP"
        else _classify_session_end(state, signal)
    )
    if classification is None:
        state["objective_active"] = False
        state["boundary"] = None
        state["outcome"] = "SUCCESS"
        return state

    decision = evaluate_boundary(
        {
            "observed_classification": classification,
            "process_alive": process_alive,
            "repository_available": False,
            "repository_relevant": False,
            "side_effect_state": "NONE",
            "raw_detail_sensitive": False,
        },
        architecture,
        taxonomy,
    )
    state["objective_active"] = False
    state["boundary"] = decision
    state["outcome"] = "BOUNDARY"
    return state


def _mutation_bucket(value: int) -> str:
    return "ZERO" if value <= 0 else ("ONE" if value == 1 else "MANY")


def compile_capsule(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("outcome") not in {"SUCCESS", "BOUNDARY"}:
        raise ObservatoryError("run is not terminal")
    boundary = state.get("boundary")
    classification = boundary["classification"] if boundary else "NONE"
    capsule = {
        "schema_version": CAPSULE_SCHEMA,
        "prompt_id": state.get("prompt_id", "UNKNOWN"),
        "prompt_release": state.get("prompt_release", "UNKNOWN"),
        "host_family": HOST_FAMILY,
        "outcome": state["outcome"],
        "boundary_class": classification,
        "contract_clause": CLAUSE_BY_BOUNDARY.get(
            classification,
            "EBE.PUBLIC_TRANSITION" if boundary else "NONE",
        ),
        "failure_type": state.get("last_failure_type", "none"),
        "mutation_bucket": _mutation_bucket(int(state.get("mutation_count_bucket", 0))),
        "recovery_disposition": boundary["recovery_disposition"] if boundary else "NONE",
        "terminal_state": boundary["execution_path"][-1] if boundary else "COMPLETE",
        "receipt_present": bool(state.get("receipt")),
    }
    validate_capsule(capsule)
    return capsule


def validate_capsule(capsule: dict[str, Any]) -> None:
    if set(capsule) != CAPSULE_KEYS:
        raise ObservatoryError(f"capsule schema drift: {sorted(set(capsule) ^ CAPSULE_KEYS)}")
    if capsule["host_family"] != HOST_FAMILY:
        raise ObservatoryError("unsupported host family")
    if capsule["outcome"] not in {"SUCCESS", "BOUNDARY"}:
        raise ObservatoryError("invalid capsule outcome")
    if capsule["prompt_id"] != "UNKNOWN":
        marker = f"[[AFK_PROMPT:{capsule['prompt_id']}@{capsule['prompt_release']}]]"
        if not MARKER_RE.fullmatch(marker):
            raise ObservatoryError("capsule provenance escaped bounded public grammar")


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return new_state()
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != STATE_SCHEMA:
        raise ObservatoryError("malformed local observatory state")
    return data


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(state, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)
