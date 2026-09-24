"""
triage/batch_runner.py
----------------------
Batch pipeline runner.

Auto-discovers Candidate/Repaired pairs, runs the full triage pipeline
on each, applies all auto-fixable patches, and writes patched .xlsx files
plus a summary JSON to Outputs/.

Usage (CLI):
    python -m triage.batch_runner

Usage (Python):
    from triage.batch_runner import run_batch
    summary = run_batch()
"""
from __future__ import annotations

import datetime
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.gate_checks import run_all as _gate_run_all
from triage.diff import diff_packages
from triage.patterns import detect_all
from triage.report import (
    recipe_from_gates,
    recipe_from_patterns,
    merge_recipes,
    PatchRecipe,
)
from triage.patcher import apply_recipe, PatchError, PatchWarning
from triage.path_policy import is_active_path

CANDIDATES_DIR = Path("Candidates")
REPAIRED_DIR   = Path("Repaired")
OUTPUTS_DIR    = Path("Outputs")


def _find_repaired(candidate: Path) -> Optional[Path]:
    """Locate the matching Repaired/ file for a Candidate by stem matching."""
    stem = candidate.stem  # e.g. CANDIDATE_DeploymentTracker_..._i076_...
    # Strategy 1: exact prefix "repaired_" + original name
    exact = REPAIRED_DIR / f"repaired_{candidate.name}"
    if exact.exists():
        return exact
    # Strategy 2: any repaired file whose name contains the candidate stem
    for r in REPAIRED_DIR.glob("*.xlsx"):
        if stem in r.name or r.stem.replace("repaired_", "") in candidate.name:
            return r
    return None


def _gate_verdict(gate_dict: dict) -> str:
    fg = gate_dict.get("failing_gates", {})
    if not fg:
        return "PASS"
    return "FAIL: " + ", ".join(f"{k}({v})" for k, v in fg.items())


def _fix_oob_dxfids(
    output_path: Path,
    repaired: Optional[Path],
    post_gate,
) -> bool:
    """
    If the post-gate shows cf_dxfId_out_of_range issues and we have a repaired
    file, replace the offending worksheet parts wholesale from the repaired file.
    Returns True if any fix was applied.
    """
    if repaired is None:
        return False
    oob_issues = [
        h for h in post_gate.styles_dxf
        if h.get("issue") == "cf_dxfId_out_of_range"
    ]
    if not oob_issues:
        return False

    # Collect unique parts that need fixing
    bad_parts = set(h["part"] for h in oob_issues)

    # Build a minimal set_part recipe
    fix_recipe: Dict[str, Any] = {"version": "1", "source_file": str(output_path), "patches": []}
    import zipfile as _zf
    with _zf.ZipFile(str(repaired), "r") as zr:
        for part in bad_parts:
            if part in zr.namelist():
                content = zr.read(part).decode("utf-8", errors="replace")
                fix_recipe["patches"].append({
                    "id": f"oob_{part.replace('/', '_')}",
                    "part": part,
                    "operation": "set_part",
                    "description": f"Replace {part} from repaired file to fix OOB dxfId.",
                    "content": content,
                })

    if not fix_recipe["patches"]:
        return False

    # Apply in-place (overwrite output_path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp_path = tmp.name
    try:
        apply_recipe(str(output_path), fix_recipe, tmp_path)
    except PatchWarning as pw:
        tmp_path = pw.output_path
    shutil.move(tmp_path, str(output_path))
    return True


def run_one(
    candidate: Path,
    repaired: Optional[Path] = None,
    outputs_dir: Path = OUTPUTS_DIR,
) -> Dict[str, Any]:
    """
    Run the full pipeline on one Candidate (+ optional Repaired) file.
    Returns a result dict with keys: name, gate_verdict, patched_path,
    patch_count, skipped, error.
    """
    result: Dict[str, Any] = {
        "name":         candidate.name,
        "repaired":     repaired.name if repaired else None,
        "gate_verdict": None,
        "patched_path": None,
        "patch_count":  0,
        "skipped":      [],
        "error":        None,
    }
    try:
        if is_active_path(outputs_dir):
            raise ValueError(
                "ENDEAVOR: Batch pipeline patch output — refused. "
                "Active/ is read-only (golden standards). "
                f"Choose Outputs/ or Deprecated/. outputs_dir={outputs_dir}"
            )
        # Phase 1: gate checks
        gate = _gate_run_all(str(candidate))
        gate_dict = gate.to_dict()
        result["gate_verdict"] = _gate_verdict(gate_dict)

        # Phase 2+3: diff & patterns (if repaired available)
        diff_report = None
        patterns    = []
        if repaired:
            diff_report = diff_packages(str(candidate), str(repaired))
            patterns    = detect_all(diff_report)

        # Phase 4: build recipe
        r_gates    = recipe_from_gates(gate)
        r_patterns = recipe_from_patterns(
            str(candidate), patterns, diff_report=diff_report
        )
        recipe = merge_recipes(r_gates, r_patterns)
        result["patch_count"] = len(recipe.patches)

        if not recipe.patches:
            result["patched_path"] = str(candidate)  # already clean
            return result

        # Phase 5: apply recipe
        outputs_dir.mkdir(parents=True, exist_ok=True)
        stem        = candidate.stem
        ts          = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = outputs_dir / f"{stem}_patched_{ts}.xlsx"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp_path = tmp.name

        try:
            apply_recipe(str(candidate), recipe.to_dict(), tmp_path)
        except PatchWarning as pw:
            result["skipped"] = list(pw.skipped)
            tmp_path = pw.output_path

        shutil.move(tmp_path, output_path)
        result["patched_path"] = str(output_path)

        # Phase 6: re-gate-check the patched output
        post_gate = _gate_run_all(str(output_path))
        result["post_gate_verdict"] = _gate_verdict(post_gate.to_dict())

        # Phase 7: auto-fix any remaining OOB dxfId issues using repaired file
        if "styles_dxf_integrity" in post_gate.failing_gates() and repaired:
            fixed = _fix_oob_dxfids(output_path, repaired, post_gate)
            if fixed:
                post_gate2 = _gate_run_all(str(output_path))
                result["post_gate_verdict"] = _gate_verdict(post_gate2.to_dict()) + " (after OOB fix)"

    except Exception as exc:
        result["error"] = str(exc)

    return result


def run_batch(
    candidates_dir: Path = CANDIDATES_DIR,
    repaired_dir:   Path = REPAIRED_DIR,
    outputs_dir:    Path = OUTPUTS_DIR,
) -> List[Dict[str, Any]]:
    """
    Run the full pipeline on every .xlsx in candidates_dir.
    Returns a list of per-file result dicts and writes a summary JSON.
    """
    candidates = sorted(candidates_dir.glob("*.xlsx"))
    results: List[Dict[str, Any]] = []

    if is_active_path(outputs_dir):
        raise ValueError(
            "ENDEAVOR: Batch pipeline summary output — refused. "
            "Active/ is read-only (golden standards). "
            f"Choose Outputs/ or Deprecated/. outputs_dir={outputs_dir}"
        )

    for c in candidates:
        repaired = _find_repaired(c)
        res = run_one(c, repaired, outputs_dir)
        results.append(res)

    # Write summary
    outputs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = outputs_dir / f"batch_summary_{ts}.json"
    summary_path.write_text(
        json.dumps({"run_at": ts, "results": results}, indent=2),
        encoding="utf-8",
    )
    return results


if __name__ == "__main__":
    results = run_batch()
    for r in results:
        print(f"\n{'='*60}")
        print(f"FILE:   {r['name']}")
        print(f"GATE:   {r['gate_verdict']}")
        print(f"PATCHES:{r['patch_count']}")
        if r.get("post_gate_verdict"):
            print(f"POST:   {r['post_gate_verdict']}")
        if r.get("patched_path"):
            print(f"OUTPUT: {r['patched_path']}")
        if r.get("skipped"):
            print(f"SKIP:   {r['skipped']}")
        if r.get("error"):
            print(f"ERROR:  {r['error']}")
    print("\nDone.")

