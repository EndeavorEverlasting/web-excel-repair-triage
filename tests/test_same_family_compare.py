"""Tests for triage.same_family_compare."""
from __future__ import annotations

from pathlib import Path

import pytest

from triage.same_family_compare.classify import classify_file
from triage.same_family_compare.compare import CompareError, run_same_family_compare
from triage.same_family_compare.scan import scan_intake
from tests.fixtures.admin_billing_summary.builders import build
from tests.fixtures.roster_log_compare import builders as rlb

REPO = Path(__file__).resolve().parent.parent


def test_classify_roster(tmp_path):
    paths = rlb.build_identical_pair(tmp_path)
    meta = classify_file(paths["left"])
    assert meta.artifact_family == "active_roster_log"
    assert meta.audience == "internal"


def test_scan_intake_empty(tmp_path):
    intake = tmp_path / "intake"
    intake.mkdir()
    scan = scan_intake(intake)
    assert scan["artifact_count"] == 0


def test_scan_finds_xlsx(tmp_path):
    intake = tmp_path / "intake"
    intake.mkdir()
    paths = rlb.build_identical_pair(intake)
    scan = scan_intake(intake)
    assert scan["artifact_count"] >= 2
    assert "active_roster_log" in scan.get("family_grouping", {})


def test_roster_same_family_compare(tmp_path):
    paths = rlb.build_older_name_newer_content(tmp_path)
    result = run_same_family_compare(paths["left"], paths["right"], family="active_roster_log")
    assert result["artifact_family"] == "active_roster_log"
    assert "engine_result" in result


def test_insufficient_metadata_mismatch(tmp_path):
    paths = rlb.build_identical_pair(tmp_path)
    result = run_same_family_compare(
        paths["left"], paths["right"], family="admin_billing_summary",
    )
    assert result.get("verdict") == "INSUFFICIENT_METADATA"


def test_baseline_missing_fails(tmp_path):
    with pytest.raises(CompareError):
        run_same_family_compare(tmp_path / "nope.xlsx", tmp_path / "nope2.xlsx")
