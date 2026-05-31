from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time
from typing import Any, Optional

from triage.admin_billing_context_rules import friday_batch_for
from triage.nw_prj_dashboard_rows import load_dashboard_rows
from triage.nw_prj_dashboard_validator import review_status_bucket
from triage.roster_parser import RosterParseError, parse_roster
from triage.tech_hours_parser import TechHoursParseError, parse_tech_hours

from .context_rules import is_placeholder_assignment, resolve_work_context
from .models import Mismatch, WorkEntry
from .workbook_io import fuzzy_get, iter_dict_rows, load_xlsx, safe_float

HOUR_TOLERANCE = 0.01


def parse_date(value: Any) -> Optional[date]:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not value:
        return None

    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def parse_time(value: Any) -> Optional[time]:
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, time):
        return value
    if not value:
        return None

    text = str(value).strip()

    datetime_formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%Y %I:%M %p",
        "%m/%d/%y %I:%M %p",
    )
    for fmt in datetime_formats:
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            pass

    if " " in text:
        time_part = text.rsplit(" ", 1)[-1]
        for fmt in ("%I:%M:%S %p", "%I:%M %p", "%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(time_part, fmt).time()
            except ValueError:
                pass

    for fmt in ("%I:%M:%S %p", "%I:%M %p", "%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            pass

    return None


def normalize_tech(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def entry_key(tech: str, work_date: date) -> tuple[str, str]:
    return (normalize_tech(tech).lower(), work_date.isoformat())


def build_task_context_index(april_context_path: str) -> dict[tuple[str, str], str]:
    """Key: (tech_lower, yyyy-mm-dd). Value: combined task text."""
    wb = load_xlsx(april_context_path, data_only=True)
    index: dict[tuple[str, str], list[str]] = defaultdict(list)

    for ws in wb.worksheets:
        for row in iter_dict_rows(ws):
            tech = normalize_tech(
                fuzzy_get(row, "Tech", "Technician", "Name", "Resource", "Tech Name")
            )
            d = parse_date(
                fuzzy_get(row, "Date", "Work Date", "Day")
            )
            if not tech or not d:
                continue

            text_parts = []
            for key, val in row.items():
                if key.startswith("_"):
                    continue
                if val not in (None, ""):
                    text_parts.append(f"{key}: {val}")

            index[(tech.lower(), d.isoformat())].append(" | ".join(text_parts))

    wb.close()
    return {k: "\n".join(v) for k, v in index.items()}


def extract_track_hours(track_hours_path: str, task_index: dict[tuple[str, str], str]) -> list[WorkEntry]:
    wb = load_xlsx(track_hours_path, data_only=True)
    entries: list[WorkEntry] = []

    for ws in wb.worksheets:
        if ws.sheet_state != "visible":
            continue

        for row in iter_dict_rows(ws):
            tech = normalize_tech(
                fuzzy_get(row, "Tech", "Technician", "Name", "Resource", "Tech Name")
            )
            work_date = parse_date(
                fuzzy_get(row, "Date", "Work Date", "Day")
            )
            if not tech or not work_date:
                continue

            hours = safe_float(
                fuzzy_get(row, "Hours", "Total Hours", "Total", "Net Hours", "Duration")
            )
            if hours <= 0:
                continue

            start_time = parse_time(
                fuzzy_get(row, "In", "Start", "Start Time", "Clock In")
            )
            end_time = parse_time(
                fuzzy_get(row, "Out", "End", "End Time", "Clock Out")
            )
            assignment = str(
                fuzzy_get(row, "Assignment", "Assignment Type", "Project", "Project Name", "Task", "Work Context", "Work / Context")
                or ""
            ).strip()

            task_text = task_index.get((tech.lower(), work_date.isoformat()), "")
            context, reason, confidence = resolve_work_context(
                assignment=assignment,
                task_text=task_text,
                work_date=work_date,
                start_time=start_time,
                end_time=end_time,
            )

            entries.append(
                WorkEntry(
                    source=track_hours_path,
                    sheet_name=ws.title,
                    row_number=int(row["_row_number"]),
                    tech=tech,
                    work_date=work_date,
                    start_time=start_time,
                    end_time=end_time,
                    hours=hours,
                    original_assignment=assignment,
                    work_context=context,  # type: ignore[arg-type]
                    context_reason=reason,
                    notes=task_text[:1000],
                    confidence=confidence,
                )
            )

    wb.close()
    return entries


def _hours_index_from_records(
    records: list[dict[str, Any]],
    *,
    staff_key: str = "staff",
    date_key: str = "date",
    hours_key: str = "net_hours",
) -> dict[tuple[str, str], float]:
    index: dict[tuple[str, str], float] = {}
    for rec in records:
        tech = normalize_tech(rec.get(staff_key) or rec.get("tech"))
        d = rec.get(date_key)
        if isinstance(d, datetime):
            d = d.date()
        if not tech or not isinstance(d, date):
            continue
        hours = safe_float(rec.get(hours_key) or rec.get("gross_hours") or rec.get("hours"))
        key = entry_key(tech, d)
        index[key] = index.get(key, 0.0) + hours
    return index


def build_roster_hours_index(roster_path: str | None) -> dict[tuple[str, str], float]:
    if not roster_path:
        return {}
    try:
        records = parse_roster(roster_path)
        return _hours_index_from_records(records)
    except RosterParseError:
        return _generic_hours_index(roster_path)


def build_admin_hours_index(admin_path: str | None) -> dict[tuple[str, str], float]:
    if not admin_path:
        return {}
    try:
        records = parse_tech_hours(admin_path)
        return _hours_index_from_records(records)
    except TechHoursParseError:
        return _generic_hours_index(admin_path)


def _generic_hours_index(path: str) -> dict[tuple[str, str], float]:
    wb = load_xlsx(path, data_only=True)
    index: dict[tuple[str, str], float] = defaultdict(float)
    for ws in wb.worksheets:
        for row in iter_dict_rows(ws):
            tech = normalize_tech(
                fuzzy_get(row, "Tech", "Technician", "Name", "Staff", "Resource", "Tech Name")
            )
            d = parse_date(
                fuzzy_get(row, "Date", "Work Date", "Day")
            )
            if not tech or not d:
                continue
            hours = safe_float(
                fuzzy_get(row, "Hours", "Total Hours", "Total", "Net Hours", "Duration")
            )
            if hours > 0:
                index[entry_key(tech, d)] += hours
    wb.close()
    return dict(index)


def build_dashboard_index(dashboard_path: str | None) -> dict[tuple[str, str], dict[str, Any]] | None:
    if not dashboard_path:
        return None
    rows_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in load_dashboard_rows(dashboard_path):
        d = parse_date(row.date)
        if not row.tech or not d:
            continue
        key = entry_key(row.tech, d)
        roster_h = safe_float(row.roster_latest_hours, default=-1.0)
        admin_h = safe_float(row.current_admin_value, default=-1.0)
        expected = safe_float(row.expected_total, default=-1.0)
        hours = roster_h if roster_h >= 0 else (admin_h if admin_h >= 0 else expected)
        rows_by_key[key].append(
            {
                "hours": hours if hours >= 0 else 0.0,
                "review_status": row.review_status,
                "reason_code": row.reason_code,
                "partial": 0 < hours < 8 if hours > 0 else False,
            }
        )

    index: dict[tuple[str, str], dict[str, Any]] = {}
    for key, rows in rows_by_key.items():
        total_hours = round(sum(safe_float(r.get("hours")) for r in rows), 2)
        worst_status = ""
        partial = False
        for r in rows:
            status = str(r.get("review_status") or "")
            bucket = review_status_bucket(status)
            if bucket not in ("resolved_green", "skipped_gray"):
                worst_status = status or worst_status
            if r.get("partial"):
                partial = True
        index[key] = {
            "hours": total_hours,
            "review_status": worst_status,
            "reason_code": rows[-1].get("reason_code", ""),
            "partial": partial,
        }
    return index


def aggregate_daily_track_hours(entries: list[WorkEntry]) -> tuple[dict[tuple[str, str], float], dict[tuple[str, str], str]]:
    totals: dict[tuple[str, str], float] = defaultdict(float)
    tech_names: dict[tuple[str, str], str] = {}
    for e in entries:
        key = entry_key(e.tech, e.work_date)
        totals[key] += e.hours
        tech_names[key] = e.tech
    return {k: round(v, 2) for k, v in totals.items()}, tech_names


def find_context_mismatches(entries: list[WorkEntry]) -> list[Mismatch]:
    mismatches: list[Mismatch] = []

    for e in entries:
        if is_placeholder_assignment(e.original_assignment):
            mismatches.append(
                Mismatch(
                    severity="amber",
                    mismatch_type="placeholder_assignment_replaced",
                    tech=e.tech,
                    work_date=e.work_date.isoformat(),
                    source_a="original_assignment",
                    source_b="resolved_context",
                    source_a_value=e.original_assignment,
                    source_b_value=e.work_context,
                    recommendation="Replace placeholder assignment with resolved work context.",
                    leadership_safe=False,
                )
            )

        if e.work_context == "Unknown / Needs Review":
            mismatch_type = "missing_work_context"
            if "disagree" in e.context_reason.lower():
                mismatch_type = "context_assignment_conflict"
            mismatches.append(
                Mismatch(
                    severity="red",
                    mismatch_type=mismatch_type,
                    tech=e.tech,
                    work_date=e.work_date.isoformat(),
                    source_a="task_tracker/roster/timing",
                    source_b="resolved_context",
                    source_a_value=e.original_assignment or "No decisive context",
                    source_b_value=e.work_context,
                    recommendation="Review task tracker or add explicit context override.",
                    leadership_safe=False,
                )
            )

    return mismatches


def _hour_delta_severity(delta: float) -> str:
    if abs(delta) >= 1.0:
        return "red"
    if abs(delta) >= 0.25:
        return "amber"
    return "blue"


def find_cross_source_mismatches(
    entries: list[WorkEntry],
    *,
    roster_index: dict[tuple[str, str], float] | None = None,
    admin_index: dict[tuple[str, str], float] | None = None,
    dashboard_index: dict[tuple[str, str], dict[str, Any]] | None = None,
    roster_enabled: bool = False,
    admin_enabled: bool = False,
    dashboard_enabled: bool = False,
) -> list[Mismatch]:
    mismatches: list[Mismatch] = []
    roster_idx = roster_index or {}
    admin_idx = admin_index or {}
    dashboard_idx = dashboard_index or {}

    daily_track, tech_names = aggregate_daily_track_hours(entries)
    seen_partial: set[tuple[str, str, str]] = set()

    for key, track_hours in daily_track.items():
        tech_key, work_date = key
        tech_display = tech_names.get(key, tech_key)

        for source_name, idx, enabled in (
            ("roster_log", roster_idx, roster_enabled),
            ("admin_copy", admin_idx, admin_enabled),
        ):
            if not enabled:
                continue
            if key not in idx:
                mismatches.append(
                    Mismatch(
                        severity="blue",
                        mismatch_type="missing_in_source",
                        tech=tech_display,
                        work_date=work_date,
                        source_a="track_hours",
                        source_b=source_name,
                        source_a_value=str(track_hours),
                        source_b_value="(absent)",
                        recommendation=f"Track row not found in {source_name}.",
                        leadership_safe=False,
                    )
                )
                continue

            other = idx[key]
            delta = round(track_hours - other, 2)
            if abs(delta) > HOUR_TOLERANCE:
                mismatches.append(
                    Mismatch(
                        severity=_hour_delta_severity(delta),  # type: ignore[arg-type]
                        mismatch_type="hours_delta",
                        tech=tech_display,
                        work_date=work_date,
                        source_a="track_hours",
                        source_b=source_name,
                        source_a_value=str(track_hours),
                        source_b_value=str(other),
                        recommendation=f"Reconcile hour delta ({delta:+.2f}h) between track hours and {source_name}.",
                        leadership_safe=False,
                    )
                )
            partial_key = (work_date, tech_key, source_name)
            if 0 < other < 8 and partial_key not in seen_partial:
                seen_partial.add(partial_key)
                mismatches.append(
                    Mismatch(
                        severity="amber",
                        mismatch_type="partial_hours",
                        tech=tech_display,
                        work_date=work_date,
                        source_a=source_name,
                        source_b="expected_full_day",
                        source_a_value=str(other),
                        source_b_value="8.0",
                        recommendation="Partial hours flagged in secondary source before submission.",
                        leadership_safe=False,
                    )
                )

        if not dashboard_enabled:
            continue

        if key not in dashboard_idx:
            mismatches.append(
                Mismatch(
                    severity="gray",
                    mismatch_type="missing_in_source",
                    tech=tech_key.title(),
                    work_date=work_date,
                    source_a="track_hours",
                    source_b="dashboard",
                    source_a_value=str(track_hours),
                    source_b_value="(absent)",
                    recommendation="Track row not found on dashboard resolution ledger.",
                    leadership_safe=False,
                )
            )
            continue

        dash = dashboard_idx[key]
        dash_h = safe_float(dash.get("hours"))
        if dash_h > 0:
            delta = round(track_hours - dash_h, 2)
            if abs(delta) > HOUR_TOLERANCE:
                mismatches.append(
                    Mismatch(
                        severity=_hour_delta_severity(delta),  # type: ignore[arg-type]
                        mismatch_type="hours_delta",
                        tech=tech_display,
                        work_date=work_date,
                        source_a="track_hours",
                        source_b="dashboard",
                        source_a_value=str(track_hours),
                        source_b_value=str(dash_h),
                        recommendation=f"Reconcile hour delta ({delta:+.2f}h) with resolution ledger.",
                        leadership_safe=False,
                    )
                )
        status = str(dash.get("review_status") or "")
        if status and track_hours > 0:
            bucket = review_status_bucket(status)
            if bucket not in ("resolved_green", "skipped_gray"):
                mismatches.append(
                    Mismatch(
                        severity="red",
                        mismatch_type="dashboard_unresolved",
                        tech=tech_display,
                        work_date=work_date,
                        source_a="dashboard_review_status",
                        source_b="track_hours",
                        source_a_value=status,
                        source_b_value=str(track_hours),
                        recommendation="Dashboard row not resolved before billing export.",
                        leadership_safe=False,
                    )
                )
        partial_key = (work_date, tech_key, "dashboard")
        if dash.get("partial") and partial_key not in seen_partial:
            seen_partial.add(partial_key)
            mismatches.append(
                Mismatch(
                    severity="amber",
                    mismatch_type="partial_hours",
                    tech=tech_key.title(),
                    work_date=work_date,
                    source_a="dashboard",
                    source_b="expected_full_day",
                    source_a_value=str(dash_h),
                    source_b_value="8.0",
                    recommendation="Partial hours flagged on dashboard resolution ledger.",
                    leadership_safe=False,
                )
            )

    return mismatches


def find_all_mismatches(
    entries: list[WorkEntry],
    *,
    roster_path: str | None = None,
    admin_path: str | None = None,
    dashboard_path: str | None = None,
) -> list[Mismatch]:
    context = find_context_mismatches(entries)
    roster_enabled = roster_path is not None
    admin_enabled = admin_path is not None
    dashboard_enabled = dashboard_path is not None
    cross = find_cross_source_mismatches(
        entries,
        roster_index=build_roster_hours_index(roster_path) if roster_enabled else None,
        admin_index=build_admin_hours_index(admin_path) if admin_enabled else None,
        dashboard_index=build_dashboard_index(dashboard_path),
        roster_enabled=roster_enabled,
        admin_enabled=admin_enabled,
        dashboard_enabled=dashboard_enabled,
    )
    return context + cross


def friday_batch_key(work_date: date) -> str:
    return friday_batch_for(work_date).isoformat()
