"""Candidate Neuron Track Hours transformation tests."""
from __future__ import annotations

from datetime import date, time

from triage.neuron_work_context_rules import CLIENT_COORDINATION, CONFIGURATIONS, INVENTORY_MANAGEMENT
from triage.nw_prj_neuron_track_hours.bonita_resolver import BonitaResolution, BonitaShift
from triage.nw_prj_neuron_track_hours.candidate_rules import build_candidate_resolution


def _shift(tech: str, assignment: str, start=time(8, 0), end=time(16, 0), hours=8.0) -> BonitaShift:
    return BonitaShift(
        month_key="2026-04",
        month_name="April",
        date=date(2026, 4, 20),
        day="Mon",
        tech=tech,
        clock_in="8:00 AM",
        clock_out="4:00 PM",
        total_hours=hours,
        assignment_type=assignment,
        start_time=start,
        end_time=end,
    )


def test_unapproved_client_coordination_removed_from_candidate_sheet():
    source = BonitaResolution(shifts=[
        _shift("Field Tech", CLIENT_COORDINATION),
        _shift("Geoff Gerber", CLIENT_COORDINATION),
    ])

    candidate, stats = build_candidate_resolution(source)

    assert [s.tech for s in candidate.shifts] == ["Geoff Gerber"]
    assert stats["removed_client_coordination_rows"] == 1
    assert any(r.category == "removed_client_coordination" for r in candidate.review)


def test_rezaul_april_shift_splits_into_inventory_and_configurations():
    source = BonitaResolution(shifts=[
        _shift("Rezaul Roman", CONFIGURATIONS, start=time(15, 30), end=time(20, 30), hours=5.0),
    ])

    candidate, stats = build_candidate_resolution(source)

    assert len(candidate.shifts) == 2
    assert [s.assignment_type for s in candidate.shifts] == [INVENTORY_MANAGEMENT, CONFIGURATIONS]
    assert [round(s.total_hours, 2) for s in candidate.shifts] == [2.5, 2.5]
    assert candidate.shifts[0].clock_out == "6:00 PM"
    assert candidate.shifts[1].clock_in == "6:00 PM"
    assert stats["rezaul_rows"] == 2
    assert stats["rezaul_total_hours"] == 5.0
