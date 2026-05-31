"""
NW PRJ target classifier — owns all resolution and authority logic.

Inputs are dumb evidence records from ``nw_prj_admin_scratch_reader`` and
``nw_prj_roster_reader`` plus optional prior dashboard rows for carry-forward.
This module decides:

  * authority hierarchy per ``configs/nw_prj_dashboard_v6_schema.json``:
    manual_admin_scratch > official_admin_workbook > roster_log > prior_dashboard
  * Rich hours protection (admin full/long day is never downgraded by weak
    roster evidence)
  * partial-hour classification (PARTIAL_HOURS_REVIEW)
  * note-bearing punch handling (NOTE_BEARING_PUNCH, time-to-calc / note-to-context)
  * false-flag handling per ``configs/weekly_attendance_dashboard_values_v1.json``
  * gray archive preservation (skipped/gray rows stay archived, never resurrected)
  * submission blocker classification (Yes / No / Review)

Readers never make these decisions. Resolution lives here.

Status: scaffolded for feature/nw-prj-ingest-admin-roster-rows. Implementations
raise NotImplementedError until the ingestion PR lands.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from triage.nw_prj_admin_scratch_reader import AdminScratchEvidence
from triage.nw_prj_dashboard_rows import DashboardRow
from triage.nw_prj_roster_reader import RosterEvidence


@dataclass
class ClassifierInputs:
    """All evidence feeding a single classification pass.

    ``admin_scratch_rows`` carries the highest authority. ``official_admin_rows``
    is consulted only when the scratch is silent for a (tech, date). Roster
    evidence informs roster check / partial hours / note context. Prior rows
    are used solely for carry-forward of manual status, gray archive
    preservation, and Rich Guard memory.
    """

    admin_scratch_rows: List[AdminScratchEvidence] = field(default_factory=list)
    official_admin_rows: List[AdminScratchEvidence] = field(default_factory=list)
    roster_evidence: List[RosterEvidence] = field(default_factory=list)
    prior_rows: List[DashboardRow] = field(default_factory=list)


@dataclass
class ClassifierOutput:
    """Classification result, partitioned by destination dashboard sheet."""

    active_rows: List[DashboardRow] = field(default_factory=list)
    archive_rows: List[DashboardRow] = field(default_factory=list)
    rich_guard_rows: List[DashboardRow] = field(default_factory=list)
    false_flag_rows: List[DashboardRow] = field(default_factory=list)
    submission_blockers: List[DashboardRow] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)


def classify(inputs: ClassifierInputs) -> ClassifierOutput:
    """Produce dashboard rows from evidence + prior carry-forward.

    Contract (binding once implemented):

      * Authority hierarchy is enforced strictly. A scratch row for (tech, date)
        overrides any official admin or roster value for that key. An override
        beats default assignment.
      * Rich hours protection: if resolved admin hours for a (tech, date) are
        >= 8 and roster evidence is absent or weaker, an entry is emitted to
        ``rich_guard_rows`` with reason ``PRESERVE_ADMIN_FULL_DAY`` and the
        active row is not downgraded.
      * Partial hours: when 0 < resolved hours < 8, the active row carries
        reason ``PARTIAL_HOURS_REVIEW`` and Work Queue Status ``AMBER``.
      * Note-bearing punches: roster evidence with non-empty ``in_note`` or
        ``out_note`` produces (or annotates) a row with reason
        ``NOTE_BEARING_PUNCH``. The note text is preserved in
        ``Roster Check Notes``; the time portion is what feeds hours math.
      * False-flag dispositions from the weekly taxonomy go to
        ``false_flag_rows`` and never to ``active_rows``.
      * Gray preservation: any prior row whose review status is in
        ``skipped_gray`` remains in ``archive_rows`` and is not resurrected
        even if fresh evidence exists for the same key. A ``gray_resurrection``
        warning is emitted if fresh evidence conflicts.
      * Submission blocker classification: ``Yes`` only when resolved evidence
        proves an admin edit is required before submission; ``Review`` for
        ambiguous; ``No`` otherwise. Rows with ``Yes`` are duplicated into
        ``submission_blockers`` for fast indexing.
      * Resolution never silently mutates roster or admin sources. This is a
        pure function over evidence.

    Implementation is pending the ingestion PR.
    """
    raise NotImplementedError("classify is scaffolded; implementation pending")


def resolve_hours_authority(
    scratch: AdminScratchEvidence | None,
    official: AdminScratchEvidence | None,
    roster: RosterEvidence | None,
) -> tuple[float | None, str]:
    """Return ``(resolved_hours, authority_label)`` for a single (tech, date).

    ``authority_label`` is one of:
      ``manual_admin_scratch``, ``official_admin_workbook``, ``roster_log``,
      or ``none`` when no evidence is present.

    The first non-empty source in hierarchy order wins. This helper is the
    only place authority order is encoded; ``classify`` calls it per key.

    Implementation is pending the ingestion PR.
    """
    raise NotImplementedError(
        "resolve_hours_authority is scaffolded; implementation pending"
    )


def is_rich_guard(resolved_hours: float | None, roster_hours: float | None) -> bool:
    """Return True iff Rich Guard should preserve resolved admin hours.

    Rule: resolved_hours >= 8 and (roster_hours is None or roster_hours <
    resolved_hours). A True result must never cause the active row to be
    downgraded by weak roster evidence.

    Implementation is pending the ingestion PR.
    """
    raise NotImplementedError("is_rich_guard is scaffolded; implementation pending")
