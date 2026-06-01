"""
NW PRJ Admin Reader — read manually corrected admin Project Team values.

Supports two sheet layouts:
  1. Multi-week block format (real admin log): row has 'Techs' in col 2,
     date serials in cols 3/7/11/15/19/23/27, In/Out/Total sub-headers
     on next row, then tech data rows. One block per calendar week.
  2. Narrow format (synthetic / legacy): tech | date | hours column layout.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.xlsx_utils import XlsxValues, num_to_col

_XL_EPOCH = datetime.date(1899, 12, 30)
_XL_DATE_MIN, _XL_DATE_MAX = 40000, 60000  # reasonable range for 2009-2064


def _xl_serial_to_iso(n: Any) -> Optional[str]:
    """Convert Excel date serial integer to ISO-8601 date string."""
    try:
        v = int(n)
        if _XL_DATE_MIN < v < _XL_DATE_MAX:
            return (_XL_EPOCH + datetime.timedelta(days=v)).isoformat()
    except (TypeError, ValueError, OverflowError):
        pass
    return None


@dataclass
class AdminRecord:
    tech: str
    date: str
    hours: float
    source_sheet: str
    source_row: int
    source_cell: str
    raw_value: Any = None


class NwPrjAdminReader:
    def __init__(self, path: str):
        self.path = Path(path)
        self._values = XlsxValues(self.path)

    def read_records(self, sheet_name: str = "Project Team") -> List[AdminRecord]:
        vals = self._values.sheet_values(sheet_name)
        if not vals:
            present = set(self._values.sheets.values())
            for s in ["Project Team_x", "Project_Team", "Sheet1"]:
                if s in present:
                    vals = self._values.sheet_values(s)
                    sheet_name = s
                    break

        if not vals:
            return []

        # Detect multi-week block format: look for a row with 'Techs' in col 2
        # and an Excel date serial in col 3.
        for (r, c), v in vals.items():
            if c == 2 and "tech" in str(v).lower():
                serial = vals.get((r, 3))
                if _xl_serial_to_iso(serial) is not None:
                    return self._read_block_format(vals, sheet_name)
            if r > 30:  # Stop scanning after 30 rows
                break

        return self._read_narrow_format(vals, sheet_name)

    # ------------------------------------------------------------------
    # Multi-week block parser (real admin log format)
    # ------------------------------------------------------------------
    def _read_block_format(self, vals: Dict, sheet_name: str) -> List[AdminRecord]:
        """Parse the weekly-block layout of the real Project Team admin sheet."""
        max_row = max(r for r, c in vals.keys())
        records: List[AdminRecord] = []

        # Locate all header rows (col 2 = 'Techs …', col 3 = date serial)
        header_rows: List[int] = []
        for r in range(1, max_row + 1):
            c2 = vals.get((r, 2))
            if c2 and "tech" in str(c2).lower():
                if _xl_serial_to_iso(vals.get((r, 3))) is not None:
                    header_rows.append(r)

        # Date columns in each week block (stride of 4: col 3,7,11,15,19,23,27)
        _DATE_COLS = [3, 7, 11, 15, 19, 23, 27]

        for i, hdr_row in enumerate(header_rows):
            next_hdr = header_rows[i + 1] if i + 1 < len(header_rows) else max_row + 1

            # Build date→total_col mapping; Total = date_col + 2
            date_total: Dict[str, int] = {}
            for dc in _DATE_COLS:
                iso = _xl_serial_to_iso(vals.get((hdr_row, dc)))
                if iso:
                    date_total[iso] = dc + 2

            if not date_total:
                continue

            # Data rows start two rows after the header (skip sub-header row)
            for r in range(hdr_row + 2, next_hdr):
                tech = vals.get((r, 2))
                if not tech or not str(tech).strip():
                    continue
                tech_name = str(tech).strip()

                for date_str, total_col in date_total.items():
                    hours_val = vals.get((r, total_col))
                    if hours_val is None:
                        continue
                    try:
                        hours = float(hours_val)
                    except (TypeError, ValueError):
                        continue
                    if hours <= 0:
                        continue

                    records.append(AdminRecord(
                        tech=tech_name,
                        date=date_str,
                        hours=hours,
                        source_sheet=sheet_name,
                        source_row=r,
                        source_cell=f"{num_to_col(total_col)}{r}",
                        raw_value=hours_val,
                    ))

        return records

    # ------------------------------------------------------------------
    # Narrow format parser (synthetic tests / legacy files)
    # ------------------------------------------------------------------
    def _read_narrow_format(self, vals: Dict, sheet_name: str) -> List[AdminRecord]:
        headers: Dict[str, int] = {}
        for (r, c), v in vals.items():
            if r in (1, 4):
                h = str(v).strip().lower()
                if h and h not in headers:
                    headers[h] = c

        col_tech = (headers.get("tech") or headers.get("staff") or
                    headers.get("name") or headers.get("resource"))
        col_date = headers.get("date")
        col_hours = (headers.get("hours") or headers.get("worked hours") or
                     headers.get("total"))

        if not col_tech or not col_hours:
            return []

        start_row = 5 if max(headers.values()) >= 4 and min(headers.values()) >= 4 else 2
        max_row = max(r for r, c in vals.keys())
        records: List[AdminRecord] = []

        for r in range(start_row, max_row + 1):
            tech = vals.get((r, col_tech))
            if not tech:
                continue
            date_val = vals.get((r, col_date)) if col_date else ""
            hours_val = vals.get((r, col_hours))
            try:
                hours = float(hours_val) if hours_val is not None else 0.0
            except (ValueError, TypeError):
                hours = 0.0

            records.append(AdminRecord(
                tech=str(tech).strip(),
                date=str(date_val).strip() if date_val else "",
                hours=hours,
                source_sheet=sheet_name,
                source_row=r,
                source_cell=f"{num_to_col(col_hours)}{r}",
                raw_value=hours_val,
            ))

        return records
