#!/usr/bin/env python3
"""Fail closed when the repository governance doctrine is missing or malformed."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE_PATH = Path("AGENTS.md")
MAX_CHARS = 5200

REQUIRED_SECTIONS = (
    "## 1. Agent operating principles",
    "## 2. Instruction precedence",
    "## 3. Mandatory sprint declaration",
    "## 4. Completion standard",
    "## 5. Safety and mutation boundaries",
    "## 6. Repository identity and product boundary",
    "## 7. Progressive disclosure and binding domain law",
)

REQUIRED_MARKERS = (
    "single repository governance authority",
    "Evidence before action",
    "Floor before furniture",
    "Bounded sprints",
    "One writer per branch",
    "Reuse before replacing",
    "No completion without proof",
    "Platform, security, legal, and repository-owner instructions",
    "Task-specific prompts and sprint instructions",
    "repository and branch/worktree",
    "owned and forbidden scope",
    "validation commands/order",
    "proof ceiling",
    "one exact next command",
    "force-push",
    "secrets, credentials",
    "spreadsheet intelligence",
    "Web Excel compatibility, billing",
    "dedicated repository under `UnderDeskDev`",
    "not yet named or created",
    "must not invent its name",
    "Prompt Kit sources here remain operationally authoritative",
    "must not become a competing Prompt Kit authority",
    "cross-repo dependencies explicit and versioned",
    "Do **not** preload",
)


def fail(message: str) -> int:
    print(f"Governance doctrine validation: FAIL: {message}", file=sys.stderr)
    return 1


def is_tracked(root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--error-unmatch", "--", GOVERNANCE_PATH.as_posix()],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def validate(root: Path) -> tuple[bool, str]:
    path = root / GOVERNANCE_PATH
    if not path.is_file():
        return False, "AGENTS.md is missing"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return False, f"AGENTS.md is unreadable UTF-8: {exc}"
    if not text.strip():
        return False, "AGENTS.md is empty"
    if len(text) > MAX_CHARS:
        return False, f"AGENTS.md exceeds context budget: {len(text)}>{MAX_CHARS} chars"
    if not is_tracked(root):
        return False, "AGENTS.md is not tracked by git"

    previous = -1
    for section in REQUIRED_SECTIONS:
        position = text.find(section)
        if position < 0:
            return False, f"missing required section: {section}"
        if position <= previous:
            return False, f"governance sections are out of order at: {section}"
        previous = position

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    if missing:
        return False, "missing required doctrine marker(s): " + ", ".join(missing)

    if "Prompt Kit" not in text or "spreadsheet intelligence" not in text:
        return False, "repository/product boundary is incomplete"

    return True, f"AGENTS.md tracked and well-formed ({len(text)} chars)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.expanduser().resolve()
    ok, detail = validate(root)
    if not ok:
        return fail(detail)
    if args.summary:
        print(f"Governance doctrine validation: PASS: {detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
