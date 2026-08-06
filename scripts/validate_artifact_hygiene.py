#!/usr/bin/env python3
"""Run tracked-artifact policy and focused local-hook regressions."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> int:
    print("[harness] running:", " ".join(command))
    completed = subprocess.run(command, cwd=ROOT, check=False)
    return completed.returncode


def main() -> int:
    commands = [
        [sys.executable, "-m", "triage.gitignore_hygiene"],
        [
            sys.executable,
            "-m",
            "unittest",
            "tests.test_gitignore_hygiene",
            "tests.test_local_hook_artifact_hygiene",
            "-v",
        ],
    ]
    for command in commands:
        code = run(command)
        if code:
            return code
    print("[harness] local hook and artifact hygiene: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
