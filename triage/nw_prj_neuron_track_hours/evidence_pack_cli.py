"""CLI for the roster-derived Neuron billing evidence pack.

Example:

    python -m triage.nw_prj_neuron_track_hours.evidence_pack_cli \
        --roster-log "Candidates/Active Roster Log.xlsx" \
        --months 2026-07 \
        --out-dir "Outputs/neuron_billing_evidence_pack/2026-07"

The roster log is always clock/hour truth. Repo month policies distribute only
heuristic assignments. ``--allocation-source`` is optional and may override only
the task label after exact shift reconciliation. Real operator workbooks remain
local and gitignored.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
from calendar import month_name
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from triage.month_validation import validate_month_key
from triage.one_marcus_recon.path_guard import assert_output_path_allowed
from triage.nw_prj_neuron_track_hours.bonita_resolver import resolve_bonita_shifts
from triage.nw_prj_neuron_track_hours.evidence_pack import (
    AllocationOverlayStats,
    apply_allocation_source,
    build_evidence_pack,
    preflight_evidence_pack,
)
from triage.nw_prj_neuron_track_hours.evidence_pack_finalize import (
    repair_visual_summary_charts,
    validate_allocation_source_exact,
)
from triage.nw_prj_neuron_track_hours.monthly_allocation import (
    apply_monthly_allocation_policies,
)

DEFAULT_OUT_DIR = "Outputs/neuron_billing_evidence_pack"


def _resolve(value: Optional[str], root: Path) -> Optional[Path]:
    if not value:
        return None
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _normalized_months(months: Sequence[str]) -> List[str]:
    result: List[str] = []
    seen: set[str] = set()
    for value in months:
        year, mon = validate_month_key(value)
        key = f"{year:04d}-{mon:02d}"
        if key not in seen:
            result.append(key)
            seen.add(key)
    if not result:
        raise ValueError("at least one --months value is required")
    return result


def _artifact_name(months: Sequence[str]) -> str:
    labels: List[str] = []
    years: List[int] = []
    for key in months:
        year, mon = (int(part) for part in key.split("-"))
        labels.append(month_name[mon])
        years.append(year)
    if len(set(years)) == 1:
        period = "_".join(labels + [str(years[0])])
    else:
        period = "_".join(
            f"{month_name[int(key.split('-')[1])]}_{key.split('-')[0]}" for key in months
        )
    period = re.sub(r"[^A-Za-z0-9_]+", "_", period).strip("_")
    return f"Neuron_Track_Hours_{period}_Evidence_Pack.xlsx"


def _assert_source_safe(source: Path, output: Path, label: str) -> None:
    try:
        same = source.resolve() == output.resolve()
    except FileNotFoundError:
        same = False
    if same:
        raise ValueError(f"{label} may not be overwritten: {source}")


def run(
    roster_log: str,
    out_dir: str = DEFAULT_OUT_DIR,
    months: Optional[Sequence[str]] = None,
    *,
    allocation_source: Optional[str] = None,
    allocation_policy: Optional[str] = None,
    apply_monthly_policy: bool = True,
    strict_allocation_source: bool = True,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Generate the workbook, manifest, and focused preflight report."""
    root = (repo_root or Path(__file__).resolve().parents[2]).resolve()
    month_keys = _normalized_months(list(months or []))
    roster_path = _resolve(roster_log, root)
    if roster_path is None or not roster_path.is_file():
        raise FileNotFoundError(f"roster-log not found: {roster_path}")
    allocation_path = _resolve(allocation_source, root)
    policy_path = _resolve(allocation_policy, root)
    if allocation_source and (allocation_path is None or not allocation_path.is_file()):
        raise FileNotFoundError(f"allocation-source not found: {allocation_path}")
    if allocation_policy and (policy_path is None or not policy_path.is_file()):
        raise FileNotFoundError(f"allocation-policy not found: {policy_path}")
    output_dir = _resolve(out_dir, root) or (root / DEFAULT_OUT_DIR)
    workbook_path = output_dir / _artifact_name(month_keys)
    assert_output_path_allowed(str(roster_path), str(workbook_path))
    _assert_source_safe(roster_path, workbook_path, "roster log")
    if allocation_path:
        _assert_source_safe(allocation_path, workbook_path, "allocation source")
    output_dir.mkdir(parents=True, exist_ok=True)

    resolution = resolve_bonita_shifts(str(roster_path), month_keys)
    overlay = AllocationOverlayStats(strict=strict_allocation_source)
    if allocation_path:
        if strict_allocation_source:
            validate_allocation_source_exact(resolution, str(allocation_path), month_keys)
        resolution, overlay = apply_allocation_source(
            resolution,
            str(allocation_path),
            month_keys,
            strict=strict_allocation_source,
        )
    policy_stats = []
    if apply_monthly_policy:
        resolution, policy_stats = apply_monthly_allocation_policies(
            resolution,
            month_keys,
            policy_path=str(policy_path) if policy_path else None,
        )

    _, tabs = build_evidence_pack(resolution, month_keys, str(workbook_path))
    repair_visual_summary_charts(str(workbook_path))
    expected_total = resolution.grand_total()
    preflight = preflight_evidence_pack(
        str(workbook_path),
        month_keys,
        expected_shift_count=len(resolution.shifts),
        expected_total_hours=expected_total,
    )
    preflight_path = output_dir / f"{workbook_path.stem}_preflight.json"
    preflight_path.write_text(
        json.dumps(preflight, indent=2, default=str), encoding="utf-8"
    )

    per_month: Dict[str, Dict[str, Any]] = {}
    for key in month_keys:
        year, mon = (int(part) for part in key.split("-"))
        shifts = [
            shift
            for shift in resolution.shifts
            if shift.date.year == year and shift.date.month == mon
        ]
        per_month[key] = {
            "sheet": f"{month_name[mon]} {year}",
            "shift_count": len(shifts),
            "total_hours": round(sum(s.total_hours for s in shifts), 2),
        }

    manifest: Dict[str, Any] = {
        "engine": "triage.nw_prj_neuron_track_hours.evidence_pack_cli",
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "roster_log": str(roster_path),
        "allocation_source": str(allocation_path) if allocation_path else "",
        "allocation_policy": str(policy_path) if policy_path else "repo default",
        "source_hierarchy": [
            "roster log clock/date/hour truth",
            "local allocation workbook task label override when supplied",
            "repo or local monthly policy for remaining heuristic task allocation",
            "deterministic audit-safe narrative with no invented specifics",
        ],
        "months": month_keys,
        "tabs": tabs,
        "per_month": per_month,
        "shift_count": len(resolution.shifts),
        "grand_total_hours": expected_total,
        "daily_narrative_rows": preflight.get("daily_narrative_rows"),
        "event_rows": preflight.get("event_rows"),
        "monthly_allocation_policies": [item.to_dict() for item in policy_stats],
        "allocation_overlay": overlay.to_dict(),
        "review_item_count": len(resolution.review),
        "warnings": resolution.warnings,
        "outputs": {
            "workbook": str(workbook_path),
            "preflight_json": str(preflight_path),
        },
        "preflight_pass": bool(preflight.get("preflight_pass")),
        "preflight": preflight,
        "proof_level": "fixture/package-level; Excel for Web manual acceptance not proven",
    }
    manifest_path = output_dir / f"{workbook_path.stem}_manifest.json"
    manifest["outputs"]["manifest_json"] = str(manifest_path)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8"
    )
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="triage.nw_prj_neuron_track_hours.evidence_pack_cli"
    )
    parser.add_argument("--roster-log", required=True)
    parser.add_argument("--months", nargs="+", required=True)
    parser.add_argument("--allocation-source")
    parser.add_argument(
        "--allocation-policy",
        help="Optional local monthly allocation policy JSON",
    )
    parser.add_argument(
        "--no-monthly-policy",
        action="store_true",
        help="Disable repo/default month allocation policy and use classifier labels only.",
    )
    parser.add_argument(
        "--allow-unmatched-allocation",
        action="store_true",
        help="Keep roster-rule assignments for unmatched shifts instead of failing.",
    )
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)
    manifest = run(
        roster_log=args.roster_log,
        out_dir=args.out_dir,
        months=args.months,
        allocation_source=args.allocation_source,
        allocation_policy=args.allocation_policy,
        apply_monthly_policy=not args.no_monthly_policy,
        strict_allocation_source=not args.allow_unmatched_allocation,
    )
    print(json.dumps(manifest, indent=2, default=str))
    return 0 if manifest["preflight_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
