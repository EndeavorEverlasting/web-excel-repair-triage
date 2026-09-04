from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Dict, List, Optional
from xml.sax.saxutils import escape

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
XDR = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"

P21_LINES = [
    "MISSION",
    "SOURCE PROMPT DISPOSITION",
    "- included",
    "- merged",
    "- deferred-to-docs",
    "- superseded",
    "- rejected-with-reason",
    "- unresolved-blocker",
    "No source requirement may disappear silently.",
    "CONFLICT RESOLUTION",
    "IMMEDIATE OWNED SCOPE",
    "FORBIDDEN SCOPE",
    "REPOSITORY EVIDENCE REQUIRED",
    "EXECUTION CONTRACT",
    "ARTIFACT EXECUTION MODE",
    "Derive the branch name from the target repository existing conventions.",
    "VALIDATION",
    "DEFERRED DOCUMENTATION BRANCH",
    "FINAL HANDOFF",
]


def _sst(values: List[str]):
    unique: List[str] = []
    index: Dict[str, int] = {}
    for value in values:
        if value not in index:
            index[value] = len(unique)
            unique.append(value)
    xml = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<sst xmlns="{MAIN}" count="{len(values)}" uniqueCount="{len(unique)}">'
        + "".join(f"<si><t>{escape(value)}</t></si>" for value in unique)
        + "</sst>"
    )
    return xml, index


def _sheet_xml(rows: List[List[tuple[str, int, int]]], dimension: str, hyperlinks: str = "", drawing: bool = False) -> str:
    row_xml = []
    for row_number, cells in enumerate(rows, 1):
        pieces = []
        for ref, string_index, style in cells:
            pieces.append(f'<c r="{ref}" s="{style}" t="s"><v>{string_index}</v></c>')
        row_xml.append(f'<row r="{row_number}">{"".join(pieces)}</row>')
    extras = hyperlinks
    if drawing:
        extras += '<drawing r:id="rId1"/>'
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{MAIN}" xmlns:r="{REL}">'
        f'<dimension ref="{dimension}"/><sheetViews><sheetView workbookViewId="0"/></sheetViews>'
        f'<sheetData>{"".join(row_xml)}</sheetData>{extras}</worksheet>'
    )


def build_prompt_kit(path: Path, prompt_count: int, *, require_backlinks: bool, header_color: str = "Color", omit_p21_heading: Optional[str] = None) -> Path:
    prompt_ids = [f"P{i:02d}" for i in range(prompt_count)]
    sheet_names = ["Prompt_Library", "Prompt_Class_Legend", *[f"{pid}_COPY_SAFE" for pid in prompt_ids]]
    all_values: List[str] = []
    headers = [
        "Seq", "Prompt ID", "Prompt Type", "Prompt Class", "Sprint Path Role",
        "Use For Progress?", "Prompt Name", "Use This When", "Inspect First",
        "Expected Output", "Next Step", "Proof / Acceptance Gate", header_color,
        "Copy-Safe Sheet",
    ]
    all_values.extend(headers)
    for i, pid in enumerate(prompt_ids):
        all_values.extend([
            str(i), pid, "TYPE", "CLASS", "ROLE", "YES", f"Name {pid}",
            f"Use {pid}", f"Inspect {pid}", f"Output {pid}", "Next", "Gate", "Amber", f"{pid}_COPY_SAFE",
        ])
    all_values.extend(["Amber", "Planning or consolidation with bounded execution."])
    prompt_lines: Dict[str, List[str]] = {}
    for pid in prompt_ids:
        if pid == "P21":
            lines = [line for line in P21_LINES if line != omit_p21_heading]
        else:
            lines = [f"{pid} TITLE", f"{pid} BODY"]
        prompt_lines[pid] = lines
        all_values.extend(lines)
    sst_xml, sst = _sst(all_values)

    parts: Dict[str, str] = {}
    sheet_entries = []
    workbook_rels = []
    content_overrides = []
    for index, name in enumerate(sheet_names, 1):
        sheet_entries.append(f'<sheet name="{name}" sheetId="{index}" r:id="rId{index}"/>')
        workbook_rels.append(f'<Relationship Id="rId{index}" Type="{REL}/worksheet" Target="worksheets/sheet{index}.xml"/>')
        content_overrides.append(f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')

    parts["xl/workbook.xml"] = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="{MAIN}" xmlns:r="{REL}"><sheets>{"".join(sheet_entries)}</sheets></workbook>'
    parts["xl/_rels/workbook.xml.rels"] = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{PKG}">{"".join(workbook_rels)}<Relationship Id="rId{len(sheet_names)+1}" Type="{REL}/styles" Target="styles.xml"/><Relationship Id="rId{len(sheet_names)+2}" Type="{REL}/sharedStrings" Target="sharedStrings.xml"/></Relationships>'
    parts["xl/sharedStrings.xml"] = sst_xml
    parts["xl/styles.xml"] = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="{MAIN}">'
        '<fonts count="2"><font><sz val="11"/><name val="Aptos"/></font><font><sz val="12"/><name val="Aptos"/></font></fonts>'
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills><borders count="1"><border/></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0"/></cellXfs>'
        '</styleSheet>'
    )

    library_rows: List[List[tuple[str, int, int]]] = []
    library_rows.append([(f"{chr(64+i)}1", sst[value], 0) for i, value in enumerate(headers, 1)])
    hyperlink_nodes = []
    for index, pid in enumerate(prompt_ids):
        row = index + 2
        values = [str(index), pid, "TYPE", "CLASS", "ROLE", "YES", f"Name {pid}", f"Use {pid}", f"Inspect {pid}", f"Output {pid}", "Next", "Gate", "Amber", f"{pid}_COPY_SAFE"]
        cells = []
        for col_index, value in enumerate(values, 1):
            col = chr(64 + col_index)
            cells.append((f"{col}{row}", sst[value], 1 if col == "H" else 0))
        library_rows.append(cells)
        last = len(prompt_lines[pid])
        location = f"{pid}_COPY_SAFE!A1:A{last}"
        hyperlink_nodes.append(f'<hyperlink ref="B{row}" location="{location}"/>')
        hyperlink_nodes.append(f'<hyperlink ref="N{row}" location="{location}"/>')
    parts["xl/worksheets/sheet1.xml"] = _sheet_xml(library_rows, f"A1:N{prompt_count+1}", f'<hyperlinks>{"".join(hyperlink_nodes)}</hyperlinks>')
    parts["xl/worksheets/sheet2.xml"] = _sheet_xml([[], [("J2", sst["Amber"], 0), ("K2", sst["Planning or consolidation with bounded execution."], 0)]], "J2:K2")

    drawing_number = 0
    for prompt_index, pid in enumerate(prompt_ids):
        sheet_number = prompt_index + 3
        lines = prompt_lines[pid]
        rows = [[(f"A{row}", sst[line], 0)] for row, line in enumerate(lines, 1)]
        parts[f"xl/worksheets/sheet{sheet_number}.xml"] = _sheet_xml(rows, f"A1:A{len(lines)}", drawing=require_backlinks)
        if require_backlinks:
            drawing_number += 1
            parts[f"xl/worksheets/_rels/sheet{sheet_number}.xml.rels"] = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{PKG}"><Relationship Id="rId1" Type="{REL}/drawing" Target="../drawings/drawing{drawing_number}.xml"/></Relationships>'
            parts[f"xl/drawings/drawing{drawing_number}.xml"] = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><xdr:wsDr xmlns:xdr="{XDR}" xmlns:a="{A}" xmlns:r="{REL}"><xdr:oneCellAnchor><xdr:from><xdr:col>2</xdr:col><xdr:colOff>0</xdr:colOff><xdr:row>0</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:from><xdr:ext cx="100" cy="100"/><xdr:sp><xdr:nvSpPr><xdr:cNvPr id="1" name="Back"><a:hlinkClick r:id="rId1"/></xdr:cNvPr><xdr:cNvSpPr/></xdr:nvSpPr><xdr:spPr/><xdr:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>Back to Prompt Library</a:t></a:r></a:p></xdr:txBody></xdr:sp><xdr:clientData/></xdr:oneCellAnchor></xdr:wsDr>'
            parts[f"xl/drawings/_rels/drawing{drawing_number}.xml.rels"] = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{PKG}"><Relationship Id="rId1" Type="{REL}/hyperlink" Target="#Prompt_Library!B{prompt_index+2}" TargetMode="External"/></Relationships>'
            content_overrides.append(f'<Override PartName="/xl/drawings/drawing{drawing_number}.xml" ContentType="application/vnd.openxmlformats-officedocument.drawing+xml"/>')

    parts["[Content_Types].xml"] = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/><Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>' + "".join(content_overrides) + "</Types>"
    parts["_rels/.rels"] = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{PKG}"><Relationship Id="rId1" Type="{REL}/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in parts.items():
            zf.writestr(name, content)
    return path


def rewrite_part(path: Path, part: str, transform) -> None:
    with zipfile.ZipFile(path) as source:
        parts = {info.filename: source.read(info.filename) for info in source.infolist()}
    parts[part] = transform(parts[part].decode("utf-8")).encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as target:
        for name, content in parts.items():
            target.writestr(name, content)
