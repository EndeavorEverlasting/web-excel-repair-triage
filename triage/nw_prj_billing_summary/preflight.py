"""Web Excel preflight for the billing summary artifact.

Self-contained (no shared repo preflight import) so the engine merges cleanly.
Scans the raw OOXML package for repair-risk tokens, calc-chain ghosts, external
links, error values, and broken workbook relationships.
"""
from __future__ import annotations

import dataclasses
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

STOP_SHIP_TOKENS = ["inlineStr", "ns0:", "xmlns:ns0", "_xlfn.", "_xludf.", "_xlpm"]
ERROR_VALUE_TOKENS = ["#REF!", "#VALUE!", "#NAME?", "#DIV/0!", "#N/A", "#NULL!"]


@dataclass
class BillingPreflight:
    artifact_name: str
    path: str
    exists: bool = False
    size_bytes: int = 0
    preflight_pass: bool = False
    zip_valid: bool = False
    has_calc_chain: bool = False
    external_link_parts: List[str] = field(default_factory=list)
    token_failures: List[str] = field(default_factory=list)
    error_value_failures: List[str] = field(default_factory=list)
    broken_relationships: List[str] = field(default_factory=list)
    sheet_count: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return dataclasses.asdict(self)


def _broken_rels(z: zipfile.ZipFile, names: List[str]) -> List[str]:
    rels_path = "xl/_rels/workbook.xml.rels"
    if rels_path not in names:
        return []
    rels = z.read(rels_path).decode("utf-8", errors="ignore")
    broken: List[str] = []
    for t in re.findall(r'Target="([^"]+)"', rels):
        if t.startswith("http") or t.startswith("/"):
            continue
        norm = ("xl/" + t).replace("xl/./", "xl/")
        norm = re.sub(r"xl/\.\./", "", norm)
        if norm not in names and t not in names:
            broken.append(t)
    return broken


def run_preflight(path: str) -> BillingPreflight:
    p = Path(path)
    res = BillingPreflight(artifact_name=p.name, path=str(p.resolve()))
    if not p.exists():
        res.errors.append("file_not_found")
        return res
    res.exists = True
    res.size_bytes = p.stat().st_size

    try:
        with zipfile.ZipFile(path, "r") as z:
            res.zip_valid = z.testzip() is None
            names = z.namelist()
            res.has_calc_chain = "xl/calcChain.xml" in names
            res.external_link_parts = [n for n in names if n.startswith("xl/externalLinks/")]

            wb_xml = ""
            all_text = ""
            for part in names:
                if not (part.endswith(".xml") or part.endswith(".rels")):
                    continue
                text = z.read(part).decode("utf-8", errors="ignore")
                all_text += text
                if part == "xl/workbook.xml":
                    wb_xml = text

            res.sheet_count = len(re.findall(r"<sheet\b[^>]*>", wb_xml))
            for tok in STOP_SHIP_TOKENS:
                if tok in all_text:
                    res.token_failures.append(tok)
            for tok in ERROR_VALUE_TOKENS:
                if tok in all_text:
                    res.error_value_failures.append(tok)
            res.broken_relationships = _broken_rels(z, names)
    except zipfile.BadZipFile:
        res.errors.append("bad_zip")
        return res

    res.preflight_pass = (
        res.zip_valid
        and not res.has_calc_chain
        and not res.external_link_parts
        and not res.token_failures
        and not res.error_value_failures
        and not res.broken_relationships
        and not res.errors
    )
    return res
