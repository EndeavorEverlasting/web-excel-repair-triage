import zipfile
from tests._prompt_kit_fixture import build_prompt_kit, rewrite_part
from triage.prompt_kit_v21_repair_regressions import validate_repair_regressions


def test_validate_repair_regressions_rejects_external_target_mode_for_internal_links(tmp_path):
    path = tmp_path / "test_drawing.xlsx"
    # build_prompt_kit creates drawing rels with TargetMode="External" by default in the fixture
    build_prompt_kit(path, 1, require_backlinks=True)

    # Verify it fails validation
    res = validate_repair_regressions(path)
    assert not res["valid"]
    assert any("TargetMode='External'" in err["error"] for err in res["errors"])

    # Fix it by removing TargetMode="External"
    # The drawing rels part is xl/drawings/_rels/drawing1.xml.rels
    rewrite_part(path, "xl/drawings/_rels/drawing1.xml.rels", lambda x: x.replace('TargetMode="External"', ''))

    # Verify it passes now
    res = validate_repair_regressions(path)
    assert res["valid"], res["errors"]


def test_validate_repair_regressions_rejects_invalid_calc_chain_sheet_id(tmp_path):
    path = tmp_path / "test_calc.xlsx"
    build_prompt_kit(path, 1, require_backlinks=False)

    # By default, build_prompt_kit doesn't write calcChain.xml. Let's add it.
    with zipfile.ZipFile(path) as source:
        parts = {info.filename: source.read(info.filename) for info in source.infolist()}

    parts["xl/calcChain.xml"] = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><calcChain xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><c r="A1" i="99"/></calcChain>'

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as target:
        for name, content in parts.items():
            target.writestr(name, content)

    # Verify it fails because sheetId 99 is invalid
    res = validate_repair_regressions(path)
    assert not res["valid"]
    assert any("calcChain refers to sheetId not present" in err["error"] for err in res["errors"])

    # Change calcChain sheetId to 1 (valid sheetId for START_HERE)
    parts["xl/calcChain.xml"] = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><calcChain xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><c r="A1" i="1"/></calcChain>'

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as target:
        for name, content in parts.items():
            target.writestr(name, content)

    # Verify it passes now
    res = validate_repair_regressions(path)
    assert res["valid"], res["errors"]
