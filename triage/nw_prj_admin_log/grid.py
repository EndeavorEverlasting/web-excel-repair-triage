"""Project Team weekly grid geometry (mirrors tech_hours_parser read path)."""
from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Dict, List, Optional, Tuple

from triage.admin_billing_summary.models import DailyRecord

FORBIDDEN_VISIBLE_PHRASES = (
    "roster log",
    "generated from",
    "source workbook",
    "automation",
    "internal",
    "holdover",
    "build notes",
    "sidecar",
    "manifest",
)


class ProjectTeamGridError(Exception):
    pass


def find_data_header_row(ws) -> Optional[int]:
    for r in range(1, min(ws.max_row + 1, 40)):
        for c in range(1, min(ws.max_column + 1, 12)):
            v = ws.cell(r, c).value
            if isinstance(v, str) and v.strip().lower().startswith("tech"):
                return r
    return None


def parse_date_columns(ws, hdr_row: int) -> Dict[int, date]:
    result: Dict[int, date] = {}
    for c in range(1, ws.max_column + 1):
        v = ws.cell(hdr_row, c).value
        if isinstance(v, datetime):
            result[c] = v.date()
        elif isinstance(v, date):
            result[c] = v
    return result


def staff_column(ws, hdr_row: int) -> int:
    for c in range(1, ws.max_column + 1):
        v = ws.cell(hdr_row, c).value
        if isinstance(v, str) and v.strip().lower().startswith("tech"):
            return c
    raise ProjectTeamGridError("cannot find Techs column")


def date_col_groups(date_cols: Dict[int, date]) -> Dict[date, Tuple[int, int, int]]:
    return {d: (dc, dc + 1, dc + 2) for dc, d in date_cols.items()}


def _copy_column_style(ws, src_col: int, dst_col: int, max_row: int) -> None:
    letter_src = ws.cell(1, src_col).column_letter
    letter_dst = ws.cell(1, dst_col).column_letter
    if letter_src in ws.column_dimensions:
        dim = ws.column_dimensions[letter_src]
        ws.column_dimensions[letter_dst].width = dim.width
        ws.column_dimensions[letter_dst].hidden = dim.hidden
    for r in range(1, max_row + 1):
        src = ws.cell(r, src_col)
        dst = ws.cell(r, dst_col)
        dst.number_format = src.number_format
        if src.has_style:
            dst.font = src.font.copy()
            dst.fill = src.fill.copy()
            dst.border = src.border.copy()
            dst.alignment = src.alignment.copy()


def ensure_dates_present(
    ws,
    hdr_row: int,
    sub_hdr_row: int,
    required: List[date],
) -> Dict[date, Tuple[int, int, int]]:
    """Insert missing date blocks (4 cols each) before the first existing block."""
    date_cols = parse_date_columns(ws, hdr_row)
    groups = date_col_groups(date_cols)
    existing = set(groups)
    missing = sorted(d for d in required if d not in existing)
    if not missing:
        return groups

    template_col = min(date_cols) if date_cols else staff_column(ws, hdr_row) + 1
    insert_at = template_col
    max_row = max(ws.max_row, sub_hdr_row + 20)

    for d in missing:
        ws.insert_cols(insert_at, 4)
        for offset in range(4):
            _copy_column_style(ws, template_col + offset, insert_at + offset, max_row)
        ws.cell(hdr_row, insert_at, value=datetime.combine(d, datetime.min.time()))
        ws.cell(sub_hdr_row, insert_at, value="In")
        ws.cell(sub_hdr_row, insert_at + 1, value="Out")
        ws.cell(sub_hdr_row, insert_at + 2, value="Total")

    date_cols = parse_date_columns(ws, hdr_row)
    return date_col_groups(date_cols)


def _find_or_create_tech_row(ws, staff_col: int, sub_hdr_row: int, tech: str) -> int:
    tech_l = tech.strip().lower()
    for r in range(sub_hdr_row + 1, ws.max_row + 1):
        v = ws.cell(r, staff_col).value
        if isinstance(v, str) and v.strip().lower() == tech_l:
            return r
        if isinstance(v, str) and v.strip().lower() in ("total", "totals", "tech total"):
            ws.insert_rows(r)
            ws.cell(r, staff_col, value=tech)
            return r
    r = ws.max_row + 1
    ws.cell(r, staff_col, value=tech)
    return r


def _write_time_cell(cell, value: Any) -> None:
    if value is None:
        cell.value = None
        return
    if isinstance(value, time):
        cell.value = value
        cell.number_format = "h:mm AM/PM"
        return
    if isinstance(value, str):
        cell.value = value
        return
    cell.value = value


def write_records_to_grid(
    ws,
    records: List[DailyRecord],
    *,
    span_start: date,
    span_end: date,
) -> None:
    hdr_row = find_data_header_row(ws)
    if hdr_row is None:
        raise ProjectTeamGridError("Project Team: Techs header row not found")
    sub_hdr_row = hdr_row + 1
    sc = staff_column(ws, hdr_row)

    roster_dates = sorted({r.date for r in records if span_start <= r.date <= span_end})
    required = roster_dates
    if span_start not in {d for d in required}:
        required = sorted(set(required) | {span_start})
    if span_end not in required:
        required = sorted(set(required) | {span_end})

    groups = ensure_dates_present(ws, hdr_row, sub_hdr_row, required)

    by_key: Dict[Tuple[str, date], DailyRecord] = {}
    for rec in records:
        if rec.date < span_start or rec.date > span_end:
            continue
        if rec.net_hours <= 0 and not rec.note:
            continue
        by_key[(rec.tech.strip(), rec.date)] = rec

    for (tech, d), rec in sorted(by_key.items(), key=lambda x: (x[0][1], x[0][0])):
        if d not in groups:
            continue
        in_c, out_c, tot_c = groups[d]
        row = _find_or_create_tech_row(ws, sc, sub_hdr_row, tech)
        marker = rec.note.strip().upper() if rec.note else ""
        if marker in ("PTO", "NON-PTO", "N/A", "OUT SICK", "OFF"):
            ws.cell(row, in_c, value=marker)
            ws.cell(row, out_c, value=None)
            ws.cell(row, tot_c, value=None)
            continue
        _write_time_cell(ws.cell(row, in_c), rec.start_time)
        _write_time_cell(ws.cell(row, out_c), rec.end_time)
        ws.cell(row, tot_c, value=round(rec.net_hours, 2))
        ws.cell(row, tot_c).number_format = "0.00"


def scan_forbidden_visible_text(ws) -> List[str]:
    hits: List[str] = []
    for row in ws.iter_rows(values_only=True):
        for val in row:
            if val is None:
                continue
            text = str(val).lower()
            for phrase in FORBIDDEN_VISIBLE_PHRASES:
                if phrase in text:
                    hits.append(phrase)
    return sorted(set(hits))
