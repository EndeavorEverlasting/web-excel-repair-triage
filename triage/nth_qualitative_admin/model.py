"""Deterministic qualitative admin Neuron Track Hours workbook builder.

This builder reproduces the stable June-completed / August-MTD management
workbook family from structured evidence. Reference workbooks are never runtime
inputs and never create labor hours. Quantitative workbook cells are derived
from detail rows at build time; worksheet formulas are intentionally absent.
"""
from __future__ import annotations

import json
import re
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "configs" / "artifact_profiles" / "nth_qualitative_admin.v1.json"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
THEME_PATH = TEMPLATE_DIR / "theme1.xml"

INVALID_XML = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
PERCENT = re.compile(r"\b\d+(?:\.\d+)?\s*%")
RANKING_TERMS = re.compile(r"\b(?:peak day|ranking|top performer)\b", re.I)
TASK_HOUR_CLAIM = re.compile(r"\b\d+(?:\.\d+)?\s*(?:hours?|h)\b.{0,40}\b(?:configuration|deployment|inventory|logistics|staging|coordination|documentation|troubleshooting|support)\b", re.I)

class QualitativeAdminError(ValueError):
    """Raised when the evidence packet violates the qualitative admin profile."""

@dataclass(frozen=True)
class Cell:
    ref: str
    style: int
    value: Any = None
    kind: str | None = None

def load_profile() -> dict[str, Any]:
    payload = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "nth-qualitative-admin-profile/v1":
        raise QualitativeAdminError("unsupported qualitative-admin profile")
    return payload

def _parse_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except Exception as exc:
        raise QualitativeAdminError(f"{field} must be YYYY-MM-DD: {value!r}") from exc

def _month_parts(month_key: str) -> tuple[int, int]:
    try:
        parsed = datetime.strptime(month_key, "%Y-%m")
    except ValueError as exc:
        raise QualitativeAdminError(f"month_key must be YYYY-MM: {month_key!r}") from exc
    return parsed.year, parsed.month

def _month_label(month_key: str) -> str:
    year, month = _month_parts(month_key)
    return date(year, month, 1).strftime("%B %Y")

def _month_day(value: date) -> str:
    return f"{value.strftime('%B')} {value.day}"

def _short_month_day(value: date) -> str:
    return f"{value.strftime('%b')} {value.day}"

def _planned_day_label(value: date) -> str:
    return f"{value.strftime('%b').upper()} {value.day}"

def _excel_serial(value: date) -> int:
    return (value - date(1899, 12, 30)).days

def _num(value: float | int) -> str:
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return (f"{number:.10f}").rstrip("0").rstrip(".")

def _clean_text(value: Any, field: str) -> str:
    text = str(value if value is not None else "").strip()
    if not text:
        raise QualitativeAdminError(f"{field} is required")
    if INVALID_XML.search(text):
        raise QualitativeAdminError(f"{field} contains XML-invalid control characters")
    return text

def _narrative_guard(text: str, *, direct_quantitative_evidence: bool, field: str) -> None:
    if direct_quantitative_evidence:
        return
    if PERCENT.search(text):
        raise QualitativeAdminError(f"{field} contains a percentage without direct_quantitative_evidence=true")
    if RANKING_TERMS.search(text):
        raise QualitativeAdminError(f"{field} contains ranking/peak language without direct quantitative evidence")
    if TASK_HOUR_CLAIM.search(text):
        raise QualitativeAdminError(f"{field} appears to allocate hours to a workstream without direct task/time evidence")

def _validate_narrative_rows(rows: Sequence[Mapping[str, Any]], fields: Iterable[str], label: str) -> None:
    for idx, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise QualitativeAdminError(f"{label}[{idx}] must be an object")
        direct = bool(row.get("direct_quantitative_evidence", False))
        for field in fields:
            text = _clean_text(row.get(field), f"{label}[{idx}].{field}")
            _narrative_guard(text, direct_quantitative_evidence=direct, field=f"{label}[{idx}].{field}")

def validate_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    if spec.get("schema_version") != "nth-qualitative-admin-input/v1":
        raise QualitativeAdminError("schema_version must be nth-qualitative-admin-input/v1")
    mode = str(spec.get("mode", "")).strip()
    if mode not in {"completed_month", "month_to_date"}:
        raise QualitativeAdminError("mode must be completed_month or month_to_date")
    month_key = str(spec.get("month_key", "")).strip()
    year, month = _month_parts(month_key)
    artifact_date = _parse_date(spec.get("artifact_date"), "artifact_date")
    detail = spec.get("detail_rows")
    if not isinstance(detail, list) or not detail:
        raise QualitativeAdminError("detail_rows must be a non-empty list")
    normalized_detail: list[dict[str, Any]] = []
    for idx, row in enumerate(detail):
        if not isinstance(row, Mapping):
            raise QualitativeAdminError(f"detail_rows[{idx}] must be an object")
        work_date = _parse_date(row.get("date"), f"detail_rows[{idx}].date")
        if (work_date.year, work_date.month) != (year, month):
            raise QualitativeAdminError(f"detail_rows[{idx}].date {work_date} is outside target month {month_key}")
        tech = _clean_text(row.get("technician"), f"detail_rows[{idx}].technician")
        program = _clean_text(row.get("program_assignment"), f"detail_rows[{idx}].program_assignment")
        context = _clean_text(row.get("qualitative_work_context"), f"detail_rows[{idx}].qualitative_work_context")
        try:
            hours = float(row.get("paid_hours"))
        except Exception as exc:
            raise QualitativeAdminError(f"detail_rows[{idx}].paid_hours must be numeric") from exc
        if hours < 0:
            raise QualitativeAdminError(f"detail_rows[{idx}].paid_hours cannot be negative")
        _narrative_guard(context, direct_quantitative_evidence=bool(row.get("direct_task_time_evidence", False)), field=f"detail_rows[{idx}].qualitative_work_context")
        normalized_detail.append({"date":work_date,"technician":tech,"paid_hours":hours,"program_assignment":program,"qualitative_work_context":context})
    normalized_detail.sort(key=lambda item: (item["date"], item["technician"].casefold()))
    tracked = spec.get("tracked_technicians", [])
    if tracked is None: tracked = []
    if not isinstance(tracked, list): raise QualitativeAdminError("tracked_technicians must be a list")
    tracked_names: list[str] = []
    seen: set[str] = set()
    for idx, name in enumerate(tracked):
        clean = _clean_text(name, f"tracked_technicians[{idx}]")
        if clean.casefold() not in seen:
            tracked_names.append(clean); seen.add(clean.casefold())
    for row in normalized_detail:
        if row["technician"].casefold() not in seen:
            tracked_names.append(row["technician"]); seen.add(row["technician"].casefold())
    themes = spec.get("operational_themes")
    if not isinstance(themes, list) or not themes: raise QualitativeAdminError("operational_themes must be a non-empty list")
    _validate_narrative_rows(themes, ("theme","readout","why"), "operational_themes")
    executive = spec.get("executive_readout", [])
    if not isinstance(executive, list): raise QualitativeAdminError("executive_readout must be a list")
    _validate_narrative_rows(executive, ("finding","management_interpretation"), "executive_readout")
    normalized: dict[str, Any] = dict(spec)
    normalized.update({"mode":mode,"month_key":month_key,"month_label":_month_label(month_key),"artifact_date":artifact_date,"detail_rows":normalized_detail,"tracked_technicians":tracked_names})
    if mode == "completed_month":
        billing = spec.get("billing_support_context")
        if not isinstance(billing, list) or not billing: raise QualitativeAdminError("completed_month requires billing_support_context")
        _validate_narrative_rows(billing, ("control","statement"), "billing_support_context")
        boundary = _clean_text(spec.get("external_use_boundary"), "external_use_boundary")
        _narrative_guard(boundary, direct_quantitative_evidence=False, field="external_use_boundary")
        prior = spec.get("prior_baseline")
        if prior is not None:
            try: prior = float(prior)
            except Exception as exc: raise QualitativeAdminError("prior_baseline must be numeric or null") from exc
            if prior < 0: raise QualitativeAdminError("prior_baseline cannot be negative")
        normalized["prior_baseline"] = prior
    else:
        through = _parse_date(spec.get("through_date"), "through_date")
        planned = _parse_date(spec.get("planned_date"), "planned_date")
        if (through.year, through.month) != (year, month): raise QualitativeAdminError("through_date must be inside target month")
        if (planned.year, planned.month) != (year, month): raise QualitativeAdminError("planned_date must be inside target month")
        if planned < through: raise QualitativeAdminError("planned_date cannot precede through_date")
        if any(row["date"] > through for row in normalized_detail): raise QualitativeAdminError("month_to_date detail_rows cannot extend beyond through_date")
        status = _clean_text(spec.get("mtd_status"), "mtd_status")
        carryover = spec.get("carryover_planned_work"); technical = spec.get("technical_scope_context")
        if not isinstance(carryover, list) or not carryover: raise QualitativeAdminError("month_to_date requires carryover_planned_work")
        if not isinstance(technical, list) or not technical: raise QualitativeAdminError("month_to_date requires technical_scope_context")
        _validate_narrative_rows(carryover, ("owner","item","project","status","context"), "carryover_planned_work")
        for idx, row in enumerate(carryover):
            planned_date = _parse_date(row.get("planned_date"), f"carryover_planned_work[{idx}].planned_date")
            if (planned_date.year, planned_date.month) != (year, month): raise QualitativeAdminError(f"carryover_planned_work[{idx}].planned_date is outside target month")
            try: posted = float(row.get("paid_hours_posted", 0))
            except Exception as exc: raise QualitativeAdminError(f"carryover_planned_work[{idx}].paid_hours_posted must be numeric") from exc
            if posted != 0: raise QualitativeAdminError(f"carryover_planned_work[{idx}] must keep paid_hours_posted at 0 until attendance posts")
            status_text = str(row.get("status", "")).upper()
            if "NOT BILLED" not in status_text and "NOT POSTED" not in status_text: raise QualitativeAdminError(f"carryover_planned_work[{idx}].status must state NOT BILLED or NOT POSTED")
        _validate_narrative_rows(technical, ("control","statement"), "technical_scope_context")
        closing = _clean_text(spec.get("technical_scope_closing_note"), "technical_scope_closing_note")
        _narrative_guard(closing, direct_quantitative_evidence=False, field="technical_scope_closing_note")
        normalized.update({"through_date":through,"planned_date":planned,"mtd_status":status})
    return normalized

def derive_metrics(spec: Mapping[str, Any]) -> dict[str, Any]:
    detail = spec["detail_rows"]
    tech: "OrderedDict[str, dict[str, Any]]" = OrderedDict((name,{"technician":name,"paid_hours":0.0,"shift_count":0}) for name in spec["tracked_technicians"])
    daily: "OrderedDict[date, dict[str, Any]]" = OrderedDict(); total = 0.0
    for row in detail:
        hours = float(row["paid_hours"]); total += hours
        if row["technician"] not in tech: tech[row["technician"]] = {"technician":row["technician"],"paid_hours":0.0,"shift_count":0}
        tech[row["technician"]]["paid_hours"] += hours; tech[row["technician"]]["shift_count"] += 1
        entry = daily.setdefault(row["date"], {"date":row["date"],"day":row["date"].strftime("%a"),"paid_hours":0.0,"shift_count":0})
        entry["paid_hours"] += hours; entry["shift_count"] += 1
    return {"total_paid_hours":round(total,10),"completed_shift_records":len(detail),"technicians":list(tech.values()),"daily":list(daily.values())}
