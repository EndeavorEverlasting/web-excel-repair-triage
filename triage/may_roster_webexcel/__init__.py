"""May 2026 roster Web Excel CF preflight and repair-free QA.

Surgical forensic + (gated) patch workflow for the May 2026 Active Roster Log:

- ``cf_inspector``   : conditional-formatting diff + month-aware Sunday/Monday
                       bleed detection.
- ``package_checks`` : Web Excel package-level preflight gates.
- ``roster_rules``   : overnight-punch classification + unassigned-hours rules.
- ``summary_builder``: values-only share-safe summary generation.
- ``cli``            : ``inspect`` and ``patch`` orchestration.

Design constraint: a workbook that opens only because Excel repaired it is
evidence of failure, not success. Reports never claim Excel for Web opened
cleanly unless an actual Graph/Web-Excel open check was performed.
"""
from __future__ import annotations

__all__ = ["cf_inspector", "package_checks", "roster_rules", "summary_builder", "cli"]

ENGINE_NAME = "triage.may_roster_webexcel"
