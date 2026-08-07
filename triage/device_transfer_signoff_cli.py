"""CLI for the Device Transfer / Stock Sign-Off generator."""
from __future__ import annotations

import argparse
import json
import sys

from triage.device_transfer_signoff import SignOffContractError, run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m triage.device_transfer_signoff_cli",
        description=(
            "Generate a shipping-ready Device Transfer / Stock Sign-Off workbook "
            "from an exact site config and a serialized device source workbook."
        ),
    )
    parser.add_argument("--source-configs", required=True, help="Read-only source .xlsx containing serialized devices.")
    parser.add_argument("--site-config", required=True, help="JSON authority for site metadata and exact shipment rows.")
    parser.add_argument("--output", help="Explicit output .xlsx path.")
    parser.add_argument(
        "--out-dir",
        default="Outputs/device_transfer_signoff",
        help="Default output directory when --output is omitted.",
    )
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run(
            args.source_configs,
            args.site_config,
            output=args.output,
            out_dir=args.out_dir,
        )
    except SignOffContractError as exc:
        print(json.dumps({"error": "device_transfer_signoff_contract", "detail": str(exc)}, indent=2))
        return 2

    print(json.dumps(result.report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
