#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from triage.july_nth_public_disclosure_report import build_report


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the July NTH public-disclosure producer report.")
    parser.add_argument("validation", type=Path, help="FUN disclosure validation JSON")
    parser.add_argument("--policy", type=Path, required=True, help="FUN July disclosure policy JSON")
    parser.add_argument("--json-output", type=Path, required=True, help="Output JSON report")
    parser.add_argument("--markdown-output", type=Path, required=True, help="Output Markdown report")
    args = parser.parse_args()

    bundle = build_report(_load(args.validation), _load(args.policy))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(bundle.report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(bundle.markdown + "\n", encoding="utf-8")
    print(bundle.markdown)
    return 0 if bundle.report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
