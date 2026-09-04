#!/usr/bin/env python3
"""Deterministic JIT grounding for exact Prompt Kit registry operations."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator

SCHEMA_VERSION = "prompt-registry-grounding/v1"
GATE_ID = "prompt-registry-contribution/v1"
GROUNDED_PASS = "GROUNDED_PASS"
UNSOURCED_BLOCK = "UNSOURCED_BLOCK"
CONTRADICTION_BLOCK = "CONTRADICTION_BLOCK"
SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
GROUNDING_FAILURE = "GROUNDING_FAILURE"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class GroundingLockError(RuntimeError):
    """Raised when the protected registry-write lock cannot be acquired."""


def _lock_path(repo_root: Path) -> Path:
    key = _hash_bytes(str(repo_root.resolve()).encode("utf-8"))[:20]
    return Path(tempfile.gettempdir()) / f"prompt-registry-{key}.lock"


@contextmanager
def registry_write_lock(
    repo_root: Path, *, timeout_seconds: float = 10.0, poll_seconds: float = 0.05
) -> Iterator[Path]:
    """Serialize same-checkout registry adders with an OS-released process lock."""
    if timeout_seconds < 0 or poll_seconds <= 0:
        raise ValueError("lock timeout must be >= 0 and poll interval must be > 0")
    path = _lock_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
        handle.write(b"\0")
        handle.flush()
    deadline = time.monotonic() + timeout_seconds
    locked = False
    try:
        while not locked:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except OSError as exc:
                if time.monotonic() >= deadline:
                    raise GroundingLockError(
                        f"prompt registry write lock is busy: {path}"
                    ) from exc
                time.sleep(poll_seconds)
        yield path
    finally:
        if locked:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_file(path: Path) -> str:
    try:
        return _hash_bytes(path.read_bytes())
    except OSError as exc:
        raise RuntimeError(f"cannot read grounding source {path}: {exc}") from exc


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return _hash_bytes(encoded)


def source_fingerprint(sources: Iterable[dict[str, Any]]) -> str:
    normalized = sorted(
        (
            {
                "source_key": str(item["source_key"]),
                "path": str(item["path"]),
                "sha256": str(item["sha256"]),
            }
            for item in sources
        ),
        key=lambda item: (item["source_key"], item["path"]),
    )
    return _fingerprint(normalized)


def packet_fingerprint(packet: dict[str, Any]) -> str:
    return _fingerprint(
        {key: value for key, value in packet.items() if key != "packet_fingerprint"}
    )


def gate_result(status: str, reason: str, **extra: Any) -> dict[str, Any]:
    result = {"status": status, "gate_id": GATE_ID, "reason": reason}
    result.update(extra)
    return result


def build_packet(
    *,
    repo_root: Path,
    registry_module: Any,
    helper_path: Path,
    required_fields: set[str],
    optional_fields: set[str],
    auto_fields: set[str],
    next_identity: dict[str, str],
    registries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a compact source-pinned packet without loading prompt bodies into it."""
    registry_entries: list[dict[str, Any]] = []
    source_specs: list[tuple[str, Path]] = [
        ("base_registry", registry_module.BASE_REGISTRY),
    ]
    for item in registries:
        path = repo_root / item["path"]
        source_key = f"registry:{item['registry_id']}"
        source_specs.append((source_key, path))
        registry_entries.append(
            {
                **item,
                "source_key": source_key,
                "sha256": _hash_file(path),
            }
        )
    for path in registry_module.CONTENT_REGISTRIES:
        source_specs.append((f"content_registry:{path.name}", path))
    source_specs.extend(
        [
            ("prompt_overrides", registry_module.PROMPT_OVERRIDES),
            ("display_order_policy", registry_module.DISPLAY_ORDER_POLICY),
            ("actionability_policy", registry_module.ACTIONABILITY_POLICY),
            ("reference", registry_module.REFERENCE),
            ("runtime:guided_recommendations", registry_module.GUIDED_RECOMMENDATIONS),
            ("runtime:prompt_journey", registry_module.PROMPT_JOURNEY_RUNTIME),
            ("runtime:polish", registry_module.POLISH_RUNTIME),
            ("runtime:correspondence", registry_module.CORRESPONDENCE_RUNTIME),
            ("runtime:management", registry_module.MANAGEMENT_RUNTIME),
            ("runtime:spec_architecture", registry_module.SPEC_ARCHITECTURE_RUNTIME),
            ("runtime:base_prompt_kit", Path(registry_module.build_prompt_kit.JS_PATH)),
            ("html_builder", Path(registry_module.build_prompt_kit.__file__).resolve()),
            ("builder", Path(registry_module.__file__).resolve()),
            ("helper", helper_path.resolve()),
        ]
    )

    seen: set[Path] = set()
    sources: list[dict[str, str]] = []
    for source_key, path in source_specs:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        sources.append(
            {
                "source_key": source_key,
                "path": _relative(resolved, repo_root),
                "sha256": _hash_file(resolved),
            }
        )

    policy = registry_module.load_actionability_policy()
    builder_path = _relative(Path(registry_module.__file__).resolve(), repo_root)
    policy_path = _relative(registry_module.ACTIONABILITY_POLICY, repo_root)
    packet: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "gate_id": GATE_ID,
        "source_fingerprint": source_fingerprint(sources),
        "sources": sources,
        "registries": registry_entries,
        "next_identity": dict(next_identity),
        "draft_fields": {
            "required": sorted(required_fields),
            "optional": sorted(optional_fields),
            "auto_owned": sorted(auto_fields),
        },
        "actionability_policy": {
            "policy_id": policy["policy_id"],
            "path": policy_path,
            "sha256": _hash_file(registry_module.ACTIONABILITY_POLICY),
        },
        "builder": {
            "path": builder_path,
            "sha256": _hash_file(Path(registry_module.__file__).resolve()),
        },
        "output": _relative(registry_module.DEFAULT_OUTPUT, repo_root),
    }
    packet["packet_fingerprint"] = packet_fingerprint(packet)
    return packet


def validate_packet(
    supplied: dict[str, Any], current: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(supplied, dict):
        return gate_result(SCHEMA_MISMATCH, "grounding_packet_not_object")
    if supplied.get("schema_version") != SCHEMA_VERSION:
        return gate_result(
            SCHEMA_MISMATCH,
            "grounding_schema_mismatch",
            expected=SCHEMA_VERSION,
            actual=supplied.get("schema_version"),
        )
    claimed_source = supplied.get("source_fingerprint")
    claimed_packet = supplied.get("packet_fingerprint")
    if not isinstance(claimed_source, str) or not _HEX64.fullmatch(claimed_source):
        return gate_result(SCHEMA_MISMATCH, "invalid_source_fingerprint")
    if not isinstance(claimed_packet, str) or not _HEX64.fullmatch(claimed_packet):
        return gate_result(SCHEMA_MISMATCH, "invalid_packet_fingerprint")
    if packet_fingerprint(supplied) != claimed_packet:
        return gate_result(CONTRADICTION_BLOCK, "tampered_grounding_packet")
    if claimed_packet != current["packet_fingerprint"]:
        return gate_result(
            CONTRADICTION_BLOCK,
            "stale_source_identity",
            supplied_source_fingerprint=claimed_source,
            current_source_fingerprint=current["source_fingerprint"],
            supplied_packet_fingerprint=claimed_packet,
            current_packet_fingerprint=current["packet_fingerprint"],
        )
    return gate_result(
        GROUNDED_PASS,
        "grounding_packet_current",
        source_fingerprint=current["source_fingerprint"],
        packet_fingerprint=current["packet_fingerprint"],
    )
