"""Neutralize formula-injection strings in exported Excel cells."""
from __future__ import annotations

from typing import Any

_FORMULA_PREFIXES = ("=", "+", "-", "@")


def websafe_cell_value(value: Any) -> Any:
    """Prefix risky strings so Excel treats them as text, not formulas."""
    if value is None:
        return value
    if isinstance(value, str):
        s = value
        if s and s[0] in _FORMULA_PREFIXES:
            return "'" + s
    return value
