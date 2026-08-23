#!/usr/bin/env python3
"""Fail closed when staged paths contain generated, secret, or machine-local material."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from triage.artifact_hygiene_policy import render_findings, scan_paths

GIT_TIMEOUT_SECONDS = 15


def staged_paths(root: Path = ROOT) -> list[str]:
    command = [
        "git",
        "diff",
        "--cached",
        "--name-only",
        "--diff-filter=ACMR",
        "-z",
    ]
    try:
        result = subprocess.run(
            command,
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"staged-path Git probe timed out after {GIT_TIMEOUT_SECONDS}s"
        ) from exc
    except OSError as exc:
        raise RuntimeError(f"staged-path Git probe failed: {exc}") from exc

    if result.returncode != 0:
        raise RuntimeError(
            f"staged-path Git probe exited with code {result.returncode}"
        )

    decoded = result.stdout.decode("utf-8", errors="replace")
    return [item for item in decoded.split("\0") if item]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Block staged generated/runtime evidence, secrets, crash dumps, "
            "and machine-local junk without opening file contents."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional explicit paths for focused validation; defaults to the staged index.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        paths = list(args.paths) if args.paths else staged_paths()
    except RuntimeError as exc:
        print(f"[harness] {exc}", file=sys.stderr)
        return 2

    findings = scan_paths(paths)
    if findings:
        print(render_findings(findings), file=sys.stderr)
        return 1

    print(f"[harness] staged artifact hygiene: PASS ({len(paths)} path(s) inspected)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
