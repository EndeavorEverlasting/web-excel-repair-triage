#!/usr/bin/env python3
"""Validate the repository-installed local Cursor failure observatory."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

try:
    from scripts.failure_observatory import CONTENT_BEARING_HOOKS, SUPPORTED_CURSOR_HOOKS
except ModuleNotFoundError:
    from failure_observatory import CONTENT_BEARING_HOOKS, SUPPORTED_CURSOR_HOOKS

ROOT = Path(__file__).resolve().parents[1]
HOOKS_PATH = ROOT / ".cursor" / "hooks.json"
CONTRACT_PATH = ROOT / "harness" / "contracts" / "privacy-preserving-failure-observatory.v1.json"
GITIGNORE_PATH = ROOT / ".gitignore"
SENTINEL_PATH = ROOT / "scripts" / "cursor_failure_sentinel.py"
STATE_IGNORE_PROBE = ".afk-observatory/privacy-canary.json"
TIMEOUT_SECONDS = 10


class CursorObservatoryInstallError(RuntimeError):
    pass


def _expected_command(hook_name: str) -> str:
    return (
        "python scripts/cursor_failure_sentinel.py "
        f"--state-dir .afk-observatory hook {hook_name}"
    )


def _state_dir_is_ignored(root: Path) -> bool:
    try:
        completed = subprocess.run(
            ["git", "check-ignore", "-q", "--", STATE_IGNORE_PROBE],
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CursorObservatoryInstallError(
            f"cannot prove device-local state ignore policy: {exc}"
        ) from exc
    if completed.returncode == 0:
        return True
    if completed.returncode == 1:
        return False
    detail = completed.stderr.strip() or f"git check-ignore exited {completed.returncode}"
    raise CursorObservatoryInstallError(
        f"cannot prove device-local state ignore policy: {detail}"
    )


def validate() -> dict[str, int | str]:
    hooks = json.loads(HOOKS_PATH.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if hooks.get("version") != 1:
        raise CursorObservatoryInstallError("Cursor project hook schema version must be 1")
    if set(hooks) != {"version", "hooks"}:
        raise CursorObservatoryInstallError("Cursor project hook top-level schema drifted")
    hook_map = hooks.get("hooks")
    if not isinstance(hook_map, dict):
        raise CursorObservatoryInstallError("Cursor project hooks must be an object")
    if set(hook_map) != SUPPORTED_CURSOR_HOOKS:
        raise CursorObservatoryInstallError(
            f"Cursor project hook coverage drifted: {sorted(set(hook_map) ^ SUPPORTED_CURSOR_HOOKS)}"
        )
    if set(hook_map) & CONTENT_BEARING_HOOKS:
        raise CursorObservatoryInstallError("content-bearing Cursor hooks are forbidden")
    for hook_name, entries in hook_map.items():
        if not isinstance(entries, list) or len(entries) != 1:
            raise CursorObservatoryInstallError(f"{hook_name} must have exactly one observatory hook")
        entry = entries[0]
        if not isinstance(entry, dict) or set(entry) != {"command", "timeout", "failClosed"}:
            raise CursorObservatoryInstallError(f"{hook_name} hook schema drifted")
        if entry["command"] != _expected_command(hook_name):
            raise CursorObservatoryInstallError(f"{hook_name} command drifted")
        if entry["timeout"] != TIMEOUT_SECONDS:
            raise CursorObservatoryInstallError(f"{hook_name} timeout drifted")
        if entry["failClosed"] is not False:
            raise CursorObservatoryInstallError(
                f"{hook_name} must remain passive/fail-open; observability cannot block agent work"
            )

    if not SENTINEL_PATH.is_file():
        raise CursorObservatoryInstallError("Cursor failure sentinel is missing")
    if not GITIGNORE_PATH.is_file():
        raise CursorObservatoryInstallError("repository .gitignore is missing")
    if not _state_dir_is_ignored(ROOT):
        raise CursorObservatoryInstallError(
            "device-local observatory state is not effectively ignored by Git"
        )

    phases = {
        item["phase"]: item
        for item in contract.get("phase_map", [])
        if isinstance(item, dict) and isinstance(item.get("phase"), str)
    }
    if phases.get("P0_LOCAL_PROTOTYPE", {}).get("status") != "VALIDATED_INTEGRATED":
        raise CursorObservatoryInstallError("P0 phase state is not integrated")
    if phases.get("P1_HOST_INSTALLATION", {}).get("status") != (
        "REPOSITORY_INSTALLATION_IMPLEMENTED_FIELD_PROOF_REQUIRED"
    ):
        raise CursorObservatoryInstallError("P1 phase state is not implementation-complete")
    if phases.get("P2_ANONYMOUS_CONTRIBUTION", {}).get("status") != (
        "BLOCKED_BY_PRIVACY_DESIGN_APPROVAL"
    ):
        raise CursorObservatoryInstallError("P2 privacy gate must remain blocked")

    return {
        "hooks": len(hook_map),
        "version": hooks["version"],
        "timeout_seconds": TIMEOUT_SECONDS,
    }


def main() -> int:
    try:
        summary = validate()
    except (CursorObservatoryInstallError, OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"CURSOR FAILURE OBSERVATORY INSTALL: FAIL: {exc}")
        return 1
    print(
        "CURSOR FAILURE OBSERVATORY INSTALL: PASS | "
        f"hooks={summary['hooks']} | version={summary['version']} | "
        f"timeout={summary['timeout_seconds']}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
