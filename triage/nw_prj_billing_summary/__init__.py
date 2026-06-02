"""NW PRJ April/May billing summary engine.

Reuses the roster/invoice parsers to produce a combined April+May broad billing
summary as a Web Excel-safe workbook plus preflight/review/manifest/zip sidecars.

Direction (see docs/BILLING_PIPELINE_DIRECTIONAL_CONTRACT.md): Roster Log to
Admin Sheet. Admin-facing sheets stay clean; raw punch notes, partial-hour rows,
and exceptions live only in the internal Review Queue.
"""
from __future__ import annotations

from .models import BillingReport, BillingRow, MonthSummary, ReviewFlag

__all__ = ["BillingReport", "BillingRow", "MonthSummary", "ReviewFlag"]
