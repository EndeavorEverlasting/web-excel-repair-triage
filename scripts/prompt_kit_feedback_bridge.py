#!/usr/bin/env python3
"""Private Prompt Kit feedback transport seam.

This module validates one browser-origin feedback envelope, pseudonymizes source
identity, persists the sanitized event in a private local spool, and can emit a
sanitized repository-dispatch receipt when explicitly enabled. It deliberately
does not schedule workers, scan pull requests, or merge repository changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

EVENT_SCHEMA = "prompt-feedback-event/v1"
PRIVATE_ENVELOPE_SCHEMA = "prompt-feedback-private-envelope/v1"
PRIVATE_DISPATCH_SCHEMA = "prompt-feedback-private-dispatch/v1"
SPOOL_SCHEMA = "prompt-feedback-private-spool/v1"
MAX_ENVELOPE_BYTES = 16 * 1024
SENSITIVE_MARKERS = (
    "prompt_body",
    "clipboard",
    "secret",
    "token",
    "password",
    "credential",
    "authorization",
    "cookie",
)
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
PROVIDER_RECEIPT_FIELDS = (
    "schema_version",
    "signal_id",
    "prompt_id",
    "event_type",
    "value",
    "has_comment",
    "source_hash",
    "sequence",
)
Runner = Callable[..., subprocess.CompletedProcess[str]]


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
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
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
        sanitized["supersedes_event_id"] = _require_text(
            event.get("supersedes_event_id"), "supersedes_event_id", 160
        )
    if event_type == "prompt_feedback":
        sanitized["comment"] = _require_text(event.get("comment"), "comment", 1000)
    elif event.get("comment") is not None:
        raise ValueError("comment is only allowed for prompt_feedback events")

    metadata = event.get("metadata")
    if metadata is not None:
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be an object")
        unknown_metadata = sorted(set(metadata) - {"runtime"})
        if unknown_metadata:
            raise ValueError("unsupported feedback metadata fields: " + ", ".join(unknown_metadata))
        runtime = metadata.get("runtime")
        if runtime is not None:
            sanitized["metadata"] = {
                "runtime": _require_text(runtime, "metadata.runtime", 120)
            }
    return sanitized


def parse_envelope(payload: bytes) -> dict[str, Any]:
    if len(payload) > MAX_ENVELOPE_BYTES:
        raise ValueError("feedback envelope exceeds maximum size")
    try:
        envelope = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid feedback envelope JSON") from exc
    if not isinstance(envelope, dict):
        raise ValueError("private feedback envelope must be an object")
    if envelope.get("schema_version") != PRIVATE_ENVELOPE_SCHEMA:
        raise ValueError("unsupported private feedback envelope")
    if envelope.get("sync_authorized") is not True:
        raise ValueError("private feedback sync requires explicit authorization")
    unknown = sorted(set(envelope) - {"schema_version", "sync_authorized", "event"})
    if unknown:
        raise ValueError("unsupported private envelope fields: " + ", ".join(unknown))
    return sanitize_event(envelope.get("event"))


def spool_paths(repo_root: Path, event_id: str) -> tuple[Path, Path]:
    root = (repo_root / "Outputs" / "prompt-kit-feedback-spool").resolve()
    safe = _safe_id(event_id)
    return root / "pending" / f"{safe}.json", root / "sent" / f"{safe}.json"


def event_digest(event: dict[str, Any]) -> str:
    data = json.dumps(
        event, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def provider_receipt(event: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema_version": PRIVATE_DISPATCH_SCHEMA,
        "signal_id": str(event["event_id"]),
        "prompt_id": str(event["prompt_id"]),
        "event_type": str(event["event_type"]),
        "value": str(event["value"]),
        "has_comment": bool(event.get("comment")),
        "source_hash": str(event["source"]),
        "sequence": int(event["sequence"]),
    }
    if tuple(receipt) != PROVIDER_RECEIPT_FIELDS:
        raise AssertionError("provider receipt field contract drift")
    return receipt


def write_pending(repo_root: Path, event: dict[str, Any], repository: str) -> Path:
    pending, sent = spool_paths(repo_root, str(event["event_id"]))
    if sent.exists():
        sent_payload = json.loads(sent.read_text(encoding="utf-8"))
        if sent_payload.get("event_digest") != event_digest(event):
            raise ValueError(f"event id conflict in sent ledger: {event['event_id']}")
        return sent
    pending.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SPOOL_SCHEMA,
        "repository": repository,
        "queued_at": utc_now(),
        "event_digest": event_digest(event),
        "event": event,
        "provider_receipt": provider_receipt(event),
    }
    if pending.exists():
        existing = json.loads(pending.read_text(encoding="utf-8"))
        if existing.get("event_digest") != payload["event_digest"]:
            raise ValueError(f"event id conflict in private spool: {event['event_id']}")
        return pending
    pending.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return pending


def mark_sent(repo_root: Path, event: dict[str, Any], pending: Path) -> Path:
    _, sent = spool_paths(repo_root, str(event["event_id"]))
    sent.parent.mkdir(parents=True, exist_ok=True)
    sent.write_text(
        json.dumps(
            {
                "schema_version": SPOOL_SCHEMA,
                "event_id": event["event_id"],
                "event_digest": event_digest(event),
                "provider_receipt": provider_receipt(event),
                "dispatched_at": utc_now(),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    if pending != sent:
        pending.unlink(missing_ok=True)
    return sent


def dispatch_repository_receipt(
    *,
    repo_root: Path,
    repository: str,
    event: dict[str, Any],
    enabled: bool = False,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    if not enabled:
        return {"status": "PROVIDER_WAKEUP_DISABLED", "signal_id": event["event_id"]}
    receipt = provider_receipt(event)
    body = json.dumps(
        {
            "event_type": "prompt-kit-feedback-receipt",
            "client_payload": receipt,
        },
        separators=(",", ":"),
    )
    proc = runner(
        [
            "gh",
            "api",
            "--method",
            "POST",
            f"repos/{repository}/dispatches",
            "--input",
            "-",
        ],
        cwd=repo_root,
        input=body,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        return {
            "status": "PROVIDER_WAKEUP_FAILED",
            "signal_id": event["event_id"],
            "error": (proc.stderr or proc.stdout).strip()[-2000:],
        }
    return {"status": "PROVIDER_WAKEUP_SENT", "signal_id": event["event_id"]}


def accept_private_feedback(
    *,
    repo_root: Path,
    repository: str,
    payload: bytes,
    provider_wakeup: bool = False,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    event = parse_envelope(payload)
    pending, sent = spool_paths(repo_root, str(event["event_id"]))
    spool_path = write_pending(repo_root, event, repository)
    if spool_path == sent:
        return {
            "status": "DUPLICATE",
            "signal_id": event["event_id"],
            "provider_receipt": provider_receipt(event),
        }

    dispatch = dispatch_repository_receipt(
        repo_root=repo_root,
        repository=repository,
        event=event,
        enabled=provider_wakeup,
        runner=runner,
    )
    if dispatch["status"] == "PROVIDER_WAKEUP_SENT":
        mark_sent(repo_root, event, pending)
        status = "ACCEPTED_AND_SIGNALLED"
    elif dispatch["status"] == "PROVIDER_WAKEUP_FAILED":
        status = "ACCEPTED_PRIVATE_RETRY_PENDING"
    else:
        status = "ACCEPTED_PRIVATE"
    return {
        "status": status,
        "signal_id": event["event_id"],
        "provider_status": dispatch["status"],
        "provider_receipt": provider_receipt(event),
    }


def retry_pending_receipts(
    *,
    repo_root: Path,
    repository: str,
    provider_wakeup: bool,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    pending_root = (repo_root / "Outputs" / "prompt-kit-feedback-spool" / "pending").resolve()
    results: list[dict[str, Any]] = []
    if not pending_root.exists():
        return {"status": "PASS", "attempted": 0, "sent": 0, "results": results}
    for path in sorted(pending_root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        event = payload.get("event")
        if not isinstance(event, dict):
            raise ValueError(f"invalid pending spool event: {path}")
        if payload.get("event_digest") != event_digest(event):
            raise ValueError(f"pending spool digest mismatch: {path}")
        dispatch = dispatch_repository_receipt(
            repo_root=repo_root,
            repository=repository,
            event=event,
            enabled=provider_wakeup,
            runner=runner,
        )
        if dispatch["status"] == "PROVIDER_WAKEUP_SENT":
            mark_sent(repo_root, event, path)
        results.append(dispatch)
    sent_count = sum(item["status"] == "PROVIDER_WAKEUP_SENT" for item in results)
    return {
        "status": "PASS",
        "attempted": len(results),
        "sent": sent_count,
        "results": results,
    }


def _read_payload(path: Path) -> bytes:
    data = path.read_bytes()
    if len(data) > MAX_ENVELOPE_BYTES:
        raise ValueError("feedback envelope exceeds maximum size")
    return data


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--repository", required=True)
    parser.add_argument("--payload", type=Path)
    parser.add_argument("--retry-pending", action="store_true")
    parser.add_argument("--provider-wakeup", action="store_true")
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    try:
        if args.retry_pending:
            if args.payload:
                raise ValueError("--payload and --retry-pending are mutually exclusive")
            report = retry_pending_receipts(
                repo_root=repo_root,
                repository=args.repository,
                provider_wakeup=args.provider_wakeup,
            )
        else:
            if not args.payload:
                raise ValueError("--payload is required unless --retry-pending is used")
            report = accept_private_feedback(
                repo_root=repo_root,
                repository=args.repository,
                payload=_read_payload(args.payload),
                provider_wakeup=args.provider_wakeup,
            )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Prompt Kit private feedback bridge failed: {exc}")
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
