#!/usr/bin/env python3
"""Validate live-thread convergence checkpoints handed to P02."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "harness" / "conversation-continuity" / "checkpoint.schema.v1.json"
SCHEMA_VERSION = "live-thread-p02-checkpoint/v1"
DISPOSITIONS = {"COMPLETE", "BLOCKED", "HANDOFF-READY", "SUSPENDED", "SUPERSEDED"}
DECISION_STATUSES = {"SETTLED", "PROVISIONAL", "REOPEN ONLY IF EVIDENCE CHANGES"}
WORK_STATUSES = {"SAFE & EXECUTABLE", "BLOCKED", "USER-ONLY", "OUT OF SCOPE", "UNKNOWN"}
ROUTES = {"RESUME IN NEW CONVERSATION", "ROUTE TO P07", "ROUTE TO DOMAIN OWNER", "USER ACTION THEN RESUME", "ARCHIVE ONLY", "NO CONTINUATION REQUIRED"}
EVIDENCE_TYPES = {"conversation", "repository", "artifact", "file", "runtime", "external-system", "other"}
TERMINAL = {"COMPLETE", "SUPERSEDED"}
REQUIRED_THREAD = {
    "id", "target", "disposition", "priority", "current_state", "last_meaningful_action",
    "first_unproven_gate", "decisions", "evidence", "changed_surfaces", "validations",
    "remaining_work", "next_action", "route", "return_trigger",
}
NEXT_ACTION_FIELDS = {"owner", "dependency", "action", "expected_output", "completion_gate"}
BLOCKER_FIELDS = {"exact_blocker", "unblock_owner", "unblocking_action", "resume_trigger", "resume_point"}
REPO_FIELDS = {"repository", "default_branch", "working_branch", "head_sha", "first_unproven_repository_gate"}


class ContractError(ValueError):
    """Raised when a checkpoint violates the repository continuity contract."""


def _require(condition: bool, message: str) -> None:
    """Raise ``ContractError`` when a contract predicate is false."""
    if not condition:
        raise ContractError(message)


def _nonempty(value: Any, field: str) -> str:
    """Return a non-empty string value or fail with a field-specific error."""
    _require(isinstance(value, str) and bool(value.strip()), f"{field} must be a non-empty string")
    return value


def _required_keys(value: Any, required: set[str], field: str) -> dict[str, Any]:
    """Require an object containing every key needed by a checkpoint field."""
    _require(isinstance(value, dict), f"{field} must be an object")
    missing = sorted(required - set(value))
    _require(not missing, f"{field} missing required fields: {missing}")
    return value


def _no_extra_keys(value: dict[str, Any], allowed: set[str], field: str) -> None:
    """Reject object keys that the strict checkpoint schema does not allow."""
    extras = sorted(set(value) - allowed)
    _require(not extras, f"{field} has unsupported fields: {extras}")


def _date_time(value: Any, field: str) -> str:
    """Require an RFC 3339-compatible timestamp with an explicit timezone."""
    raw = _nonempty(value, field)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"{field} must be an RFC 3339 date-time") from exc
    _require(parsed.utcoffset() is not None, f"{field} must include a timezone")
    return raw


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object while converting file and parse failures to contract errors."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read JSON {path}: {exc}") from exc
    _require(isinstance(value, dict), f"{path} must contain a JSON object")
    return value


def validate_schema_contract(schema: dict[str, Any] | None = None) -> None:
    """Verify that the tracked JSON Schema still matches validator-owned invariants."""
    schema = schema or load_json(SCHEMA_PATH)
    _require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "checkpoint schema must use JSON Schema 2020-12")
    _require(schema.get("$id") == SCHEMA_VERSION, "checkpoint schema $id drift")
    _require(schema.get("schema_version") == SCHEMA_VERSION, "checkpoint schema version drift")
    top_required = set(schema.get("required", []))
    _require({"handoff_version", "source_controller", "source_conversation_state", "created_at", "threads"} <= top_required, "top-level checkpoint fields are incomplete")
    thread = schema.get("$defs", {}).get("thread", {})
    _require(REQUIRED_THREAD <= set(thread.get("required", [])), "thread checkpoint required fields are incomplete")
    dispositions = set(thread.get("properties", {}).get("disposition", {}).get("enum", []))
    _require(dispositions == DISPOSITIONS, "thread disposition enum drift")
    work_statuses = set(schema.get("$defs", {}).get("remaining_work", {}).get("properties", {}).get("status", {}).get("enum", []))
    _require(work_statuses == WORK_STATUSES, "remaining-work status enum drift")
    routes = set(thread.get("properties", {}).get("route", {}).get("enum", []))
    _require(routes == ROUTES, "checkpoint route enum drift")
    evidence_types = set(schema.get("$defs", {}).get("evidence", {}).get("properties", {}).get("type", {}).get("enum", []))
    _require(evidence_types == EVIDENCE_TYPES, "checkpoint evidence-type enum drift")


def _validate_decisions(items: Any, prefix: str) -> None:
    """Validate preserved decisions and their evidence/status fields."""
    _require(isinstance(items, list), f"{prefix}.decisions must be an array")
    for index, item in enumerate(items):
        field = f"{prefix}.decisions[{index}]"
        obj = _required_keys(item, {"decision", "status", "evidence"}, field)
        _no_extra_keys(obj, {"decision", "status", "evidence"}, field)
        _nonempty(obj["decision"], f"{field}.decision")
        _require(obj["status"] in DECISION_STATUSES, f"{field}.status is invalid")
        _nonempty(obj["evidence"], f"{field}.evidence")


def _validate_evidence(items: Any, prefix: str) -> bool:
    """Validate evidence anchors and report whether repository state is required."""
    _require(isinstance(items, list), f"{prefix}.evidence must be an array")
    has_repository = False
    for index, item in enumerate(items):
        field = f"{prefix}.evidence[{index}]"
        obj = _required_keys(item, {"type", "identity", "value", "mutable"}, field)
        _no_extra_keys(obj, {"type", "identity", "value", "mutable"}, field)
        _require(obj["type"] in EVIDENCE_TYPES, f"{field}.type is invalid")
        _nonempty(obj["identity"], f"{field}.identity")
        _nonempty(obj["value"], f"{field}.value")
        _require(isinstance(obj["mutable"], bool), f"{field}.mutable must be boolean")
        has_repository |= obj["type"] == "repository"
    return has_repository


def _validate_validations(items: Any, prefix: str) -> None:
    """Validate proof records without promoting UNKNOWN or SKIPPED results."""
    _require(isinstance(items, list), f"{prefix}.validations must be an array")
    for index, item in enumerate(items):
        field = f"{prefix}.validations[{index}]"
        obj = _required_keys(item, {"check", "target", "result"}, field)
        _no_extra_keys(obj, {"check", "target", "result", "evidence"}, field)
        _nonempty(obj["check"], f"{field}.check")
        _nonempty(obj["target"], f"{field}.target")
        _require(obj["result"] in {"PASS", "FAIL", "UNKNOWN", "SKIPPED"}, f"{field}.result is invalid")
        _require(obj.get("evidence") is None or isinstance(obj.get("evidence"), str), f"{field}.evidence must be string or null")


def _validate_remaining_work(items: Any, prefix: str) -> None:
    """Validate classified remaining work and its dependency/consequence fields."""
    _require(isinstance(items, list), f"{prefix}.remaining_work must be an array")
    for index, item in enumerate(items):
        field = f"{prefix}.remaining_work[{index}]"
        obj = _required_keys(item, {"item", "status", "dependency", "consequence"}, field)
        _no_extra_keys(obj, {"item", "status", "dependency", "consequence"}, field)
        for key in ("item", "dependency", "consequence"):
            _nonempty(obj[key], f"{field}.{key}")
        _require(obj["status"] in WORK_STATUSES, f"{field}.status is invalid")


def _validate_next_action(value: Any, prefix: str) -> None:
    """Require a complete executable continuation for a nonterminal thread."""
    obj = _required_keys(value, NEXT_ACTION_FIELDS, f"{prefix}.next_action")
    _no_extra_keys(obj, NEXT_ACTION_FIELDS, f"{prefix}.next_action")
    for key in NEXT_ACTION_FIELDS:
        _nonempty(obj[key], f"{prefix}.next_action.{key}")


def _validate_repository_state(value: Any, prefix: str) -> None:
    """Require exact repository identity/head data when repository evidence exists."""
    obj = _required_keys(value, REPO_FIELDS, f"{prefix}.repository_state")
    for key in ("repository", "default_branch", "working_branch", "first_unproven_repository_gate"):
        _nonempty(obj[key], f"{prefix}.repository_state.{key}")
    _require(isinstance(obj["head_sha"], str) and re.fullmatch(r"[0-9a-f]{7,40}", obj["head_sha"]) is not None, f"{prefix}.repository_state.head_sha must be a 7-40 character lowercase hex SHA")


def validate_checkpoint(payload: dict[str, Any]) -> None:
    """Enforce cross-field resumability rules for every checkpoint thread."""
    _require(isinstance(payload, dict), "checkpoint must be an object")
    _no_extra_keys(payload, {"handoff_version", "source_controller", "source_conversation_state", "created_at", "threads"}, "checkpoint")
    _require(payload.get("handoff_version") == SCHEMA_VERSION, "unsupported handoff_version")
    _require(payload.get("source_controller") == "live-thread-convergence-controller", "unsupported source_controller")
    _require(payload.get("source_conversation_state") in {"ACTIVE", "DEGRADED", "CLOSING", "TERMINAL"}, "invalid source_conversation_state")
    _date_time(payload.get("created_at"), "created_at")
    threads = payload.get("threads")
    _require(isinstance(threads, list) and bool(threads), "threads must be a non-empty array")
    seen: set[str] = set()
    for index, item in enumerate(threads):
        prefix = f"threads[{index}]"
        thread = _required_keys(item, REQUIRED_THREAD, prefix)
        _no_extra_keys(thread, REQUIRED_THREAD | {"blocker", "repository_state"}, prefix)
        thread_id = _nonempty(thread["id"], f"{prefix}.id")
        _require(thread_id not in seen, f"duplicate thread id: {thread_id}")
        seen.add(thread_id)
        _nonempty(thread["target"], f"{prefix}.target")
        disposition = thread["disposition"]
        _require(disposition in DISPOSITIONS, f"{prefix}.disposition is invalid")
        priority = _required_keys(thread["priority"], {"rank", "rationale"}, f"{prefix}.priority")
        _no_extra_keys(priority, {"rank", "rationale"}, f"{prefix}.priority")
        _require(isinstance(priority["rank"], int) and priority["rank"] >= 1, f"{prefix}.priority.rank must be >= 1")
        _nonempty(priority["rationale"], f"{prefix}.priority.rationale")
        _nonempty(thread["current_state"], f"{prefix}.current_state")
        _nonempty(thread["last_meaningful_action"], f"{prefix}.last_meaningful_action")
        _validate_decisions(thread["decisions"], prefix)
        has_repo_evidence = _validate_evidence(thread["evidence"], prefix)
        _require(isinstance(thread["changed_surfaces"], list), f"{prefix}.changed_surfaces must be an array")
        for surface_index, surface in enumerate(thread["changed_surfaces"]):
            _nonempty(surface, f"{prefix}.changed_surfaces[{surface_index}]")
        _validate_validations(thread["validations"], prefix)
        _validate_remaining_work(thread["remaining_work"], prefix)
        _require(thread["route"] in ROUTES, f"{prefix}.route is invalid")

        if disposition in TERMINAL:
            _require(thread["first_unproven_gate"] is None, f"{prefix}.first_unproven_gate must be null for terminal disposition")
            _require(thread["next_action"] is None, f"{prefix}.next_action must be null for terminal disposition")
            _require(thread["route"] in {"ARCHIVE ONLY", "NO CONTINUATION REQUIRED"}, f"{prefix}.route must be terminal")
        else:
            _nonempty(thread["first_unproven_gate"], f"{prefix}.first_unproven_gate")
            _validate_next_action(thread["next_action"], prefix)

        if disposition == "SUSPENDED":
            _nonempty(thread["return_trigger"], f"{prefix}.return_trigger")
        if disposition == "BLOCKED":
            blocker = _required_keys(thread.get("blocker"), BLOCKER_FIELDS, f"{prefix}.blocker")
            _no_extra_keys(blocker, BLOCKER_FIELDS, f"{prefix}.blocker")
            for key in BLOCKER_FIELDS:
                _nonempty(blocker[key], f"{prefix}.blocker.{key}")
        if disposition == "HANDOFF-READY":
            _require(thread["route"] not in {"ARCHIVE ONLY", "NO CONTINUATION REQUIRED"}, f"{prefix}.HANDOFF-READY requires a continuation route")
        if has_repo_evidence:
            _validate_repository_state(thread.get("repository_state"), prefix)


def main(argv: list[str] | None = None) -> int:
    """Run schema-only or checkpoint-instance validation from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", nargs="?", type=Path)
    parser.add_argument("--schema-only", action="store_true", help="Validate the repository-owned schema contract without an instance")
    args = parser.parse_args(argv)
    try:
        validate_schema_contract()
        if args.schema_only:
            print(json.dumps({"status": "PASS", "schema": SCHEMA_VERSION}, indent=2))
            return 0
        if args.checkpoint is None:
            parser.error("checkpoint is required unless --schema-only is used")
        validate_checkpoint(load_json(args.checkpoint))
    except ContractError as exc:
        print(f"[FAIL] {exc}")
        return 2
    print(json.dumps({"status": "PASS", "schema": SCHEMA_VERSION, "checkpoint": str(args.checkpoint)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
