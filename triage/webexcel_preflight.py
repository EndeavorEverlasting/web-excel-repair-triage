"""
Web Excel Preflight — scan package XML for repair risks and required features.
"""
from __future__ import annotations

import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.gate_checks import run_all, GateReport
from triage.nw_prj_config import stop_ship_tokens

@dataclass
class PreflightReport:
    artifact_name: str
    path: str
    exists: bool = False
    size_bytes: int = 0
    webexcel_preflight_pass: bool = False
    zip_valid: bool = False
    has_filters: bool = False
    has_frozen_header: bool = False
    has_cf_dictionary: bool = False
    has_conditional_formatting: bool = False
    has_dropdowns_where_expected: bool = False
    token_failures: List[str] = field(default_factory=list)
    gate_failures: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        import dataclasses
        return dataclasses.asdict(self)

def run_preflight(path: str, expected_sheets: List[str] = None) -> PreflightReport:
    p = Path(path)
    res = PreflightReport(artifact_name=p.name, path=str(p.resolve()))
    
    if not p.exists():
        res.errors.append("file_not_found")
        return res
    
    res.exists = True
    res.size_bytes = p.stat().st_size
    
    # 1. Run standard gate checks
    gate = run_all(str(p))
    res.zip_valid = gate.pass_all # simplified
    for k, n in gate.failing_gates().items():
        res.gate_failures.append(f"{k}:{n}")
        if k == "stopship_tokens":
             # gate_checks already found these, but we'll add more context below
             pass

    # 2. Artifact-specific checks
    try:
        with zipfile.ZipFile(path, "r") as z:
            namelist = z.namelist()
            
            # Check for forbidden files
            if "xl/calcChain.xml" in namelist:
                res.token_failures.append("calcChain.xml")
            
            # Check for shared strings
            has_shared = "xl/sharedStrings.xml" in namelist
            
            # Scan all XML for extra tokens not in gate_checks
            extra_tokens = ["inlineStr", "ns0:", "xmlns:ns0"]
            all_xml = b""
            
            # Identify sheets
            ws_parts = [n for n in namelist if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
            
            for part in namelist:
                if part.endswith(".xml") or part.endswith(".rels"):
                    content = z.read(part)
                    all_xml += content
                    
                    if part in ws_parts:
                        text = content.decode("utf-8", errors="ignore")
                        if "<autoFilter" in text or "<x:autoFilter" in text:
                            res.has_filters = True
                        if 'state="frozen"' in text:
                            res.has_frozen_header = True
                        if "conditionalFormatting" in text:
                            res.has_conditional_formatting = True
                        if "dataValidation" in text:
                            res.has_dropdowns_where_expected = True

            for t in extra_tokens:
                if t.encode("utf-8") in all_xml:
                    res.token_failures.append(t)
            
            # Check for expected sheets in workbook.xml
            if "xl/workbook.xml" in namelist:
                wb_xml = z.read("xl/workbook.xml").decode("utf-8", errors="ignore")
                if "CF_Dictionary" in wb_xml or "CF Dictionary" in wb_xml:
                    res.has_cf_dictionary = True
                
                if expected_sheets:
                    for s in expected_sheets:
                        if f'name="{s}"' not in wb_xml:
                            res.errors.append(f"missing_expected_sheet:{s}")

    except Exception as e:
        res.errors.append(f"preflight_exception:{str(e)}")

    # 3. Final verdict
    res.webexcel_preflight_pass = (
        res.zip_valid and 
        not res.token_failures and 
        not res.errors and 
        res.has_filters and 
        res.has_frozen_header
    )
    
    return res
