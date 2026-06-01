"""
NW PRJ CLI — orchestrate local artifact generation pipeline.

Reads roster log + admin control workbook(s), classifies, exports billing
summaries, Neuron Track Hours, guided dashboard, runs WebExcel preflight,
and bundles outputs into an outer ZIP.

No network. Local artifacts only.
"""
from __future__ import annotations

import argparse
import csv
import json
import zipfile
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.nw_prj_admin_reader import AdminRecord, NwPrjAdminReader
from triage.nw_prj_billing_summary_exporter import export_billing_summary
from triage.nw_prj_classifier import ClassificationResult, NwPrjClassifier
from triage.nw_prj_neuron_track_hours_exporter import export_neuron_track_hours
from triage.nw_prj_roster_reader import NwPrjRosterReader, RosterRecord
from triage.webexcel_preflight import run_preflight


def _load_config(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _resolve(p: Optional[str], base: Path) -> Optional[Path]:
    if not p:
        return None
    pp = Path(p)
    if not pp.is_absolute():
        pp = (base / pp).resolve()
    return pp


def _select_records_for_month(
    results: List[ClassificationResult], month_prefix: str
) -> List[ClassificationResult]:
    """Filter results whose date starts with a YYYY-MM prefix."""
    return [r for r in results if (r.date or "").startswith(month_prefix)]


def _write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def _admin_records_csv(path: Path, records: List[AdminRecord]) -> None:
    rows = [
        {
            "tech": r.tech, "date": r.date, "hours": r.hours,
            "source_sheet": r.source_sheet, "source_row": r.source_row,
            "source_cell": r.source_cell,
        }
        for r in records
    ]
    _write_csv(path, rows, ["tech", "date", "hours", "source_sheet", "source_row", "source_cell"])


def _roster_records_csv(path: Path, records: List[RosterRecord]) -> None:
    rows = [
        {
            "tech": r.tech, "date": r.date, "project": r.project,
            "worked_project": r.worked_project or "", "hours": r.hours,
            "punch_in": r.punch_in, "punch_out": r.punch_out, "notes": r.notes,
            "source_sheet": r.source_sheet, "source_row": r.source_row,
        }
        for r in records
    ]
    _write_csv(path, rows, [
        "tech", "date", "project", "worked_project", "hours",
        "punch_in", "punch_out", "notes", "source_sheet", "source_row",
    ])


def _reconciliation_csv(path: Path, results: List[ClassificationResult]) -> None:
    rows = [
        {
            "tech": r.tech, "date": r.date, "resolved_hours": r.resolved_hours,
            "status": r.status, "reason_code": r.reason_code,
            "action_needed": r.action_needed, "is_blocker": r.is_blocker,
            "notes": r.notes,
        }
        for r in results
    ]
    _write_csv(path, rows, [
        "tech", "date", "resolved_hours", "status", "reason_code",
        "action_needed", "is_blocker", "notes",
    ])


def _build_zip(zip_path: Path, files: List[Path]) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            if f.exists():
                zf.write(f, arcname=f.name)


def run(
    roster_log: str,
    admin_folder: Optional[str],
    out_dir: str,
    months: List[str],
    admin_april: Optional[str] = None,
    admin_may: Optional[str] = None,
    webexcel: bool = True,
    zip_output: bool = True,
    run_date: str = "2026-06-01",
    protected_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    # ── Read inputs ──
    roster_reader = NwPrjRosterReader(roster_log)
    roster_records = roster_reader.read_all_records()

    admin_records: List[AdminRecord] = []
    admin_paths: Dict[str, Optional[Path]] = {}
    if admin_april:
        admin_paths["2026-04"] = Path(admin_april)
    if admin_may:
        admin_paths["2026-05"] = Path(admin_may)
    if not admin_paths and admin_folder:
        folder = Path(admin_folder)
        for f in sorted(folder.glob("*.xlsx")):
            admin_records.extend(NwPrjAdminReader(str(f)).read_records())
    else:
        for month, p in admin_paths.items():
            if p and p.exists():
                admin_records.extend(NwPrjAdminReader(str(p)).read_records())

    # ── Classify ──
    classifier = NwPrjClassifier(protected_names=protected_names or ["Rich Perez", "Richard Perez"])
    results = classifier.classify(admin_records, roster_records)

    # ── Per-month split ──
    by_month: Dict[str, List[ClassificationResult]] = {}
    for m in months:
        by_month[m] = _select_records_for_month(results, m)

    # ── Reports (CSV) ──
    _admin_records_csv(out / "nw_prj_admin_project_team_control_records.csv", admin_records)
    _roster_records_csv(out / "nw_prj_roster_work_records_april_may.csv", roster_records)
    _reconciliation_csv(out / "nw_prj_reconciliation_queue.csv", results)

    # ── Exporters ──
    artifacts: List[Path] = []
    month_labels = {"2026-04": ("April", "NW_PRJ_April_2026_Billing_Summary_WEBSAFE.xlsx"),
                    "2026-05": ("May", "NW_PRJ_May_2026_Billing_Summary_WEBSAFE.xlsx")}

    for m in months:
        if m in month_labels:
            label, fname = month_labels[m]
            p = out / fname
            export_billing_summary(by_month[m], label + " 2026", str(p))
            artifacts.append(p)

    neuron_path = out / "Neuron_Track_Hours_April_May_2026_WEBSAFE.xlsx"
    export_neuron_track_hours(
        by_month.get("2026-04", []), by_month.get("2026-05", []), str(neuron_path)
    )
    artifacts.append(neuron_path)

    # ── Preflight ──
    preflight_reports: Dict[str, Any] = {}
    if webexcel:
        for a in artifacts:
            rpt = run_preflight(str(a))
            preflight_reports[a.name] = rpt.to_dict()
        (out / "nw_prj_workbook_preflight_report.json").write_text(
            json.dumps(preflight_reports, indent=2), encoding="utf-8"
        )

    # ── Manifest ──
    manifest = {
        "run_date": run_date,
        "out_dir": str(out),
        "months": months,
        "artifacts": [
            {
                "artifact_name": a.name,
                "path": str(a),
                "exists": a.exists(),
                "size_bytes": a.stat().st_size if a.exists() else 0,
                "webexcel_preflight_pass": preflight_reports.get(a.name, {}).get("webexcel_preflight_pass", False),
                "has_filters": preflight_reports.get(a.name, {}).get("has_filters", False),
                "has_frozen_header": preflight_reports.get(a.name, {}).get("has_frozen_header", False),
                "has_cf_dictionary": preflight_reports.get(a.name, {}).get("has_cf_dictionary", False),
                "has_conditional_formatting": preflight_reports.get(a.name, {}).get("has_conditional_formatting", False),
                "has_dropdowns_where_expected": preflight_reports.get(a.name, {}).get("has_dropdowns_where_expected", False),
            }
            for a in artifacts
        ],
        "counts": {
            "admin_records": len(admin_records),
            "roster_records": len(roster_records),
            "classification_results": len(results),
            "blockers": sum(1 for r in results if r.is_blocker),
        },
    }
    (out / "nw_prj_artifact_scan_report.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    # ── Outer ZIP ──
    if zip_output:
        zip_name = f"NW_PRJ_Billing_Outer_Pack_{run_date}_WEBEXCEL_READY.zip"
        zip_path = out / zip_name
        extras = [
            out / "nw_prj_admin_project_team_control_records.csv",
            out / "nw_prj_roster_work_records_april_may.csv",
            out / "nw_prj_reconciliation_queue.csv",
            out / "nw_prj_workbook_preflight_report.json",
            out / "nw_prj_artifact_scan_report.json",
        ]
        _build_zip(zip_path, artifacts + extras)
        manifest["outer_zip"] = str(zip_path)

    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="triage.nw_prj_cli")
    ap.add_argument("--config", help="JSON config file with all parameters")
    ap.add_argument("--roster-log")
    ap.add_argument("--admin-folder")
    ap.add_argument("--admin-april")
    ap.add_argument("--admin-may")
    ap.add_argument("--out-dir", default="Outputs/nw_prj")
    ap.add_argument("--months", nargs="+", default=["2026-04", "2026-05"])
    ap.add_argument("--webexcel", action="store_true", default=True)
    ap.add_argument("--no-webexcel", dest="webexcel", action="store_false")
    ap.add_argument("--zip", dest="zip_output", action="store_true", default=True)
    ap.add_argument("--no-zip", dest="zip_output", action="store_false")
    ap.add_argument("--run-date", default="2026-06-01")
    args = ap.parse_args(argv)

    params: Dict[str, Any] = {}
    if args.config:
        cfg_path = Path(args.config).resolve()
        cfg = _load_config(str(cfg_path))
        base = cfg_path.parent
        for k in ("roster_log", "admin_folder", "admin_april", "admin_may", "out_dir"):
            v = cfg.get(k)
            if v:
                rp = _resolve(v, base)
                params[k] = str(rp) if rp else None
        for k in ("months", "webexcel", "zip_output", "run_date", "protected_names"):
            if k in cfg:
                params[k] = cfg[k]

    # CLI flags override config
    for k in ("roster_log", "admin_folder", "admin_april", "admin_may", "out_dir", "run_date"):
        cli_val = getattr(args, k.replace("admin_april", "admin_april").replace("admin_may", "admin_may"), None)
        if cli_val and (k not in params or k == "out_dir" and params.get(k) is None):
            params[k] = cli_val
    if args.months:
        params.setdefault("months", args.months)
    params.setdefault("webexcel", args.webexcel)
    params.setdefault("zip_output", args.zip_output)
    params.setdefault("out_dir", args.out_dir)

    if not params.get("roster_log"):
        ap.error("--roster-log (or roster_log in config) is required")

    manifest = run(
        roster_log=params["roster_log"],
        admin_folder=params.get("admin_folder"),
        admin_april=params.get("admin_april"),
        admin_may=params.get("admin_may"),
        out_dir=params["out_dir"],
        months=params.get("months", ["2026-04", "2026-05"]),
        webexcel=params.get("webexcel", True),
        zip_output=params.get("zip_output", True),
        run_date=params.get("run_date", "2026-06-01"),
        protected_names=params.get("protected_names"),
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
