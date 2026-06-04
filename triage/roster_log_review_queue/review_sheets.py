"""Review layer sheet XML builders (Stage A)."""
from __future__ import annotations

# Stage A: extract review sheet XML templates from blessed reference and graft.
# See workbook_graft.py for sheet insertion/reorder.

REVIEW_QUEUE_COLUMNS = [
    "Review ID",
    "Month",
    "Date",
    "Staff",
    "Source Sheet",
    "Source Cell(s)",
    "Rule Code",
    "Severity",
    "Current Status",
    "Detected Value",
    "Expected Value",
    "Suggested Resolution",
    "Resolution Value",
    "Resolution Source",
    "Owner",
    "Last Reviewed",
    "Notes",
]
