#!/usr/bin/env python3
"""Install repository hooks through local Git configuration only."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

HOOKS_PATH = ".githooks"
REQUIRED_HOOKS = ("pre-commit", "pre-push")
GIT_TIMEOUT_SECONDS = 15


class HookInstallError(RuntimeError):
    """Raised when local hook installation cannot proceed safely."""


def _run_git(root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise HookInstallError(
            f"git {' '.join(arguments)} timed out after {GIT_TIMEOUT_SECONDS}s"
        ) from exc
    except OSError as exc:
        raise HookInstallError(f"git {' '.join(arguments)} failed: {exc}") from exc


def _decode(value: bytes) -> str:
    return value.decode("utf-8", errors="replace").strip()


def repository_root(start: Path) -> Path:
    result = _run_git(start, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        raise HookInstallError("current path is not inside a Git repository")
    return Path(_decode(result.stdout)).resolve()


def current_hooks_path(root: Path) -> str | None:
    result = _run_git(root, "config", "--local", "--get", "core.hooksPath")
    if result.returncode == 1:
        return None
    if result.returncode != 0:
        raise HookInstallError(
            f"could not read local core.hooksPath (exit {result.returncode})"
        )
    value = _decode(result.stdout)
    return value or None


def verify_hook_files(root: Path) -> None:
    missing = [
        str(Path(HOOKS_PATH) / name)
        for name in REQUIRED_HOOKS
        if not (root / HOOKS_PATH / name).is_file()
    ]
    if missing:
        raise HookInstallError(
            "required tracked hook file(s) are missing: " + ", ".join(missing)
        )


def install_local_hooks(root: Path, *, replace: bool = False) -> str:
    root = repository_root(root)
    verify_hook_files(root)
    existing = current_hooks_path(root)

    if existing not in (None, HOOKS_PATH) and not replace:
        raise HookInstallError(
            "local core.hooksPath already points to "
            f"{existing!r}; rerun with --replace only after preserving that setup"
        )

    result = _run_git(root, "config", "--local", "core.hooksPath", HOOKS_PATH)
    if result.returncode != 0:
        raise HookInstallError(
            f"could not set local core.hooksPath (exit {result.returncode})"
        )

    configured = current_hooks_path(root)
    if configured != HOOKS_PATH:
        raise HookInstallError(
            f"local core.hooksPath verification failed: {configured!r}"
        )
    return configured


def check_local_hooks(root: Path) -> str:
    root = repository_root(root)
    verify_hook_files(root)
    configured = current_hooks_path(root)
    if configured != HOOKS_PATH:
        raise HookInstallError(
            f"local hooks are not active; core.hooksPath={configured!r}"
        )
    return configured


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Opt in to this repository's tracked hooks using only local Git "
            "configuration. No global hook settings are changed."
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify local hooks without changing configuration.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace a different local hooksPath after explicit operator review.",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repository path; defaults to the current directory.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        configured = (
            check_local_hooks(args.repo)
            if args.check
            else install_local_hooks(args.repo, replace=args.replace)
        )
    except HookInstallError as exc:
        print(f"[harness] local hook setup failed: {exc}", file=sys.stderr)
        return 1

    action = "verified" if args.check else "configured"
    print(f"[harness] local hooks {action}: core.hooksPath={configured}")
    print(
        "[harness] next: stage a normal code/docs change and run "
        "python scripts/validate_staged_artifacts.py before committing."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
