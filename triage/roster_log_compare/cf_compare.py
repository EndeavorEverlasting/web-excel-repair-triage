"""Conditional formatting comparison (section E)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from triage.cf_engine import extract_cf_dictionary
from triage.roster_log_compare.load import load_workbook

_OVERRIDE_RANGE_RE = re.compile(r"\$?A\$?206:\$?C\$?505", re.I)


def _sqref_area(sqref: str) -> int:
    total = 0
    for part in str(sqref).split():
        part = part.strip()
        if ":" in part:
            a, b = part.split(":", 1)
            total += 2
        else:
            total += 1
    return total


def _cf_from_openpyxl(path: Path) -> Dict[str, Dict[str, Any]]:
    wb = load_workbook(path, data_only=False)
    out: Dict[str, Dict[str, Any]] = {}
    try:
        for name in wb.sheetnames:
            ws = wb[name]
            rules = []
            ranges: List[str] = []
            try:
                for cf in ws.conditional_formatting:
                    ranges.append(str(cf.sqref))
                    for rule in cf.rules:
                        formulas = []
                        if getattr(rule, "formula", None):
                            formulas.append(str(rule.formula))
                        if getattr(rule, "formula2", None):
                            formulas.append(str(rule.formula2))
                        rules.append({
                            "type": rule.type,
                            "formulas": formulas,
                        })
            except Exception:
                pass
            out[name] = {
                "blocks": len(ranges),
                "rules": len(rules),
                "sqrefs": sorted(ranges),
                "rule_details": rules,
            }
    finally:
        wb.close()
    return out


def _cf_from_engine(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    cfd = extract_cf_dictionary(str(path))
    per_sheet: Dict[str, List[Dict[str, Any]]] = {}
    for block in cfd.blocks:
        per_sheet.setdefault(block.sheet_name or block.sheet_part, []).append({
            "sqref": block.sqref,
            "formulas": [r.formula for r in block.rules if r.formula],
        })
    return per_sheet


def compare_conditional_formatting(left_path: Path, right_path: Path) -> Dict[str, Any]:
    op_l = _cf_from_openpyxl(left_path)
    op_r = _cf_from_openpyxl(right_path)
    eng_l = _cf_from_engine(left_path)
    eng_r = _cf_from_engine(right_path)
    sheets = sorted(set(op_l) | set(op_r) | set(eng_l) | set(eng_r))
    rows: List[Dict[str, Any]] = []
    fragmented: List[Dict[str, Any]] = []
    left_rules = right_rules = 0
    for sheet in sheets:
        sl = op_l.get(sheet, {})
        sr = op_r.get(sheet, {})
        left_rules += sl.get("rules", 0)
        right_rules += sr.get("rules", 0)
        sq_l = set(sl.get("sqrefs") or [])
        sq_r = set(sr.get("sqrefs") or [])
        added = sorted(sq_r - sq_l)
        removed = sorted(sq_l - sq_r)
        for sq in added:
            if _sqref_area(sq) <= 1:
                fragmented.append({"sheet": sheet, "sqref": sq, "kind": "single_cell_new_on_right"})
        rows.append({
            "sheet": sheet,
            "left_blocks": sl.get("blocks", 0),
            "right_blocks": sr.get("blocks", 0),
            "left_rules": sl.get("rules", 0),
            "right_rules": sr.get("rules", 0),
            "ranges_added_on_right": added,
            "ranges_removed_on_right": removed,
        })
    return {
        "per_sheet": rows,
        "left_total_rules": left_rules,
        "right_total_rules": right_rules,
        "right_has_more_cf_coverage": right_rules > left_rules,
        "fragmented_cf_introduced": fragmented,
    }
