"""CLI for Candidate Neuron Track Hours generation.

This command generates the polished Candidate workbook from the private roster log
without committing workbook bytes to the repo.

Example:

    python -m triage.nw_prj_neuron_track_hours.candidate_cli \
      --roster-log Candidates/INTERNAL_Active_Roster_Log.xlsx \
      --months 2026-04 2026-05 \
      --out-dir Outputs/candidate_neuron_track_hours_2026_06_04 \
      --websafe
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.nw_prj_neuron_track_hours.bonita_cli import preflight_bonita
from triage.nw_prj_neuron_track_hours.bonita_resolver import BonitaResolution, resolve_bonita_shifts
from triage.nw_prj_neuron_track_hours.candidate_exporter import build_candidate_workbook
from triage.nw_prj_neuron_track_hours.candidate_rules import build_candidate_resolution
from triage.nw_prj_neuron_track_hours.reader import _month_label

DEFAULT_MONTHS = ["2026-04", "2026-05"]
WORKBOOK_NAME = "Candidate_Neuron Track Hours_April-May_2026_Rezaul_ColorCoded.xlsx"
MANIFEST_NAME = "Candidate_Neuron Track Hours_April-May_2026_manifest.json"
REVIEW_NAME = "Candidate_Neuron Track Hours_April-May_2026_review_removed_rows.csv"
PREFLIGHT_NAME = "Candidate_Neuron Track Hours_April-May_2026_preflight.json"


def _resolve(p: Optional[str], base: Path) -> Optional[Path]:
    if not p:
        return None
    pp = Path(p)
    return pp if pp.is_absolute() else (base / pp).resolve()


def _safe_csv_value(value: object) -> object:
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@"):
        return "'" + value
    return value


def _write_removed_rows(path: Path, resolution: BonitaResolution) -> None:
    cols = ["Category", "Month", "Date", "Day", "Tech", "Start Time", "End Time", "Total Hours", "Project", "Note", "Source Cell", "Detail"]
    rows = [item.to_dict() for item in resolution.review if item.category == "removed_client_coordination"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in rows:
            w.writerow({k: _safe_csv_value(row.get(k, "")) for k in cols})


def _per_month(resolution: BonitaResolution, months: List[str]) -> Dict[str, Dict[str, Any]]:
    from calendar import month_name

    out: Dict[str, Dict[str, Any]] = {}
    for mk in months:
        _, _, mon = _month_label(mk)
        month = month_name[mon]
        shifts = resolution.shifts_for_month(month)
        out[mk] = {
            "month_name": month,
            "row_count": len(shifts),
            "total_hours": round(sum(round(s.total_hours, 2) for s in shifts), 2),
            "client_coordination_rows": sum(1 for s in shifts if s.assignment_type == "Client Coordination"),
        }
    return out


def run(
    roster_log: str,
    out_dir: str,
    months: Optional[List[str]] = None,
    websafe: bool = True,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parent.parent.parent
    months = months or list(DEFAULT_MONTHS)
    roster_path = _resolve(roster_log, root)
    if roster_path is None or not roster_path.exists():
        raise FileNotFoundError(f"roster-log not found: {roster_path}")

    out = _resolve(out_dir, root) or (root / "Outputs" / "candidate_neuron_track_hours")
    out.mkdir(parents=True, exist_ok=True)

    source_resolution = resolve_bonita_shifts(str(roster_path), months)
    candidate_resolution, stats = build_candidate_resolution(source_resolution)

    workbook_path = out / WORKBOOK_NAME
    _, tabs = build_candidate_workbook(candidate_resolution, months, str(workbook_path), stats=stats)

    removed_rows_path = out / REVIEW_NAME
    _write_removed_rows(removed_rows_path, candidate_resolution)

    preflight = preflight_bonita(str(workbook_path)) if websafe else {}
    preflight_path = out / PREFLIGHT_NAME
    preflight_path.write_text(json.dumps(preflight, indent=2, default=str), encoding="utf-8")

    manifest = {
        "engine": "triage.nw_prj_neuron_track_hours.candidate_cli",
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "roster_log": str(roster_path),
        "months": months,
        "tabs": [tab for _, tab in tabs] + ["Rules & Legend"],
        "candidate_rules": {
            "client_coordination_allowed": [
                "Richard Perez / Rich Perez",
                "Khadejah Harrison",
                "Alejandro Perales",
                "Geoff Gerber",
            ],
            "unauthorized_client_coordination": "removed_from_clean_time_sheets",
            "rezaul_roman": "split_april_2026_neuron_work_between_inventory_management_and_configurations",
        },
        "stats": stats,
        "per_month": _per_month(candidate_resolution, months),
        "source_shift_count": len(source_resolution.shifts),
        "candidate_shift_count": len(candidate_resolution.shifts),
        "websafe_preflight_pass": bool(preflight.get("preflight_pass")) if websafe else None,
        "preflight_data": preflight if websafe else {},
        "outputs": {
            "workbook": str(workbook_path),
            "removed_rows_csv": str(removed_rows_path),
            "preflight_json": str(preflight_path),
        },
    }
    manifest_path = out / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    manifest["outputs"]["manifest_json"] = str(manifest_path)
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="triage.nw_prj_neuron_track_hours.candidate_cli")
    ap.add_argument("--roster-log", required=True)
    ap.add_argument("--months", nargs="+", default=DEFAULT_MONTHS)
    ap.add_argument("--out-dir", default="Outputs/candidate_neuron_track_hours_2026_06_04")
    ap.add_argument("--websafe", action="store_true", default=True)
    ap.add_argument("--no-websafe", action="store_false", dest="websafe")
    args = ap.parse_args(argv)
    manifest = run(
        roster_log=args.roster_log,
        months=args.months,
        out_dir=args.out_dir,
        websafe=args.websafe,
    )
    print(json.dumps(manifest, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
