"""Conservative payroll alignment rules."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AlignmentClass = Literal[
    "aligned",
    "rounding_noise",
    "raise_roster_to_paylocity",
    "likely_payroll_cutoff_shortage",
    "conscious_cut_review",
]

PAYROLL_DELTA_TOLERANCE_HOURS = 0.