"""
triage/billing_workbook_profile.py
----------------------------------
Detect known billing workbook structures from OOXML ZIP contents.

This module is READ-ONLY: it inspects sheet names, table names, and key cell
values to decide whether a workbook matches the expected Billing Bridge profile.
"""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from triage.xlsx_utils import read_text, sheet_name_map, table_parts


# Known billing sheet name keywords (lowercase)
BILLING_SHEET_KEYWORDS: Set[str] = {
    "billing", "invoice", "hours", "timesheet", "payroll", "project team",
    "deployments", "tracker", "summary", "admin", "adjustment", "roster",
    "cost", "rate", "po", "purchase order", "log",
}

# Known billing table keywords (lowercase)
BILLING_TABLE_KEYWORDS: Set[str] = {
    "billing", "hours", "timesheet", "invoice", "project", "staff", "employee",
    "rate", "cost", "adjustment", "summary", "tracker", "roster",
}

# Known formula tokens that strongly indicate billing logic
BILLING_FORMULA_PATTERNS: List[str] = [
    r"SUM\s*\(",
    r"HOUR",
    r"RATE",
    r"COST",
    r"BILL",
    r"PAY",
    r"TOTAL.*HOUR",
    r"NET.*BILL",
]


@dataclass
class BillingProfileResult:
    is_billing_workbook: bool = False
    confidence: str = "low"   # low | medium | high
    matched_sheet_names: List[str] = field(default_factory=list)
    matched_table_names: List[str] = field(default_factory=list)
    formula_indicators: List[str] = field(default_factory=list)
    sheet_count: int = 0
    table_count: int = 0

    def to_dict(self) -> dict:
        return {
            "is_billing_workbook": self.is_billing_workbook,
            "confidence": self.confidence,
            "matched_sheet_names": self.matched_sheet_names,
            "matched_table_names": self.matched_table_names,
            "formula_indicators": self.formula_indicators,
            "sheet_count": self.sheet_count,
            "table_count": self.table_count,
        }


def _normalize(text: str) -> str:
    return text.lower().replace("_", " ").replace("-", " ")


def _sheet_names_from_workbook(z: zipfile.ZipFile) -> List[str]:
    """Return display sheet names from workbook.xml."""
    wb = read_text(z, "xl/workbook.xml")
    return [m.group(1) for m in re.finditer(r'<sheet\b[^>]*\bname="([^"]*)"', wb)]


def _table_names(z: zipfile.ZipFile) -> List[str]:
    """Return table display names from all xl/tables/table*.xml parts."""
    names: List[str] = []
    for part in table_parts(z):
        txt = read_text(z, part)
        for m in re.finditer(r'<table\b[^>]*\bdisplayName="([^"]*)"', txt):
            names.append(m.group(1))
        # Fallback: table/@name if displayName absent
        if not names:
            for m in re.finditer(r'<table\b[^>]*\bname="([^"]*)"', txt):
                names.append(m.group(1))
    return names


def _scan_formula_indicators(z: zipfile.ZipFile) -> List[str]:
    """Return up to 5 distinct formula snippets that match billing patterns."""
    hits: List[str] = []
    sheets = [n for n in z.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
    for part in sheets[:3]:  # sample first 3 sheets only for speed
        txt = read_text(z, part)
        for pat in BILLING_FORMULA_PATTERNS:
            for m in re.finditer(rf"<f\b[^>]*>([^<]{{0,120}})</f>", txt):
                snippet = m.group(1)
                if re.search(pat, snippet, re.IGNORECASE):
                    hits.append(snippet[:80])
                    if len(hits) >= 5:
                        return hits
    return hits


def profile_workbook(path: str) -> BillingProfileResult:
    """Inspect *path* and return a BillingProfileResult."""
    result = BillingProfileResult()
    try:
        with zipfile.ZipFile(path, "r") as z:
            sheet_names = _sheet_names_from_workbook(z)
            table_names = _table_names(z)
            result.sheet_count = len(sheet_names)
            result.table_count = len(table_names)

            for name in sheet_names:
                norm = _normalize(name)
                if any(kw in norm for kw in BILLING_SHEET_KEYWORDS):
                    result.matched_sheet_names.append(name)

            for name in table_names:
                norm = _normalize(name)
                if any(kw in norm for kw in BILLING_TABLE_KEYWORDS):
                    result.matched_table_names.append(name)

            result.formula_indicators = _scan_formula_indicators(z)
    except Exception:
        # ZIP malformed or unreadable → leave as low-confidence / false
        return result

    score = 0
    if result.matched_sheet_names:
        score += len(result.matched_sheet_names) * 2
    if result.matched_table_names:
        score += len(result.matched_table_names) * 2
    if result.formula_indicators:
        score += len(result.formula_indicators)

    if score >= 6:
        result.confidence = "high"
        result.is_billing_workbook = True
    elif score >= 3:
        result.confidence = "medium"
        result.is_billing_workbook = True
    elif score >= 1:
        result.confidence = "low"
        # Still considered billing-adjacent for safety
        result.is_billing_workbook = True

    return result
