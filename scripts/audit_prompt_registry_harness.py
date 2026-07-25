#!/usr/bin/env python3
"""CLI for prompt-registry passage profiling and canary coverage audits."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from prompt_registry_harness_contracts import PromptRegistryHarnessError
from prompt_registry_profiles import build_report, print_summary, write_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Profile every effective prompt and audit canary coverage."
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--prompt")
    parser.add_argument("--strict-canary", action="store_true")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    try:
        report = build_report(
            prompt_id=args.prompt,
            strict_canary=args.strict_canary,
        )
        output = write_report(report, args.output) if args.output else None
    except (
        PromptRegistryHarnessError,
        SystemExit,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(
            f"Prompt registry harness audit failed: {exc}",
            file=sys.stderr,
        )
        return 2

    if args.summary or not args.output:
        print_summary(report, output)
    if not report["coverage_complete"]:
        return 1
    if args.strict_canary and not report["canary_ready"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
