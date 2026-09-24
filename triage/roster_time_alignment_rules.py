"""Roster time alignment rules for payroll delta cleanup.

When the roster has standard placeholder punches but Paylocity shows real OT,
the practical first correction is to edit the roster out-time so the
roster-derived payable hours match Paylocity within tolerance.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import time

PAYROLL_DELTA_TOLERANCE_HOURS = 0.10  # 6 minutes; prevents .02/.05 hour noise.
LUNCH_HOURS_FOR_OT_DAY = 1.0


@dataclass(frozen=True)
class TimeAlignmentDecision:
    start_time: time
    suggested_end_time: time
    crosses_midnight: bool
    gross_hours: float
    net_payable_hours: float
    paylocity_hours: float
    delta_hours: float
    within_tolerance: bool


def _time_to_hours(value: time) -> float:
    return value.hour + value.minute / 60 + value.second / 3600


def _hours_to_time(value: float) -> time:
    value = value % 24
    hour = int(value)
    rem = (value - hour) * 60
    minute = int(rem)
    second = round((rem - minute) * 60)
    if second == 60:
        second = 0
        minute += 1
    if minute == 60:
        minute = 0
        hour = (hour + 1) % 24
    return time(hour, minute, second)


def suggest_out_time_for_paid_hours(
    *,
    start_time: time,
    paylocity_hours: float,
    lunch_hours: float = LUNCH_HOURS_FOR_OT_DAY,
) -> TimeAlignmentDecision:
    """Suggest the roster out-time that makes net payable hours match Paylocity.

    Net payable hours = gross span - lunch_hours.
    """
    gross_hours = float(paylocity_hours) + float(lunch_hours)
    start_hours = _time_to_hours(start_time)
    end_hours_absolute = start_hours + gross_hours
    suggested_end = _hours_to_time(end_hours_absolute)
    crosses_midnight = end_hours_absolute >= 24
    net_payable = round(gross_hours - float(lunch_hours), 4)
    delta = round(net_payable - float(paylocity_hours), 4)
    return TimeAlignmentDecision(
        start_time=start_time,
        suggested_end_time=suggested_end,
        crosses_midnight=crosses_midnight,
        gross_hours=round(gross_hours, 4),
        net_payable_hours=net_payable,
        paylocity_hours=round(float(paylocity_hours), 4),
        delta_hours=delta,
        within_tolerance=abs(delta) <= PAYROLL_DELTA_TOLERANCE_HOURS,
    )


def delta_is_noise(delta_hours: float, tolerance_hours: float = PAYROLL_DELTA_TOLERANCE_HOURS) -> bool:
    """Return True when a daily payroll delta is too small to flag."""
    return abs(float(delta_hours)) <= float(tolerance_hours)
