"""Provenance JSON writer for roster log review queue graft."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore

from .models import LiveCFPatchStats


def _now_iso(tz_name: str = "America/New_York") -> str:
    if ZoneInfo is not None:
        try:
            tz = ZoneInfo(tz_name)
            return datetime.now(tz).isoformat()
        except Exception:
            pass
    return datetime.now(timezone.utc).isoformat()


def build_provenance(
    *,
    input_workbook: str,
    output_workbook: str,
    method: str,
    live_cf_stats: Dict[str, LiveCFPatchStats],
    verification: Dict[str, Any],
    output_zip: Optional[str] = None,
    review_queue_rows: int = 0,
    review_rules_rows: int = 17,
    cf_dictionary_rows_after: int = 0,
    mode: str = "full",
    openpyxl_save_used: bool = False,
) -> Dict[str, Any]:
    live_cf = {name: st.to_dict() for name, st in live_cf_stats.items() if st.patched}
    live_cf_counts_after = {
        name: st.cf_groups_after for name, st in live_cf_stats.items()
    }

    verification = dict(verification)
    verification.setdefault("review_queue_rows", review_queue_rows)
    verification.setdefault("review_rules_rows", review_rules_rows)

    return {
        "generated_at": _now_iso(),
        "timezone": "America/New_York",
        "method": method,
        "mode": mode,
        "input_workbook": input_workbook,
        "output_workbook": output_workbook,
        "output_zip": output_zip,
        "repair_safety": {
            "openpyxl_save_used": openpyxl_save_used,
            "structured_tables_added": False,
        },
        "verification": verification,
        "live_cf": live_cf,
        "live_cf_counts_after": live_cf_counts_after,
        "cf_dictionary_rows_after": cf_dictionary_rows_after,
    }
