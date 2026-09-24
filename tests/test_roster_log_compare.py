"""Tests for triage.roster_log_compare."""
from __future__ import annotations

from pathlib import Path

import openpyxl
import pytest

from triage.roster_log_compare.compare import main, run_comparison
from tests.fixtures.roster_log_compare import builders as b

FIX = Path(__file__).resolve().parent / "fixtures" / "roster_log_compare"


@pytest.fixture
def roster_base(tmp_path):
    d = tmp_path / "roster_pairs"
    d.mkdir()
    return d


@pytest.mark.parametrize(
    "builder,expected",
    [
        (b.build_identical_pair, "manual_review_required"),
        (b.build_newer_filename_same_content, "manual_review_required"),
        (b.build_older_name_newer_content, "use_right"),
        (b.build_punch_diff, "manual_review_required"),
        (b.build_increased_cf, "use_right"),
    ],
)
def test_verdict_scenarios(roster_base, builder, expected):
    paths = builder(roster_base)
    exp = paths.get("expect", expected)
    result = run_comparison(paths["left"], paths["right"])
    assert result["verdict"]["recommendation"] == exp


def test_cli_outputs_json_and_xlsx(roster_base, tmp_path):
    paths = b.build_punch_diff(roster_base)
    out_xlsx = tmp_path / "comparison.xlsx"
    out_json = tmp_path / "comparison.json"
    code = main([
        "--left", str(paths["left"]),
        "--right", str(paths["right"]),
        "--out", str(out_xlsx),
        "--json-out", str(out_json),
    ])
    assert code == 0
    assert out_json.is_file()
    assert out_xlsx.is_file()
    wb = openpyxl.load_workbook(out_xlsx, read_only=True)
    assert "Live Date Diffs" in wb.sheetnames
    wb.close()


def test_live_diff_lists_staff_date(roster_base):
    paths = b.build_punch_diff(roster_base)
    result = run_comparison(paths["left"], paths["right"])
    diffs = result["sections"]["live"]["diffs"]
    assert any(d.get("staff") == "Mensa Dee" for d in diffs)


def test_month_validation_invalid():
    from triage.month_validation import validate_month_key
    with pytest.raises(ValueError, match="01-12"):
        validate_month_key("2026-13")


def test_websafe_formula_prefix():
    from triage.websafe_cell import websafe_cell_value
    assert websafe_cell_value("=SUM(A1)") == "'=SUM(A1)"
