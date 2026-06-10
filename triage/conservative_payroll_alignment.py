"""Conservative payroll alignment rules.

Do not blindly cut roster hours to match a lower Paylocity value when the result
would imply an implausibly early clock-out. Those cases are likely payroll
cutoff / missed clock-out / unpaid-hours shortages unless the operator confirms
that the roster should be reduced.
"""

PAYROLL_DELTA_TOLERANCE_MINUTES = 6
EARLY_CUTOFF_HOUR_