"""Build the clean, submission-grade Bonita Neuron Track Hours workbook.

Exactly two tabs (``Apr 26`` / ``May 26``), two-line headers, one row per
included shift, values only (no formulas, no notes/commentary). Reuses the
proven private inlineStr repair from ``exporter`` for Web Excel safety.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple

from triage.nw_prj_neuron_track_hours.bonita_resolver import BonitaResolution, BonitaShift
from triage.nw_prj_neuron_track_hours.exporter import _repair_inlinestr

# Two-line column headers: (top line, bottom line). The first column is the
# day/date locator; the rest match the embedded Bonitas Tracker layout.
HEADER_TOP = ["DATE", "TECH", "START", "END", "TOTAL", "PROJECT", "ASSIGNMENT"]
HEADER_BOTTOM = ["(DAY)", "NAME", "TIME", "TIME", "HOURS", "NAME", "TYPE"]

_MONTH_ABBR = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
               7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}

_HEADER_FILL = "1F365C"


def tab_name_for_month_key(month_key: str) -> str:
    """'2026-04' -> 'Apr 26'."""
    year, mon = month_key.split("-")[0], int(month_key.split("-")[1])
    return f"{_MONTH_ABBR[mon]} {year[-2:]}"


def _require_openpyxl():
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    return Workbook, Alignment, Font, PatternFill, get_column_letter


def _shift_row(shift: BonitaShift) -> List[object]:
    locator = f"{shift.date.strftime('%b %d')} ({shift.day})"
    return [
        locator,
        shift.tech,
        shift.clock_in,
        shift.clock_out,
        round(shift.total_hours, 2),
        shift.project_name,
        shift.assignment_type,
    ]


def _write_month_tab(wb, tab: str, shifts: List[BonitaShift]) -> None:
    Workbook, Alignment, Font, PatternFill, get_column_letter = _require_openpyxl()
    ws = wb.create_sheet(tab)
    fill = PatternFill("solid", fgColor=_HEADER_FILL)
    for c, (top, bottom) in enumerate(zip(HEADER_TOP, HEADER_BOTTOM), 1):
        t = ws.cell(row=1, column=c, value=top)
        b = ws.cell(row=2, column=c, value=bottom)
        for cell in (t, b):
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = fill
            cell.alignment = Alignment(horizontal="center")

    for r_idx, shift in enumerate(shifts, 3):
        for c, val in enumerate(_shift_row(shift), 1):
            ws.cell(row=r_idx, column=c, value=val)

    last_row = max(2, len(shifts) + 2)
    last_col = get_column_letter(len(HEADER_TOP))
    ws.freeze_panes = ws.cell(row=3, column=1).coordinate
    ws.auto_filter.ref = f"A2:{last_col}{last_row}"
    widths = [16, 22, 12, 12, 11, 22, 26]
    for c, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(c)].width = w


def build_bonita_workbook(
    resolution: BonitaResolution,
    months: List[str],
    out_path: str,
) -> Tuple[str, List[Tuple[str, str]]]:
    """Write the two-tab workbook. Returns (path, [(month_key, tab_name)...])."""
    Workbook, *_ = _require_openpyxl()
    wb = Workbook()
    wb.remove(wb.active)

    from triage.nw_prj_neuron_track_hours.reader import _month_label
    from calendar import month_name

    tabs: List[Tuple[str, str]] = []
    for mk in months:
        tab = tab_name_for_month_key(mk)
        _, _, mon = _month_label(mk)
        short = month_name[mon]
        shifts = resolution.shifts_for_month(short)
        _write_month_tab(wb, tab, shifts)
        tabs.append((mk, tab))

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    _repair_inlinestr(out_path)
    return out_path, tabs
