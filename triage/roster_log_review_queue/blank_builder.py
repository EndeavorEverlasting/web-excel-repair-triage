"""Build a new roster review workbook shell for ``--mode blank``."""
from __future__ import annotations

from calendar import month_abbr, month_name, monthrange
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from triage.month_validation import validate_month_key

REVIEW_QUEUE_HEADERS = [
    "Review ID",
    "Month",
    "Date",
    "Staff",
    "Source Sheet",
    "Source Cells",
    "Rule Code",
    "Severity",
    "Current Status",
    "Detected Value",
    "Expected Value",
    "Suggested Resolution",
    "Resolution Value",
    "Resolution Source",
    "Owner",
    "Last Reviewed",
    "Notes",
]

REVIEW_RULES: List[Tuple[str, str, str, str]] = [
    ("MISSING_PROJECT", "Red", "Staff row has no project", "Assign or confirm the project."),
    ("INCOMPLETE_PUNCH", "Red", "Only one punch is present", "Confirm the missing clock value."),
    ("NON_WORK_MARKER", "Green", "Punch contains PTO, sick, N/A, or day-off text", "Confirm the non-work marker."),
    ("LONG_SHIFT_12_PLUS", "Blue", "Gross punch span is at least 12 hours", "Review the shift and confirm the hours."),
    ("EXTENDED_SHIFT_8_TO_12", "Purple", "Gross punch span is over 8 and under 12 hours", "Review for lunch or split-shift context."),
    ("SHORT_SHIFT_UNDER_8", "Amber", "Gross punch span is over 0 and under 8 hours", "Confirm the partial shift."),
    ("NOTE_BEARING_PUNCH", "Light Blue", "Punch contains a note delimiter", "Review and preserve the note as evidence."),
]

CF_DICTIONARY: List[Tuple[str, str, str]] = [
    ("Red", "Missing project or incomplete punch", "MISSING_PROJECT, INCOMPLETE_PUNCH"),
    ("Green", "Documented non-work marker", "NON_WORK_MARKER"),
    ("Blue", "Shift is 12 hours or longer", "LONG_SHIFT_12_PLUS"),
    ("Purple", "Shift is over 8 and under 12 hours", "EXTENDED_SHIFT_8_TO_12"),
    ("Amber", "Shift is under 8 hours", "SHORT_SHIFT_UNDER_8"),
    ("Light Blue", "Punch contains reviewable note text", "NOTE_BEARING_PUNCH"),
]


def _normalize_months(months: Iterable[str]) -> List[Tuple[str, int, int, str]]:
    values = list(months or [])
    if not values:
        raise ValueError("--months is required for blank mode")

    result: List[Tuple[str, int, int, str]] = []
    seen: set[str] = set()
    for key in values:
        year, month = validate_month_key(key)
        normalized = f"{year:04d}-{month:02d}"
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append((normalized, year, month, f"{month_name[month]} {year}"))
    return result


def _style_header(ws, row: int, *, fill, font, alignment) -> None:
    for cell in ws[row]:
        if cell.value is None:
            continue
        cell.fill = fill
        cell.font = font
        cell.alignment = alignment


def build_blank_roster(path: str | Path, months: Iterable[str]) -> Dict[str, object]:
    """Create a review-first blank roster shell and return build metadata.

    The new workbook is intentionally generated with openpyxl. Existing workbook
    modes remain package/XML-only and never pass through an openpyxl save.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    month_specs = _normalize_months(months)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    wb.remove(wb.active)

    header_fill = PatternFill("solid", fgColor="1F4E78")
    header_font = Font(bold=True, color="FFFFFF")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    dashboard = wb.create_sheet("Review Dashboard")
    dashboard["A1"] = "Roster Log Review Dashboard"
    dashboard["A1"].font = Font(bold=True, size=16, color="FFFFFF")
    dashboard["A1"].fill = header_fill
    dashboard.merge_cells("A1:D1")
    dashboard.append([])
    dashboard.append(["Workbook State", "Blank operator shell"])
    dashboard.append(["Months", ", ".join(spec[0] for spec in month_specs)])
    dashboard.append(["Review Queue", "No source rows loaded"])
    dashboard.append([
        "Instructions",
        "Enter staff, project, and punches on the Live tabs. Run full or review-only mode against a populated roster to build review evidence.",
    ])
    dashboard.column_dimensions["A"].width = 22
    dashboard.column_dimensions["B"].width = 92
    dashboard.freeze_panes = "A3"

    queue = wb.create_sheet("Review Queue")
    queue.append(REVIEW_QUEUE_HEADERS)
    _style_header(queue, 1, fill=header_fill, font=header_font, alignment=header_alignment)
    queue.freeze_panes = "A2"
    queue.auto_filter.ref = f"A1:{get_column_letter(len(REVIEW_QUEUE_HEADERS))}1"
    for idx, width in enumerate([16, 14, 14, 24, 24, 18, 24, 12, 16, 24, 24, 34, 24, 24, 20, 18, 40], 1):
        queue.column_dimensions[get_column_letter(idx)].width = width

    rules = wb.create_sheet("Review Rules")
    rules.append(["Rule Code", "Severity", "Trigger", "Suggested Resolution"])
    for row in REVIEW_RULES:
        rules.append(row)
    _style_header(rules, 1, fill=header_fill, font=header_font, alignment=header_alignment)
    rules.freeze_panes = "A2"
    for col, width in zip("ABCD", [28, 14, 52, 52]):
        rules.column_dimensions[col].width = width

    dictionary = wb.create_sheet("CF Dictionary")
    dictionary.append(["Color", "Meaning", "Rule Codes"])
    for row in CF_DICTIONARY:
        dictionary.append(row)
    _style_header(dictionary, 1, fill=header_fill, font=header_font, alignment=header_alignment)
    dictionary.freeze_panes = "A2"
    for col, width in zip("ABC", [18, 44, 48]):
        dictionary.column_dimensions[col].width = width

    live_sheets: List[str] = []
    for _, year, month, label in month_specs:
        title = f"Live - {label}"
        ws = wb.create_sheet(title)
        live_sheets.append(title)
        ws.append([f"{label} - Attendance"])
        headers = ["Staff Name", "Project"]
        for day in range(1, monthrange(year, month)[1] + 1):
            prefix = f"{month_abbr[month]} {day:02d}"
            headers.extend([f"{prefix} - Clock In", f"{prefix} - Clock Out"])
        ws.append(headers)
        _style_header(ws, 2, fill=header_fill, font=header_font, alignment=header_alignment)
        ws.freeze_panes = "C3"
        ws.column_dimensions["A"].width = 24
        ws.column_dimensions["B"].width = 28
        for col in range(3, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 17
        ws.auto_filter.ref = f"A2:{get_column_letter(len(headers))}202"

    wb.save(out)
    wb.close()
    return {
        "months": [spec[0] for spec in month_specs],
        "live_sheets": live_sheets,
        "review_rules_rows": len(REVIEW_RULES),
        "cf_dictionary_rows": len(CF_DICTIONARY),
    }
