"""CLI orchestrator for Cybernet target sprint automation."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.cybernet_targets.compare import carry_forward_manual_status
from triage.cybernet_targets.config import load_scope, targets_schema
from triage.cybernet_targets.enrich import enrich_from_deployment_tracker
from triage.cybernet_targets.exporter import (
    export_websafe_target_dashboard,
    write_reconciliation_csv,
    write_shortage_csv,
    write_sidecar_json,
)
from triage.cybernet_targets.extractor import (
    extract_wave3_targets,
    read_all_wave_workbook,
    read_sprint_dashboard,
)
from triage.cybernet_targets.models import rows_to_dicts
from triage.cybernet_targets.resolver import resolve_sprint_targets
from triage.nw_prj_config import is_repair_filename
from triage.webexcel_preflight import run_preflight
from triage.sidecar_html.adapters import cybernet_sections
from triage.output_policy import (
    allocate_run_dir,
    assert_out_dir_allowed,
    run_id_from_dir,
    source_manifest_fields,
)
from triage.sidecar_html.portal import build_run_portal


def _resolve(p: Optional[str], base: Path) -> Optional[Path]:
    if not p:
        return None
    pp = Path(p)
    if not pp.is_absolute():
        pp = (base / pp).resolve()
    return pp


def run(
    all_wave: str,
    existing_dashboard: str,
    out_dir: str,
    scope_path: Optional[str] = None,
    deployment_tracker: Optional[str] = None,
    as_of: str = "2026-06-01",
    websafe: bool = True,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parent.parent.parent
    scope = load_scope(scope_path)
    warnings: List[str] = []

    aw_path = _resolve(all_wave, root)
    dash_path = _resolve(existing_dashboard, root)
    out = assert_out_dir_allowed(_resolve(out_dir, root) or root / "Outputs")
    deploy_path = _resolve(deployment_tracker, root) if deployment_tracker else None

    for label, p in [("all_wave", aw_path), ("existing_dashboard", dash_path)]:
        if p is None or not p.exists():
            raise FileNotFoundError(f"{label} not found: {p}")
        if is_repair_filename(p.name):
            raise ValueError(f"Stop-ship repaired filename: {p.name}")

    all_wave_data = read_all_wave_workbook(str(aw_path), scope)
    wave3 = extract_wave3_targets(all_wave_data, scope)
    sprint_data = read_sprint_dashboard(str(dash_path), scope)

    resolver_rpt = resolve_sprint_targets(wave3, all_wave_data, sprint_data, scope)
    warnings.extend(resolver_rpt.warnings)

    compare_rpt = carry_forward_manual_status(resolver_rpt.targets, sprint_data, scope)
    targets = compare_rpt.targets

    if deploy_path and deploy_path.exists():
        warnings.extend(enrich_from_deployment_tracker(targets, str(deploy_path), scope))
    else:
        warnings.append("deployment_tracker_omitted:hostname_enrichment_skipped")

    blank_hosts = sum(1 for t in targets if not (t.hostname or "").strip())
    if blank_hosts:
        warnings.append(f"blank_hostnames:{blank_hosts}")

    site_counts = {s: sum(1 for t in targets if t.site == s) for s in scope["active_scope"]}
    total = sum(site_counts.values())

    xlsx_name = f"Cybernet_Targets_Sprint_{as_of}_WEBSAFE.xlsx"
    xlsx_path = out / xlsx_name

    manifest_inputs = {
        "generator": "triage.cybernet_targets.cli",
        "as_of": as_of,
        "all_wave": str(aw_path),
        "existing_dashboard": str(dash_path),
        "deployment_tracker": str(deploy_path) if deploy_path else "",
        "scope": scope_path or "configs/cybernet_sprint_scope_2026_06.json",
    }

    export_websafe_target_dashboard(
        targets,
        resolver_rpt,
        compare_rpt,
        str(xlsx_path),
        as_of,
        manifest_inputs,
        existing_dashboard_path=str(dash_path),
    )

    json_path = out / f"cybernet_targets_sprint_{as_of}.json"
    write_sidecar_json(json_path, rows_to_dicts(targets))

    recon_path = out / f"cybernet_amb_reconciliation_{as_of}.csv"
    write_reconciliation_csv(recon_path, resolver_rpt.amb_reconciliation)

    shortage_path = out / f"cybernet_shortage_queue_{as_of}.csv"
    write_shortage_csv(shortage_path, targets)

    preflight_result = None
    if websafe:
        preflight_result = run_preflight(str(xlsx_path), expected_sheets=targets_schema()["required_sheets"])
        if not preflight_result.webexcel_preflight_pass:
            warnings.append("preflight_failed")

    manifest = {
        "as_of": as_of,
        "run_id": run_id_from_dir(out),
        **source_manifest_fields(aw_path, dash_path),
        "total_active_targets": total,
        "site_counts": site_counts,
        "amb_counts": {
            "sprint_consolidated": len(sprint_data.get("AMB", [])),
            "wave3_cybernet_raw": len(resolver_rpt.amb_raw),
            "ane_wave2_hardware": sum(1 for r in resolver_rpt.amb_reconciliation if r.layer == "ane_wave2_hardware"),
        },
        "blank_hostnames": blank_hosts,
        "warnings": warnings,
        "outputs": {
            "workbook": str(xlsx_path),
            "targets_json": str(json_path),
            "amb_reconciliation_csv": str(recon_path),
            "shortage_csv": str(shortage_path),
        },
        "inputs": manifest_inputs,
        "preflight": asdict(preflight_result) if preflight_result else None,
    }

    manifest_path = out / f"cybernet_targets_manifest_{as_of}.json"
    write_sidecar_json(manifest_path, manifest)
    manifest["manifest_path"] = str(manifest_path)

    portal_path = build_run_portal(
        out,
        title="Cybernet Targets Sprint — Run Review",
        subtitle=f"As of {as_of}",
        sections=cybernet_sections(manifest),
    )
    manifest["html_portal"] = str(portal_path)
    manifest["outputs"]["html_portal"] = str(portal_path)
    write_sidecar_json(manifest_path, manifest)
    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="triage.cybernet_targets.cli")
    ap.add_argument("--all-wave", required=True)
    ap.add_argument("--existing-dashboard", required=True)
    ap.add_argument("--scope", default="configs/cybernet_sprint_scope_2026_06.json")
    ap.add_argument("--deployment-tracker")
    ap.add_argument("--out-dir", default=None, help="Run dir under Outputs/cybernet_targets/")
    ap.add_argument("--as-of", default="2026-06-01")
    ap.add_argument("--websafe", action="store_true", default=True)
    ap.add_argument("--no-websafe", action="store_false", dest="websafe")
    args = ap.parse_args(argv)

    slug = args.as_of.replace("-", "")
    out_dir = args.out_dir or str(allocate_run_dir("cybernet_targets", slug))
    manifest = run(
        all_wave=args.all_wave,
        existing_dashboard=args.existing_dashboard,
        scope_path=args.scope,
        deployment_tracker=args.deployment_tracker,
        out_dir=out_dir,
        as_of=args.as_of,
        websafe=args.websafe,
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
