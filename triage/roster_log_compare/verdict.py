"""Weighted deterministic verdict for roster log comparison."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def compute_verdict(
    metadata: Dict[str, Any],
    live: Dict[str, Any],
    cf: Dict[str, Any],
    override: Dict[str, Any],
    expected: Dict[str, Any],
    header: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    left_score = 0.0
    right_score = 0.0
    reasons: List[str] = []
    risks: List[Dict[str, Any]] = []

    stats = live.get("stats") or {}
    if stats.get("right_nonempty_punches", 0) > stats.get("left_nonempty_punches", 0):
        right_score += 3
        reasons.append("right_more_complete_live_punches")
    elif stats.get("left_nonempty_punches", 0) > stats.get("right_nonempty_punches", 0):
        left_score += 3
        reasons.append("left_more_complete_live_punches")

    diffs = live.get("diffs") or []
    right_fresher = 0
    left_fresher = 0
    for d in diffs:
        lv, rv = d.get("left_value"), d.get("right_value")
        if (lv in ("", None)) and rv not in ("", None):
            right_fresher += 1
        elif (rv in ("", None)) and lv not in ("", None):
            left_fresher += 1
    if right_fresher > left_fresher:
        right_score += 2
        reasons.append("right_fills_more_empty_punch_cells")
    elif left_fresher > right_fresher:
        left_score += 2
        reasons.append("left_fills_more_empty_punch_cells")

    if cf.get("right_has_more_cf_coverage"):
        right_score += 1.5
        reasons.append("right_more_conditional_formatting")
    elif cf.get("left_total_rules", 0) > cf.get("right_total_rules", 0):
        left_score += 1.5
        reasons.append("left_more_conditional_formatting")

    for frag in cf.get("fragmented_cf_introduced") or []:
        risks.append({
            "severity": "warn",
            "code": "fragmented_cf_introduced",
            "detail": frag,
        })

    for row in override.get("rows") or []:
        left_s = row.get("left") or {}
        right_s = row.get("right") or {}
        sheet = row.get("sheet", "")
        if left_s.get("override_table_present") and not right_s.get("override_table_present"):
            risks.append({
                "severity": "stop",
                "code": "override_table_regression",
                "detail": f"{sheet}: present on left, missing on right",
            })
            right_score -= 5
        elif right_s.get("override_table_present") and not left_s.get("override_table_present"):
            risks.append({
                "severity": "warn",
                "code": "override_table_added_on_right",
                "detail": sheet,
            })
            right_score += 0.5
        for side_key, label in (("right", "right"), ("left", "left")):
            side = row.get(side_key) or {}
            if side.get("override_table_present") and not side.get("formulas_reference_override_range"):
                risks.append({
                    "severity": "warn",
                    "code": "override_refs_missing",
                    "detail": f"{side.get('sheet', sheet)} on {label}",
                })

    for eh in expected.get("rows") or []:
        for side_key in ("left", "right"):
            s = eh.get(side_key) or {}
            if s.get("stale_snapshot_warning"):
                risks.append({
                    "severity": "warn",
                    "code": "stale_expected_hours_snapshot",
                    "detail": f"{eh.get('sheet')} {side_key}",
                })
                if side_key == "right":
                    right_score -= 0.5

    header_diff_count = sum(
        1 for sheet in (header.get("sheets") or []) if not sheet.get("header_identical")
    )
    if header_diff_count and cf.get("right_has_more_cf_coverage"):
        right_score += 0.5
        reasons.append("right_header_or_cf_refresh")

    left_meta = metadata.get("left") or {}
    right_meta = metadata.get("right") or {}
    fn_l = left_meta.get("filename_date_token")
    fn_r = right_meta.get("filename_date_token")
    if fn_l and fn_r:
        if fn_r > fn_l:
            right_score += 0.5
            reasons.append("filename_date_favors_right")
        elif fn_l > fn_r:
            left_score += 0.5
            reasons.append("filename_date_favors_left")
    mt_l = left_meta.get("file_mtime_utc") or ""
    mt_r = right_meta.get("file_mtime_utc") or ""
    if mt_r > mt_l:
        right_score += 0.25
    elif mt_l > mt_r:
        left_score += 0.25

    filename_favors = "right" if fn_r and fn_l and fn_r > fn_l else (
        "left" if fn_r and fn_l and fn_l > fn_r else None
    )
    content_favors = "right" if right_score > left_score + 0.5 else (
        "left" if left_score > right_score + 0.5 else None
    )
    recommendation = "manual_review_required"
    confidence = "medium"
    if filename_favors and content_favors and filename_favors != content_favors:
        reasons.append("conflicting_filename_and_content_signals")
    elif right_score > left_score + 0.5:
        recommendation = "use_right"
        confidence = "high" if right_score - left_score >= 2 else "medium"
    elif left_score > right_score + 0.5:
        recommendation = "use_left"
        confidence = "high" if left_score - right_score >= 2 else "medium"
    elif abs(right_score - left_score) < 0.1 and not diffs:
        reasons.append("equivalent_evidence")
    else:
        reasons.append("insufficient_margin_or_conflicts")

    stop_on_right = any(r["severity"] == "stop" for r in risks)
    if recommendation == "use_right" and stop_on_right:
        recommendation = "manual_review_required"
        reasons.append("major_override_risk_on_recommended_side")

    verdict = {
        "recommendation": recommendation,
        "confidence": confidence,
        "reasons": reasons,
        "left_score": round(left_score, 2),
        "right_score": round(right_score, 2),
    }
    return verdict, risks
