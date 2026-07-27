"""Independent validator CLI for generated Device Transfer / Stock Sign-Off workbooks."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from triage.device_transfer_signoff import (
    SignOffContractError,
    _extract_serialized_items,
    _read_json,
    _serial_layout,
    preflight_workbook,
    validate_config,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m triage.device_transfer_signoff_validator",
        description="Validate a generated sign-off against its exact source workbook and site config.",
    )
    parser.add_argument("--workbook", required=True)
    parser.add_argument("--source-configs", required=True)
    parser.add_argument("--site-config", required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    try:
        config = _read_json(Path(args.site_config))
        validate_config(config)
        _, serialized = _extract_serialized_items(Path(args.source_configs), config)
        layout = _serial_layout(len(config["shipment"]), serialized)
        report = preflight_workbook(Path(args.workbook), config, serialized, layout)
    except SignOffContractError as exc:
        report = {"preflight_pass": False, "error": str(exc)}

    text = json.dumps(report, indent=2)
    print(text)
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    return 0 if report.get("preflight_pass") else 1


if __name__ == "__main__":
    sys.exit(main())
