import zipfile

from tests._prompt_kit_fixture import build_prompt_kit
from triage.prompt_kit_contract import validate_prompt_kit_contract
from triage.prompt_kit_common import MAIN_NS, drawing_backlink_target, shared_strings, workbook_sheet_map, xml_root, cell_value


def test_v21_has_44_forward_links_22_backlinks_and_artifact_execution_contract(tmp_path):
    path = build_prompt_kit(tmp_path / "v21.xlsx", 22, require_backlinks=True)
    report = validate_prompt_kit_contract(path, "v21")
    assert report.contract_valid, report.to_dict()
    with zipfile.ZipFile(path) as zf:
        sheets = workbook_sheet_map(zf)
        shared = shared_strings(zf)
        library = xml_root(zf, sheets["Prompt_Library"])
        assert len(library.findall(f'.//{{{MAIN_NS}}}hyperlink')) == 44
        for index in range(22):
            pid = f"P{index:02d}"
            label, target = drawing_backlink_target(zf, sheets[f"{pid}_COPY_SAFE"])
            assert label == "Back to Prompt Library"
            assert target == f"#Prompt_Library!B{index+2}"
        p21 = xml_root(zf, sheets["P21_COPY_SAFE"])
        text = "\n".join(cell_value(cell, shared) for cell in p21.findall(f'.//{{{MAIN_NS}}}c'))
        assert "ARTIFACT EXECUTION MODE" in text
        assert "No source requirement may disappear silently." in text
