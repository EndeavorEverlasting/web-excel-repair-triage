from __future__ import annotations

import copy
import json
import zipfile
from pathlib import Path

import pytest

from triage import harness_bidirectional_conversion_contract as contract


def test_bidirectional_contract_schema_and_repository_wiring_are_valid() -> None:
    assert contract.validate_all() == ()


def test_sidecar_portal_html_selects_website_to_spreadsheet_first(tmp_path: Path) -> None:
    source = tmp_path / "index.html"
    source.write_text(
        '<!doctype html><script>const PORTAL = {"title":"Run Review","sections":[{"id":"kpi"}]};</script>',
        encoding="utf-8",
    )
    result = contract.analyze_input(source)
    assert result["source_kind"] == "sidecar_portal_html"
    assert result["recommended_direction"] == "website_to_spreadsheet"
    assert result["structured_payload_available"] is True
    assert result["extraction_strategy"] == "embedded_portal_json"
    assert result["mapping_profile"] == "sidecar_portal_v1"
    assert result["implementation_priority"] == 1
    assert result["portal_section_count"] == 1
    assert result["blockers"] == []


def test_generic_html_requires_an_operator_approved_mapping_profile(tmp_path: Path) -> None:
    source = tmp_path / "generic.html"
    source.write_text("<html><body><table><tr><td>A</td></tr></table></body></html>", encoding="utf-8")
    result = contract.analyze_input(source)
    assert result["source_kind"] == "generic_html"
    assert result["recommended_direction"] == "website_to_spreadsheet"
    assert result["extraction_strategy"] == "semantic_dom_tables_and_labels"
    assert result["blockers"] == ["operator_approved_mapping_profile_required"]


def test_xlsx_selects_spreadsheet_to_website_second(tmp_path: Path) -> None:
    source = tmp_path / "artifact.xlsx"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr("xl/workbook.xml", "<workbook />")
    result = contract.analyze_input(source)
    assert result["source_kind"] == "xlsx_workbook"
    assert result["recommended_direction"] == "spreadsheet_to_website"
    assert result["structured_payload_available"] is True
    assert result["extraction_strategy"] == "package_preserving_workbook_reader"
    assert result["implementation_priority"] == 2
    assert "approved_sheet_and_range_mapping_profile_required" in result["blockers"]


def test_policy_rejects_reversing_the_implementation_priority() -> None:
    policy = copy.deepcopy(contract.load_policy())
    policy["directions"][0]["implementation_priority"] = 2
    policy["directions"][1]["implementation_priority"] = 1
    issues = contract.validate_policy(policy)
    assert any("website_to_spreadsheet" in issue for issue in issues)
    assert any("spreadsheet_to_website" in issue for issue in issues)


def test_policy_rejects_actionless_conversion_claims() -> None:
    policy = copy.deepcopy(contract.load_policy())
    policy["action_commitment"]["conversion_claim_requires_output_artifact"] = False
    issues = contract.validate_policy(policy)
    assert any("conversion_claim_requires_output_artifact" in issue for issue in issues)


def test_network_urls_are_not_silently_fetched() -> None:
    with pytest.raises(ValueError, match="network website fetch requires explicit implementation scope"):
        contract.analyze_input("https://example.com")


def test_cli_writes_analysis_artifact(tmp_path: Path) -> None:
    source = tmp_path / "index.html"
    source.write_text('<script>const PORTAL = {"title":"Portal","sections":[]};</script>', encoding="utf-8")
    output = tmp_path / "conversion_analysis.json"
    assert contract.main(["--analyze-input", str(source), "--out", str(output), "--json"]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert payload["analysis"]["recommended_direction"] == "website_to_spreadsheet"


def test_repository_validator_rejects_stale_artifact_routing(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    registry = json.loads((root / "configs/harness/artifact_registry_v1.json").read_text(encoding="utf-8"))
    analysis = next(item for item in registry["artifacts"] if item["id"] == "web-spreadsheet-input-analysis")
    analysis["generator"] = "write a plan only"
    fake_root = tmp_path / "repo"
    for relative in (
        "configs/harness",
        "triage/sidecar_html",
        "triage",
        "docs",
    ):
        (fake_root / relative).mkdir(parents=True, exist_ok=True)
    for relative in (
        "configs/harness/bidirectional_web_spreadsheet_v1.json",
        "configs/harness/web_spreadsheet_ir_v1.schema.json",
        "triage/harness_bidirectional_conversion_contract.py",
        "docs/HARNESS_BIDIRECTIONAL_WEB_SPREADSHEET.md",
        "triage/sidecar_html/portal.py",
        "triage/sidecar_html/rebuild.py",
        "triage/sidecar_html/adapters.py",
    ):
        (fake_root / relative).write_text("{}", encoding="utf-8")
    (fake_root / "configs/harness/harness_manifest_v1.json").write_text(
        (root / "configs/harness/harness_manifest_v1.json").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (fake_root / "configs/harness/workflows_v1.json").write_text(
        (root / "configs/harness/workflows_v1.json").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (fake_root / "configs/harness/artifact_registry_v1.json").write_text(
        json.dumps(registry), encoding="utf-8"
    )
    issues = contract.validate_repository(fake_root)
    assert any("must route through the bidirectional analyzer" in issue for issue in issues)
