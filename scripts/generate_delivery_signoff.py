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

CANONICAL_OUTPUT_ROOT = (ROOT / "Outputs" / "delivery-signoff").resolve()


def _validated_output_root(spec_path: Path, output_root: Path) -> Path:
    source = spec_path.resolve()
    candidate = output_root.resolve()
    try:
        candidate.relative_to(CANONICAL_OUTPUT_ROOT)
    except ValueError as exc:
        raise SignoffValidationError(
            f"output root must be {CANONICAL_OUTPUT_ROOT} or one of its descendants"
        ) from exc
    try:
        source.relative_to(CANONICAL_OUTPUT_ROOT)
    except ValueError:
        pass
    else:
        raise SignoffValidationError("input specification must not be stored inside generated output")
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an editable, validated delivery sign-off package.")
    parser.add_argument("spec", type=Path, help="delivery-signoff-spec/v1 JSON")
    parser.add_argument("--output-root", type=Path, default=CANONICAL_OUTPUT_ROOT)
    args = parser.parse_args()
    try:
        output_root = _validated_output_root(args.spec, args.output_root)
        result = generate_signoff(args.spec, output_root)
    except SignoffValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: unexpected generation error: {type(exc).__name__}: {exc}", file=sys.stderr)
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
