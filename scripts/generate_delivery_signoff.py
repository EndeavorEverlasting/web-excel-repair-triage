#!/usr/bin/env python3
"""CLI for the Triage delivery sign-off generator."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from triage.delivery_signoff import SignoffValidationError, generate_signoff  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an editable, validated delivery sign-off package.")
    parser.add_argument("spec", type=Path, help="delivery-signoff-spec/v1 JSON")
    parser.add_argument("--output-root", type=Path, default=Path("Outputs/delivery-signoff"))
    args = parser.parse_args()
    try:
        result = generate_signoff(args.spec, args.output_root)
    except SignoffValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: delivery sign-off generated")
    print(f"- package: {result.package_dir}")
    print(f"- docx: {result.docx_path}")
    print(f"- preview: {result.preview_pdf_path}")
    print(f"- manifest: {result.manifest_path}")
    print(f"- validation: {result.validation_log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
