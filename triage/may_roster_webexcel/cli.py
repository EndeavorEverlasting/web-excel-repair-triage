"""CLI for the May roster Web Excel CF preflight + repair-free QA engine.

Modes
-----
inspect : diff candidate vs reference, run package preflight, detect Sunday
          bleed, classify overnight punches, and name unassigned hours.
patch   : produce a repair-free workbook ONLY if every gate passes. If safe
          patching cannot be proven, fail with a report and write no workbook.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.cf_engine import CFDictionary, apply_cf_dictionary, extract_cf_dictionary
from triage.may_roster_webexcel.cf_inspector import (
    diff_cf,
    sunday_bleed_report,
)
from triage.may_roster_webexcel.package_checks import run_package_preflight
from triage.may_roster_webexcel.roster_rules import (
    STATUS_MALFORMED,
    STATUS_OVERNIGHT,
    classify_punch,
)
from triage.may_roster_webexcel.summary_builder import (
    build_sharesafe_summary,
    read_live_records,
)

DEFAULT_SHEET = "Live - May 2026"
DEFAULT_YEAR = 2026
DEFAULT_MONTH = 5


def _resolve(p: Optional[str], base: Path) -> Optional[Path]:
    if not p:
        return None
    pp = Path(p)
    return pp if pp.is_absolute() else (base / pp).resolve()


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


# ───────────────────────── inspect ─────────────────────────


def _overnight_report(records) -> Dict[str, Any]:
    overnight: List[dict] = []
    malformed: List[dict] = []
    for rec in records:
        cls = classify_punch(rec.clock_in_raw, rec.clock_out_raw, is_weekend=rec.day_type == "weekend")
        entry = {
            "tech": rec.tech,
            "date": rec.date.isoformat() if rec.date else "",
            "clock_in": cls.clock_in,
            "clock_out": cls.clock_out,
            "gross_hours": cls.gross_hours,
            "reason": cls.reason,
        }
        if cls.status == STATUS_OVERNIGHT:
            overnight.append(entry)
        elif cls.status == STATUS_MALFORMED:
            malformed.append(entry)
    return {
        "overnight_count": len(overnight),
        "malformed_count": len(malformed),
        "overnight": overnight,
        "malformed": malformed,
    }


def _write_unassigned_csv(path: Path, records) -> int:
    from triage.may_roster_webexcel.roster_rules import build_unassigned_rows

    rows = build_unassigned_rows([r.as_dict() for r in records])
    cols = ["Tech", "Date", "Actual Paid Hours", "Current Project / Assignment", "Status"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r.to_dict())
    return len(rows)


def run_inspect(
    candidate: str,
    reference: Optional[str],
    out_dir: str,
    sheet: str = DEFAULT_SHEET,
    year: int = DEFAULT_YEAR,
    month: int = DEFAULT_MONTH,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    cand_path = _resolve(candidate, root)
    if cand_path is None or not cand_path.exists():
        raise FileNotFoundError(f"candidate not found: {cand_path}")
    ref_path = _resolve(reference, root) if reference else None
    out = _resolve(out_dir, root) or (root / "Outputs")
    out.mkdir(parents=True, exist_ok=True)

    # CF diff (only when a reference is supplied).
    if ref_path and ref_path.exists():
        diff = diff_cf(str(cand_path), str(ref_path), sheet)
        diff_dict = diff.to_dict()
    else:
        diff_dict = {"sheet": sheet, "note": "no reference supplied; diff skipped"}
    _write_json(out / "cf_diff_report.json", diff_dict)

    preflight = run_package_preflight(str(cand_path))
    _write_json(out / "package_preflight.json", preflight.to_dict())

    bleed = sunday_bleed_report(str(cand_path), sheet, year, month)
    _write_json(out / "sunday_bleed_report.json", bleed.to_dict())

    records = read_live_records(str(cand_path), sheet, year)
    overnight = _overnight_report(records)
    _write_json(out / "overnight_punch_report.json", overnight)

    unassigned_count = _write_unassigned_csv(out / "unassigned_hours_report.csv", records)

    summary = {
        "mode": "inspect",
        "candidate": str(cand_path),
        "reference": str(ref_path) if ref_path else None,
        "sheet": sheet,
        "cf_diff_identical": diff_dict.get("identical"),
        "package_preflight_passed": preflight.passed,
        "package_preflight_message": preflight.message,
        "sunday_bleed_clean": bleed.clean,
        "sunday_bleed_findings": len(bleed.findings),
        "overnight_count": overnight["overnight_count"],
        "malformed_count": overnight["malformed_count"],
        "unassigned_count": unassigned_count,
        "record_count": len(records),
    }
    _write_carryover(out / "carryover.md", summary, bleed)
    _write_json(out / "inspect_manifest.json", summary)
    return summary


def _write_carryover(path: Path, summary: Dict[str, Any], bleed) -> None:
    lines = [
        "# May Roster Web Excel CF Preflight - Carryover",
        "",
        "A workbook that opens only because Excel repaired it is evidence, not success.",
        "",
        "## Inspect summary",
        f"- Candidate: {summary['candidate']}",
        f"- Reference: {summary.get('reference')}",
        f"- Package preflight: {'PASS' if summary['package_preflight_passed'] else 'FAIL'} "
        f"({summary['package_preflight_message']})",
        f"- Sunday bleed: {'CLEAN' if summary['sunday_bleed_clean'] else str(summary['sunday_bleed_findings']) + ' finding(s)'}",
        f"- Overnight punches: {summary['overnight_count']} (not malformed)",
        f"- Malformed punches: {summary['malformed_count']}",
        f"- Unassigned rows (named): {summary['unassigned_count']}",
        "",
        "## Sunday/Monday boundaries checked",
    ]
    for b in bleed.boundaries:
        lines.append(f"- {b['sunday']} (cols {b['sunday_columns']}) -> "
                     f"{b['monday'] or 'no in-sheet Monday'} (cols {b['monday_columns']})")
    if bleed.findings:
        lines += ["", "## Bleed findings"]
        for f in bleed.findings:
            lines.append(f"- [{f.kind}] sqref={f.sqref} :: {f.detail}")
    lines += [
        "",
        "## Manual confirmation still required",
        "- Operator must open the workbook in Excel for Web and confirm no repair prompt.",
        "- Confirm blank Sunday stays neutral when the following Monday is populated.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


# ───────────────────────── patch (gated) ─────────────────────────


def run_patch(
    base: str,
    reference: str,
    out_dir: str,
    as_of: str,
    sheet: str = DEFAULT_SHEET,
    year: int = DEFAULT_YEAR,
    month: int = DEFAULT_MONTH,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    base_path = _resolve(base, root)
    ref_path = _resolve(reference, root)
    if base_path is None or not base_path.exists():
        raise FileNotFoundError(f"base not found: {base_path}")
    if ref_path is None or not ref_path.exists():
        raise FileNotFoundError(f"reference not found: {ref_path}")
    out = _resolve(out_dir, root) or (root / "Outputs")
    out.mkdir(parents=True, exist_ok=True)

    # Gate 1: the reference's Sunday rules must be clean, else it cannot be a
    # trusted source of corrected CF.
    ref_bleed = sunday_bleed_report(str(ref_path), sheet, year, month)

    # Build a candidate patch: replace the Live-sheet CF with the reference's.
    ref_cfd = extract_cf_dictionary(str(ref_path))
    ref_cfd.blocks = [b for b in ref_cfd.blocks
                      if (b.sheet_name or "").strip().lower() == sheet.strip().lower()]

    patched_bytes = apply_cf_dictionary(base_path.read_bytes(), ref_cfd, mode="replace")

    # Verify on a temp file before committing to a real output.
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tf:
        tf.write(patched_bytes)
        tmp_path = tf.name
    trial_preflight = run_package_preflight(tmp_path)
    trial_bleed = sunday_bleed_report(tmp_path, sheet, year, month)
    Path(tmp_path).unlink(missing_ok=True)

    safe = ref_bleed.clean and trial_preflight.passed and trial_bleed.clean

    manifest: Dict[str, Any] = {
        "mode": "patch",
        "as_of": as_of,
        "base": str(base_path),
        "reference": str(ref_path),
        "sheet": sheet,
        "reference_sunday_bleed_clean": ref_bleed.clean,
        "patched_package_preflight_passed": trial_preflight.passed,
        "patched_package_preflight_message": trial_preflight.message,
        "patched_sunday_bleed_clean": trial_bleed.clean,
        "safe_to_ship": safe,
    }

    if not safe:
        manifest["result"] = "REFUSED"
        manifest["reason"] = (
            "Safe patching could not be proven; no workbook written. "
            "See gate details below."
        )
        manifest["trial_preflight"] = trial_preflight.to_dict()
        manifest["trial_sunday_bleed"] = trial_bleed.to_dict()
        manifest["reference_sunday_bleed"] = ref_bleed.to_dict()
        _write_json(out / "repairfree_manifest.json", manifest)
        _write_json(out / "webexcel_preflight.json", trial_preflight.to_dict())
        (out / "carryover.md").write_text(
            "# Patch REFUSED\n\n"
            "Safe patching could not be proven. No repair-free workbook was written.\n"
            f"- reference Sunday bleed clean: {ref_bleed.clean}\n"
            f"- patched package preflight passed: {trial_preflight.passed}\n"
            f"- patched Sunday bleed clean: {trial_bleed.clean}\n",
            encoding="utf-8",
        )
        return manifest

    # Safe: write the repair-free workbook.
    out_name = (
        f"CANDIDATE_Active_Roster_Log_2026-05-19_May_Billing_"
        f"EXPECTED_HOURS_INTERNAL_vNEXT4_REPAIRFREE_XMLSAFE.xlsx"
    )
    out_path = out / out_name
    out_path.write_bytes(patched_bytes)

    final_preflight = run_package_preflight(str(out_path))
    manifest["result"] = "WRITTEN"
    manifest["workbook"] = str(out_path)
    manifest["final_preflight_passed"] = final_preflight.passed
    _write_json(out / "repairfree_manifest.json", manifest)
    _write_json(out / "webexcel_preflight.json", final_preflight.to_dict())
    (out / "carryover.md").write_text(
        f"# Repair-free patch written\n\n{final_preflight.message}\n\n"
        f"- workbook: {out_path}\n"
        "- Operator must still open in Excel for Web to confirm no repair prompt.\n",
        encoding="utf-8",
    )
    return manifest


# ───────────────────────── argparse ─────────────────────────


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="triage.may_roster_webexcel.cli")
    sub = ap.add_subparsers(dest="mode", required=True)

    ins = sub.add_parser("inspect", help="diagnose CF bleed / package / punches")
    ins.add_argument("--candidate", required=True)
    ins.add_argument("--reference")
    ins.add_argument("--out-dir", default="Outputs/may_roster_webexcel_2026_06_02")
    ins.add_argument("--sheet", default=DEFAULT_SHEET)
    ins.add_argument("--year", type=int, default=DEFAULT_YEAR)
    ins.add_argument("--month", type=int, default=DEFAULT_MONTH)

    pat = sub.add_parser("patch", help="write a repair-free workbook only if safe")
    pat.add_argument("--base", required=True)
    pat.add_argument("--reference", required=True)
    pat.add_argument("--out-dir", default="Outputs/may_roster_webexcel_2026_06_02")
    pat.add_argument("--as-of", default="2026-06-02")
    pat.add_argument("--sheet", default=DEFAULT_SHEET)
    pat.add_argument("--year", type=int, default=DEFAULT_YEAR)
    pat.add_argument("--month", type=int, default=DEFAULT_MONTH)

    args = ap.parse_args(argv)
    if args.mode == "inspect":
        result = run_inspect(
            candidate=args.candidate, reference=args.reference, out_dir=args.out_dir,
            sheet=args.sheet, year=args.year, month=args.month,
        )
    else:
        result = run_patch(
            base=args.base, reference=args.reference, out_dir=args.out_dir,
            as_of=args.as_of, sheet=args.sheet, year=args.year, month=args.month,
        )
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
