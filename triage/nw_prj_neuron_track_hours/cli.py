"""CLI orchestrator for the NW PRJ Neuron Track Hours engine."""
from __future__ import annotations

import argparse
import csv
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.nw_prj_neuron_track_hours.classifier import (
    build_review_flags,
    build_tech_summary,
)
from triage.nw_prj_neuron_track_hours.exporter import EXPECTED_SHEETS, build_workbook
from triage.sidecar_html.adapters import neuron_track_sections
from triage.sidecar_html.portal import build_run_portal
from triage.nw_prj_neuron_track_hours.models import TrackHoursReport
from triage.nw_prj_neuron_track_hours.preflight import run_preflight
from triage.nw_prj_neuron_track_hours.reader import read_track_hours

DEFAULT_MONTHS = ["2026-04", "2026-05"]
WORKBOOK_NAME = "Neuron_Track_Hours_April_May_2026_WEBSAFE.xlsx"

# Regression targets from the proven reference artifact (tolerance applied).
REFERENCE_TARGETS = {
    "total": 1746.02,
    "april": 1048.19,
    "may": 697.83,
    "go_live_rows": 2,
    "go_live_hours": 22.0,
}


def _resolve(p: Optional[str], base: Path) -> Optional[Path]:
    if not p:
        return None
    pp = Path(p)
    return pp if pp.is_absolute() else (base / pp).resolve()


def build_report(
    roster_path: str,
    months: List[str],
    pinned_techs: Optional[List[str]] = None,
) -> TrackHoursReport:
    rows, warnings = read_track_hours(roster_path, months, pinned_techs=pinned_techs)
    report = TrackHoursReport(rows=rows, warnings=warnings)
    report.tech_summary = build_tech_summary(rows)
    report.review_flags = build_review_flags(rows)
    return report


def _qc_against_reference(report: TrackHoursReport) -> Dict[str, Any]:
    april = report.month_total("April")
    may = report.month_total("May")
    total = report.grand_total()
    go_rows = len(report.go_live_rows())
    go_hours = report.go_live_hours()
    tol = 0.05
    checks = {
        "april": (april, REFERENCE_TARGETS["april"], abs(april - REFERENCE_TARGETS["april"]) <= tol),
        "may": (may, REFERENCE_TARGETS["may"], abs(may - REFERENCE_TARGETS["may"]) <= tol),
        "total": (total, REFERENCE_TARGETS["total"], abs(total - REFERENCE_TARGETS["total"]) <= tol),
        "go_live_rows": (go_rows, REFERENCE_TARGETS["go_live_rows"], go_rows == REFERENCE_TARGETS["go_live_rows"]),
        "go_live_hours": (go_hours, REFERENCE_TARGETS["go_live_hours"], abs(go_hours - REFERENCE_TARGETS["go_live_hours"]) <= tol),
    }
    all_pass = all(v[2] for v in checks.values())
    return {
        "result": "PASS" if all_pass else "REVIEW",
        "notes": "; ".join(f"{k}={v[0]} (target {v[1]})" for k, v in checks.items()),
        "checks": {k: {"computed": v[0], "target": v[1], "pass": v[2]} for k, v in checks.items()},
        "all_pass": all_pass,
    }


def _write_reconciliation_json(path: Path, report: TrackHoursReport, qc: Dict[str, Any]) -> None:
    data = {
        "totals": {
            "total": report.grand_total(),
            "april": report.month_total("April"),
            "may": report.month_total("May"),
            "go_live_rows": len(report.go_live_rows()),
            "go_live_hours": report.go_live_hours(),
        },
        "reference_qc": qc,
        "row_count": len(report.rows),
        "tech_summary": [s.to_dict() for s in report.tech_summary],
        "warnings": report.warnings,
    }
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _write_review_queue_csv(path: Path, report: TrackHoursReport) -> None:
    cols = ["Severity", "Issue Type", "Action Status", "Review Result",
            "Month", "Date", "Day", "Tech", "Project",
            "Clock In", "Clock Out", "Gross Hours", "Note"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for fl in report.review_flags:
            row = fl.to_dict()
            for k, v in list(row.items()):
                if isinstance(v, str) and v[:1] in ("=", "+", "-", "@"):
                    row[k] = "'" + v
            w.writerow(row)


def _write_carryover_md(path: Path, report: TrackHoursReport, qc: Dict[str, Any]) -> None:
    lines = [
        "# Neuron Track Hours Carryover",
        "",
        "Roster-derived Neuron Deployment hours for April and May 2026.",
        "",
        "## Totals",
        f"- Total: {report.grand_total()} (target {REFERENCE_TARGETS['total']})",
        f"- April: {report.month_total('April')} (target {REFERENCE_TARGETS['april']})",
        f"- May: {report.month_total('May')} (target {REFERENCE_TARGETS['may']})",
        f"- Go Live weekend rows: {len(report.go_live_rows())} / hours: {report.go_live_hours()}",
        "",
        "## Carry forward",
        "- Action Status and Review Result columns are manual; preserve on regen.",
        "- PURPLE Rich Guard rows must not be downgraded.",
        "- Pinned techs are not roster-missing failures.",
        "",
        f"## Reference QC: {qc['result']}",
        f"- {qc['notes']}",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(
    roster_log: str,
    out_dir: str,
    months: Optional[List[str]] = None,
    admin_control: Optional[str] = None,
    reference: Optional[str] = None,
    pinned_techs: Optional[List[str]] = None,
    websafe: bool = True,
    zip_output: bool = False,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parent.parent.parent
    months = months or DEFAULT_MONTHS
    roster_path = _resolve(roster_log, root)
    if roster_path is None or not roster_path.exists():
        raise FileNotFoundError(f"roster-log not found: {roster_path}")
    out = _resolve(out_dir, root) or (root / "Outputs")
    out.mkdir(parents=True, exist_ok=True)

    report = build_report(str(roster_path), months, pinned_techs=pinned_techs)
    qc = _qc_against_reference(report)

    xlsx_path = out / WORKBOOK_NAME
    build_workbook(report, str(xlsx_path), reference_totals=qc)

    recon_path = out / "neuron_track_hours_reconciliation.json"
    _write_reconciliation_json(recon_path, report, qc)
    review_path = out / "neuron_track_hours_review_queue.csv"
    _write_review_queue_csv(review_path, report)
    carry_path = out / "neuron_track_hours_carryover.md"
    _write_carryover_md(carry_path, report, qc)

    preflight = None
    if websafe:
        preflight = run_preflight(str(xlsx_path), expected_sheets=EXPECTED_SHEETS)
    preflight_path = out / "neuron_track_hours_webexcel_preflight.json"
    preflight_path.write_text(
        json.dumps(preflight.to_dict() if preflight else {}, indent=2, default=str),
        encoding="utf-8",
    )

    outputs = {
        "workbook": str(xlsx_path),
        "reconciliation_json": str(recon_path),
        "review_queue_csv": str(review_path),
        "preflight_json": str(preflight_path),
        "carryover_md": str(carry_path),
    }

    zip_path = None
    if zip_output:
        zip_path = out / "Neuron_Track_Hours_April_May_2026_WEBSAFE.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for label, fp in outputs.items():
                p = Path(fp)
                if p.exists():
                    zf.write(p, arcname=p.name)
        outputs["zip"] = str(zip_path)

    manifest = {
        "engine": "triage.nw_prj_neuron_track_hours.cli",
        "roster_log": str(roster_path),
        "admin_control": str(_resolve(admin_control, root)) if admin_control else "",
        "reference": str(_resolve(reference, root)) if reference else "",
        "months": months,
        "pinned_techs": pinned_techs or [],
        "row_count": len(report.rows),
        "totals": {
            "total": report.grand_total(),
            "april": report.month_total("April"),
            "may": report.month_total("May"),
            "go_live_rows": len(report.go_live_rows()),
            "go_live_hours": report.go_live_hours(),
        },
        "reference_qc": qc,
        "review_flag_count": len(report.review_flags),
        "warnings": report.warnings,
        "websafe_preflight_pass": bool(preflight.preflight_pass) if preflight else None,
        "outputs": outputs,
    }
    manifest_path = out / "neuron_track_hours_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)

    portal_path = build_run_portal(
        out,
        title="Neuron Track Hours — Run Review",
        subtitle=f"Roster: {roster_path.name}",
        sections=neuron_track_sections(manifest),
    )
    manifest["html_portal"] = str(portal_path)
    manifest["outputs"]["html_portal"] = str(portal_path)
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="triage.nw_prj_neuron_track_hours.cli")
    ap.add_argument("--roster-log", required=True)
    ap.add_argument("--admin-control")
    ap.add_argument("--reference")
    ap.add_argument("--out-dir", default="Outputs/nw_prj_neuron_track_hours_2026_06_01")
    ap.add_argument("--months", nargs="+", default=DEFAULT_MONTHS)
    ap.add_argument("--pinned", nargs="*", default=[])
    ap.add_argument("--websafe", action="store_true", default=True)
    ap.add_argument("--no-websafe", action="store_false", dest="websafe")
    ap.add_argument("--zip", action="store_true", default=False, dest="zip_output")
    args = ap.parse_args(argv)

    manifest = run(
        roster_log=args.roster_log,
        out_dir=args.out_dir,
        months=args.months,
        admin_control=args.admin_control,
        reference=args.reference,
        pinned_techs=args.pinned,
        websafe=args.websafe,
        zip_output=args.zip_output,
    )
    print(json.dumps(manifest, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
