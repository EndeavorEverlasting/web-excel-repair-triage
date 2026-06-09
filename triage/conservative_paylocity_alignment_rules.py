"""Conservative Paylocity alignment rules.

When the operator consciously edits roster clock-outs to match Paylocity, that is
an artifact-generation posture, not an admission that no work happened later.

This module preserves that distinction so reports do not turn conservative
alignment into a false factual claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

AlignmentPosture = Literal["conservative_paylocity_match", "claim_roster_hours", "needs_evidence_review