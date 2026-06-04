"""Web Excel package-level preflight gates for generated workbooks.

Wraps the repo's :func:`triage.gate_checks.run_all` battery and adds the
sprint-specific structural gates from the contract (namespace leakage,
``mc:Ignorable`` hygiene, function-namespace tokens, relationship integrity,
content-type coverage, and share-safe purity).

Honesty contract: a ZIP/XML pass is necessary but NOT sufficient. This module
never reports that Excel for Web opened cleanly. It reports only that the
available structural gates passed and that manual/Graph confirmation is still
required.
"""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from triage.gate_checks import run_all

# Generated-namespace leakage tokens (openpyxl / lxml round-trip smell).
_NS_LEAK_TOKENS = ("ns0:", "ns1:", "ns2:", "xmlns:ns0", "xmlns:ns1", "xmlns:ns2")
# Function / parameter namespace tokens Web Excel rejects.
_FN_TOKENS = ("_xlfn.", "_xludf.", "_xlpm.")

PREFLIGHT_PASSED_MESSAGE = (
    "Package preflight passed. Excel for Web manual open confirmation still required."
)
PREFLIGHT_FAILED_MESSAGE = (
    "Package preflight FAILED. Do not ship; workbook would likely trigger an "
    "Excel for Web repair prompt."
)


@dataclass
class PackagePreflight:
    path: str
    exists: bool = False
    zip_valid: bool = False
    sharesafe: bool = False
    gate_failures: Dict[str, int] = field(default_factory=dict)
    findings: Dict[str, List] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return (
            self.exists
            and self.zip_valid
            and not self.gate_failures
            and not any(self.findings.values())
            and not self.errors
        )

    @property
    def message(self) -> str:
        return PREFLIGHT_PASSED_MESSAGE if self.passed else PREFLIGHT_FAILED_MESSAGE

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "exists": self.exists,
            "zip_valid": self.zip_valid,
            "sharesafe": self.sharesafe,
            "passed": self.passed,
            "message": self.message,
            "gate_failures": self.gate_failures,
            "findings": {k: v for k, v in self.findings.items() if v},
            "errors": self.errors,
        }


def _add(findings: Dict[str, List], key: str, value) -> None:
    findings.setdefault(key, []).append(value)


def run_package_preflight(path: str, *, sharesafe: bool = False) -> PackagePreflight:
    """Run the full package preflight battery against ``path``."""
    p = Path(path)
    res = PackagePreflight(path=str(p), sharesafe=sharesafe)
    res.findings = {}

    if not p.exists():
        res.errors.append("file_not_found")
        return res
    res.exists = True

    # 1. Standard repo gate battery (XML wellformed, rels, dxf, calcChain, ...).
    try:
        gate = run_all(str(p))
        res.zip_valid = True
        res.gate_failures = gate.failing_gates()
    except zipfile.BadZipFile:
        res.errors.append("bad_zip")
        return res
    except Exception as e:  # pragma: no cover - defensive
        res.errors.append(f"gate_exception:{type(e).__name__}:{e}")
        return res

    # 2. Sprint-specific structural gates.
    try:
        with zipfile.ZipFile(str(p), "r") as z:
            namelist = z.namelist()
            xml_parts = [n for n in namelist if n.lower().endswith((".xml", ".rels"))]

            for part in xml_parts:
                text = z.read(part).decode("utf-8", errors="ignore")
                for tok in _NS_LEAK_TOKENS:
                    if tok in text:
                        _add(res.findings, "namespace_leakage", {"part": part, "token": tok})
                for tok in _FN_TOKENS:
                    if tok in text:
                        _add(res.findings, "function_namespace_tokens", {"part": part, "token": tok})
                if "inlineStr" in text and part.startswith("xl/worksheets/"):
                    _add(res.findings, "inline_str", {"part": part})

            _check_mc_ignorable(z, namelist, res.findings)
            _check_workbook_rels(z, namelist, res.findings)
            _check_content_types(z, namelist, res.findings)

            if sharesafe:
                _check_sharesafe(z, namelist, res.findings)
    except Exception as e:  # pragma: no cover - defensive
        res.errors.append(f"preflight_exception:{type(e).__name__}:{e}")

    return res


def _check_mc_ignorable(z: zipfile.ZipFile, namelist: List[str], findings: Dict[str, List]) -> None:
    """Every prefix listed in mc:Ignorable must be declared via xmlns."""
    for part in [n for n in namelist if n.lower().endswith(".xml")]:
        text = z.read(part).decode("utf-8", errors="ignore")
        for m in re.finditer(r'mc:Ignorable="([^"]*)"', text):
            for prefix in m.group(1).split():
                prefix = prefix.strip()
                if not prefix:
                    continue
                if f"xmlns:{prefix}" not in text:
                    _add(findings, "undeclared_mc_ignorable_prefix", {"part": part, "prefix": prefix})


def _check_workbook_rels(z: zipfile.ZipFile, namelist: List[str], findings: Dict[str, List]) -> None:
    """Duplicate workbook rel IDs and every sheet r:id must resolve."""
    rels_path = "xl/_rels/workbook.xml.rels"
    wb_path = "xl/workbook.xml"
    if rels_path not in namelist or wb_path not in namelist:
        return
    rels = z.read(rels_path).decode("utf-8", errors="ignore")
    wb = z.read(wb_path).decode("utf-8", errors="ignore")

    rid_seen: Dict[str, int] = {}
    for m in re.finditer(r'<Relationship\b[^>]*\bId="([^"]+)"', rels):
        rid_seen[m.group(1)] = rid_seen.get(m.group(1), 0) + 1
    for rid, n in rid_seen.items():
        if n > 1:
            _add(findings, "duplicate_workbook_rel_id", {"rId": rid, "count": n})

    declared = set(rid_seen)
    for m in re.finditer(r'<sheet\b[^>]*\br:id="([^"]+)"', wb):
        rid = m.group(1)
        if rid not in declared:
            _add(findings, "sheet_rid_missing_target", {"rId": rid})


def _check_content_types(z: zipfile.ZipFile, namelist: List[str], findings: Dict[str, List]) -> None:
    """Each worksheet part should be covered by [Content_Types].xml."""
    ct_path = "[Content_Types].xml"
    if ct_path not in namelist:
        _add(findings, "missing_content_types", {"part": ct_path})
        return
    ct = z.read(ct_path).decode("utf-8", errors="ignore")
    has_default_xml = bool(re.search(r'<Default\b[^>]*Extension="xml"', ct))
    for sheet_part in [n for n in namelist if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]:
        override = f'PartName="/{sheet_part}"'
        if override not in ct and not has_default_xml:
            _add(findings, "sheet_missing_content_type", {"part": sheet_part})


def _check_sharesafe(z: zipfile.ZipFile, namelist: List[str], findings: Dict[str, List]) -> None:
    """Share-safe workbooks must contain no formulas and no external links."""
    if any(n.startswith("xl/externalLinks/") for n in namelist):
        _add(findings, "external_links_present", {"count": sum(1 for n in namelist if n.startswith("xl/externalLinks/"))})
    if "xl/calcChain.xml" in namelist:
        _add(findings, "stale_calcchain", {"part": "xl/calcChain.xml"})
    for sheet_part in [n for n in namelist if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]:
        text = z.read(sheet_part).decode("utf-8", errors="ignore")
        if re.search(r"<f\b", text):
            _add(findings, "formula_in_sharesafe", {"part": sheet_part})
