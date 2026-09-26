"""tests/test_output_policy.py
-----------------------------
Tests for the harness output allocation and source immutability checks.
"""
from __future__ import annotations

from pathlib import Path

from triage.harness.output_policy import (
    is_source_path,
    is_output_path,
    validate_output_allocation,
    refuse_source_writes,
)
from triage.path_policy import repo_root


class TestIsSourcePath:
    def test_candidates(self):
        assert is_source_path("Candidates/roster.xlsx")

    def test_active(self):
        assert is_source_path("Active/roster.xlsx")

    def test_references(self):
        assert is_source_path("References/template.xlsx")

    def test_artifact_intake(self):
        assert is_source_path("ArtifactIntake/file.xlsx")

    def test_not_source(self):
        assert not is_source_path("Outputs/report.xlsx")

    def test_not_source_tests(self):
        assert not is_source_path("tests/fixtures/mini.xlsx")


class TestIsOutputPath:
    def test_outputs(self):
        assert is_output_path("Outputs/runs/abc12345")

    def test_outputs_full(self):
        assert is_output_path(repo_root() / "Outputs" / "something")

    def test_not_outputs(self):
        assert not is_output_path("Candidates/something")


class TestValidateOutputAllocation:
    def test_clean_output(self):
        v = validate_output_allocation("Outputs/runs/test", ["Active/roster.xlsx"])
        assert v == []

    def test_not_under_outputs(self):
        v = validate_output_allocation("tmp/output")
        assert len(v) >= 1

    def test_equals_input(self):
        v = validate_output_allocation("Outputs/x", ["Outputs/x"])
        assert any("equals input" in x for x in v)

    def test_overlaps_source(self):
        v = validate_output_allocation("Candidates/output")
        assert any("source" in x.lower() for x in v)


class TestRefuseSourceWrites:
    def test_refuses_candidates(self):
        v = refuse_source_writes(["Candidates/output.xlsx"])
        assert len(v) == 1

    def test_refuses_active(self):
        v = refuse_source_writes(["Active/output.xlsx"])
        assert len(v) == 1

    def test_allows_outputs(self):
        v = refuse_source_writes(["Outputs/clean.xlsx"])
        assert v == []

    def test_empty_list(self):
        v = refuse_source_writes([])
        assert v == []
