"""Phase 4: submission readiness report."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


def build_submission_readiness(
    *,
    same_family_pass: Optional[bool] = None,
    preflight_pass: Optional[bool] = None,
    semantic_pass: Optional[bool] = None,
    browser_excel_status: str = "UNKNOWN",
    blockers: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    blockers = list(blockers or [])
    warnings = list(warnings or [])
    verdict = "NOT_READY"

    if browser_excel_status != "PROVEN":
        verdict = "EXCEL_FOR_WEB_NOT_PROVEN"
        blockers.append("excel_for_web_manual_check_not_proven")
    elif same_family_pass is None:
        verdict = "INSUFFICIENT_METADATA"
        blockers.append("same_family_comparison_not_run")
    elif not same_family_pass:
        verdict = "NOT_READY"
        blockers.append("same_family_comparison_failed")
    elif preflight_pass is False:
        verdict = "NOT_READY"
        blockers.append("package_preflight_failed")
    elif semantic_pass is False:
        verdict = "NOT_READY"
        blockers.append("semantic_integrity_failed")
    elif warnings and not blockers:
        verdict = "READY_WITH_EXCLUSIONS"
    elif not blockers:
        verdict = "READY"

    return {"verdict": verdict, "blockers": blockers, "warnings": warnings}


def write_submission_readiness(payload: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Submission readiness",
        "",
        f"**Verdict:** `{payload.get('verdict')}`",
        "",
    ]
    if payload.get("blockers"):
        lines.append("## Blockers")
        for b in payload["blockers"]:
            lines.append(f"- {b}")
    if payload.get("warnings"):
        lines.append("## Warnings")
        for w in payload["warnings"]:
            lines.append(f"- {w}")
    lines.append("")
    lines.append("Submit delivery artifacts only from `outputs/admin-ready/`.")
    path.write_text("\n".join(lines), encoding="utf-8")
