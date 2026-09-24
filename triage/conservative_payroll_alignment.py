"""Conservative payroll alignment rules.

Lower Paylocity hours are not automatically a reason to cut roster hours.
When matching Paylocity would imply an unusually early clock-out, classify the
row as a likely payroll cutoff / missed clock-out shortage unless the operator
explicitly confirms the roster should be reduced.
"""
from __future__ import annotations

from dataclasses import dataclass

PAY