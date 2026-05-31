"""
Contract tests for the NW PRJ target classifier.

These tests are xfail-strict against ``NotImplementedError`` because the
classifier is scaffolded for feature/nw-prj-ingest-admin-roster-rows and the
resolution logic has not landed yet. When implementation arrives, the xfails
flip to passes automatically and the strict flag fails the suite if a test
unexpectedly passes for the wrong reason.

Each test pins one rule from the binding contract in
``triage.nw_prj_target_classifier.classify``.
"""
from __future__ import annotations

import pytest

from triage.nw_prj_admin_scratch_reader import AdminScratchEvidence
from triage.nw_prj_dashboard_rows import DashboardRow
from triage.nw_prj_roster_reader import RosterEvidence
from triage.nw_prj_target_classifier import (
    ClassifierInputs,
    ClassifierOutput,
    classify,
    is_rich_guard,
    resolve_hours_authority,
)


def _scratch(tech: str, date: str, total: float | None = None) -> AdminScratchEvidence:
    return AdminScratchEvidence(
        tech=tech,
        date=date,
        source_workbook="scratch.xlsx",
        source_sheet="Hours",
        source_row=2,
        total_value=total,
    )


def _roster(tech: str, date: str, net: float | None) -> RosterEvidence:
    return RosterEvidence(
        tech=tech,
        date=date,
        project="NW PRJ",
        clock_in_raw=None,
        clock_out_raw=None,
        clock_in_hours=None,
        clock_out_hours=None,
        gross_hours=net,
        lunch_deduction=None,
        net_hours=net,
        long_shift=False,
    )


# ── shape ──


def test_classifier_inputs_defaults_are_empty():
    inp = ClassifierInputs()
    assert inp.admin_scratch_rows == []
    assert inp.official_admin_rows == []
    assert inp.roster_evidence == []
    assert inp.prior_rows == []


def test_classifier_output_partitions_exist():
    out = ClassifierOutput()
    assert out.active_rows == []
    assert out.archive_rows == []
    assert out.rich_guard_rows == []
    assert out.false_flag_rows == []
    assert out.submission_blockers == []


# ── authority hierarchy ──


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="ingestion PR pending")
def test_scratch_beats_official_and_roster():
    hours, label = resolve_hours_authority(
        scratch=_scratch("Alice", "2026-05-01", total=7.5),
        official=_scratch("Alice", "2026-05-01", total=8.0),
        roster=_roster("Alice", "2026-05-01", net=4.0),
    )
    assert hours == 7.5
    assert label == "manual_admin_scratch"


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="ingestion PR pending")
def test_official_beats_roster_when_scratch_silent():
    hours, label = resolve_hours_authority(
        scratch=None,
        official=_scratch("Alice", "2026-05-01", total=8.0),
        roster=_roster("Alice", "2026-05-01", net=4.0),
    )
    assert hours == 8.0
    assert label == "official_admin_workbook"


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="ingestion PR pending")
def test_roster_used_when_no_admin_evidence():
    hours, label = resolve_hours_authority(
        scratch=None, official=None, roster=_roster("Alice", "2026-05-01", net=4.0)
    )
    assert hours == 4.0
    assert label == "roster_log"


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="ingestion PR pending")
def test_no_evidence_returns_none_authority():
    hours, label = resolve_hours_authority(scratch=None, official=None, roster=None)
    assert hours is None
    assert label == "none"


# ── Rich hours protection ──


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="ingestion PR pending")
def test_rich_guard_triggers_when_admin_full_and_roster_weak():
    assert is_rich_guard(resolved_hours=8.0, roster_hours=4.0) is True


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="ingestion PR pending")
def test_rich_guard_triggers_when_admin_full_and_roster_missing():
    assert is_rich_guard(resolved_hours=8.0, roster_hours=None) is True


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="ingestion PR pending")
def test_rich_guard_silent_when_admin_short():
    assert is_rich_guard(resolved_hours=4.0, roster_hours=4.0) is False


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="ingestion PR pending")
def test_rich_guard_silent_when_roster_meets_admin():
    assert is_rich_guard(resolved_hours=8.0, roster_hours=8.0) is False


# ── classify: end-to-end rules ──


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="ingestion PR pending")
def test_partial_hours_become_amber_review():
    out = classify(
        ClassifierInputs(
            admin_scratch_rows=[_scratch("Alice", "2026-05-01", total=4.5)],
        )
    )
    assert out.active_rows
    row = out.active_rows[0]
    assert row.reason_code == "PARTIAL_HOURS_REVIEW"
    assert row.work_queue_status == "AMBER"


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="ingestion PR pending")
def test_gray_prior_rows_are_archived_not_resurrected():
    prior = DashboardRow(
        review_status="Skipped/Gray",
        tech="Bob",
        date="2026-05-02",
        edit_sheet="Hours",
        edit_row="3",
    )
    out = classify(
        ClassifierInputs(
            admin_scratch_rows=[_scratch("Bob", "2026-05-02", total=8.0)],
            prior_rows=[prior],
        )
    )
    assert any(r.review_status == "Skipped/Gray" for r in out.archive_rows)
    assert not any(
        r.tech == "Bob" and r.date == "2026-05-02" for r in out.active_rows
    )
    assert any("gray_resurrection" in w for w in out.warnings)


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="ingestion PR pending")
def test_rich_guard_row_emitted_with_preserve_reason():
    out = classify(
        ClassifierInputs(
            admin_scratch_rows=[_scratch("Rich", "2026-05-03", total=8.0)],
            roster_evidence=[_roster("Rich", "2026-05-03", net=4.0)],
        )
    )
    assert out.rich_guard_rows
    assert out.rich_guard_rows[0].reason_code == "PRESERVE_ADMIN_FULL_DAY"


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="ingestion PR pending")
def test_note_bearing_punch_preserves_note_in_roster_check_notes():
    ev = RosterEvidence(
        tech="Carol",
        date="2026-05-04",
        project="NW PRJ",
        clock_in_raw="9:28:00 AM/ Bonita",
        clock_out_raw=None,
        clock_in_hours=9.466,
        clock_out_hours=None,
        gross_hours=None,
        lunch_deduction=None,
        net_hours=None,
        long_shift=False,
        in_note="Bonita",
    )
    out = classify(ClassifierInputs(roster_evidence=[ev]))
    assert out.active_rows
    row = out.active_rows[0]
    assert row.reason_code == "NOTE_BEARING_PUNCH"
    assert "Bonita" in row.roster_check_notes


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="ingestion PR pending")
def test_submission_blockers_are_duplicated_into_blocker_list():
    out = classify(
        ClassifierInputs(
            admin_scratch_rows=[_scratch("Dana", "2026-05-05", total=0.0)],
        )
    )
    assert any(r.submission_blocker == "Yes" for r in out.submission_blockers)
