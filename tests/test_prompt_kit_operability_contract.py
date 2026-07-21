from __future__ import annotations

import io
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from triage.prompt_kit_operability_contract import (
    validate_gnhf_launch_command,
    validate_prompt_kit_operability,
)

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"

VALID_COMMAND = '''gnhf `
  --agent opencode `
  --worktree `
  --max-iterations 3 `
  --max-tokens 300000 `
  --prevent-sleep on `
  --stop-when "One bounded mutation is committed and validated." `
  "Repo: xyz_repo_or_path

Sprint: xyz_sprint_name

Objective:
Modify one owned repository surface, run xyz_canonical_proof, commit the coherent change, and stop.

Forbidden:
- push
- credentials
- live targets

Report:
- commit
- validation
- git status"'''


def _col(number: int) -> str:
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _cell(ref: str, value: str, style: int = 0) -> str:
    return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'


def _worksheet(
    rows: list[tuple[int, list[str]]],
    *,
    hyperlinks: list[tuple[str, str]] | None = None,
) -> str:
    row_xml = "".join(
        f'<row r="{number}">{"".join(cells)}</row>' for number, cells in rows
    )
    link_xml = ""
    if hyperlinks:
        link_xml = "<hyperlinks>" + "".join(
            f'<hyperlink ref="{ref}" location="{escape(location)}"/>'
            for ref, location in hyperlinks
        ) + "</hyperlinks>"
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{MAIN}"><sheetData>{row_xml}</sheetData>'
        f'<sheetProtection sheet="1" objects="1" scenarios="1"/>{link_xml}</worksheet>'
    )


def _valid_prompt_command(prompt_id: str) -> list[str]:
    return VALID_COMMAND.replace(
        "xyz_sprint_name", f"{prompt_id} atomic lane"
    ).splitlines()


def _rewrite_zip_part(path: Path, part: str, transform) -> None:
    with zipfile.ZipFile(path, "r") as source:
        entries = {name: source.read(name) for name in source.namelist()}
    entries[part] = transform(entries[part].decode("utf-8")).encode("utf-8")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as target:
        for name, payload in entries.items():
            target.writestr(name, payload)
    path.write_bytes(buffer.getvalue())


def build_v32_fixture(path: Path) -> Path:
    prompt_ids = [f"P{index:02d}" for index in range(37)]
    sheets = [
        "Prompt_Library",
        "Prompt_Sequence",
        "Opportunity_Discovery",
        "GNHF_Workflow_Map",
    ] + [f"{prompt_id}_COPY_SAFE" for prompt_id in prompt_ids]
    parts: dict[str, str] = {}

    sheet_entries = []
    workbook_rels = []
    overrides = []
    for index, name in enumerate(sheets, start=1):
        sheet_entries.append(
            f'<sheet name="{name}" sheetId="{index}" r:id="rId{index}"/>'
        )
        workbook_rels.append(
            f'<Relationship Id="rId{index}" Type="{REL}/worksheet" '
            f'Target="worksheets/sheet{index}.xml"/>'
        )
        overrides.append(
            f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.'
            'spreadsheetml.worksheet+xml"/>'
        )

    parts["xl/workbook.xml"] = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<workbook xmlns="{MAIN}" xmlns:r="{REL}">'
        f'<workbookProtection lockStructure="1"/>'
        f'<sheets>{"".join(sheet_entries)}</sheets></workbook>'
    )
    parts["xl/_rels/workbook.xml.rels"] = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{PKG}">{"".join(workbook_rels)}'
        f'<Relationship Id="rId{len(sheets)+1}" Type="{REL}/styles" '
        f'Target="styles.xml"/></Relationships>'
    )
    parts["xl/styles.xml"] = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<styleSheet xmlns="{MAIN}">'
        '<fonts count="6">'
        '<font><sz val="10"/><name val="Aptos"/></font>'
        '<font><sz val="10"/><color rgb="FF3730A3"/><name val="Aptos"/></font>'
        '<font><b/><sz val="10"/><color rgb="FF3730A3"/><name val="Aptos"/></font>'
        '<font><b/><sz val="28"/><color rgb="FF3730A3"/><name val="Aptos"/></font>'
        '<font><b/><sz val="12"/><color rgb="FF3730A3"/><name val="Aptos"/></font>'
        '<font><b/><sz val="10"/><color rgb="FF047857"/><name val="Aptos"/></font>'
        '</fonts>'
        '<fills count="3">'
        '<fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="solid">'
        '<fgColor rgb="FFE0E7FF"/></patternFill></fill>'
        '<fill><patternFill patternType="solid">'
        '<fgColor rgb="FFD1FAE5"/></patternFill></fill>'
        '</fills>'
        '<borders count="1"><border/></borders>'
        '<cellStyleXfs count="1">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>'
        '</cellStyleXfs>'
        '<cellXfs count="7">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="1" borderId="0" xfId="0" '
        'applyFont="1" applyFill="1"/>'
        '<xf numFmtId="0" fontId="2" fillId="1" borderId="0" xfId="0" '
        'applyFont="1" applyFill="1"/>'
        '<xf numFmtId="0" fontId="3" fillId="1" borderId="0" xfId="0" '
        'applyFont="1" applyFill="1"/>'
        '<xf numFmtId="0" fontId="4" fillId="1" borderId="0" xfId="0" '
        'applyFont="1" applyFill="1"/>'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" '
        'applyProtection="1"><protection locked="0" hidden="0"/></xf>'
        '<xf numFmtId="0" fontId="5" fillId="2" borderId="0" xfId="0" '
        'applyFont="1" applyFill="1"/>'
        '</cellXfs></styleSheet>'
    )

    headers = [
        "Seq",
        "Prompt ID",
        "Prompt Type",
        "Prompt Class",
        "Sprint Path Role",
        "Use For Progress?",
        "Prompt Name",
        "Use This When",
        "Inspect First",
        "Expected Output",
        "Next Step",
        "Proof / Acceptance Gate",
        "Color",
        "Copy-Safe Sheet",
    ]
    library_rows: list[tuple[int, list[str]]] = [
        (
            1,
            [_cell("A1", "↓ Bottom", 6)]
            + [
                _cell(f"{_col(index)}1", value)
                for index, value in enumerate(headers, start=2)
            ]
            + [_cell("P1", "↓ Bottom", 6)],
        )
    ]
    library_links = [
        ("A1", "'Prompt_Library'!A39"),
        ("P1", "'Prompt_Library'!P39"),
    ]
    for index, prompt_id in enumerate(prompt_ids):
        row = index + 2
        values = [
            f"{index:02d}",
            prompt_id,
            "TYPE",
            "CLASS",
            "ROLE",
            "YES",
            f"Name {prompt_id}",
            f"Use {prompt_id}",
            f"Inspect {prompt_id}",
            f"Output {prompt_id}",
            "Next",
            "Gate",
            "Night",
            f"{prompt_id}_COPY_SAFE",
        ]
        styles = [2, 3, 2, 2, 1, 2, 4, 1, 1, 1, 1, 1, 2, 2]
        library_rows.append(
            (
                row,
                [
                    _cell(f"{_col(column)}{row}", value, styles[column - 2])
                    for column, value in enumerate(values, start=2)
                ],
            )
        )
        lines = (
            _valid_prompt_command(prompt_id)
            if index >= 26
            else [f"{prompt_id} CHAT PROMPT", "Body"]
        )
        target = f"'{prompt_id}_COPY_SAFE'!A1:A{len(lines)}"
        library_links.extend(((f"C{row}", target), (f"O{row}", target)))
    library_rows.append(
        (39, [_cell("A39", "↑ Top", 6), _cell("P39", "↑ Top", 6)])
    )
    library_links.extend(
        (("A39", "'Prompt_Library'!A1"), ("P39", "'Prompt_Library'!P1"))
    )
    parts["xl/worksheets/sheet1.xml"] = _worksheet(
        library_rows, hyperlinks=library_links
    )
    parts["xl/worksheets/sheet2.xml"] = _worksheet(
        [(1, [_cell("A1", "Prompt Sequence")])]
    )

    opportunity_rows = []
    for row in range(1, 101):
        opportunity_rows.append(
            (
                row,
                [
                    _cell(f"{_col(column)}{row}", "", 5)
                    for column in range(1, 19)
                ],
            )
        )
    parts["xl/worksheets/sheet3.xml"] = _worksheet(opportunity_rows)
    parts["xl/worksheets/sheet4.xml"] = _worksheet(
        [(1, [_cell("A1", "GNHF Workflow Map")])]
    )

    for offset, prompt_id in enumerate(prompt_ids, start=5):
        lines = (
            _valid_prompt_command(prompt_id)
            if int(prompt_id[1:]) >= 26
            else [f"{prompt_id} CHAT PROMPT", "Body"]
        )
        rows = []
        for row, line in enumerate(lines, start=1):
            cells = [_cell(f"A{row}", line)]
            if row in (1, len(lines)):
                cells.append(_cell(f"C{row}", "Back to Prompt Library", 6))
            rows.append((row, cells))
        parts[f"xl/worksheets/sheet{offset}.xml"] = _worksheet(
            rows,
            hyperlinks=[
                ("C1", "'Prompt_Library'!A1"),
                (f"C{len(lines)}", "'Prompt_Library'!A1"),
            ],
        )

    parts["[Content_Types].xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.'
        'spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.'
        'spreadsheetml.styles+xml"/>'
        + "".join(overrides)
        + "</Types>"
    )
    parts["_rels/.rels"] = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{PKG}"><Relationship Id="rId1" '
        f'Type="{REL}/officeDocument" Target="xl/workbook.xml"/>'
        f"</Relationships>"
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in parts.items():
            zf.writestr(name, content)
    return path


def test_valid_gnhf_command_is_terminal_launchable():
    assert validate_gnhf_launch_command(VALID_COMMAND) == []


def test_bare_chat_prompt_is_not_a_powershell_launch_command():
    findings = validate_gnhf_launch_command(
        "We covered a lot. Convert this chat into a sprint map."
    )
    assert findings
    assert findings[0]["rule"] == "command starts with PowerShell gnhf continuation"


def test_worktree_and_current_branch_are_mutually_exclusive():
    broken = VALID_COMMAND.replace(
        "  --worktree `", "  --worktree `\n  --current-branch `"
    )
    findings = validate_gnhf_launch_command(broken)
    assert any(item["rule"] == "exactly one Git execution mode" for item in findings)


def test_caps_are_required():
    broken = VALID_COMMAND.replace("  --max-tokens 300000 `\n", "")
    findings = validate_gnhf_launch_command(broken)
    assert any(item["rule"] == "required flag: max_tokens" for item in findings)


def test_synthetic_v32_operability_contract(tmp_path):
    workbook = build_v32_fixture(tmp_path / "prompt-kit-v32.xlsx")
    report = validate_prompt_kit_operability(workbook)
    assert report.valid, report.to_dict()


def test_rejects_unlocked_cell_outside_sole_edit_range(tmp_path):
    workbook = build_v32_fixture(tmp_path / "prompt-kit-v32-unlocked.xlsx")

    def add_unlocked_cell(text: str) -> str:
        return text.replace(
            "</sheetData>",
            f'<row r="101">{_cell("S101", "unexpected edit", 5)}</row></sheetData>',
            1,
        )

    _rewrite_zip_part(workbook, "xl/worksheets/sheet3.xml", add_unlocked_cell)
    report = validate_prompt_kit_operability(workbook)
    check = next(
        item
        for item in report.checks
        if item.name == "no unlocked cells outside sole edit range"
    )
    assert check.status == "FAIL"
    assert any(item["cell"] == "S101" for item in check.findings)


def test_rejects_wrong_body_font_in_semantic_column(tmp_path):
    workbook = build_v32_fixture(tmp_path / "prompt-kit-v32-font.xlsx")

    def make_f2_oversized_bold(text: str) -> str:
        original = _cell("F2", "ROLE", 1)
        replacement = _cell("F2", "ROLE", 3)
        assert original in text
        return text.replace(original, replacement, 1)

    _rewrite_zip_part(workbook, "xl/worksheets/sheet1.xml", make_f2_oversized_bold)
    report = validate_prompt_kit_operability(workbook)
    check = next(
        item
        for item in report.checks
        if item.name == "Prompt Library semantic fonts and color coordination"
    )
    assert check.status == "FAIL"
    assert any(item.get("cell") == "F2" for item in check.findings)
