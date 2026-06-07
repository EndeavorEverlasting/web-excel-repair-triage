"""Web Excel preflight for NW PRJ Admin Log Project Team workbooks."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List

import openpyxl

from triage.nw_prj_admin_log.grid import FORBIDDEN_VISIBLE_PHRASES, scan_forbidden_visible_text
from triage.nw_prj_admin_log.visual_donor import PROJECT_TEAM_SHEET

_INLINE_CELL = 't="inlineStr"'
_STOP_SHIP = ["ns0:", "xmlns:ns0", "_xlfn.", "_xludf.", "_xlpm."]
_FORMULA_ERRORS = ("#REF!", "#VALUE!", "#NAME?", "#DIV/0!", "#NULL!", "#NUM!", "#N/A")


def preflight_project_team(path: str) -> Dict[str, Any]:
    p = Path(path)
    res: Dict[str, Any] = {
        "artifact": p.name,
        "path": str(p.resolve()),
        "exists": p.exists(),
        "zip_valid": False,
        "token_failures": [],
        "has_calc_chain": False,
        "has_external_links": False,
        "sharedstrings_count_ok": True,
        "sharedstrings_declared_count": None,
        "sharedstrings_actual_refs": 0,
        "forbidden_visible_phrases": [],
        "column_a_hidden": False,
        "freeze_panes": None,
        "visible_sheet_count": 0,
        "sheet_names": [],
        "excel_for_web_manual_check": "NOT_PROVEN",
        "preflight_pass": False,
    }
    if not p.exists():
        res["error"] = "file_not_found"
        return res

    try:
        with zipfile.ZipFile(path, "r") as z:
            res["zip_valid"] = z.testzip() is None
            names = z.namelist()
            if "xl/calcChain.xml" in names:
                res["has_calc_chain"] = True
            if any("externalLink" in n for n in names):
                res["has_external_links"] = True
            all_text = ""
            wb_xml = ""
            for name in names:
                if not (name.endswith(".xml") or name.endswith(".rels")):
                    continue
                text = z.read(name).decode("utf-8", errors="ignore")
                all_text += text
                if name == "xl/workbook.xml":
                    wb_xml = text
            for name in names:
                if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
                    ws_text = z.read(name).decode("utf-8", errors="ignore")
                    if _INLINE_CELL in ws_text:
                        res["token_failures"].append("inlineStr")
                        break
            for tok in _STOP_SHIP:
                if tok in all_text:
                    res["token_failures"].append(tok)
            for err in _FORMULA_ERRORS:
                if err in all_text:
                    res["token_failures"].append(f"formula_error:{err}")
            res["sheet_names"] = re.findall(r'<sheet[^>]*name="([^"]+)"', wb_xml)
            refs = sum(
                z.read(n).decode("utf-8", errors="ignore").count('t="s"')
                for n in names
                if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")
            )
            res["sharedstrings_actual_refs"] = refs
            if "xl/sharedStrings.xml" in names:
                ss = z.read("xl/sharedStrings.xml").decode("utf-8", errors="ignore")
                m = re.search(r'\bcount="(\d+)"', ss)
                declared = int(m.group(1)) if m else -1
                res["sharedstrings_declared_count"] = declared
                res["sharedstrings_count_ok"] = declared == refs
            elif refs > 0:
                res["sharedstrings_count_ok"] = False
            res["drawing_part_count"] = len([n for n in names if n.startswith("xl/drawings/")])
            res["media_part_count"] = len([n for n in names if n.startswith("xl/media/")])
    except zipfile.BadZipFile:
        res["error"] = "bad_zip"
        return res

    wb = openpyxl.load_workbook(path)
    visible = [s for s in wb.worksheets if s.sheet_state == "visible"]
    res["visible_sheet_count"] = len(visible)
    if PROJECT_TEAM_SHEET not in wb.sheetnames:
        res["token_failures"].append(f"missing_sheet:{PROJECT_TEAM_SHEET}")
    else:
        ws = wb[PROJECT_TEAM_SHEET]
        res["freeze_panes"] = ws.freeze_panes
        res["column_a_hidden"] = bool(ws.column_dimensions["A"].hidden)
        res["forbidden_visible_phrases"] = scan_forbidden_visible_text(ws)
        if ws.freeze_panes != "C1":
            res["token_failures"].append(f"freeze_not_C1:{ws.freeze_panes}")
        if not res["column_a_hidden"]:
            res["token_failures"].append("column_a_not_hidden")
    wb.close()

    if res["visible_sheet_count"] != 1:
        res["token_failures"].append(f"visible_sheets:{res['visible_sheet_count']}")
    if res["forbidden_visible_phrases"]:
        res["token_failures"].append("forbidden_visible_text")

    res["preflight_pass"] = (
        bool(res["zip_valid"])
        and not res["token_failures"]
        and not res["has_calc_chain"]
        and not res["has_external_links"]
        and res["sharedstrings_count_ok"]
    )
    return res
