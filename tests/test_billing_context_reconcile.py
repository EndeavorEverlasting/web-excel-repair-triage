from datetime import date, time

from triage.billing_context.models import WorkEntry
from triage.billing_context.reconcile import find_all_mismatches, find_context_mismatches


def test_placeholder_mismatch_created():
    entries = [
        WorkEntry(
            source="x.xlsx",
            sheet_name="April",
            row_number=2,
            tech="Example Tech",
            work_date=date(2026, 4, 26),
            start_time=time(9, 0),
            end_time=time(17, 0),
            hours=8,
            original_assignment="Neuron Installation",
            work_context="Deployment Support",
            context_reason="April Saturday rule applied.",
            notes="",
            confidence="medium",
        )
    ]

    mismatches = find_context_mismatches(entries)
    assert len(mismatches) == 1
    assert mismatches[0].mismatch_type == "placeholder_assignment_replaced"


def test_hours_delta_mismatch():
    entries = [
        WorkEntry(
            source="x.xlsx",
            sheet_name="May",
            row_number=2,
            tech="Example Tech",
            work_date=date(2026, 5, 14),
            start_time=time(9, 0),
            end_time=time(17, 0),
            hours=8,
            original_assignment="Configuration",
            work_context="Configuration",
            context_reason="Non-placeholder assignment retained.",
        )
    ]
    roster_index = {("example tech", "2026-05-14"): 6.0}
    mismatches = find_all_mismatches(entries, roster_path=None)
    cross = [m for m in mismatches if m.mismatch_type == "hours_delta"]
    assert not cross

    from triage.billing_context.reconcile import find_cross_source_mismatches

    cross_only = find_cross_source_mismatches(entries, roster_index=roster_index)
    assert any(m.mismatch_type == "hours_delta" for m in cross_only)
