"""Aggregate resolved daily records into the My Preferred Format rollups."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

from triage.admin_billing_summary.models import (
    BillingBucketRow,
    DailyRecord,
    MonthSummary,
    ProjectSummaryRow,
    TechProjectRow,
    TechSummaryRow,
    billing_bucket,
)
from triage.admin_billing_summary.reader import _month_label, read_month


def _project_rows(records: List[DailyRecord]) -> List[ProjectSummaryRow]:
    by: Dict[str, Dict[str, object]] = defaultdict(
        lambda: {"techs": set(), "days": 0, "gross": 0.0, "lunch": 0.0, "net": 0.0}
    )
    for r in records:
        b = by[r.project]
        b["techs"].add(r.tech)            # type: ignore[union-attr]
        b["days"] += 1                    # type: ignore[operator]
        b["gross"] += r.gross_span        # type: ignore[operator]
        b["lunch"] += r.lunch             # type: ignore[operator]
        b["net"] += r.net_hours           # type: ignore[operator]
    rows = [
        ProjectSummaryRow(
            project=proj,
            tech_count=len(v["techs"]),   # type: ignore[arg-type]
            worked_days=int(v["days"]),   # type: ignore[arg-type]
            gross_span=float(v["gross"]),
            lunch_deducted=float(v["lunch"]),
            net_hours=float(v["net"]),
        )
        for proj, v in by.items()
    ]
    rows.sort(key=lambda x: -x.net_hours)
    return rows


def _tech_rows(records: List[DailyRecord]) -> List[TechSummaryRow]:
    by: Dict[str, Dict[str, object]] = defaultdict(
        lambda: {"projects": set(), "days": 0, "gross": 0.0, "lunch": 0.0, "net": 0.0}
    )
    for r in records:
        b = by[r.tech]
        b["projects"].add(r.project)      # type: ignore[union-attr]
        b["days"] += 1                    # type: ignore[operator]
        b["gross"] += r.gross_span        # type: ignore[operator]
        b["lunch"] += r.lunch             # type: ignore[operator]
        b["net"] += r.net_hours           # type: ignore[operator]
    rows = [
        TechSummaryRow(
            tech=tech,
            projects=", ".join(sorted(v["projects"])),   # type: ignore[arg-type]
            worked_days=int(v["days"]),                   # type: ignore[arg-type]
            gross_span=float(v["gross"]),
            lunch_deducted=float(v["lunch"]),
            net_hours=float(v["net"]),
        )
        for tech, v in by.items()
    ]
    rows.sort(key=lambda x: -x.net_hours)
    return rows


def _tech_project_rows(records: List[DailyRecord]) -> List[TechProjectRow]:
    by: Dict[Tuple[str, str], Dict[str, float]] = defaultdict(
        lambda: {"days": 0, "gross": 0.0, "lunch": 0.0, "net": 0.0}
    )
    for r in records:
        b = by[(r.tech, r.project)]
        b["days"] += 1
        b["gross"] += r.gross_span
        b["lunch"] += r.lunch
        b["net"] += r.net_hours
    rows = [
        TechProjectRow(
            tech=tech,
            project=proj,
            worked_days=int(v["days"]),
            gross_span=v["gross"],
            lunch_deducted=v["lunch"],
            net_hours=v["net"],
        )
        for (tech, proj), v in by.items()
    ]
    rows.sort(key=lambda x: (x.tech, -x.net_hours))
    return rows


def _bucket_rows(records: List[DailyRecord]) -> List[BillingBucketRow]:
    by: Dict[str, Dict[str, object]] = defaultdict(
        lambda: {"techs": set(), "rows": 0, "hours": 0.0}
    )
    for r in records:
        b = by[billing_bucket(r.project)]
        b["techs"].add(r.tech)            # type: ignore[union-attr]
        b["rows"] += 1                    # type: ignore[operator]
        b["hours"] += r.net_hours         # type: ignore[operator]
    rows = [
        BillingBucketRow(
            bucket=bucket,
            tech_count=len(v["techs"]),   # type: ignore[arg-type]
            worked_rows=int(v["rows"]),   # type: ignore[arg-type]
            billable_hours=float(v["hours"]),
        )
        for bucket, v in by.items()
    ]
    rows.sort(key=lambda x: -x.billable_hours)
    return rows


def build_month_summary(roster_path: str, month_key: str) -> MonthSummary:
    label, _, _ = _month_label(month_key)
    records, warnings, malformed = read_month(roster_path, month_key)
    summary = MonthSummary(
        month_key=month_key,
        month_name=label,
        records=records,
        warnings=warnings,
        malformed=malformed,
    )
    summary.project_rows = _project_rows(records)
    summary.tech_rows = _tech_rows(records)
    summary.tech_project_rows = _tech_project_rows(records)
    summary.bucket_rows = _bucket_rows(records)
    return summary
