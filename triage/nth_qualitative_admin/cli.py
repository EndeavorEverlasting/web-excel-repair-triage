"""CLI for deterministic qualitative admin Neuron Track Hours workbooks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .builder import build_package, validate_spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the current June-completed/August-MTD qualitative admin NTH workbook family from a structured evidence packet."
    )
    parser.add_argument("--spec", required=True, type=Path, help="nth-qualitative-admin-input/v1 JSON evidence packet")
    parser.add_argument("--out-dir", type=Path, default=Path("Outputs/nth-qualitative-admin"))
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    payload = json.loads(args.spec.read_text(encoding="utf-8"))
    normalized = validate_spec(payload)
    if args.check_only:
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "mode": normalized["mode"],
                    "month_key": normalized["month_key"],
                    "detail_rows": len(normalized["detail_rows"]),
                },
                indent=2,
            )
        )
        return 0
    manifest = build_package(payload, args.out_dir)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
