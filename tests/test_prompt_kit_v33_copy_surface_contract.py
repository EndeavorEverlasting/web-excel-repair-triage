from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from tests.test_prompt_kit_v33_artifact_contract import _make_valid_artifact
from triage.prompt_kit_v33_copy_surface_contract import validate_v33_copy_surfaces


def test_v33_copy_surface_contract_allows_navigation_rails(tmp_path: Path) -> None:
    artifact = tmp_path / "AI_Harness_Prompt_Kit_v33.xlsx"
    _make_valid_artifact(artifact)
    result = validate_v33_copy_surfaces(artifact)
    assert result.passed, result.findings
    assert result.prompt_count == 50


def test_v33_copy_surface_contract_rejects_column_a_payload_after_linked_range(tmp_path: Path) -> None:
    artifact = tmp_path / "AI_Harness_Prompt_Kit_v33.xlsx"
    _make_valid_artifact(artifact)
    workbook = load_workbook(artifact)
    workbook["P00_COPY_SAFE"]["A4"] = "outside linked range"
    workbook.save(artifact)

    result = validate_v33_copy_surfaces(artifact)
    assert not result.passed
    assert any("P00 has column-A payload after A3" in finding for finding in result.findings)
