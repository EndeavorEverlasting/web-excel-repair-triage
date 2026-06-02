"""Build the My Preferred Format admin billing workbook (with native charts).

Tab set mirrors the April "My Preferred Format" reference:
  Executive Summary | Project Summary (chart) | Tech Summary |
  Tech Project Summary (chart) | Trucking Reference | Billing Bucket Snapshot |
  Time Alignment | Roster QA - Internal | Daily Detail - Internal |
  Build Notes | Next Chat Prompt | <Neuron tracker tab e.g. "May 26">

Charts are native openpyxl BarCharts so they remain editable in Excel for Web.
The Neuron tracker tab is Neuron-only and rendered in the Bonita two-line
format, built from the SAME resolved records as the summary (one source of
truth, so Neuron Net and the tracker agree).
"""
from __future__ import annotations

from calendar import month_name as _month_name
from pathlib import Path
from typing import Any, Dict, List, Tuple

from triage.admin_billing_summary.models import (
    DailyRecord,
    MonthSummary,
    billing_bucket,
)
from triage.nw_prj_neuron_track_hours.bonita_exporter import (
    _write_month_tab,
    tab_name_for_month_key,
)
from triage.nw_prj_neuron_track_hours.bonita_resolver import (
    BonitaShift,
    NEURON_DISPLAY_NAME,
    _classify_assignment,
)
from triage.nw_prj_neuron_track_hours.exporter import _repair_inlinestr

_HEADER_FILL = "1F365C"
_SUBTITLE_FILL = "EAF1F8"


def _xl():
    from openpyxl import Workbook
    from openpyxl.chart import BarChart, Reference
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    return Workbook, BarChart, Reference, Alignment, Font, PatternFill, get_column_letter


def _band(ws, title: str, subtitle: str, width: int) -> None:
    _, _, _, _, Font, PatternFill, _ = _xl()
    ws.cell(row=1, column=1, value=title).font = Font(bold=True, size=14, color="FFFFFF")
    tf = PatternFill("solid", fgColor=_HEADER_FILL)
    sf = PatternFill("solid", fgColor=_SUBTITLE_FILL)
    for c in range(1, max(2, width + 1)):
        ws.cell(row=1, column=c).fill = tf
        ws.cell(row=2, column=c).fill = sf
    ws.cell(row=2, column=1, value=subtitle)


def _write_table(ws, title: str, subtitle: str, headers: List[str],
                 rows: List[Dict[str, Any]], header_row: int = 4) -> Tuple[int, int]:
    _, _, _, Alignment, Font, PatternFill, get_column_letter = _xl()
    _band(ws, title, subtitle, len(headers))
    fill = PatternFill("solid", fgColor=_HEADER_FILL)
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=c, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = fill
        cell.alignment = Alignment(horizontal="center")
    for ri, row in enumerate(rows, header_row + 1):
        for c, h in enumerate(headers, 1):
            ws.cell(row=ri, column=c, value=row.get(h, ""))
    last_row = max(header_row, len(rows) + header_row)
    ws.freeze_panes = ws.cell(row=header_row + 1, column=1).coordinate
    ws.auto_filter.ref = f"A{header_row}:{get_column_letter(len(headers))}{last_row}"
    for c in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(c)].width = 24 if c <= 2 else 16
    return header_row, last_row


def _add_net_hours_chart(ws, title: str, headers: List[str], header_row: int,
                         last_row: int, anchor: str) -> None:
    if last_row <= header_row:
        return
    _, BarChart, Reference, _, _, _, _ = _xl()
    net_col = headers.index("Net Hours") + 1
    chart = BarChart()
    chart.type = "col"
    chart.title = title
    chart.y_axis.title = "Net Hours"
    chart.height = 9
    chart.width = 20
    data = Reference(ws, min_col=net_col, min_row=header_row, max_row=last_row)
    cats = Reference(ws, min_col=1, min_row=header_row + 1, max_row=last_row)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.legend = None
    ws.add_chart(chart, anchor)


def _neuron_shifts(summary: MonthSummary) -> List[BonitaShift]:
    _, _, mon = _parse_key(summary.month_key)
    short = _month_name[mon]
    shifts: List[BonitaShift] = []
    for r in summary.neuron_records():
        assignment_type, _ = _classify_assignment(r.note, r.worked_label)
        shifts.append(BonitaShift(
            month_key=summary.month_key,
            month_name=short,
            date=r.date,
            day=r.day,
            tech=r.tech,
            clock_in=r.clock_in,
            clock_out=r.clock_out,
            total_hours=r.gross_span,
            project_name=NEURON_DISPLAY_NAME,
            assignment_type=assignment_type,
            note=r.note,
            long_shift=r.long_shift,
        ))
    shifts.sort(key=lambda s: (s.date, s.tech))
    return shifts


def _parse_key(month_key: str):
    import re
    m = re.match(r"^(\d{4})-(\d{1,2})$", month_key.strip())
    return m.group(1), int(m.group(1)), int(m.group(2))


def build_workbook(summary: MonthSummary, out_path: str,
                   roster_name: str = "") -> str:
    Workbook, *_ = _xl()
    wb = Workbook()
    wb.remove(wb.active)
    label = summary.month_name

    # ── Executive Summary ──
    ws = wb.create_sheet("Executive Summary")
    _band(ws, f"{label} Admin Billing Summary",
          "Admin-facing rollup: net hours after lunch, multi-project resolved.", 7)
    grid = [
        (8, [("Total Net Hours", summary.total_net), ("Gross Span", summary.total_gross),
             ("Lunch / Unpaid", summary.total_lunch), ("Techs Reflected", summary.techs_reflected)]),
        (11, [("Projects Reflected", summary.projects_reflected),
              ("Neuron Net", summary.net_for_bucket("Neurons")),
              ("Projects Team Net", summary.net_for_bucket("Projects Team")),
              ("Delivery / Transport Net", summary.net_for_bucket("Delivery / Transport / Disposal"))]),
    ]
    from openpyxl.styles import Font as _F
    for label_row, items in grid:
        for i, (name, _v) in enumerate(items):
            ws.cell(row=label_row, column=1 + i * 2, value=name).font = _F(bold=True)
        for i, (_n, value) in enumerate(items):
            ws.cell(row=label_row + 1, column=1 + i * 2, value=value)
    for c in range(1, 8):
        ws.column_dimensions[chr(64 + c)].width = 18

    # ── Project Summary (+ chart) ──
    ws = wb.create_sheet("Project Summary")
    headers = ["Project", "Tech Count", "Worked Days", "Gross Span Hours", "Lunch Deducted", "Net Hours"]
    hr, lr = _write_table(ws, f"{label} Project Summary",
                          "Roster-based project rollup (net hours after lunch).",
                          headers, [r.to_dict() for r in summary.project_rows])
    _add_net_hours_chart(ws, "Net Hours by Project", headers, hr, lr, "H4")

    # ── Tech Summary ──
    ws = wb.create_sheet("Tech Summary")
    th = ["Tech", "Project(s)", "Worked Days", "Gross Span Hours", "Lunch Deducted", "Net Hours"]
    _write_table(ws, f"{label} Technician Summary",
                 "Summary-only technician rollup with project list.",
                 th, [r.to_dict() for r in summary.tech_rows])

    # ── Tech Project Summary (+ chart) ──
    ws = wb.create_sheet("Tech Project Summary")
    tph = ["Tech", "Project", "Worked Days", "Gross Span Hours", "Lunch Deducted", "Net Hours"]
    hr, lr = _write_table(ws, f"{label} Technician by Project",
                          "Technician/project aggregate (net hours after lunch).",
                          tph, [r.to_dict() for r in summary.tech_project_rows])
    _add_net_hours_chart(ws, "Net Hours by Technician and Project", tph, hr, lr, "H4")

    # ── Trucking Reference ──
    ws = wb.create_sheet("Trucking Reference")
    crew = sorted({r.tech for r in summary.records
                   if billing_bucket(r.project) == "Delivery / Transport / Disposal"})
    _write_table(ws, "Trucking Crew Standard Model",
                 "Consistent monthly model for the delivery/transport crew.",
                 ["Field", "Value", "Notes"],
                 [{"Field": "Crew count", "Value": len(crew), "Notes": ", ".join(crew)},
                  {"Field": "Standard schedule", "Value": "8:00 AM-5:00 PM", "Notes": "9-hour span"},
                  {"Field": "Billing bucket", "Value": "Delivery / Transport / Disposal", "Notes": ""}])

    # ── Billing Bucket Snapshot ──
    ws = wb.create_sheet("Billing Bucket Snapshot")
    bh = ["Billing Bucket", "Tech Count", "Worked Rows", "Billable Hours"]
    _write_table(ws, f"{label} Billing Bucket Snapshot",
                 "Bucket-scoped net hours across all resolved rows.",
                 bh, [r.to_dict() for r in summary.bucket_rows])

    # ── Time Alignment (informational) ──
    ws = wb.create_sheet("Time Alignment")
    _write_table(ws, f"{label} Time Alignment",
                 "Roster-derived span vs net; submitted payroll feed not in roster.",
                 ["Metric", "Hours", "Note"],
                 [{"Metric": "Gross Span Hours", "Hours": summary.total_gross, "Note": "From roster punches."},
                  {"Metric": "Lunch / Unpaid", "Hours": summary.total_lunch, "Note": "Lunch policy deduction."},
                  {"Metric": "Net Hours", "Hours": summary.total_net, "Note": "Gross minus lunch."},
                  {"Metric": "Submitted Regular / OT", "Hours": "", "Note": "External payroll feed - provide to populate."}])

    # ── Roster QA - Internal ──
    ws = wb.create_sheet("Roster QA - Internal")
    _write_table(ws, "Roster QA Review - Internal",
                 "Hidden support tab: parse warnings and malformed rows.",
                 ["QA Type", "Count", "Detail"],
                 [{"QA Type": "Errors", "Count": len(summary.malformed),
                   "Detail": "; ".join(summary.malformed[:5])},
                  {"QA Type": "Warnings", "Count": len(summary.warnings),
                   "Detail": "; ".join(summary.warnings[:5])}])
    ws.sheet_state = "hidden"

    # ── Daily Detail - Internal ──
    ws = wb.create_sheet("Daily Detail - Internal")
    dh = ["Date", "Day", "Tech", "Project", "Clock In", "Clock Out",
          "Gross Span", "Lunch", "Net Hours", "Flag"]
    _write_table(ws, "Daily Detail - Internal",
                 "Hidden support tab: daily resolved records.",
                 dh, [r.to_detail_dict() for r in summary.records])
    ws.sheet_state = "hidden"

    # ── Build Notes ──
    ws = wb.create_sheet("Build Notes")
    _write_table(ws, "Build Notes", "Hidden support tab: build provenance.",
                 ["Item", "Value"],
                 [{"Item": "Source workbook", "Value": roster_name},
                  {"Item": "Primary extraction layer", "Value": f"Worked Projects / Assignments - {label}"},
                  {"Item": "Project resolution", "Value": "Override > Worked > Assignment > Live default"},
                  {"Item": "Net hours", "Value": "Gross span minus lunch (>=8h:1.0, >=6h:0.5)"}])
    ws.sheet_state = "hidden"

    # ── Next Chat Prompt ──
    ws = wb.create_sheet("Next Chat Prompt")
    _band(ws, "Next Chat Prompt", "Hidden support tab for continuity.", 2)
    ws.cell(row=4, column=1, value=(
        f"Continuing the admin billing summary for {label}. Regenerate from the "
        "Active Roster Log; preserve multi-project resolution and the Neuron "
        "Track Hours tracker tab; compare to prior month for deltas."))
    ws.sheet_state = "hidden"

    # ── Neuron Track Hours tracker tab (e.g. "May 26") ──
    _write_month_tab(wb, tab_name_for_month_key(summary.month_key), _neuron_shifts(summary))

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    _repair_inlinestr(out_path)
    return out_path
