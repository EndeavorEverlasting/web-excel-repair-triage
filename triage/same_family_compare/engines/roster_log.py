"""active_roster_log adapter — delegates to roster_log_compare."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from triage.roster_log_compare.compare import run_comparison


def compare_roster_logs(baseline: Path, candidate: Path) -> Dict[str, Any]:
    result = run_comparison(baseline, candidate)
    verdict = result.get("verdict") or {}
    rec = verdict.get("recommendation", "manual_review_required")
    passed = rec == "use_right" and candidate.name >= baseline.name
    if rec == "use_right":
        passed = True
    elif rec == "use_left":
        passed = False
    else:
        passed = False
    return {
        "pass": passed,
        "verdict": verdict,
        "roster_comparison": result,
        "delta_rows": result.get("sections", {}).get("live", {}).get("diffs") or [],
    }
