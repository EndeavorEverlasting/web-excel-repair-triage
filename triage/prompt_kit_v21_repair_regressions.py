"""Repair regression validators for AI Harness Prompt Kit V21.

1. Same-workbook drawing hyperlinks must not use TargetMode="External".
2. calcChain.xml uses worksheet sheetId, not worksheet ordinal position.
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from triage.prompt_kit_common import MAIN_NS, PKG_REL_NS, xml_root, workbook_sheet_map

NS = {"m": MAIN_NS, "pr": PKG_REL_NS}


def validate_drawing_hyperlinks(zf: zipfile.ZipFile) -> list[dict]:
    """Ensure no same-workbook drawing hyperlinks use TargetMode='External'."""
    findings = []
    for name in zf.namelist():
        if "xl/drawings/_rels/" in name and name.endswith(".rels"):
            try:
                root = xml_root(zf, name)
                for rel in root:
                    target = rel.attrib.get("Target", "")
                    target_mode = rel.attrib.get("TargetMode", "")
                    # Same-workbook drawing hyperlink targets usually start with '#'
                    if target.startswith("#") and target_mode == "External":
                        findings.append({
                            "part": name,
                            "id": rel.attrib.get("Id"),
                            "target": target,
                            "target_mode": target_mode,
                            "error": "Same-workbook hyperlink must not use TargetMode='External'",
                        })
            except Exception as e:
                findings.append({"part": name, "error": f"Failed to parse rels: {e}"})
    return findings


def validate_calc_chain_sheet_ids(zf: zipfile.ZipFile) -> list[dict]:
    """Ensure calcChain.xml uses worksheet sheetId, not worksheet ordinal position."""
    findings = []
    if "xl/calcChain.xml" not in zf.namelist():
        return findings

    try:
        # Load sheets from xl/workbook.xml to get their sheetIds
        wb_root = xml_root(zf, "xl/workbook.xml")
        sheet_ids = set()
        sheet_names_by_id = {}
        for sheet in wb_root.findall("m:sheets/m:sheet", NS):
            sid = sheet.attrib.get("sheetId")
            name = sheet.attrib.get("name")
            if sid:
                sheet_ids.add(sid)
                sheet_names_by_id[sid] = name

        calc_root = xml_root(zf, "xl/calcChain.xml")
        # calcChain contains <c r="A1" i="28"/>
        # i attribute is the sheetId. It must exist in the workbook's sheets.
        for idx, c_node in enumerate(calc_root.findall("m:c", NS)):
            sheet_id_attr = c_node.attrib.get("i")
            if sheet_id_attr is not None:
                if sheet_id_attr not in sheet_ids:
                    findings.append({
                        "node_index": idx,
                        "ref": c_node.attrib.get("r"),
                        "invalid_sheet_id": sheet_id_attr,
                        "error": "calcChain refers to sheetId not present in workbook",
                    })
            else:
                # If 'i' is missing, it inherits from the previous element.
                # However, the first element must have 'i'.
                if idx == 0:
                    findings.append({
                        "node_index": idx,
                        "ref": c_node.attrib.get("r"),
                        "error": "First calcChain cell is missing sheetId attribute 'i'",
                    })
    except Exception as e:
        findings.append({"part": "xl/calcChain.xml", "error": f"Failed to parse calcChain: {e}"})
    return findings


def validate_repair_regressions(path: str | Path) -> dict:
    """Run all repair-regression checks on a workbook."""
    workbook = Path(path)
    if not workbook.exists():
        return {
            "path": str(workbook),
            "valid": False,
            "errors": [{"error": f"File does not exist: {workbook}"}],
        }

    try:
        with zipfile.ZipFile(workbook) as zf:
            drawing_errors = validate_drawing_hyperlinks(zf)
            calc_chain_errors = validate_calc_chain_sheet_ids(zf)

            errors = drawing_errors + calc_chain_errors
            return {
                "path": str(workbook),
                "valid": len(errors) == 0,
                "errors": errors,
            }
    except Exception as e:
        return {
            "path": str(workbook),
            "valid": False,
            "errors": [{"error": f"Failed to read package: {e}"}],
        }
