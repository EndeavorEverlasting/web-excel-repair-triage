"""Aggregations for the NW PRJ billing summary (per-month + combined)."""
from __future__ import annotations

from calendar import month_name
from collections import defaultdict
from typing import Any, Dict, List, Tuple

from .models import BillingRow, MonthSummary


def _month_label(month_key: str) -> str:
    parts = month_key.split("-")
    if len(parts) == 2 and parts[1].isdigit():
        return f"{month_name[int(parts[1])]} {parts[0]}"
    return month_key


def summarize_months(rows: List[BillingRow]) -> List[MonthSummary]:
    """Build one MonthSummary per distinct month_key present in rows."""
    by_month: Dict[str, List[BillingRow]] = defaultdict(list)
    for r in rows:
        by_month[r.month_key].append(r)

    summaries: List[MonthSummary] = []
    for mk in sorted(by_month):
        mrows = by_month[mk]
        ms = MonthSummary(month_key=mk, month_label=_month_label(mk))
        staff = set()
        by_project: Dict[str, float] = defaultdict(float)
        by_batch: Dict[str, float] = defaultdict(float)
        for r in mrows:
            ms.gross_hours += r.gross_hours
            ms.lunch_deduction += r.lunch_deduction
            ms.net_hours += r.net_hours
            staff.add(r.staff)
            by_project[r.project] += r.net_hours
            by_batch[r.friday_batch.isoformat()] += r.net_hours
        ms.gross_hours = round(ms.gross_hours, 2)
        ms.lunch_deduction = round(ms.lunch_deduction, 2)
        ms.net_hours = round(ms.net_hours, 2)
        ms.staff_count = len(staff)
        ms.daily_rows = len(mrows)
        ms.by_project = {k: round(v, 2) for k, v in sorted(by_project.items())}
        ms.by_friday_batch = {k: round(v, 2) for k, v in sorted(by_batch.items())}
        summaries.append(ms)
    return summaries


def combined_totals(rows: List[BillingRow]) -> Tuple[float, float, float]:
    gross = round(sum(r.gross_hours for r in rows), 2)
    lunch = round(sum(r.lunch_deduction for r in rows), 2)
    net = round(sum(r.net_hours for r in rows), 2)
    return gross, lunch, net


def invoice_pivot(invoices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Roll up invoice dicts (invoice_parser shape) by cost category + vendor."""
    by_cat: Dict[Tuple[str, str], float] = defaultdict(float)
    for inv in invoices or []:
        cat = str(inv.get("cost_category") or inv.get("category") or "Uncategorized")
        vendor = str(inv.get("vendor") or "Unknown Vendor")
        amount = float(inv.get("total") or 0.0)
        by_cat[(cat, vendor)] += amount
    pivot = [
        {"cost_category": cat, "vendor": vendor, "total": round(amt, 2)}
        for (cat, vendor), amt in sorted(by_cat.items())
    ]
    return pivot
