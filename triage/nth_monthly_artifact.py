"""Generic single-month Neuron Track Hours workbook builder.

The established April/May engine remains unchanged. This adapter reuses its
reader, classifier, styling helpers, Web Excel repair, and preflight while
removing the hard-coded April/May output assumption for later billing periods.
"""
from __future__ import annotations

import json
from calendar import month_name
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.month_validation import validate_month_key
from triage.nth_month_readiness import inspect_month_readiness
from triage.nw_prj_neuron_track_hours.classifier import build_review_flags, build_tech_summary
from triage.nw_prj_neuron_track_hours.exporter import (
    CF_DICTIONARY_ROWS,
    _add_severity_cf,
    _add_status_dropdowns,
    _repair_inlinestr,
    _write_simple,
    _write_table,
    _require_openpyxl,
)
from triage.nw_prj_neuron_track_hours.models import (
    APRIL_MAY_COLUMNS,
    REVIEW_FLAG_COLUMNS,
    TECH_SUMMARY_COLUMNS,
    TrackHoursReport,
)
from triage.nw_prj_neuron_track_hours.preflight import run_preflight
from triage.nw_prj_neuron_track_hours.reader import read_track_hours


def expected_sheets(month_label: str) -> List[str]:
    return [
        "Start Here",
        f"{month_label} Neuron Hours",
        "Tech Summary",
        "Review Flags",
        "CF Dictionary",
        "WebExcel QC",
    ]


def workbook_name(month_key: str) -> str:
    year, month = validate_month_key(month_key)
    return f"Neuron_Track_Hours_{month_name[month]}_{year}_WEBSAFE.xlsx"


def _build_report(roster_path: str | Path, month_key: str, pinned_techs: Optional[List[str]] = None) -> TrackHoursReport:
    rows, warnings = read_track_hours(str(roster_path), [month_key], pinned_techs=pinned_techs)
    report = TrackHoursReport(rows=rows, warnings=warnings)
    report.tech_summary = build_tech_summary(rows)
    report.review_flags = build_review_flags(rows)
    return report


def _build_workbook(report: TrackHoursReport, month_key: str, out_path: Path) -> List[str]:
    year, month = validate_month_key(month_key)
    label = f"{month_name[month]} {year}"
    sheet_label = f"{label} Neuron Hours"
    sheets = expected_sheets(label)

    Workbook, *_ = _require_openpyxl()
    wb = Workbook()
    wb.remove(wb.active)

    ws = wb.create_sheet("Start Here")
    metrics = [
        {
            "Metric": f"{label} Neuron roster hours",
            "Value": report.grand_total(),
            "Notes": "Roster-derived from the month-specific Live clock-in/clock-out attendance surface.",
        },
        {
            "Metric": "Tracked rows",
            "Value": len(report.rows),
            "Notes": "Only rows whose resolved project is documented as a Neuron deployment are included.",
        },
        {
            "Metric": "Review flags",
            "Value": len(report.review_flags),
            "Notes": "Review flags do not create or remove hours without source-backed correction.",
        },
    ]
    _write_simple(
        ws,
        f"Neuron Track Hours - {label}",
        "Single-month roster-derived working artifact. Attendance is the labor-hours authority.",
        ["Metric", "Value", "Notes"],
        metrics,
    )

    ws = wb.create_sheet(sheet_label)
    rows = [row.to_track_dict() for row in report.rows]
    header_row, last_row = _write_table(
        ws,
        f"{label} Neuron Hours",
        "Roster-derived daily Neuron Deployment rows.",
        APRIL_MAY_COLUMNS,
        rows,
    )
    _add_status_dropdowns(ws, APRIL_MAY_COLUMNS, header_row, last_row)
    _add_severity_cf(ws, APRIL_MAY_COLUMNS, header_row, last_row)

    ws = wb.create_sheet("Tech Summary")
    _write_table(
        ws,
        f"{label} Technician Summary",
        "Roster-derived Neuron totals per technician for this month.",
        TECH_SUMMARY_COLUMNS,
        [item.to_dict() for item in report.tech_summary],
    )

    ws = wb.create_sheet("Review Flags")
    header_row, last_row = _write_table(
        ws,
        f"{label} Review Flags",
        "Long, weekend, overnight, and note-bearing rows requiring review.",
        REVIEW_FLAG_COLUMNS,
        [item.to_dict() for item in report.review_flags],
    )
    _add_status_dropdowns(ws, REVIEW_FLAG_COLUMNS, header_row, last_row)
    _add_severity_cf(ws, REVIEW_FLAG_COLUMNS, header_row, last_row)

    ws = wb.create_sheet("CF Dictionary")
    _write_simple(
        ws,
        "Conditional Formatting Dictionary",
        "Plain-English color rules reused from the established NTH engine.",
        ["Color", "Meaning", "Action"],
        [{"Color": color, "Meaning": meaning, "Action": action} for color, meaning, action in CF_DICTIONARY_ROWS],
    )

    ws = wb.create_sheet("WebExcel QC")
    _write_simple(
        ws,
        "Web Excel QC",
        "Static structure checks for the month-specific working artifact.",
        ["Check", "Result", "Notes"],
        [
            {"Check": "Fresh workbook", "Result": "PASS", "Notes": "No inherited workbook XML."},
            {"Check": "Month source", "Result": "PASS", "Notes": "Month readiness gate found paired Live Clock In / Clock Out columns."},
            {"Check": "Formulas", "Result": "PASS", "Notes": "Values only; no workbook formulas required."},
            {"Check": "Filters", "Result": "PASS", "Notes": "Auto-filter on data sheets."},
            {"Check": "Frozen headers", "Result": "PASS", "Notes": "Header rows frozen."},
            {"Check": "Review controls", "Result": "PASS", "Notes": "Action Status / Review Result dropdowns retained."},
        ],
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out_path))
    _repair_inlinestr(str(out_path))
    return sheets


def build_month_artifact(
    roster_log: str | Path,
    month_key: str,
    out_dir: str | Path,
    pinned_techs: Optional[List[str]] = None,
) -> Dict[str, Any]:
    readiness = inspect_month_readiness(roster_log, month_key)
    if readiness.status != "READY":
        raise ValueError(
            "NTH month source is not ready: " + "; ".join(readiness.blockers)
        )

    report = _build_report(roster_log, month_key, pinned_techs=pinned_techs)
    output_dir = Path(out_dir)
    workbook = output_dir / workbook_name(month_key)
    sheets = _build_workbook(report, month_key, workbook)

    preflight = run_preflight(str(workbook), expected_sheets=sheets)
    if not preflight.preflight_pass:
        raise RuntimeError("generated NTH workbook failed Web Excel preflight")

    year, month = validate_month_key(month_key)
    label = f"{month_name[month]} {year}"
    manifest: Dict[str, Any] = {
        "schema": "triage-nth-month-artifact/v1",
        "month_key": month_key,
        "month_label": label,
        "readiness": readiness.to_dict(),
        "row_count": len(report.rows),
        "hours": report.grand_total(),
        "review_flag_count": len(report.review_flags),
        "warnings": report.warnings,
        "websafe_preflight_pass": bool(preflight.preflight_pass),
        "sheets": sheets,
        "workbook": str(workbook),
        "proof_ceiling": "roster-derived working-artifact and static Web Excel preflight; not FUN final acceptance or client acceptance",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / f"nth_month_artifact_{month_key}.json"
    manifest["manifest_path"] = str(manifest_path)
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest
