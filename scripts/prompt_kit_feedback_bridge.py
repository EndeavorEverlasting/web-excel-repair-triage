#!/usr/bin/env python3
"""Private loopback bridge from Prompt Kit browser feedback to trusted local AFK work."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import prompt_kit_afk_local_loop as afk  # noqa: E402

EVENT_SCHEMA = "prompt-feedback-event/v1"
PRIVATE_ENVELOPE_SCHEMA = "prompt-feedback-private-envelope/v1"
PRIVATE_DISPATCH_SCHEMA = "prompt-feedback-private-dispatch/v1"
SPOOL_SCHEMA = "prompt-feedback-private-spool/v1"
MAX_ENVELOPE_BYTES = 16 * 1024
SENSITIVE_MARKERS = ("prompt_body", "clipboard", "secret", "token", "password", "credential", "authorization")
ALLOWED_EVENT_KEYS = {
    "event_id",
    "prompt_id",
    "event_type",
    "value",
    "timestamp",
    "schema_version",
    "source",
    "sequence",
    "supersedes_event_id",
    "comment",
    "metadata",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_text(value: object, field: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    text = value.strip()
    if len(text) > maximum:
        raise ValueError(f"{field} exceeds {maximum} characters")
    return text


def reject_sensitive_payload(value: object, path: str = "event") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if any(marker in key_text.casefold() for marker in SENSITIVE_MARKERS):
                raise ValueError(f"sensitive feedback field rejected: {path}.{key_text}")
            reject_sensitive_payload(item, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_sensitive_payload(item, f"{path}[{index}]")


def _safe_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)
    return cleaned[:120] or hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _source_hash(source: str) -> str:
    return "bridge-local:" + hashlib.sha256(source.encode("utf-8")).hexdigest()[:24]


def sanitize_event(event: object) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise ValueError("feedback event must be an object")
    reject_sensitive_payload(event)
    unknown = sorted(set(event) - ALLOWED_EVENT_KEYS)
    if unknown:
        raise ValueError("unsupported feedback fields: " + ", ".join(unknown))
    if event.get("schema_version") != EVENT_SCHEMA:
        raise ValueError("unsupported feedback event schema")
    event_id = _require_text(event.get("event_id"), "event_id", 160)
    prompt_id = _require_text(event.get("prompt_id"), "prompt_id", 40).upper()
    event_type = _require_text(event.get("event_type"), "event_type", 40)
    if event_type not in {"prompt_vote", "prompt_feedback", "prompt_usage"}:
        raise ValueError("unsupported feedback event type")
    value = _require_text(event.get("value"), "value", 40).casefold()
    if event_type == "prompt_vote" and value not in {"like", "dislike"}:
        raise ValueError("unsupported vote")
    if event_type == "prompt_feedback" and value != "comment":
        raise ValueError("prompt_feedback value must be comment")
    if event_type == "prompt_usage" and value not in {"detail-open", "copy"}:
        raise ValueError("unsupported prompt usage value")
    timestamp = _require_text(event.get("timestamp"), "timestamp", 64)
    source = _require_text(event.get("source"), "source", 160)
    sequence = event.get("sequence", 0)
    if not isinstance(sequence, int) or sequence < 0:
        raise ValueError("sequence must be a non-negative integer")
    sanitized: dict[str, Any] = {
        "event_id": event_id,
        "prompt_id": prompt_id,
        "event_type": event_type,
        "value": value,
        "timestamp": timestamp,
        "schema_version": EVENT_SCHEMA,
        "source": _source_hash(source),
        "sequence": sequence,
    }
    if event.get("supersedes_event_id") is not None:
        sanitized["supersedes_event_id"] = _require_text(event.get("supersedes_event_id"), "supersedes_event_id", 160)
    if event_type == "prompt_feedback":
        sanitized["comment"] = _require_text(event.get("comment"), "comment", 1000)
    metadata = event.get("metadata")
    if metadata is not None:
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be an object")
        runtime = metadata.get("runtime")
        if runtime is not None:
            sanitized["metadata"] = {"runtime": _require_text(runtime, "metadata.runtime", 120)}
    return sanitized


def parse_envelope(payload: bytes) -> dict[str, Any]:
    if len(payload) > MAX_ENVELOPE_BYTES:
        raise ValueError("feedback envelope exceeds maximum size")
    try:
        envelope = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid feedback envelope JSON") from exc
    if not isinstance(envelope, dict) or envelope.get("schema_version") != PRIVATE_ENVELOPE_SCHEMA:
        raise ValueError("unsupported private feedback envelope")
    return sanitize_event(envelope.get("event"))


def spool_paths(repo_root: Path, event_id: str) -> tuple[Path, Path]:
    root = (repo_root / "Outputs" / "prompt-kit-feedback-spool").resolve()
    safe = _safe_id(event_id)
    return root / "pending" / f"{safe}.json", root / "sent" / f"{safe}.json"


def event_digest(event: dict[str, Any]) -> str:
    data = json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def write_pending(repo_root: Path, event: dict[str, Any], repo: str) -> Path:
    pending, _ = spool_paths(repo_root, str(event["event_id"]))
    pending.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SPOOL_SCHEMA,
        "repository": repo,
        "queued_at": utc_now(),
        "event": event,
    }
    if pending.exists():
        existing = json.loads(pending.read_text(encoding="utf-8"))
        if event_digest(existing.get("event", {})) != event_digest(event):
            raise ValueError(f"event id conflict in private spool: {event['event_id']}")
        return pending
    pending.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return pending


def _sent_status(repo_root: Path, event: dict[str, Any]) -> dict[str, Any] | None:
    _, sent = spool_paths(repo_root, str(event["event_id"]))
    if not sent.exists():
        return None
    payload = json.loads(sent.read_text(encoding="utf-8"))
    digest = event_digest(event)
    if payload.get("event_digest") != digest:
        raise ValueError(f"event id conflict in sent ledger: {event['event_id']}")
    return payload


def mark_sent(repo_root: Path, event: dict[str, Any], pending: Path) -> None:
    _, sent = spool_paths(repo_root, str(event["event_id"]))
    sent.parent.mkdir(parents=True, exist_ok=True)
    sent.write_text(
        json.dumps(
            {
                "schema_version": SPOOL_SCHEMA,
                "event_id": event["event_id"],
                "event_digest": event_digest(event),
                "dispatched_at": utc_now(),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    pending.unlink(missing_ok=True)


def dispatch_repository_event(repo_root: Path, repo: str, event: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    client_payload = {
        "schema_version": PRIVATE_DISPATCH_SCHEMA,
        "event": event,
    }
    body = json.dumps({"event_type": "prompt-kit-feedback", "client_payload": client_payload})
    if dry_run:
        return {"status": "DRY_RUN_DISPATCH", "event_id": event["event_id"]}
    proc = subprocess.run(
        ["gh", "api", "--method", "POST", f"repos/{repo}/dispatches", "--input", "-"],
        cwd=repo_root,
        input=body,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        return {
            "status": "DISPATCH_FAILED",
            "event_id": event["event_id"],
            "error": (proc.stderr or proc.stdout).strip()[-2000:],
        }
    return {"status": "DISPATCHED", "event_id": event["event_id"]}


def run_afk_pass(repo_root: Path, repo: str, event: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    state_path = afk.resolve_output(repo_root, afk.DEFAULT_STATE)
    request_root = afk.resolve_output(repo_root, afk.DEFAULT_REQUEST_ROOT)
    worker = afk.parse_worker_command(os.environ.get("PROMPT_KIT_AFK_WORKER_COMMAND"))
    return afk.one_pass(
        repo_root=repo_root,
        repo=repo,
        state_path=state_path,
        request_root=request_root,
        worker_argv=worker,
        feedback_event=event,
        dry_run=dry_run,
    )


def accept_private_feedback(
    *,
    repo_root: Path,
    repo: str,
    payload: bytes,
    dry_run: bool = False,
) -> dict[str, Any]:
    event = parse_envelope(payload)
    prior = _sent_status(repo_root, event)
    if prior:
        afk_report = run_afk_pass(repo_root, repo, event, dry_run=dry_run)
        return {
            "status": "DUPLICATE",
            "event_id": event["event_id"],
            "afk_changed": bool(afk_report.get("changed")),
        }
    pending = write_pending(repo_root, event, repo)
    dispatch = dispatch_repository_event(repo_root, repo, event, dry_run=dry_run)
    # Local development should continue even if provider dispatch is temporarily unavailable.
    afk_report = run_afk_pass(repo_root, repo, event, dry_run=dry_run)
    if dispatch["status"] in {"DISPATCHED", "DRY_RUN_DISPATCH"}:
        if not dry_run:
            mark_sent(repo_root, event, pending)
        return {
            "status": dispatch["status"],
            "event_id": event["event_id"],
            "afk_changed": bool(afk_report.get("changed")),
            "afk_action_count": len(afk_report.get("actions", [])),
        }
    return {
        "status": "QUEUED_PRIVATE_RETRY",
        "event_id": event["event_id"],
        "afk_changed": bool(afk_report.get("changed")),
        "afk_action_count": len(afk_report.get("actions", [])),
        "provider_error": dispatch.get("error"),
    }


def pending_count(repo_root: Path) -> int:
    root = (repo_root / "Outputs" / "prompt-kit-feedback-spool" / "pending").resolve()
    return len(list(root.glob("*.json"))) if root.exists() else 0
