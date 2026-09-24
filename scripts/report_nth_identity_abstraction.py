#!/usr/bin/env python3
"""Emit a fail-closed triage report from FUN identity-abstraction validation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from triage.nth_identity_abstraction_report import build_report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation", required=True, type=Path, help="fun-nth-identity-abstraction-result/v1 JSON")
    parser.add_argument("--policy", required=True, type=Path, help="fun-nth-identity-abstraction-policy/v1 JSON")
    parser.add_argument("--json-out", required=True, type=Path, help="triage report JSON output")
    parser.add_argument("--markdown-out", required=True, type=Path, help="triage report Markdown output")
    return parser.parse_args(argv)


def load_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        validation = load_object(args.validation)
        policy = load_object(args.policy)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL: cannot load report inputs: {exc}")
        return 2
    bundle = build_report(validation, policy)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(bundle.report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(bundle.markdown, encoding="utf-8")
    print(bundle.markdown, end="")
    return 0 if bundle.report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
