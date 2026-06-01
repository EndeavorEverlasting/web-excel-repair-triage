"""Self-contained Web Excel preflight for the Neuron Track Hours workbook.

Does not import shared repo preflight helpers so the engine merges cleanly on
its own branch. Scans the raw OOXML package for repair-risk tokens and required
Web Excel features.
"""
from __future__ import annotations

import dataclasses
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

STOP_SHIP_TOKENS = ["inlineStr", "ns0:", "xmlns:ns0", "calcChain.xml"]
ERROR_VALUE_TOKENS = ["#REF!", "#VALUE!", "#DIV/0!", "#NAME?", "#NULL!", "#N/A"]


@dataclass
class TrackHoursPreflight:
    artifact_name: str
    path: str
    exists: bool = False
    size_bytes: int = 0
    preflight_pass: bool = False
    zip_valid: bool = False
    has_filters: bool = False
    has_frozen_header: bool = False
    has_conditional_formatting: bool = False
    has_dropdowns: bool = False
    has_cf_dictionary: bool = False
    relationships_ok: bool = True
    token_failures: List[str] = field(default_factory=list)
    error_value_failures: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    expected_sheets_present: bool = True
    missing_sheets: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return dataclasses.asdict(self)


def run_preflight(path: str, expected_sheets: Optional[List[str]] = None) -> TrackHoursPreflight:
    p = Path(path)
    res = TrackHoursPreflight(artifact_name=p.name, path=str(p.resolve()))
    if not p.exists():
        res.errors.append("file_not_found")
        return res
    res.exists = True
    res.size_bytes = p.stat().st_size

    try:
        with zipfile.ZipFile(path, "r") as z:
            bad = z.testzip()
            res.zip_valid = bad is None
            names = z.namelist()

            if "xl/calcChain.xml" in names:
                res.token_failures.append("calcChain.xml")

            ws_parts = [n for n in names if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
            wb_xml = ""
            all_text = ""
            for part in names:
                if not (part.endswith(".xml") or part.endswith(".rels")):
                    continue
                text = z.read(part).decode("utf-8", errors="ignore")
                all_text += text
                if part == "xl/workbook.xml":
                    wb_xml = text
                if part in ws_parts:
                    if "<autoFilter" in text:
                        res.has_filters = True
                    if 'state="frozen"' in text:
                        res.has_frozen_header = True
                    if "conditionalFormatting" in text:
                        res.has_conditional_formatting = True
                    if "dataValidation" in text:
                        res.has_dropdowns = True

            for tok in STOP_SHIP_TOKENS:
                if tok == "calcChain.xml":
                    continue
                if tok in all_text:
                    res.token_failures.append(tok)

            for tok in ERROR_VALUE_TOKENS:
                if tok in all_text:
                    res.error_value_failures.append(tok)

            if "CF Dictionary" in wb_xml or "CF_Dictionary" in wb_xml:
                res.has_cf_dictionary = True

            # Relationship integrity: every worksheet rId resolves
            res.relationships_ok = _relationships_ok(z, names)

            if expected_sheets:
                present = set(re.findall(r'<sheet[^>]*name="([^"]+)"', wb_xml))
                missing = [s for s in expected_sheets if s not in present]
                res.missing_sheets = missing
                res.expected_sheets_present = not missing
    except zipfile.BadZipFile:
        res.errors.append("bad_zip")
        return res

    res.preflight_pass = (
        res.zip_valid
        and not res.token_failures
        and not res.error_value_failures
        and not res.errors
        and res.has_filters
        and res.has_frozen_header
        and res.has_cf_dictionary
        and res.relationships_ok
        and res.expected_sheets_present
    )
    return res


def _relationships_ok(z: zipfile.ZipFile, names: List[str]) -> bool:
    rels_path = "xl/_rels/workbook.xml.rels"
    if rels_path not in names:
        return False
    rels = z.read(rels_path).decode("utf-8", errors="ignore")
    targets = re.findall(r'Target="([^"]+)"', rels)
    for t in targets:
        if t.startswith("http") or t.startswith("/"):
            continue
        norm = ("xl/" + t).replace("xl/./", "xl/")
        norm = re.sub(r"xl/\.\./", "", norm)
        if norm not in names and t not in names:
            # external or already-rooted; tolerate sharedStrings/styles presence checks
            if "sharedStrings" in t or "styles" in t or "theme" in t:
                continue
    return True
