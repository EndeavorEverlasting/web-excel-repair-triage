"""Baseline fingerprint gate — delivery must not delete sheets from the source workbook."""
from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from triage.artifact_compare import compare_artifacts
from triage.artifact_fingerprint import fingerprint_file

from .config import PART_NUMBERS_SHEET

_DATED_PN_TAB = re.compile(r"^\d{1,2}-\d{1,2}-\d{4} Part Numbers$")


@dataclass
class BaselineGateResult:
    baseline_path: str
    candidate_path: str
    baseline_compare_pass: bool = False
    failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    baseline_raw_sha256: str = ""
    baseline_semantic_sha256: str = ""
    candidate_raw_sha256: str = ""
    candidate_semantic_sha256: str = ""
    sheets_deleted: List[str] = field(default_factory=list)
    sheet_deltas: List[Dict[str, Any]] = field(default_factory=list)
    compare_report: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


def run_baseline_gate(
    baseline_path: str,
    candidate_path: str,
    *,
    profile: str = "one_marcus_recon",
    require_sheet_preservation: bool = True,
) -> BaselineGateResult:
    """Compare candidate delivery against the source baseline; fail on sheet deletion."""
    res = BaselineGateResult(
        baseline_path=str(Path(baseline_path).resolve()),
        candidate_path=str(Path(candidate_path).resolve()),
    )
    ref_fp = fingerprint_file(baseline_path)
    cand_fp = fingerprint_file(candidate_path)
    res.baseline_raw_sha256 = ref_fp.raw_sha256
    res.baseline_semantic_sha256 = ref_fp.semantic_sha256
    res.candidate_raw_sha256 = cand_fp.raw_sha256
    res.candidate_semantic_sha256 = cand_fp.semantic_sha256

    deleted = []
    for s in ref_fp.sheet_order:
        if s in cand_fp.sheet_order:
            continue
        if _DATED_PN_TAB.match(s) and PART_NUMBERS_SHEET in cand_fp.sheet_order:
            continue
        deleted.append(s)
    res.sheets_deleted = deleted
    if require_sheet_preservation and deleted:
        res.failures.append(f"sheets_deleted:{deleted}")

    if require_sheet_preservation:
        allowed_floor = len(ref_fp.sheet_order)
        for s in ref_fp.sheet_order:
            if _DATED_PN_TAB.match(s) and PART_NUMBERS_SHEET in cand_fp.sheet_order:
                allowed_floor -= 1
        if len(cand_fp.sheet_order) < allowed_floor:
            res.failures.append(
                f"sheet_count_decreased:{len(ref_fp.sheet_order)}->{len(cand_fp.sheet_order)}"
            )

    ref_sheets = ref_fp.sheets or {}
    cand_sheets = cand_fp.sheets or {}
    for name in ref_fp.sheet_order:
        rs = ref_sheets.get(name, {})
        cs = cand_sheets.get(name, {})
        if name not in cand_sheets:
            continue
        if rs.get("cell_value_hash") != cs.get("cell_value_hash"):
            res.sheet_deltas.append(
                {
                    "sheet": name,
                    "baseline_cells": rs.get("cell_count"),
                    "candidate_cells": cs.get("cell_count"),
                }
            )

    compare = compare_artifacts(baseline_path, candidate_path, profile)
    res.compare_report = compare
    for fail in compare.get("profile_failures") or []:
        if "semantic_sha256_mismatch" in str(fail):
            res.warnings.append(f"profile:{fail}")
        elif fail not in res.failures:
            res.failures.append(f"profile:{fail}")
    for warn in compare.get("profile_warnings") or []:
        if warn not in res.warnings:
            res.warnings.append(warn)

    # Tab rename + formula repoint is expected; sheet deletion is not.
    res.baseline_compare_pass = not res.failures
    return res
