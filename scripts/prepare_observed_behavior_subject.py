#!/usr/bin/env python3
"""Fail closed before Chromium if the served Prompt Kit is not exact-head."""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_REL = "web/prompt-kit/index.html"
CLEAN_WORKTREE_CHECK = "git status --porcelain=v1 --untracked-files=no"
GENERATED_PARITY_COMMAND_DISPLAY = (
    "python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check"
)


class ExactHeadError(RuntimeError):
    """Raised when Chromium must not launch because HEAD/artifact evidence is unclean."""


def _git_output(args: list[str], cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True)


def tracked_modifications_porcelain(cwd: Path | None = None) -> str:
    root = cwd or ROOT
    return _git_output(["status", "--porcelain=v1", "--untracked-files=no"], root)


def git_head_sha(cwd: Path | None = None) -> str:
    return _git_output(["rev-parse", "HEAD"], cwd or ROOT).strip()


def run_generated_parity(cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    root = cwd or ROOT
    return subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_prompt_kit_registry.py"),
            "--output",
            str(root / ARTIFACT_REL),
            "--check",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def prepare_exact_head_subject(
    *,
    cwd: Path | None = None,
    porcelain_fn: Callable[[], str] | None = None,
    parity_fn: Callable[[], subprocess.CompletedProcess[str]] | None = None,
    head_fn: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Reject tracked modifications, check generated parity, then record exact-head subject evidence.

    Chromium must not be launched if this raises.
    """
    root = cwd or ROOT
    porcelain = (porcelain_fn or (lambda: tracked_modifications_porcelain(root)))()
    if porcelain.strip():
        raise ExactHeadError(
            "tracked modifications present; Chromium was not launched:\n" + porcelain
        )
    parity = (parity_fn or (lambda: run_generated_parity(root)))()
    if parity.returncode != 0:
        detail = (parity.stderr or parity.stdout or "").strip() or f"exit {parity.returncode}"
        raise ExactHeadError(
            "generated Prompt Kit parity failed; Chromium was not launched:\n" + detail
        )
    sha = (head_fn or (lambda: git_head_sha(root)))()
    artifact = root / ARTIFACT_REL
    if not artifact.is_file():
        raise ExactHeadError(f"canonical generated Prompt Kit is missing: {ARTIFACT_REL}")
    return {
        "commit_sha": sha,
        "clean_worktree": {
            "tracked_modifications": False,
            "status": "PASS",
            "check": CLEAN_WORKTREE_CHECK,
        },
        "generated_parity": {
            "status": "PASS",
            "command": GENERATED_PARITY_COMMAND_DISPLAY,
            "artifact_path": ARTIFACT_REL,
        },
        "artifact": {
            "path": ARTIFACT_REL,
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        },
    }


def exact_head_field_errors(subject: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    clean = subject.get("clean_worktree") or {}
    if not isinstance(clean, dict):
        errors.append("subject.clean_worktree is required")
        clean = {}
    if clean.get("tracked_modifications") is not False:
        errors.append("subject.clean_worktree.tracked_modifications must be false")
    if clean.get("status") != "PASS":
        errors.append("subject.clean_worktree.status must be PASS")
    if clean.get("check") != CLEAN_WORKTREE_CHECK:
        errors.append("subject.clean_worktree.check must record the porcelain tracked-only command")
    parity = subject.get("generated_parity") or {}
    if not isinstance(parity, dict):
        errors.append("subject.generated_parity is required")
        parity = {}
    if parity.get("status") != "PASS":
        errors.append("subject.generated_parity.status must be PASS")
    if parity.get("command") != GENERATED_PARITY_COMMAND_DISPLAY:
        errors.append("subject.generated_parity.command must be the canonical --check command")
    if parity.get("artifact_path") != ARTIFACT_REL:
        errors.append("subject.generated_parity.artifact_path must be the canonical Prompt Kit")
    return errors


def reverify_exact_head_tree(
    subject: dict[str, Any],
    *,
    cwd: Path | None = None,
    porcelain_fn: Callable[[], str] | None = None,
    parity_fn: Callable[[], subprocess.CompletedProcess[str]] | None = None,
    head_fn: Callable[[], str] | None = None,
) -> list[str]:
    root = cwd or ROOT
    errors: list[str] = []
    porcelain = (porcelain_fn or (lambda: tracked_modifications_porcelain(root)))()
    if porcelain.strip():
        errors.append("worktree has tracked modifications; receipt is stale")
    parity = (parity_fn or (lambda: run_generated_parity(root)))()
    if parity.returncode != 0:
        errors.append("generated Prompt Kit parity no longer holds; receipt is stale")
    live_sha = (head_fn or (lambda: git_head_sha(root)))()
    recorded = str(subject.get("commit_sha") or "")
    if recorded and recorded != live_sha:
        errors.append(f"receipt SHA {recorded} does not match live HEAD {live_sha}")
    return errors
