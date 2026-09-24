#!/usr/bin/env python3
"""Install and verify this repository's tracked Git hooks using local config only."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

HOOKS_PATH = ".githooks"
REQUIRED_HOOKS = ("pre-commit", "pre-push")
REQUIRED_GIT_MODE = "100755"
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


def require_single_worktree(root: Path) -> None:
    result = _run_git(root, "worktree", "list", "--porcelain")
    if result.returncode != 0:
        raise HookInstallError(
            f"could not inspect linked worktrees (exit {result.returncode})"
        )
    count = sum(
        1 for line in _decode(result.stdout).splitlines() if line.startswith("worktree ")
    )
    if count != 1:
        raise HookInstallError(
            "repository has linked worktrees; refusing to change shared local "
            "core.hooksPath because sibling checkouts could be affected"
        )


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


def tracked_mode(root: Path, relative_path: str) -> str | None:
    result = _run_git(root, "ls-files", "--stage", "--", relative_path)
    if result.returncode != 0:
        raise HookInstallError(
            f"could not inspect tracked hook mode for {relative_path!r} "
            f"(exit {result.returncode})"
        )
    output = _decode(result.stdout)
    if not output:
        return None
    lines = [line for line in output.splitlines() if line.strip()]
    if len(lines) != 1:
        raise HookInstallError(
            f"expected exactly one tracked entry for {relative_path!r}, found {len(lines)}"
        )
    return lines[0].split(maxsplit=1)[0]


def verify_hook_files(root: Path) -> None:
    problems: list[str] = []
    for name in REQUIRED_HOOKS:
        relative = str(Path(HOOKS_PATH) / name).replace("\\", "/")
        path = root / HOOKS_PATH / name
        if not path.is_file():
            problems.append(f"missing:{relative}")
            continue
        mode = tracked_mode(root, relative)
        if mode is None:
            problems.append(f"untracked:{relative}")
            continue
        if mode != REQUIRED_GIT_MODE:
            problems.append(f"mode:{relative}={mode};expected={REQUIRED_GIT_MODE}")
    if problems:
        raise HookInstallError(
            "required tracked hooks are not install-ready: " + ", ".join(problems)
        )


def default_hook_path(root: Path, name: str) -> Path:
    result = _run_git(root, "rev-parse", "--git-path", f"hooks/{name}")
    if result.returncode != 0:
        raise HookInstallError(
            f"could not resolve default Git hook path for {name!r} "
            f"(exit {result.returncode})"
        )
    value = Path(_decode(result.stdout))
    return value if value.is_absolute() else root / value


def existing_default_hooks(root: Path) -> list[str]:
    existing: list[str] = []
    for name in REQUIRED_HOOKS:
        path = default_hook_path(root, name)
        if path.exists() or path.is_symlink():
            existing.append(name)
    return existing


def install_local_hooks(root: Path, *, replace: bool = False) -> str:
    root = repository_root(root)
    require_single_worktree(root)
    verify_hook_files(root)
    existing = current_hooks_path(root)

    if existing is None:
        default_hooks = existing_default_hooks(root)
        if default_hooks:
            raise HookInstallError(
                "default Git hook(s) already exist and would be bypassed by "
                "core.hooksPath: " + ", ".join(default_hooks)
            )

    if existing not in (None, HOOKS_PATH) and not replace:
        raise HookInstallError(
            "local core.hooksPath already points to "
            f"{existing!r}; preserve that setup or rerun with --replace after review"
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
    require_single_worktree(root)
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
            "Activate this repository's tracked hooks using only local Git config. "
            "No global hook setting is changed."
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify hook files and local activation without changing configuration.",
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
        "[harness] tracked hooks: pre-commit and pre-push are present at Git mode 100755"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
