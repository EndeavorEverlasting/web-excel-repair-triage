#!/usr/bin/env python3
"""Route one accepted Prompt Kit/Operant signal into bounded AFK work.

This module is intentionally not a scheduler, telemetry collector, or promotion
authority. P99 owns usage/friction semantics, P115 owns semantic AFK
coordination, and P105/pr-floor owns integration.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_SCHEMA = "prompt-kit-afk-signal-state/v1"
REQUEST_SCHEMA = "prompt-kit-afk-work-request/v1"
RESULT_SCHEMA = "prompt-kit-afk-route-result/v1"
EVENT_SCHEMA = "prompt-feedback-event/v1"
SENSITIVE_MARKERS = (
    "prompt_body",
    "clipboard",
    "secret",
    "token",
    "password",
    "credential",
    "authorization",
    "search_query",
    "typed_text",
    "user_id",
    "user_email",
    "ip_address",
    "session_history",
    "navigation_history",
    "raw_usage",
    "page_url",
    "referrer",
)
PROMPT_ID_RE = re.compile(r"^P\d{2,4}$")
SURFACE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
FRICTION_VALUES = {"stale_guidance", "route_miss", "action_failure", "recovery_loop"}
FRICTION_MINIMUMS = {
    "deterministic_runtime_failure": 1,
    "repeated_local_pattern": 3,
}


class RoutingError(ValueError):
    """Raised for malformed or unsafe signal input."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def reject_sensitive_payload(value: object, path: str = "signal") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if any(marker in key_text for marker in SENSITIVE_MARKERS):
                raise RoutingError(f"sensitive field rejected: {path}.{key}")
            reject_sensitive_payload(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_sensitive_payload(item, f"{path}[{index}]")


def require_text(value: object, field: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RoutingError(f"{field} must be a non-empty string")
    text = value.strip()
    if len(text) > maximum:
        raise RoutingError(f"{field} exceeds {maximum} characters")
    return text


def optional_prompt_id(value: object) -> str | None:
    if value in {None, ""}:
        return None
    prompt_id = require_text(value, "prompt_id", 40).upper()
    if not PROMPT_ID_RE.fullmatch(prompt_id):
        raise RoutingError(f"invalid prompt_id: {prompt_id}")
    return prompt_id


def require_occurrence_count(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RoutingError("occurrence_count must be an integer")
    if value < 1 or value > 10000:
        raise RoutingError("occurrence_count must be between 1 and 10000")
    return value


def normalize_signal(raw: object) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise RoutingError("signal must be a JSON object")
    reject_sensitive_payload(raw)

    signal_id = require_text(raw.get("event_id") or raw.get("signal_id"), "signal_id", 160)
    event_type = require_text(raw.get("event_type"), "event_type", 40)
    if event_type not in {"prompt_vote", "prompt_feedback", "prompt_usage", "operant_friction"}:
        raise RoutingError(f"unsupported event_type: {event_type}")

    prompt_id = optional_prompt_id(raw.get("prompt_id"))
    if event_type != "operant_friction" and prompt_id is None:
        raise RoutingError("prompt_id is required for prompt feedback, vote, and usage events")

    value = require_text(raw.get("value"), "value", 80).lower()
    if event_type == "prompt_vote" and value not in {"like", "dislike"}:
        raise RoutingError(f"unsupported vote: {value}")
    if event_type == "prompt_feedback" and value != "comment":
        raise RoutingError("prompt_feedback value must be comment")
    if event_type == "prompt_usage" and value not in {"open", "copy", "invoke", "favorite"}:
        raise RoutingError(f"unsupported prompt_usage value: {value}")
    if event_type == "operant_friction" and value not in FRICTION_VALUES:
        raise RoutingError(f"unsupported operant_friction value: {value}")

    comment = raw.get("comment")
    if event_type == "prompt_feedback":
        comment = require_text(comment, "comment", 1000)
    elif comment not in {None, ""}:
        raise RoutingError("comment is allowed only for prompt_feedback")

    sequence = raw.get("sequence", 0)
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        raise RoutingError("sequence must be a non-negative integer")

    normalized: dict[str, Any] = {
        "signal_id": signal_id,
        "event_type": event_type,
        "value": value,
        "sequence": sequence,
        "timestamp": raw.get("timestamp"),
        "source_hash": raw.get("source_hash"),
    }
    if prompt_id:
        normalized["prompt_id"] = prompt_id
    if comment:
        normalized["comment"] = comment

    if event_type == "operant_friction":
        surface_id = require_text(raw.get("surface_id"), "surface_id", 80).lower()
        if not SURFACE_ID_RE.fullmatch(surface_id):
            raise RoutingError(f"invalid surface_id: {surface_id}")
        evidence_kind = require_text(raw.get("evidence_kind"), "evidence_kind", 80).lower()
        if evidence_kind not in FRICTION_MINIMUMS:
            raise RoutingError(f"unsupported evidence_kind: {evidence_kind}")
        normalized.update(
            {
                "surface_id": surface_id,
                "evidence_kind": evidence_kind,
                "occurrence_count": require_occurrence_count(raw.get("occurrence_count")),
            }
        )
    return normalized


def classify_signal(signal: dict[str, Any]) -> str:
    if signal["event_type"] == "prompt_feedback":
        return "ACTIONABLE_REPAIR"
    if signal["event_type"] == "prompt_vote" and signal["value"] == "dislike":
        return "ACTIONABLE_REPAIR"
    if signal["event_type"] == "operant_friction":
        minimum = FRICTION_MINIMUMS[signal["evidence_kind"]]
        if signal["occurrence_count"] >= minimum:
            return "ACTIONABLE_REPAIR"
    return "INFORMATION_ONLY"


def default_state() -> dict[str, Any]:
    return {"schema_version": STATE_SCHEMA, "signals": {}}


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return default_state()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != STATE_SCHEMA:
        raise RoutingError(f"unsupported state schema: {path}")
    if not isinstance(payload.get("signals"), dict):
        raise RoutingError(f"state signals must be an object: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def work_request(signal: dict[str, Any]) -> dict[str, Any]:
    evidence = {
        "signal_id": signal["signal_id"],
        "event_type": signal["event_type"],
        "value": signal["value"],
        "sequence": signal.get("sequence", 0),
        "timestamp": signal.get("timestamp"),
    }
    if signal.get("prompt_id"):
        evidence["prompt_id"] = signal["prompt_id"]
    if signal.get("comment"):
        evidence["private_comment"] = signal["comment"]
    if signal["event_type"] == "operant_friction":
        evidence.update(
            {
                "surface_id": signal["surface_id"],
                "evidence_kind": signal["evidence_kind"],
                "occurrence_count": signal["occurrence_count"],
            }
        )

    if signal.get("prompt_id"):
        target = f"Prompt Kit {signal['prompt_id']}"
    else:
        target = f"Operant surface {signal['surface_id']}"

    return {
        "schema_version": REQUEST_SCHEMA,
        "created_at": utc_now(),
        "coordinator": "P115 AFK Feedback-Driven Development Loop Executor",
        "preferred_mutation_owner": "P07 Repo Sprint Executor",
        "signal_class": "ACTIONABLE_REPAIR",
        "target": target,
        "evidence": evidence,
        "owned_surface": "Resolve the smallest current canonical owner for the prompt or Operant behavior implicated by this accepted signal before mutation.",
        "acceptance_condition": "Reproduce or validate the accepted feedback/friction evidence, repair only the current owning surface when warranted, add or retain regression proof, and return the exact validated candidate to normal review/integration gates.",
        "forbidden_scope": [
            "browser or worker credentials in tracked files",
            "raw private feedback in provider dispatch payloads",
            "raw usage/session/navigation history",
            "search queries, typed content, user identity, URLs, clipboard contents, or prompt bodies in friction receipts",
            "cross-user behavior profiling or engagement optimization",
            "force push",
            "direct merge from the feedback router",
            "test weakening",
            "generated-output-only repair when a canonical source exists",
        ],
        "telemetry_semantic_owner": "P99",
        "promotion_owner": "P105/pr-floor-integration",
    }


def parse_worker_argv(value: str | None) -> list[str] | None:
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise RoutingError("PROMPT_KIT_AFK_WORKER_ARGV_JSON must be a JSON array") from exc
    if not isinstance(parsed, list) or not parsed or not all(isinstance(item, str) and item for item in parsed):
        raise RoutingError("PROMPT_KIT_AFK_WORKER_ARGV_JSON must be a non-empty string array")
    if sum(item.count("{request}") for item in parsed) != 1:
        raise RoutingError("worker argv must contain {request} exactly once")
    return parsed


def invoke_worker(worker_argv: list[str], request_path: Path) -> int:
    argv = [item.replace("{request}", str(request_path)) for item in worker_argv]
    completed = subprocess.run(argv, cwd=REPO_ROOT, check=False)
    return completed.returncode


def route_signal(
    raw: object,
    *,
    state_path: Path,
    requests_dir: Path,
    worker_argv: list[str] | None = None,
) -> dict[str, Any]:
    signal = normalize_signal(raw)
    disposition = classify_signal(signal)
    state = load_state(state_path)
    signal_id = signal["signal_id"]
    previous = state["signals"].get(signal_id)

    if previous and previous.get("status") != "BLOCKED_WORKER_UNCONFIGURED":
        return {
            "schema_version": RESULT_SCHEMA,
            "signal_id": signal_id,
            "disposition": previous.get("disposition", disposition),
            "status": "DUPLICATE_ALREADY_CONSUMED",
            "request_path": previous.get("request_path"),
        }

    if disposition == "INFORMATION_ONLY":
        state["signals"][signal_id] = {
            "disposition": disposition,
            "status": "CONSUMED_INFORMATION_ONLY",
            "consumed_at": utc_now(),
        }
        write_json(state_path, state)
        return {
            "schema_version": RESULT_SCHEMA,
            "signal_id": signal_id,
            "disposition": disposition,
            "status": "CONSUMED_INFORMATION_ONLY",
            "request_path": None,
        }

    request = work_request(signal)
    request_path = requests_dir / f"{signal_id}.json"
    write_json(request_path, request)

    if worker_argv is None:
        state["signals"][signal_id] = {
            "disposition": disposition,
            "status": "BLOCKED_WORKER_UNCONFIGURED",
            "request_path": request_path.as_posix(),
            "updated_at": utc_now(),
        }
        write_json(state_path, state)
        return {
            "schema_version": RESULT_SCHEMA,
            "signal_id": signal_id,
            "disposition": disposition,
            "status": "BLOCKED_WORKER_UNCONFIGURED",
            "request_path": request_path.as_posix(),
        }

    return_code = invoke_worker(worker_argv, request_path)
    status = "DISPATCHED" if return_code == 0 else "BLOCKED_WORKER_FAILED"
    state["signals"][signal_id] = {
        "disposition": disposition,
        "status": status,
        "request_path": request_path.as_posix(),
        "worker_returncode": return_code,
        "updated_at": utc_now(),
    }
    write_json(state_path, state)
    return {
        "schema_version": RESULT_SCHEMA,
        "signal_id": signal_id,
        "disposition": disposition,
        "status": status,
        "request_path": request_path.as_posix(),
        "worker_returncode": return_code,
    }


def read_signal(path: str) -> object:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True, help="JSON feedback/friction event path, or - for stdin")
    parser.add_argument("--state", type=Path, default=Path("Outputs/prompt-kit-afk/state.json"))
    parser.add_argument("--requests-dir", type=Path, default=Path("Outputs/prompt-kit-afk/work-requests"))
    parser.add_argument(
        "--worker-argv-json",
        default=os.environ.get("PROMPT_KIT_AFK_WORKER_ARGV_JSON"),
        help="JSON argv array containing {request} exactly once; no shell evaluation is used",
    )
    args = parser.parse_args(argv)
    try:
        result = route_signal(
            read_signal(args.event),
            state_path=args.state,
            requests_dir=args.requests_dir,
            worker_argv=parse_worker_argv(args.worker_argv_json),
        )
    except (OSError, json.JSONDecodeError, RoutingError) as exc:
        print(f"Prompt Kit AFK signal routing failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    if result["status"] in {"BLOCKED_WORKER_FAILED"}:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
