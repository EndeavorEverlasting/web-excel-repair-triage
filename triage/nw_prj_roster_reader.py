"""
NW PRJ Roster Reader — read Live/Worked Projects tabs from the active roster log.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from triage.xlsx_utils import XlsxValues  # I'll check if this exists and is suitable

@dataclass
class RosterRecord:
    tech: str
    date: str
    project: str
    worked_project: Optional[str] = None
    punch_in: str = ""
    punch_out: str = ""
    hours: float = 0.0
    expected_hours: Optional[float] = None  # for partial-hours flagging
    notes: str = ""
    source_sheet: str = ""
    source_row: int = 0
    raw_in: str = ""
    raw_out: str = ""

def split_note_bearing_punch(value: Any) -> Tuple[str, str]:
    if value is None:
        return "", ""
    text = str(value).strip()
    if "/" in text:
        left, right = text.split("/", 1)
        return left.strip(), right.strip()
    return text, ""

def _parse_hours(v: Any) -> float:
    try:
        return float(v) if v is not None else 0.0
    except (ValueError, TypeError):
        return 0.0

class NwPrjRosterReader:
    def __init__(self, path: str):
        self.path = Path(path)
        self._values = XlsxValues(self.path)

    def read_all_records(self) -> List[RosterRecord]:
        """Read roster records, preferring real-file month-labeled sheets over narrow format."""
        records: List[RosterRecord] = []
        present = set(self._values.sheets.values())

        # Priority 1: Real roster log — month-labeled tall sheets with title row
        for sheet in sorted(present):
            if sheet.startswith("Expected Hours - ") or sheet.startswith("Billing Exceptions - "):
                records.extend(self._read_tall_with_title(sheet))

        # Priority 2: Synthetic / legacy narrow format
        if not records:
            for sheet in ["Live Projects", "Worked Projects"]:
                if sheet in present:
                    records.extend(self._read_sheet(sheet))

        return records

    def _read_tall_with_title(self, sheet_name: str) -> List[RosterRecord]:
        """Parse sheets where row 1 is a title, row 2 is headers, data from row 3."""
        vals = self._values.sheet_values(sheet_name)
        if not vals:
            return []

        headers: Dict[str, int] = {}
        for (r, c), v in vals.items():
            if r == 2:
                headers[str(v).strip().lower()] = c

        # Column aliases
        col_tech = (headers.get("tech") or headers.get("staff name") or
                    headers.get("staff") or headers.get("name"))
        col_date = headers.get("date")
        col_project = (headers.get("project / assignment") or headers.get("project") or
                       headers.get("assignment"))
        col_hours = (headers.get("actual paid hours") or headers.get("actual hours") or
                     headers.get("hours") or headers.get("worked hours"))
        col_exp_hours = (headers.get("expected paid hours") or headers.get("expected hours"))
        col_in = headers.get("clock in") or headers.get("in")
        col_out = headers.get("clock out") or headers.get("out")
        col_notes = (headers.get("status") or headers.get("source / evidence") or
                     headers.get("notes"))

        if not all([col_tech, col_date]):
            return []

        max_row = max(r for r, c in vals.keys()) if vals else 0
        records: List[RosterRecord] = []

        for r in range(3, max_row + 1):
            tech = vals.get((r, col_tech))
            if not tech:
                continue
            date_val = vals.get((r, col_date))
            if not date_val:
                continue

            raw_in = str(vals.get((r, col_in)) or "") if col_in else ""
            raw_out = str(vals.get((r, col_out)) or "") if col_out else ""
            punch_in, note_in = split_note_bearing_punch(raw_in)
            punch_out, note_out = split_note_bearing_punch(raw_out)
            notes_val = str(vals.get((r, col_notes)) or "") if col_notes else ""
            notes = " ".join(filter(None, [notes_val, note_in, note_out])).strip()

            exp_h: Optional[float] = None
            if col_exp_hours:
                exp_h = _parse_hours(vals.get((r, col_exp_hours)))

            records.append(RosterRecord(
                tech=str(tech).strip(),
                date=str(date_val).strip(),
                project=str(vals.get((r, col_project)) or "").strip() if col_project else "",
                hours=_parse_hours(vals.get((r, col_hours)) if col_hours else 0),
                expected_hours=exp_h,
                punch_in=punch_in,
                punch_out=punch_out,
                notes=notes,
                source_sheet=sheet_name,
                source_row=r,
                raw_in=raw_in,
                raw_out=raw_out,
            ))

        return records

    def _read_sheet(self, sheet_name: str) -> List[RosterRecord]:
        vals = self._values.sheet_values(sheet_name)
        if not vals:
            return []

        # Find headers
        headers: Dict[str, int] = {}
        for (r, c), v in vals.items():
            if r == 1:
                headers[str(v).strip().lower()] = c

        records: List[RosterRecord] = []
        # Roster logs typically have headers on row 1
        max_row = max(r for r, c in vals.keys()) if vals else 0
        
        # Identify columns
        col_tech = headers.get("tech") or headers.get("staff") or headers.get("name")
        col_date = headers.get("date")
        col_project = headers.get("project")
        col_worked = headers.get("worked project") or headers.get("worked-project")
        col_in = headers.get("in") or headers.get("punch in")
        col_out = headers.get("out") or headers.get("punch out")
        col_hours = headers.get("hours") or headers.get("worked hours")

        if not all([col_tech, col_date]):
            return []

        for r in range(2, max_row + 1):
            tech = vals.get((r, col_tech))
            if not tech:
                continue
            
            date_val = vals.get((r, col_date))
            # Handle excel date serial if needed, but XlsxValues might already do it or we do it here
            # For now assume it's string or handled by XlsxValues
            
            raw_in_val = vals.get((r, col_in)) if col_in else ""
            raw_out_val = vals.get((r, col_out)) if col_out else ""
            
            punch_in, note_in = split_note_bearing_punch(raw_in_val)
            punch_out, note_out = split_note_bearing_punch(raw_out_val)
            
            notes = (note_in + " " + note_out).strip()
            
            rec = RosterRecord(
                tech=str(tech).strip(),
                date=str(date_val).strip() if date_val else "",
                project=str(vals.get((r, col_project)) or "").strip() if col_project else "",
                worked_project=str(vals.get((r, col_worked)) or "").strip() if col_worked else None,
                punch_in=punch_in,
                punch_out=punch_out,
                hours=_parse_hours(vals.get((r, col_hours)) if col_hours else 0),
                notes=notes,
                source_sheet=sheet_name,
                source_row=r,
                raw_in=str(raw_in_val or ""),
                raw_out=str(raw_out_val or "")
            )
            records.append(rec)
            
        return records
