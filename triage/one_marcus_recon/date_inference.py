"""Recon update-date inference.

Precedence (contract):
1. Explicit CLI/config date.
2. Workbook filename date.
3. Existing latest dated Part Numbers tab.
4. File modified timestamp (last resort, warns).
"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import List, Optional, Tuple

from .models import DateCandidate

# Matches "5-28-2026", "05-28-2026"; also tolerant of "5/28/2026".
_MDY = re.compile(r"(?<!\d)(\d{1,2})[-/](\d{1,2})[-/](\d{4})(?!\d)")
# Matches ISO "2026-05-28".
_ISO = re.compile(r"(?<!\d)(\d{4})-(\d{1,2})-(\d{1,2})(?!\d)")
# A dated Part Numbers tab title, e.g. "5-28-2026 Part Numbers".
PART_NUMBERS_TAB = re.compile(
    r"(?P<m>\d{1,2})-(?P<d>\d{1,2})-(?P<y>\d{4})\s+part\s+numbers", re.IGNORECASE
)


class AmbiguousDateError(ValueError):
    """Raised in strict mode when multiple distinct dated tabs compete."""


def _to_iso(month: int, day: int, year: int) -> Optional[str]:
    try:
        return _dt.date(year, month, day).isoformat()
    except ValueError:
        return None


def parse_explicit(value: str) -> Optional[str]:
    """Parse an explicit --date value (ISO or M-D-YYYY). 'auto'/'' -> None."""
    if not value or value.strip().lower() == "auto":
        return None
    v = value.strip()
    m = _ISO.search(v)
    if m:
        return _to_iso(int(m.group(2)), int(m.group(3)), int(m.group(1)))
    m = _MDY.search(v)
    if m:
        return _to_iso(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def date_from_filename(path: str) -> Optional[str]:
    stem = Path(path).name
    m = _ISO.search(stem)
    if m:
        iso = _to_iso(int(m.group(2)), int(m.group(3)), int(m.group(1)))
        if iso:
            return iso
    m = _MDY.search(stem)
    if m:
        return _to_iso(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def dated_part_number_tabs(sheet_names: List[str]) -> List[Tuple[str, str]]:
    """Return [(sheet_name, iso_date)] for every dated Part Numbers tab."""
    out: List[Tuple[str, str]] = []
    for name in sheet_names:
        m = PART_NUMBERS_TAB.search(name)
        if not m:
            continue
        iso = _to_iso(int(m.group("m")), int(m.group("d")), int(m.group("y")))
        if iso:
            out.append((name, iso))
    return out


def infer_update_date(
    input_path: str,
    cli_date: str,
    sheet_names: List[str],
    *,
    file_mtime: Optional[float] = None,
    strict: bool = False,
) -> Tuple[DateCandidate, List[DateCandidate], List[str]]:
    """Resolve the update date.

    Returns (chosen, all_candidates, warnings). Raises AmbiguousDateError in
    strict mode when multiple distinct dated tabs exist and no explicit/filename
    date disambiguates them.
    """
    warnings: List[str] = []
    candidates: List[DateCandidate] = []

    explicit = parse_explicit(cli_date)
    if explicit:
        candidates.append(DateCandidate(explicit, "cli", cli_date))

    fname = date_from_filename(input_path)
    if fname:
        candidates.append(DateCandidate(fname, "filename", Path(input_path).name))

    tabs = dated_part_number_tabs(sheet_names)
    distinct_tab_dates = sorted({iso for _, iso in tabs})
    for name, iso in sorted(tabs, key=lambda t: t[1]):
        candidates.append(DateCandidate(iso, "tab", name))

    # Ambiguity: more than one distinct dated Part Numbers tab and the operator
    # gave no explicit/filename date to anchor the intended source.
    ambiguous = len(distinct_tab_dates) > 1 and not (explicit or fname)
    if len(distinct_tab_dates) > 1:
        msg = (
            "ambiguous date candidates: multiple dated Part Numbers tabs "
            f"{distinct_tab_dates}"
        )
        if ambiguous and strict:
            raise AmbiguousDateError(msg)
        warnings.append(msg)

    chosen: Optional[DateCandidate] = None
    # Precedence: cli > filename > latest tab > mtime.
    for src in ("cli", "filename"):
        for c in candidates:
            if c.source == src:
                chosen = c
                break
        if chosen:
            break
    if chosen is None and distinct_tab_dates:
        latest = distinct_tab_dates[-1]
        chosen = next(c for c in candidates if c.source == "tab" and c.date_iso == latest)
    if chosen is None:
        ts = file_mtime if file_mtime is not None else Path(input_path).stat().st_mtime
        iso = _dt.date.fromtimestamp(ts).isoformat()
        chosen = DateCandidate(iso, "mtime", str(ts))
        candidates.append(chosen)
        warnings.append(
            "update date inferred from file modified timestamp (last-resort fallback)"
        )

    return chosen, candidates, warnings
