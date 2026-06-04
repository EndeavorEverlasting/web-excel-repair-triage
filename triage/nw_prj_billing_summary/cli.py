"""CLI for the NW PRJ April/May billing summary engine.

Example:
    python -m triage.nw_prj_billing_summary.cli \\
        --roster-log "Candidates/<private active roster log>.xlsx" \\
        --months 2026-04 2026-05 \\
        --out-dir Outputs/nw_prj_billing_summary_2026_06_02 \\
        --websafe --zip

Private workbook paths are accepted but never committed. Invoices are optional
(.docx parsed via triage.invoice_parser) and roll up into the Invoice Pivot tab.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .exporter import DEFAULT_ARTIFACT, run_export


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m triage.nw_prj_billing_summary.cli",
        description="Generate a combined April+May NW PRJ billing summary (Web Excel-safe).",
    )
    p.add_argument("--roster-log", required=True, help="Active Roster Log workbook (.xlsx).")
    p.add_argument("--months", nargs="+", default=["2026-04", "2026-05"],
                   help="Month keys (YYYY-MM). Default: 2026-04 2026-05.")
    p.add_argument("--invoices", nargs="*", default=[], help="Optional invoice files (.docx).")
    p.add_argument("--out-dir", default="Outputs/nw_prj_billing_summary",
                   help="Output directory for the workbook and sidecars.")
    p.add_argument("--artifact", default=DEFAULT_ARTIFACT, help="Artifact base name.")
    p.add_argument("--websafe", action="store_true", help="Apply Web Excel-safe pass + preflight.")
    p.add_argument("--zip", dest="make_zip", action="store_true", help="Also write a DELIVERY.zip.")
    p.add_argument("--report-json", help="Write the report manifest JSON to this path.")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    invoices = []
    if args.invoices:
        try:
            from triage.invoice_parser import parse_invoices

            invoices = parse_invoices(args.invoices)
        except Exception as exc:  # noqa: BLE001 - invoices are optional context
            print(json.dumps({"warning": "invoice_parse_failed", "detail": str(exc)}))

    result = run_export(
        args.roster_log,
        args.months,
        args.out_dir,
        websafe=args.websafe,
        make_zip=args.make_zip,
        invoices=invoices,
        artifact=args.artifact,
    )

    manifest = result.report.to_manifest()
    manifest["outputs"] = result.outputs
    print(json.dumps(manifest, indent=2))

    if args.report_json:
        Path(args.report_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report_json).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if args.websafe and not result.report.webexcel_preflight_pass:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
