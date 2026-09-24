"""Rebuild index.html from an existing manifest.json (no workbook regeneration)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.sidecar_html.adapters import (
    admin_billing_sections,
    bonita_sections,
    cybernet_sections,
    neuron_track_sections,
    one_marcus_sections,
)
from triage.sidecar_html.portal import PortalSection, build_run_portal


def _load_manifest(out_dir: Path) -> tuple[Dict[str, Any], Path]:
    for name in sorted(out_dir.glob("*manifest*.json")):
        with name.open("r", encoding="utf-8") as f:
            return json.load(f), name
    raise FileNotFoundError(f"No manifest JSON in {out_dir}")


def sections_for_manifest(manifest: Dict[str, Any], out_dir: Path) -> List[PortalSection]:
    engine = manifest.get("engine", "")
    if "admin_billing_summary" in engine:
        return admin_billing_sections(manifest, out_dir)
    if "bonita_cli" in engine:
        return bonita_sections(manifest)
    if "nw_prj_neuron_track_hours.cli" in engine:
        return neuron_track_sections(manifest)
    if manifest.get("formula_cells_patched") is not None:
        return one_marcus_sections(manifest)
    if manifest.get("total_active_targets") is not None:
        return cybernet_sections(manifest)
    return []


def rebuild_portal(out_dir: str | Path) -> Path:
    out = Path(out_dir)
    manifest, _ = _load_manifest(out)
    title = manifest.get("engine", "Artifact run").split(".")[-1].replace("_", " ").title()
    sections = sections_for_manifest(manifest, out)
    path = build_run_portal(
        out,
        title=f"{title} — Run Review",
        subtitle=str(manifest.get("generated_utc") or manifest.get("as_of") or out.name),
        sections=sections,
    )
    manifest["html_portal"] = str(path)
  # caller may rewrite manifest
    return path
