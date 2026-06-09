"""Conservative payroll alignment rules.

These rules prevent the pipeline from blindly suggesting that a roster day should
be cut down to match Paylocity when the lower Paylocity value is more likely a
payroll cutoff, missed clock-out, or lunch-cutoff artifact.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from typing import Literal

AlignmentClass = Literal[
    "aligned",
    "round