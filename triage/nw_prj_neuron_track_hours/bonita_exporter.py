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

# Two-line column headers matching the "Mon YY" reference tracker tab. Column A
# is the day/date locator and intentionally has no header text (the weekday name
# and date are stacked there per date group, exactly like the reference).
HEADER_TOP = ["", "TECH", "START", "END", "TOTAL", "PROJECT", "ASSIGNMENT"]
HEADER_BOTTOM = ["", "NAME", "TIME", "TIME", "HOURS", "NAME", "TYPE"]

_MONTH_ABBR = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
               7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}

_HEADER_FILL = "1F365C"
# Excel number formats matching the reference tracker.
_TIME_FMT = "h:mm AM/PM"
_DATE_FMT = "mm-dd-yy"


def tab_name_for_month_key(month_key: str) -> str:
    """'2026-04' -> 'Apr 26'."""
    year, mon = month_key.split("-")[0], int(month_key.split("-")[1])
    return f"{_MONTH_ABBR[mon]} {year[-2:]}"


def _require_openpyxl():
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    return Workbook, Alignment, Font, PatternFill, get_column_letter


def _group_locators(shifts: List[BonitaShift]) -> List[object]:
    """Column-A locator per row: weekday name on the first row of a date group,
    the date value on the second row, blank thereafter (reference layout).

    Single-row date groups get the date directly so the date is never dropped.
    """
    locators: List[object] = []
    n = len(shifts)
    i = 0
    while i < n:
        j = i
        while j < n and shifts[j].date == shifts[i].date:
            j += 1
        size = j - i
        if size == 1:
            locators.append(shifts[i].date)
        else:
            locators.append(shifts[i].date.strftime("%A").upper())
            locators.append(shifts[i].date)
            locators.extend([""] * (size - 2))
        i = j
    return locators


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

    bold = Font(bold=True)
    locators = _group_locators(shifts)
    for r_idx, (shift, locator) in enumerate(zip(shifts, locators), 3):
        a = ws.cell(row=r_idx, column=1, value=locator)
        a.font = bold
        if isinstance(locator, date):
            a.number_format = _DATE_FMT

        tech = ws.cell(row=r_idx, column=2, value=shift.tech)

        # Real time cells (h:mm AM/PM) when available, else the display string.
        if shift.start_time is not None:
            si = ws.cell(row=r_idx, column=3, value=shift.start_time)
            si.number_format = _TIME_FMT
        else:
            si = ws.cell(row=r_idx, column=3, value=shift.clock_in)
        if shift.end_time is not None:
            so = ws.cell(row=r_idx, column=4, value=shift.end_time)
            so.number_format = _TIME_FMT
        else:
            so = ws.cell(row=r_idx, column=4, value=shift.clock_out)

        tot = ws.cell(row=r_idx, column=5, value=round(shift.total_hours, 2))
        tot.number_format = "0.00"
        proj = ws.cell(row=r_idx, column=6, value=shift.project_name)
        asn = ws.cell(row=r_idx, column=7, value=shift.assignment_type)
        for cell in (tech, si, so, tot, proj, asn):
            cell.font = bold

    widths = [14, 27, 12, 12, 11, 22, 28]
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
