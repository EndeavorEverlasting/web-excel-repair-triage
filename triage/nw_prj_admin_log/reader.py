"""Load roster attendance records for Project Team export."""
from __future__ import annotations

from datetime import date
from typing import List, Tuple

from triage.admin_billing_summary.models import DailyRecord
from triage.admin_billing_summary.reader import read_month


def month_span_bounds(month_keys: List[str]) -> Tuple[date, date]:
    keys = sorted(month_keys)
    y0, m0 = map(int, keys[0].split("-"))
    y1, m1 = map(int, keys[-1].split("-"))
    from calendar import monthrange
    start = date(y0, m0, 1)
    end = date(y1, m1, monthrange(y1, m1)[1])
    return start, end


def required_grid_dates(
    month_keys: List[str],
    records: List[DailyRecord],
) -> List[date]:
    span_start, span_end = month_span_bounds(month_keys)
    needed = {r.date for r in records if span_start <= r.date <= span_end}
    if span_start.month == 4 and span_start.year == 2026:
        for day in range(1, 6):
            needed.add(date(2026, 4, day))
    if span_end.month == 5 and span_end.year == 2026:
        needed.add(date(2026, 5, 31))
    return sorted(d for d in needed if span_start <= d <= span_end)


def load_roster_records(
    roster_path: str,
    month_keys: List[str],
) -> Tuple[List[DailyRecord], List[str]]:
    records: List[DailyRecord] = []
    warnings: List[str] = []
    for mk in month_keys:
        recs, w, _malformed = read_month(roster_path, mk)
        records.extend(recs)
        warnings.extend(w)
    records.sort(key=lambda r: (r.date, r.tech))
    return records, warnings
