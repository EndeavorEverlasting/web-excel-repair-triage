#!/usr/bin/env python3
"""Private Prompt Kit feedback transport seam.

Validate one explicitly authorized browser-origin feedback envelope, pseudonymize
source identity, persist the full event only in a user-local private spool, and
optionally publish a sanitized repository-dispatch receipt only when a matching
consumer is registered. This module never schedules workers, scans PRs, or
merges repository changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from scripts import build_prompt_kit_registry as registry  # noqa: E402

EVENT_SCHEMA = "prompt-feedback-event/v1"
PRIVATE_ENVELOPE_SCHEMA = "prompt-feedback-private-envelope/v1"
PRIVATE_DISPATCH_SCHEMA = "prompt-feedback-private-dispatch/v1"
SPOOL_SCHEMA = "prompt-feedback-private-spool/v2"
PROVIDER_EVENT_TYPE = "prompt-kit-feedback-receipt"
PROVIDER_TIMEOUT_SECONDS = 20
MAX_ENVELOPE_BYTES = 16 * 1024
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
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


def canonical_prompt_ids() -> set[str]:
    return {
        str(prompt.get("id", "")).strip().upper()
        for prompt in registry.load_prompt_kit_registry()
        if isinstance(prompt, dict) and str(prompt.get("id", "")).strip()
    }


def default_spool_root() -> Path:
    """Resolve a per-user state location; never default raw feedback into the repo."""
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "PromptKit" / "feedback-spool"
    state = os.environ.get("XDG_STATE_HOME")
    base = Path(state) if state else Path.home() / ".local" / "state"
    return base / "prompt-kit" / "feedback-spool"


def _require_text(value: object, field: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    text = value.strip()
    if len(text) > maximum:
        raise ValueError(f"{field} exceeds {maximum} characters")
    return text


def _require_repository(value: object) -> str:
    repository = _require_text(value, "repository", 180)
    if not REPOSITORY_RE.fullmatch(repository):
        raise ValueError("repository must use owner/name form")
    return repository


def _validate_timestamp(value: object) -> str:
    text = _require_text(value, "timestamp", 64)
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid timestamp: {text}") from exc
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


def _spool_key(event_id: str) -> str:
    readable = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in event_id)[:64]
    digest = hashlib.sha256(event_id.encode("utf-8")).hexdigest()[:20]
    return f"{readable or 'event'}-{digest}"


def _source_hash(source: str) -> str:
    return "bridge-local:" + hashlib.sha256(source.encode("utf-8")).hexdigest()[:24]


def _ensure_private_directory(path: Path) -> None:
    path.mkdir(parents=False, exist_ok=True, mode=0o700)
    if os.name != "nt":
        os.chmod(path, 0o700)


def _ensure_spool_layout(spool_root: Path) -> None:
    root = spool_root.expanduser().resolve()
    root_parent = root.parent
    root_parent.mkdir(parents=True, exist_ok=True)
    _ensure_private_directory(root)
    _ensure_private_directory(root / "accepted")
    _ensure_private_directory(root / "receipts")
    _ensure_private_directory(root / "receipts" / "pending")
    _ensure_private_directory(root / "receipts" / "sent")


def _write_private_json(path: Path, payload: dict[str, Any]) -> None:
    encoded = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        raise
    if os.name != "nt":
        os.chmod(path, 0o600)


def sanitize_event(event: object, prompt_ids: set[str] | None = None) -> dict[str, Any]:
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
    known = prompt_ids if prompt_ids is not None else canonical_prompt_ids()
    if prompt_id not in known:
        raise ValueError(f"unknown prompt identity: {prompt_id}")
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

    timestamp = _validate_timestamp(event.get("timestamp"))
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
            sanitized["metadata"] = {"runtime": _require_text(runtime, "metadata.runtime", 120)}
    return sanitized


def parse_envelope(payload: bytes, prompt_ids: set[str] | None = None) -> dict[str, Any]:
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
    return sanitize_event(envelope.get("event"), prompt_ids=prompt_ids)


def spool_paths(spool_root: Path, event_id: str) -> tuple[Path, Path, Path]:
    key = _spool_key(event_id)
    root = spool_root.expanduser().resolve()
    return (
        root / "accepted" / f"{key}.json",
        root / "receipts" / "pending" / f"{key}.json",
        root / "receipts" / "sent" / f"{key}.json",
    )


def event_digest(event: dict[str, Any]) -> str:
    data = json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
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


def _same_receipt_shape(receipt: object) -> bool:
    return (
        isinstance(receipt, dict)
        and len(receipt) == len(PROVIDER_RECEIPT_FIELDS)
        and set(receipt) == set(PROVIDER_RECEIPT_FIELDS)
    )


def write_accepted(spool_root: Path, event: dict[str, Any], repository: str) -> tuple[Path, bool]:
    repository = _require_repository(repository)
    _ensure_spool_layout(spool_root)
    accepted, _, _ = spool_paths(spool_root, str(event["event_id"]))
    digest = event_digest(event)
    if accepted.exists():
        existing = json.loads(accepted.read_text(encoding="utf-8"))
        existing_event = existing.get("event") if isinstance(existing, dict) else None
        if (
            existing.get("event_digest") != digest
            or not isinstance(existing_event, dict)
            or existing_event.get("event_id") != event["event_id"]
        ):
            raise ValueError(f"event id conflict in private spool: {event['event_id']}")
        return accepted, False
    _write_private_json(
        accepted,
        {
            "schema_version": SPOOL_SCHEMA,
            "repository": repository,
            "accepted_at": utc_now(),
            "event_digest": digest,
            "event": event,
            "provider_receipt": provider_receipt(event),
        },
    )
    return accepted, True


def queue_provider_receipt(spool_root: Path, event: dict[str, Any], repository: str) -> Path:
    repository = _require_repository(repository)
    _ensure_spool_layout(spool_root)
    _, pending, sent = spool_paths(spool_root, str(event["event_id"]))
    if sent.exists():
        return sent
    payload = {
        "schema_version": SPOOL_SCHEMA,
        "repository": repository,
        "event_digest": event_digest(event),
        "provider_receipt": provider_receipt(event),
        "queued_at": utc_now(),
    }
    if pending.exists():
        existing = json.loads(pending.read_text(encoding="utf-8"))
        if existing.get("event_digest") != payload["event_digest"] or existing.get("repository") != repository:
            raise ValueError(f"receipt conflict in private spool: {event['event_id']}")
        return pending
    _write_private_json(pending, payload)
    return pending


def provider_consumer_registered(repo_root: Path) -> bool:
    workflow = repo_root / ".github" / "workflows" / "prompt-kit-feedback-hook.yml"
    if not workflow.is_file():
        return False
    text = workflow.read_text(encoding="utf-8")
    return "repository_dispatch:" in text and PROVIDER_EVENT_TYPE in text


def dispatch_repository_receipt(
    *,
    repo_root: Path,
    repository: str,
    receipt: dict[str, Any],
    enabled: bool = False,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    repository = _require_repository(repository)
    if not enabled:
        return {"status": "PROVIDER_WAKEUP_DISABLED", "signal_id": receipt["signal_id"]}
    if not provider_consumer_registered(repo_root):
        return {"status": "PROVIDER_CONSUMER_UNREGISTERED", "signal_id": receipt["signal_id"]}
    body = json.dumps(
        {"event_type": PROVIDER_EVENT_TYPE, "client_payload": receipt},
        separators=(",", ":"),
    )
    try:
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
            timeout=PROVIDER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return {"status": "PROVIDER_WAKEUP_TIMEOUT", "signal_id": receipt["signal_id"]}
    if proc.returncode:
        return {
            "status": "PROVIDER_WAKEUP_FAILED",
            "signal_id": receipt["signal_id"],
            "error": (proc.stderr or proc.stdout).strip()[-2000:],
        }
    return {"status": "PROVIDER_WAKEUP_SENT", "signal_id": receipt["signal_id"]}


def mark_receipt_sent(spool_root: Path, event_id: str, pending: Path) -> Path:
    _ensure_spool_layout(spool_root)
    _, _, sent = spool_paths(spool_root, event_id)
    payload = json.loads(pending.read_text(encoding="utf-8"))
    payload["dispatched_at"] = utc_now()
    _write_private_json(sent, payload)
    pending.unlink(missing_ok=True)
    return sent


def accept_private_feedback(
    *,
    repo_root: Path,
    repository: str,
    payload: bytes,
    spool_root: Path | None = None,
    provider_wakeup: bool = False,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    repository = _require_repository(repository)
    spool_root = (spool_root or default_spool_root()).expanduser().resolve()
    event = parse_envelope(payload)
    _, created = write_accepted(spool_root, event, repository)
    if not created:
        return {
            "status": "DUPLICATE",
            "signal_id": event["event_id"],
            "provider_receipt": provider_receipt(event),
        }
    if not provider_wakeup:
        return {
            "status": "ACCEPTED_PRIVATE",
            "signal_id": event["event_id"],
            "provider_status": "PROVIDER_WAKEUP_DISABLED",
            "provider_receipt": provider_receipt(event),
        }

    pending = queue_provider_receipt(spool_root, event, repository)
    dispatch = dispatch_repository_receipt(
        repo_root=repo_root,
        repository=repository,
        receipt=provider_receipt(event),
        enabled=True,
        runner=runner,
    )
    if dispatch["status"] == "PROVIDER_WAKEUP_SENT":
        mark_receipt_sent(spool_root, str(event["event_id"]), pending)
        status = "ACCEPTED_AND_SIGNALLED"
    else:
        status = "ACCEPTED_PRIVATE_RETRY_PENDING"
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
    spool_root: Path | None = None,
    provider_wakeup: bool,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    repository = _require_repository(repository)
    spool_root = (spool_root or default_spool_root()).expanduser().resolve()
    pending_root = spool_root / "receipts" / "pending"
    results: list[dict[str, Any]] = []
    if not pending_root.exists():
        return {"status": "PASS", "attempted": 0, "sent": 0, "results": results}
    for path in sorted(pending_root.glob("*.json")):
        queued = json.loads(path.read_text(encoding="utf-8"))
        stored_repository = _require_repository(queued.get("repository"))
        if stored_repository != repository:
            raise ValueError(
                f"pending receipt repository mismatch: stored={stored_repository} requested={repository}"
            )
        receipt = queued.get("provider_receipt")
        if not _same_receipt_shape(receipt):
            raise ValueError(f"invalid pending provider receipt: {path}")
        dispatch = dispatch_repository_receipt(
            repo_root=repo_root,
            repository=stored_repository,
            receipt=receipt,
            enabled=provider_wakeup,
            runner=runner,
        )
        if dispatch["status"] == "PROVIDER_WAKEUP_SENT":
            mark_receipt_sent(spool_root, str(receipt["signal_id"]), path)
        results.append(dispatch)
    sent_count = sum(item["status"] == "PROVIDER_WAKEUP_SENT" for item in results)
    return {"status": "PASS", "attempted": len(results), "sent": sent_count, "results": results}


def _read_payload(path: Path) -> bytes:
    data = path.read_bytes()
    if len(data) > MAX_ENVELOPE_BYTES:
        raise ValueError("feedback envelope exceeds maximum size")
    return data


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--repository", required=True)
    parser.add_argument("--spool-root", type=Path)
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
                spool_root=args.spool_root,
                provider_wakeup=args.provider_wakeup,
            )
        else:
            if not args.payload:
                raise ValueError("--payload is required unless --retry-pending is used")
            report = accept_private_feedback(
                repo_root=repo_root,
                repository=args.repository,
                payload=_read_payload(args.payload),
                spool_root=args.spool_root,
                provider_wakeup=args.provider_wakeup,
            )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Prompt Kit private feedback bridge failed: {exc}")
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
