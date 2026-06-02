"""Conditional-formatting Sunday/Monday bleed + diff tests."""
from __future__ import annotations

from datetime import date

import pytest

from tests.fixtures.may_roster_webexcel.builders import (
    build_bad_cf_workbook,
    build_good_cf_workbook,
)
from triage.may_roster_webexcel.cf_inspector import (
    diff_cf,
    expand_sqref_columns,
    formula_column_refs,
    sunday_bleed_report,
    sunday_monday_boundaries,
)

SHEET = "Live - May 2026"


def test_sunday_monday_boundaries_may_2026():
    pairs = sunday_monday_boundaries(2026, 5)
    sundays = [s.isoformat() for s, _ in pairs]
    assert sundays == ["2026-05-03", "2026-05-10", "2026-05-17", "2026-05-24", "2026-05-31"]
    # May 31 is the trailing Sunday: no in-month Monday.
    assert pairs[-1][1] is None
    # May 17 -> May 18.
    assert pairs[2] == (date(2026, 5, 17), date(2026, 5, 18))


def test_expand_sqref_and_formula_refs():
    assert expand_sqref_columns("AI3:AL202") == ["AI", "AJ", "AK", "AL"]
    assert expand_sqref_columns("AI3:AI22 AK3:AK50") == ["AI", "AK"]
    assert formula_column_refs('AND($AI3="",$AK3<>"")') == {"AI", "AK"}


def test_good_workbook_is_clean(tmp_path):
    p = build_good_cf_workbook(str(tmp_path / "good.xlsx"))
    rpt = sunday_bleed_report(p, SHEET, 2026, 5)
    assert rpt.clean, [f.__dict__ for f in rpt.findings]


def test_bad_workbook_flags_all_three_defects(tmp_path):
    p = build_bad_cf_workbook(str(tmp_path / "bad.xlsx"))
    rpt = sunday_bleed_report(p, SHEET, 2026, 5)
    assert not rpt.clean
    kinds = {f.kind for f in rpt.findings}
    assert "sunday_rule_references_monday" in kinds
    assert "always_true_blanket_over_sunday" in kinds
    assert "merged_range_crosses_sunday_monday" in kinds


def test_bad_findings_anchor_on_may_17_18(tmp_path):
    p = build_bad_cf_workbook(str(tmp_path / "bad.xlsx"))
    rpt = sunday_bleed_report(p, SHEET, 2026, 5)
    cross = [f for f in rpt.findings if f.kind == "sunday_rule_references_monday"]
    assert cross and cross[0].sunday == "2026-05-17" and cross[0].monday == "2026-05-18"


def test_diff_detects_cf_divergence(tmp_path):
    good = build_good_cf_workbook(str(tmp_path / "good.xlsx"))
    bad = build_bad_cf_workbook(str(tmp_path / "bad.xlsx"))
    diff = diff_cf(bad, good, SHEET)
    assert not diff.identical
    # The bad workbook has extra blocks the good one lacks.
    assert diff.only_in_candidate
