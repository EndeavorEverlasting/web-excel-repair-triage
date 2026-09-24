from datetime import date, time

from triage.billing_context.models import Mismatch, WorkEntry
from triage.billing_context.reconcile import (
    aggregate_daily_track_hours,
    find_all_mismatches,
    find_context_mismatches,
    find_cross_source_mismatches,
    parse_time,
)


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
        )
    ]

    mismatches = find_context_mismatches(entries)
    assert len(mismatches) == 1
    assert mismatches[0].mismatch_type == "placeholder_assignment_replaced"


def test_hours_delta_uses_daily_aggregate():
    entries = [
        WorkEntry(
            source="x.xlsx",
            sheet_name="May",
            row_number=2,
            tech="Example Tech",
            work_date=date(2026, 5, 14),
            start_time=time(9, 0),
            end_time=time(12, 0),
            hours=4,
            original_assignment="Configuration",
            work_context="Configuration",
            context_reason="",
        ),
        WorkEntry(
            source="x.xlsx",
            sheet_name="May",
            row_number=3,
            tech="Example Tech",
            work_date=date(2026, 5, 14),
            start_time=time(13, 0),
            end_time=time(17, 0),
            hours=4,
            original_assignment="Configuration",
            work_context="Configuration",
            context_reason="",
        ),
    ]
    daily, _ = aggregate_daily_track_hours(entries)
    assert daily[("example tech", "2026-05-14")] == 8.0

    roster_index = {("example tech", "2026-05-14"): 8.0}
    cross = find_cross_source_mismatches(
        entries,
        roster_index=roster_index,
        roster_enabled=True,
    )
    assert not any(m.mismatch_type == "hours_delta" for m in cross)


def test_missing_source_only_when_enabled():
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
            context_reason="",
        )
    ]
    disabled = find_cross_source_mismatches(entries, roster_enabled=False)
    assert not any(m.mismatch_type == "missing_in_source" for m in disabled)

    enabled = find_cross_source_mismatches(entries, roster_index={}, roster_enabled=True)
    assert any(m.mismatch_type == "missing_in_source" for m in enabled)


def test_parse_time_datetime_string():
    assert parse_time("2026-05-14 18:00") == time(18, 0)


def test_csv_injection_neutralized(tmp_path):
    from triage.billing_context.exporters import export_mismatches

    mismatches = [
        Mismatch(
            severity="red",
            mismatch_type="hours_delta",
            tech="Tech",
            work_date="2026-05-14",
            source_a="track_hours",
            source_b="roster_log",
            source_a_value="=CMD()",
            source_b_value="8",
            recommendation="test",
        )
    ]
    csv_path = tmp_path / "m.csv"
    export_mismatches(mismatches, str(tmp_path / "m.json"), str(csv_path))
    text = csv_path.read_text(encoding="utf-8")
    assert "'=CMD()" in text
