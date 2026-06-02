"""CLI for the Admin Billing Summary (My Preferred Format) generator.

    python -m triage.admin_billing_summary.cli \
        --roster-log <roster.xlsx> --months 2026-04 2026-05 \
        --out-dir Outputs/admin_billing_summary_2026_06_02 \
        --prior "<April preferred-format copy>.xlsx" --websafe

Produces one workbook per month plus gitignored manifest / review-queue /
preflight sidecars, and a delta report when --prior is given (e.g. refreshed
April vs the prior submitted copy).
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.admin_billing_summary.aggregator import build_month_summary
from triage.admin_billing_summary.exporter import build_workbook
from triage.admin_billing_summary.models import MonthSummary, billing_bucket
from triage.nw_prj_neuron_track_hours.bonita_cli import preflight_bonita

DEFAULT_MONTHS = ["2026-04", "2026-05"]


def _resolve(p: Optional[str], base: Path) -> Optional[Path]:
    if not p:
        return None
    pp = Path(p)
    return pp if pp.is_absolute() else (base / pp).resolve()


def _workbook_name(month_key: str) -> str:
    y, m = month_key.split("-")
    from calendar import month_name
    return f"{month_name[int(m)]}_{y}_Admin_Billing_Summary_MyPreferredFormat.xlsx"


def _read_prior_project_net(prior_path: Path) -> Dict[str, float]:
    """Extract {project: net hours} from a prior preferred-format workbook."""
    import openpyxl
    out: Dict[str, float] = {}
    try:
        wb = openpyxl.load_workbook(str(prior_path), data_only=True, read_only=True)
    except Exception:
        return out
    try:
        if "Project Summary" not in wb.sheetnames:
            return out
        ws = wb["Project Summary"]
        rows = list(ws.iter_rows(values_only=True))
        hdr_idx = None
        for i, row in enumerate(rows):
            if row and str(row[0]).strip().lower() == "project":
                hdr_idx = i
                break
        if hdr_idx is None:
            return out
        header = [str(c).strip() if c is not None else "" for c in rows[hdr_idx]]
        try:
            net_col = header.index("Net Hours")
        except ValueError:
            net_col = len(header) - 1
        for row in rows[hdr_idx + 1:]:
            if not row or row[0] is None:
                continue
            proj = str(row[0]).strip()
            val = row[net_col] if net_col < len(row) else None
            if isinstance(val, (int, float)):
                out[proj] = round(float(val), 2)
    finally:
        wb.close()
    return out


def _delta(summary: MonthSummary, prior_path: Path) -> Dict[str, Any]:
    prior = _read_prior_project_net(prior_path)
    current = {r.project: round(r.net_hours, 2) for r in summary.project_rows}
    keys = sorted(set(prior) | set(current))
    rows = []
    for k in keys:
        pv = prior.get(k)
        cv = current.get(k)
        delta = round((cv or 0.0) - (pv or 0.0), 2)
        rows.append({"Project": k, "Prior Net": pv, "Current Net": cv, "Delta": delta})
    return {
        "prior_file": str(prior_path),
        "prior_total_net": round(sum(prior.values()), 2),
        "current_total_net": summary.total_net,
        "total_net_delta": round(summary.total_net - sum(prior.values()), 2),
        "by_project": rows,
    }


def _write_review_csv(path: Path, summary: MonthSummary) -> None:
    cols = ["Category", "Date", "Day", "Tech", "Project", "Project Source",
            "Clock In", "Clock Out", "Gross Span", "Net Hours", "Note"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in summary.records:
            cat = None
            if r.long_shift:
                cat = "long_shift"
            elif r.project_source == "override":
                cat = "override_applied"
            elif r.project == "Unassigned / Review":
                cat = "unassigned"
            if not cat:
                continue
            row = {
                "Category": cat, "Date": r.date.isoformat(), "Day": r.day, "Tech": r.tech,
                "Project": r.project, "Project Source": r.project_source,
                "Clock In": r.clock_in, "Clock Out": r.clock_out,
                "Gross Span": round(r.gross_span, 2), "Net Hours": round(r.net_hours, 2),
                "Note": r.note,
            }
            for k, v in list(row.items()):
                if isinstance(v, str) and v[:1] in ("=", "+", "-", "@"):
                    row[k] = "'" + v
            w.writerow(row)
        for m in summary.malformed:
            w.writerow({"Category": "malformed", "Note": m})


def run(roster_log: str, out_dir: str, months: Optional[List[str]] = None,
        prior: Optional[str] = None, websafe: bool = True,
        repo_root: Optional[Path] = None) -> Dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parent.parent.parent
    months = months or DEFAULT_MONTHS
    roster_path = _resolve(roster_log, root)
    if roster_path is None or not roster_path.exists():
        raise FileNotFoundError(f"roster-log not found: {roster_path}")
    out = _resolve(out_dir, root) or (root / "Outputs")
    out.mkdir(parents=True, exist_ok=True)
    prior_path = _resolve(prior, root)

    months_out: Dict[str, Any] = {}
    for mk in months:
        summary = build_month_summary(str(roster_path), mk)
        xlsx_path = out / _workbook_name(mk)
        build_workbook(summary, str(xlsx_path), roster_name=roster_path.name)

        review_path = out / f"{xlsx_path.stem}_review_queue.csv"
        _write_review_csv(review_path, summary)

        preflight = preflight_bonita(str(xlsx_path)) if websafe else {}
        preflight_path = out / f"{xlsx_path.stem}_preflight.json"
        preflight_path.write_text(json.dumps(preflight, indent=2, default=str), encoding="utf-8")

        delta = None
        # Apply prior delta only to the matching month of the prior file (April).
        if prior_path and prior_path.exists() and mk.endswith("-04"):
            delta = _delta(summary, prior_path)
            (out / f"{xlsx_path.stem}_delta.json").write_text(
                json.dumps(delta, indent=2, default=str), encoding="utf-8")

        months_out[mk] = {
            "month_name": summary.month_name,
            "workbook": str(xlsx_path),
            "review_queue_csv": str(review_path),
            "preflight_json": str(preflight_path),
            "row_count": len(summary.records),
            "total_net": summary.total_net,
            "total_gross": summary.total_gross,
            "neuron_net": summary.net_for_bucket("Neurons"),
            "projects_reflected": summary.projects_reflected,
            "techs_reflected": summary.techs_reflected,
            "project_net": {r.project: round(r.net_hours, 2) for r in summary.project_rows},
            "websafe_preflight_pass": bool(preflight.get("preflight_pass")) if websafe else None,
            "warnings": summary.warnings,
            "malformed_count": len(summary.malformed),
            "delta_vs_prior": delta,
        }

    manifest = {
        "engine": "triage.admin_billing_summary.cli",
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "roster_log": str(roster_path),
        "prior": str(prior_path) if prior_path else "",
        "months": months,
        "per_month": months_out,
    }
    manifest_path = out / "admin_billing_summary_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="triage.admin_billing_summary.cli")
    ap.add_argument("--roster-log", required=True)
    ap.add_argument("--months", nargs="+", default=DEFAULT_MONTHS)
    ap.add_argument("--out-dir", default="Outputs/admin_billing_summary_2026_06_02")
    ap.add_argument("--prior")
    ap.add_argument("--websafe", action="store_true", default=True)
    ap.add_argument("--no-websafe", action="store_false", dest="websafe")
    args = ap.parse_args(argv)
    manifest = run(
        roster_log=args.roster_log, out_dir=args.out_dir, months=args.months,
        prior=args.prior, websafe=args.websafe,
    )
    print(json.dumps(manifest, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
