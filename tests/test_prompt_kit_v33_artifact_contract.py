from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Protection

from triage.prompt_kit_v33_artifact_contract import validate_artifact
from triage.prompt_kit_v33_layout_finalizer import canonicalize_layout
from tests.test_prompt_kit_v33_layout_finalizer import _make_pre_layout_artifact


def _make_valid_artifact(path: Path) -> None:
    _make_pre_layout_artifact(path)
    canonicalize_layout(path)


def test_valid_artifact_passes(tmp_path: Path) -> None:
    artifact = tmp_path / "AI_Harness_Prompt_Kit_v33.xlsx"
    _make_valid_artifact(artifact)
    result = validate_artifact(artifact)
    assert result.passed is True
    assert result.prompt_count == 48
    assert result.prompt_ids[0] == "P00"
    assert result.prompt_ids[-1] == "P47"
    assert result.findings == ()
    assert len(result.sha256) == 64


def test_contract_rejects_range_link_order_color_and_protection_drift(tmp_path: Path) -> None:
    artifact = tmp_path / "AI_Harness_Prompt_Kit_v33.xlsx"
    _make_valid_artifact(artifact)
    workbook = load_workbook(artifact)
    workbook["P07_COPY_SAFE"]["C1"].hyperlink = None
    workbook["P07_COPY_SAFE"]["C1"] = "Copy A1:A3 only"
    workbook["P46_COPY_SAFE"].sheet_properties.tabColor = "FF0000"
    workbook["Opportunity_Discovery"].protection.sheet = True
    workbook["START_HERE"].protection.sheet = False
    workbook._sheets[2], workbook._sheets[3] = workbook._sheets[3], workbook._sheets[2]
    workbook.save(artifact)

    findings = validate_artifact(artifact).findings
    assert any("worksheet order does not match" in item for item in findings)
    assert any("P07_COPY_SAFE!C1 range-recovery target" in item for item in findings)
    assert any("P46_COPY_SAFE tab color" in item for item in findings)
    assert any("excluded worksheet is protected: Opportunity_Discovery" in item for item in findings)
    assert any("worksheet is not protected: START_HERE" in item for item in findings)


def test_contract_rejects_unexpected_color_unlocked_cell_and_missing_prompt(tmp_path: Path) -> None:
    artifact = tmp_path / "AI_Harness_Prompt_Kit_v33.xlsx"
    _make_valid_artifact(artifact)
    workbook = load_workbook(artifact)
    workbook["START_HERE"].sheet_properties.tabColor = "00FF00"
    workbook["Prompt_Library"]["C2"].protection = Protection(locked=False)
    library = workbook["Prompt_Library"]
    p47_row = next(row for row in range(2, library.max_row) if library.cell(row=row, column=3).value == "P47")
    library.cell(row=p47_row, column=2).value = ""
    library.cell(row=p47_row, column=3).value = ""
    library.cell(row=p47_row, column=3).hyperlink = None
    workbook.save(artifact)

    findings = validate_artifact(artifact).findings
    assert any("unexpected tab color: START_HERE" in item for item in findings)
    assert any("protected worksheet contains unlocked cell: Prompt_Library!C2" in item for item in findings)
    assert "missing required prompt: P47" in findings
