"""Shared YYYY-MM month key validation."""
from __future__ import annotations

import re
from typing import Tuple

_MONTH_KEY_RE = re.compile(r"^(\d{4})-(\d{1,2})$")


def validate_month_key(month_key: str) -> Tuple[int, int]:
    """Return (year, month) or raise ValueError with a clear message."""
    m = _MONTH_KEY_RE.match((month_key or "").strip())
    if not m:
        raise ValueError(f"Invalid month key (expected YYYY-MM): {month_key!r}")
    year, mon = int(m.group(1)), int(m.group(2))
    if mon < 1 or mon > 12:
        raise ValueError(f"Invalid month number in {month_key!r} (must be 01-12)")
    return year, mon
