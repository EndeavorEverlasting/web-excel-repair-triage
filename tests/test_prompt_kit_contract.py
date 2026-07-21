import zipfile

from tests._prompt_kit_fixture import build_prompt_kit, rewrite_part
from triage.prompt_kit_common import workbook_sheet_map
from triage.prompt_kit_contract import validate_prompt_kit_contract


def test_v20_profile_accepts_p00_through_p20_and_color_header(tmp_path):
    path = build_prompt_kit(tmp_path / "v20.xlsx", 21, require_backlinks=False)
    report = validate_prompt_kit_contract(path, "v20")
    assert report.contract_valid, report.to_dict()


def test_v21_profile_requires_p21_and_backlinks(tmp_path):
    path = build_prompt_kit(tmp_path / "v21.xlsx", 22, require_backlinks=True)
    report = validate_prompt_kit_contract(path, "v21")
    assert report.contract_valid, report.to_dict()
    checks = {check.name: check for check in report.checks}
    assert checks["forward links target exact payload ranges"].summary == "44/44 links"
    assert checks["drawing backlinks target matching library rows"].summary == "22/22 valid"


def test_rejects_stale_color_meaning_header(tmp_path):
    path = build_prompt_kit(
        tmp_path / "bad_header.xlsx",
        21,
        require_backlinks=False,
        header_color="Color Meaning",
    )
    report = validate_prompt_kit_contract(path, "v20")
    assert not report.contract_valid
    assert any(
        check.name == "Prompt Library headers" and check.status == "FAIL"
        for check in report.checks
    )


def test_rejects_incomplete_p21_contract(tmp_path):
    path = build_prompt_kit(
        tmp_path / "bad_p21.xlsx",
        22,
        require_backlinks=True,
        omit_p21_heading="CONFLICT RESOLUTION",
    )
    report = validate_prompt_kit_contract(path, "v21")
    assert not report.contract_valid
    p21 = next(
        check for check in report.checks if check.name == "P21 consolidation contract"
    )
    assert {"missing_heading": "CONFLICT RESOLUTION"} in p21.findings


def test_malformed_xml_returns_fail_report_instead_of_crashing(tmp_path):
    path = build_prompt_kit(tmp_path / "malformed.xlsx", 21, require_backlinks=False)
    rewrite_part(path, "xl/workbook.xml", lambda text: text.replace("</workbook>", "<"))
    report = validate_prompt_kit_contract(path, "v20")
    assert not report.contract_valid
    package = next(check for check in report.checks if check.name == "package readable")
    assert package.status == "FAIL"


def test_p21_contract_ignores_cells_outside_exact_column_a(tmp_path):
    path = build_prompt_kit(
        tmp_path / "bad_p21_aa.xlsx",
        22,
        require_backlinks=True,
        omit_p21_heading="CONFLICT RESOLUTION",
    )
    with zipfile.ZipFile(path) as archive:
        part = workbook_sheet_map(archive)["P21_COPY_SAFE"]

    def add_aa_heading(text):
        return text.replace(
            "</sheetData>",
            '<row r="999"><c r="AA999" t="inlineStr"><is><t>CONFLICT RESOLUTION</t></is></c></row></sheetData>',
        )

    rewrite_part(path, part, add_aa_heading)
    report = validate_prompt_kit_contract(path, "v21")
    p21 = next(
        check for check in report.checks if check.name == "P21 consolidation contract"
    )
    assert {"missing_heading": "CONFLICT RESOLUTION"} in p21.findings
