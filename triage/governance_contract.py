"""Validate the repository's canonical agent governance contract."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Optional, Sequence

DEFAULT_REPO_ROOT = Path(__file__).parents[1]
GOVERNANCE_PATH = Path("HARNESS.md")

_REQUIRED_SECTIONS = (
    "Agent Operating Principles",
    "Instruction Precedence",
    "Mandatory Sprint Declaration",
    "Shared Planning Directory Governance",
    "Executable Loop",
    "Completion Standard",
    "Forbidden Behaviors",
)

_REQUIRED_PRINCIPLES = (
    "evidence before action",
    "floor before furniture",
    "bounded sprints with declared scope",
    "one writer per branch",
    "reuse before replacing",
    "no completion without proof",
)

_PRECEDENCE = (
    "Platform, security, legal, and explicit repository-owner instructions.",
    "This governance contract.",
    "Task-specific prompts and execution contracts.",
    "Generic defaults.",
)

_REQUIRED_SPRINT_MARKERS = (
    "repository and branch or worktree",
    "lane and mission",
    "owned scope and forbidden scope",
    "expected tracked artifacts",
    "validation commands",
    "proof ceiling",
)

_REQUIRED_COMPLETION_MARKERS = (
    "files changed are named",
    "validation was actually run",
    "a commit SHA exists",
    "push or PR state is reported",
    "one exact next command is given",
)

_REQUIRED_FORBIDDEN_MARKERS = (
    "acknowledgment without mutation",
    "plans without execution",
    "summaries without proof",
    "completion claims without running checks",
    "secret, credential",
)

_REQUIRED_PLANNING_MARKERS = (
    "one canonical shared planning directory",
    "competing planning roots are forbidden",
    "one writer per branch also applies to plan files",
    "plans and handoffs are coordination artifacts, not execution or completion proof",
)

_EXECUTABLE_LOOP = (
    "request -> evidence review -> bounded decision -> repo/Git/GitHub mutation "
    "-> artifacts -> validation -> report -> next decision"
)


def _headings(text: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in re.finditer(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
    }


def validate_text(text: str) -> tuple[str, ...]:
    issues: list[str] = []
    lowered = text.lower()

    if not text.startswith("# Repository Agent Governance Contract"):
        issues.append("HARNESS.md must declare the Repository Agent Governance Contract")
    if "single source of truth" not in lowered:
        issues.append("governance must declare itself the single source of truth")

    headings = _headings(text)
    for section in _REQUIRED_SECTIONS:
        if section not in headings:
            issues.append(f"governance section missing: {section}")

    for principle in _REQUIRED_PRINCIPLES:
        if principle not in lowered:
            issues.append(f"agent operating principle missing: {principle}")

    positions: list[int] = []
    for item in _PRECEDENCE:
        position = text.find(item)
        if position < 0:
            issues.append(f"instruction precedence item missing: {item}")
        positions.append(position)
    if all(position >= 0 for position in positions) and positions != sorted(positions):
        issues.append("instruction precedence order is invalid")

    for marker in _REQUIRED_SPRINT_MARKERS:
        if marker.lower() not in lowered:
            issues.append(f"mandatory sprint declaration marker missing: {marker}")

    if _EXECUTABLE_LOOP not in text:
        issues.append("governance executable loop is missing or malformed")

    for marker in _REQUIRED_COMPLETION_MARKERS:
        if marker.lower() not in lowered:
            issues.append(f"completion standard marker missing: {marker}")

    for marker in _REQUIRED_FORBIDDEN_MARKERS:
        if marker.lower() not in lowered:
            issues.append(f"forbidden behavior marker missing: {marker}")

    for marker in _REQUIRED_PLANNING_MARKERS:
        if marker.lower() not in lowered:
            issues.append(f"shared planning governance marker missing: {marker}")

    if "task-specific rules may refine" not in lowered:
        issues.append("governance must preserve task-specific refinement without lowering precedence")
    if "preservation before cleanup" not in lowered:
        issues.append("governance must require preservation before cleanup")

    return tuple(issues)


def _is_tracked(repo_root: Path, relative_path: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "--error-unmatch", relative_path.as_posix()],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def validate_repository(repo_root: str | Path = DEFAULT_REPO_ROOT) -> tuple[str, ...]:
    root = Path(repo_root).resolve()
    path = root / GOVERNANCE_PATH
    issues: list[str] = []

    if not path.is_file():
        return (f"canonical governance file missing: {GOVERNANCE_PATH.as_posix()}",)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return (f"cannot read governance file: {exc}",)

    issues.extend(validate_text(text))
    if not _is_tracked(root, GOVERNANCE_PATH):
        issues.append("canonical governance file is not tracked by Git: HARNESS.md")
    return tuple(issues)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    issues = validate_repository(args.repo_root)
    result = {
        "valid": not issues,
        "governance_file": str((args.repo_root.resolve() / GOVERNANCE_PATH)),
        "tracked": not any("not tracked" in issue for issue in issues),
        "issues": list(issues),
    }
    print(
        json.dumps(result, indent=2)
        if args.json or issues
        else "agent governance contract: PASS"
    )
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
