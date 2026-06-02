"""CLI for the Bonita-format Neuron Track Hours generator.

Builds the clean two-tab (Apr 26 / May 26) submission workbook from a roster
log, plus gitignored manifest / review-queue / preflight sidecars.

    python -m triage.nw_prj_neuron_track_hours.bonita_cli \
        --roster-log <x> --admin-log <y> [--template <t>] \
        --months 2026-04 2026-05 \
        --out-dir Outputs/neuron_track_hours_2026_06_02 --websafe

The admin log is used for reconciliation context only (manifest / review),
never as workbook truth. The template is style-only and optional.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.nw_prj_neuron_track_hours.bonita_exporter import (
    build_bonita_workbook,
    tab_name_for_month_key,
)
from triage.nw_prj_neuron_track_hours.bonita_resolver import resolve_bonita_shifts
from triage.nw_prj_neuron_track_hours.reader import _month_label

DEFAULT_MONTHS = ["2026-04", "2026-05"]
WORKBOOK_NAME = "Bonita_Neuron_Track_Hours_April_May_2026.xlsx"
MANIFEST_NAME = "Neuron_Track_Hours_April_May_2026_manifest.json"
REVIEW_NAME = "Neuron_Track_Hours_April_May_2026_review_queue.csv"
PREFLIGHT_NAME = "Neuron_Track_Hours_April_May_2026_preflight.json"

# Reference totals for the full-month source (sanity comparison only).
REFERENCE_TOTALS = {"april": 1064.19, "may": 819.58}

_STOP_SHIP_TOKENS = ["inlineStr", "ns0:", "xmlns:ns0"]


def _resolve(p: Optional[str], base: Path) -> Optional[Path]:
    if not p:
        return None
    pp = Path(p)
    return pp if pp.is_absolute() else (base / pp).resolve()


def preflight_bonita(path: str) -> Dict[str, Any]:
    """Focused Web Excel preflight for the clean Bonita workbook.

    Passes when the package is a valid zip with no inlineStr / ns0 namespace
    pollution, no calcChain, and no external links. This workbook is values-only
    and intentionally minimal, so it does not require the richer dashboard
    features (filters/CF dictionary) that the main engine's preflight enforces.
    """
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
        "tabs": [],
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
            for tok in _STOP_SHIP_TOKENS:
                if tok in all_text:
                    res["token_failures"].append(tok)
            res["tabs"] = re.findall(r'<sheet[^>]*name="([^"]+)"', wb_xml)
            # sharedStrings invariant: declared count must equal the total
            # number of t="s" references across worksheets. A mismatch is the
            # exact corruption that makes Excel for Web "repair" the workbook.
            if "xl/sharedStrings.xml" in names:
                ss = z.read("xl/sharedStrings.xml").decode("utf-8", errors="ignore")
                m = re.search(r'\bcount="(\d+)"', ss)
                declared = int(m.group(1)) if m else -1
                refs = 0
                for n in names:
                    if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"):
                        refs += z.read(n).decode("utf-8", errors="ignore").count('t="s"')
                res["sharedstrings_declared_count"] = declared
                res["sharedstrings_actual_refs"] = refs
                res["sharedstrings_count_ok"] = (declared == refs)
    except zipfile.BadZipFile:
        res["error"] = "bad_zip"
        return res

    res["preflight_pass"] = (
        bool(res["zip_valid"])
        and not res["token_failures"]
        and not res["has_calc_chain"]
        and not res["has_external_links"]
        and bool(res["sharedstrings_count_ok"])
    )
    return res


def _write_review_queue_csv(path: Path, resolution) -> None:
    cols = ["Category", "Month", "Date", "Day", "Tech", "Start Time", "End Time",
            "Total Hours", "Project", "Note", "Source Cell", "Detail"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for item in resolution.review:
            row = item.to_dict()
            for k, v in list(row.items()):
                if isinstance(v, str) and v[:1] in ("=", "+", "-", "@"):
                    row[k] = "'" + v
            w.writerow(row)


def run(
    roster_log: str,
    out_dir: str,
    months: Optional[List[str]] = None,
    admin_log: Optional[str] = None,
    template: Optional[str] = None,
    websafe: bool = True,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parent.parent.parent
    months = months or DEFAULT_MONTHS
    roster_path = _resolve(roster_log, root)
    if roster_path is None or not roster_path.exists():
        raise FileNotFoundError(f"roster-log not found: {roster_path}")
    out = _resolve(out_dir, root) or (root / "Outputs")
    out.mkdir(parents=True, exist_ok=True)

    resolution = resolve_bonita_shifts(str(roster_path), months)

    xlsx_path = out / WORKBOOK_NAME
    _, tabs = build_bonita_workbook(resolution, months, str(xlsx_path))

    review_path = out / REVIEW_NAME
    _write_review_queue_csv(review_path, resolution)

    preflight = preflight_bonita(str(xlsx_path)) if websafe else {}
    preflight_path = out / PREFLIGHT_NAME
    preflight_path.write_text(json.dumps(preflight, indent=2, default=str), encoding="utf-8")

    per_month: Dict[str, Dict[str, Any]] = {}
    for mk in months:
        _, _, mon = _month_label(mk)
        from calendar import month_name
        short = month_name[mon]
        shifts = resolution.shifts_for_month(short)
        per_month[mk] = {
            "tab": tab_name_for_month_key(mk),
            "month_name": short,
            "row_count": len(shifts),
            "total_hours": resolution.month_total(short),
            "reference_total": REFERENCE_TOTALS.get(short.lower()),
        }

    manifest = {
        "engine": "triage.nw_prj_neuron_track_hours.bonita_cli",
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "roster_log": str(roster_path),
        "admin_log": str(_resolve(admin_log, root)) if admin_log else "",
        "template": str(_resolve(template, root)) if template else "",
        "months": months,
        "sheets_used": ["Live - {Month}", "Worked Projects - {Month}", "Assignments - {Month}"],
        "tabs": [t for _, t in tabs],
        "per_month": per_month,
        "grand_total_hours": resolution.grand_total(),
        "shift_count": len(resolution.shifts),
        "review_item_count": len(resolution.review),
        "review_by_category": _count_categories(resolution),
        "websafe_preflight_pass": bool(preflight.get("preflight_pass")) if websafe else None,
        "warnings": resolution.warnings,
        "outputs": {
            "workbook": str(xlsx_path),
            "review_queue_csv": str(review_path),
            "preflight_json": str(preflight_path),
        },
    }
    manifest_path = out / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    manifest["outputs"]["manifest_json"] = str(manifest_path)
    return manifest


def _count_categories(resolution) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for item in resolution.review:
        out[item.category] = out.get(item.category, 0) + 1
    return out


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="triage.nw_prj_neuron_track_hours.bonita_cli")
    ap.add_argument("--roster-log", required=True)
    ap.add_argument("--admin-log")
    ap.add_argument("--template")
    ap.add_argument("--months", nargs="+", default=DEFAULT_MONTHS)
    ap.add_argument("--out-dir", default="Outputs/neuron_track_hours_2026_06_02")
    ap.add_argument("--websafe", action="store_true", default=True)
    ap.add_argument("--no-websafe", action="store_false", dest="websafe")
    args = ap.parse_args(argv)

    manifest = run(
        roster_log=args.roster_log,
        out_dir=args.out_dir,
        months=args.months,
        admin_log=args.admin_log,
        template=args.template,
        websafe=args.websafe,
    )
    print(json.dumps(manifest, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
