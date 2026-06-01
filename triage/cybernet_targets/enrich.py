"""Optional deployment tracker enrichment for hostname/asset assignment."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from triage.cybernet_targets.extractor import read_sheet_table
from triage.cybernet_targets.models import TargetRow


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().upper())


def read_deployment_records(path: str, scope: Dict[str, Any]) -> List[Dict[str, Any]]:
    anchor = scope["reader_anchors"]["deployment_tracker"]
    _, rows = read_sheet_table(path, anchor["sheet"], anchor["header_row"], anchor["data_start_row"])
    return rows


def enrich_from_deployment_tracker(
    targets: List[TargetRow],
    tracker_path: str,
    scope: Dict[str, Any],
) -> List[str]:
    """Match hostnames from Deployments tab. Returns warnings."""
    warnings: List[str] = []
    rows = read_deployment_records(tracker_path, scope)
    by_cyb_host: Dict[str, Dict[str, Any]] = {}
    by_loc: Dict[str, Dict[str, Any]] = {}

    for rd in rows:
        deployed = str(rd.get("Deployed") or "").strip().lower()
        if deployed not in ("yes", "y", "true", "1"):
            continue
        cyb = str(rd.get("Cybernet Hostname") or "").strip()
        neu = str(rd.get("Neuron Hostname") or "").strip()
        building = str(rd.get("Current Building") or rd.get("Install Building") or "").strip()
        room = str(rd.get("Room") or rd.get("Area/Unit/Dept") or "").strip()
        loc_key = _norm(f"{building}|{room}")
        if cyb:
            by_cyb_host[_norm(cyb)] = rd
        if loc_key.strip("|"):
            by_loc[loc_key] = rd

    for tr in targets:
        if tr.hostname and tr.hostname.strip():
            hit = by_cyb_host.get(_norm(tr.hostname))
            if hit:
                tr.asset_assignment_status = "assigned"
                tr.review_status = tr.review_status or "confirmed"
                continue

        # Fuzzy: match location tokens in building+room
        loc_norm = _norm(tr.location)
        matched: Optional[Dict[str, Any]] = None
        for lk, rd in by_loc.items():
            if loc_norm and (loc_norm in lk or lk in loc_norm):
                matched = rd
                break
        if matched:
            cyb = str(matched.get("Cybernet Hostname") or "").strip()
            if cyb and not tr.hostname:
                tr.hostname = cyb
                tr.asset_assignment_status = "assigned"
            elif cyb:
                tr.review_status = "needs_review"
                warnings.append(f"fuzzy_match:{tr.target_id}")
        tr.apply_readiness()

    return warnings
