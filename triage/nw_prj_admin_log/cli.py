"""CLI — NW PRJ Admin Log Project Team generator (roster data, donor visuals)."""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.artifact_fingerprint import raw_sha256
from triage.nw_prj_admin_log.preflight import preflight_project_team
from triage.nw_prj_admin_log.project_team_exporter import delivery_filename, export_project_team_workbook
from triage.nw_prj_admin_log.reader import load_roster_records
from triage.nw_prj_admin_log.visual_compare import run_visual_compare
from triage.output_policy import (
    SourcePathWriteForbiddenError,
    allocate_run_dir,
    assert_out_dir_allowed,
    assert_output_path_allowed,
    ensure_run_subdirs,
    run_id_from_dir,
    source_manifest_fields,
)

DEFAULT_MONTHS = ["2026-04", "2026-05"]


def _resolve(path: Optional[str], base: Path) -> Optional[Path]:
    if not path:
        return None
    pp = Path(path)
    return pp if pp.is_absolute() else (base / pp).resolve()


def _assert_inputs_unchanged(before: Dict[str, str], after: Dict[str, str]) -> None:
    for label, sha in before.items():
        if after.get(label) != sha:
            raise RuntimeError(f"source immutability violated: {label} bytes changed after run")


def run(
    roster_log: str,
    visual_donor: str,
    out_dir: str,
    months: Optional[List[str]] = None,
    accepted_reference: Optional[str] = None,
    websafe: bool = True,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parent.parent.parent
    months = months or DEFAULT_MONTHS

    roster_path = _resolve(roster_log, root)
    donor_path = _resolve(visual_donor, root)
    ref_path = _resolve(accepted_reference, root)
    if roster_path is None or not roster_path.is_file():
        raise FileNotFoundError(f"roster-log not found: {roster_log}")
    if donor_path is None or not donor_path.is_file():
        raise FileNotFoundError(f"visual-donor not found: {visual_donor}")

    run_dir = assert_out_dir_allowed(_resolve(out_dir, root) or allocate_run_dir("nw_prj_admin_log", "project_team"))
    ensure_run_subdirs(run_dir)
    delivery_dir = run_dir / "delivery"
    sidecars_dir = run_dir / "sidecars"
    delivery_dir.mkdir(parents=True, exist_ok=True)
    sidecars_dir.mkdir(parents=True, exist_ok=True)

    delivery_path = delivery_dir / delivery_filename()
    assert_output_path_allowed(
        roster_path,
        donor_path,
        ref_path,
        output_path=delivery_path,
    )

    before_sha = {
        "roster_log": raw_sha256(roster_path),
        "visual_donor": raw_sha256(donor_path),
    }
    if ref_path and ref_path.is_file():
        before_sha["accepted_reference"] = raw_sha256(ref_path)

    records, warnings = load_roster_records(str(roster_path), months)
    export_project_team_workbook(
        roster_records=records,
        month_keys=months,
        visual_donor_path=donor_path,
        output_path=delivery_path,
    )

    after_sha = {
        "roster_log": raw_sha256(roster_path),
        "visual_donor": raw_sha256(donor_path),
    }
    if ref_path and ref_path.is_file():
        after_sha["accepted_reference"] = raw_sha256(ref_path)
    _assert_inputs_unchanged(before_sha, after_sha)

    preflight = preflight_project_team(str(delivery_path)) if websafe else {}
    preflight_path = sidecars_dir / "preflight.json"
    preflight_path.write_text(json.dumps(preflight, indent=2, default=str), encoding="utf-8")

    visual = run_visual_compare(
        delivery_path,
        reference_path=str(ref_path) if ref_path and ref_path.is_file() else None,
    )
    visual_path = sidecars_dir / "visual_compare.json"
    visual_path.write_text(json.dumps(visual, indent=2, default=str), encoding="utf-8")

    manifest: Dict[str, Any] = {
        "engine": "triage.nw_prj_admin_log.cli",
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "run_id": run_id_from_dir(run_dir),
        **source_manifest_fields(roster_path),
        "roster_log": str(roster_path),
        "visual_donor": str(donor_path),
        "accepted_reference": str(ref_path) if ref_path else "",
        "months": months,
        "record_count": len(records),
        "source_immutability": {
            "before": before_sha,
            "after": after_sha,
            "pass": before_sha == after_sha,
        },
        "websafe_preflight_pass": bool(preflight.get("preflight_pass")) if websafe else None,
        "visual_compare_pass": visual.get("visual_compare_pass"),
        "warnings": warnings,
        "outputs": {
            "delivery_workbook": str(delivery_path),
            "manifest": str(sidecars_dir / "manifest.json"),
            "preflight_json": str(preflight_path),
            "visual_compare_json": str(visual_path),
        },
    }
    manifest_path = sidecars_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")

    return {
        "manifest": manifest,
        "delivery_workbook": str(delivery_path),
        "preflight": preflight,
        "visual_compare": visual,
        "run_dir": str(run_dir),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate company-style NW PRJ Admin Log Project Team workbook from roster log.",
    )
    parser.add_argument("--roster-log", required=True, help="Active roster log (data authority)")
    parser.add_argument("--visual-donor", required=True, help="Prior admin workbook (style only)")
    parser.add_argument("--accepted-reference", default="", help="Optional golden reference for visual compare")
    parser.add_argument("--months", nargs="+", default=DEFAULT_MONTHS)
    parser.add_argument("--out-dir", default="", help="Run directory under Outputs/ (delivery/ + sidecars/)")
    parser.add_argument("--websafe", action="store_true", default=True)
    parser.add_argument("--no-websafe", action="store_false", dest="websafe")
    args = parser.parse_args(argv)

    try:
        result = run(
            roster_log=args.roster_log,
            visual_donor=args.visual_donor,
            out_dir=args.out_dir,
            months=args.months,
            accepted_reference=args.accepted_reference or None,
            websafe=args.websafe,
        )
    except SourcePathWriteForbiddenError as exc:
        print(f"source_path_write_forbidden: {exc}", file=sys.stderr)
        return 2
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    pf = result.get("preflight") or {}
    print(json.dumps({
        "delivery_workbook": result["delivery_workbook"],
        "preflight_pass": pf.get("preflight_pass"),
        "visual_compare_pass": result["visual_compare"].get("visual_compare_pass"),
        "run_dir": result["run_dir"],
    }, indent=2))
    return 0 if pf.get("preflight_pass", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
