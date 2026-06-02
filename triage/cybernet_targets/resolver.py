"""AMB three-layer resolver, site aliases, SSUH location replacement."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from triage.cybernet_targets.config import load_scope, normalize_site
from triage.cybernet_targets.models import TargetRow, sprint_match_key


def _norm_wave(val: Any) -> Optional[int]:
    if val is None or val == "":
        return None
    try:
        return int(float(str(val).strip()))
    except (TypeError, ValueError):
        return None


def _norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().upper())


def _group_key_from_amb_dep(name: str) -> str:
    """First bracketed dep id or normalized prefix."""
    m = re.search(r"\[(\d+)\]", name or "")
    if m:
        return m.group(1)
    return _norm_text(name)[:40]


@dataclass
class AmbReconciliationRow:
    layer: str
    source_row: str
    practice_location: str
    group_key: str
    in_sprint: bool
    in_wave3_cybernet: bool
    in_wave2_ane: bool
    action_needed: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer": self.layer,
            "source_row": self.source_row,
            "practice_location": self.practice_location,
            "group_key": self.group_key,
            "in_sprint": self.in_sprint,
            "in_wave3_cybernet": self.in_wave3_cybernet,
            "in_wave2_ane": self.in_wave2_ane,
            "action_needed": self.action_needed,
        }


@dataclass
class ResolverReport:
    targets: List[TargetRow] = field(default_factory=list)
    amb_raw: List[TargetRow] = field(default_factory=list)
    amb_grouped: List[TargetRow] = field(default_factory=list)
    amb_reconciliation: List[AmbReconciliationRow] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def extract_amb_raw_from_neuron(all_wave_data: Dict[str, Any], scope: Dict[str, Any]) -> List[TargetRow]:
    aliases = scope.get("site_aliases", {})
    source_path = all_wave_data["path"]
    out: List[TargetRow] = []
    for rd in all_wave_data["neuron_cybernet"]["rows"]:
        wave = _norm_wave(rd.get("Wave"))
        source_site = str(rd.get("Site") or "").strip()
        if wave != 3 or "AMB" not in source_site.upper():
            continue
        location = str(rd.get("Location") or "").strip()
        row_num = str(rd.get("_row_num", ""))
        hostname = str(rd.get("PC Name") or "").strip()
        tr = TargetRow(
            target_id=f"AMB-RAW|{row_num}",
            sprint_scope="AMB",
            wave="3",
            site="AMB",
            source_site=source_site,
            location=location,
            source_workbook=__import__("pathlib").Path(source_path).name,
            source_sheet="Neuron Cybernet",
            source_row=row_num,
            target_type=str(rd.get("Device Type") or "Cybernet"),
            cybernet_count=1,
            hostname=hostname,
            amb_wave_bucket="wave3_cybernet",
            milestone=scope.get("milestones", {}).get("AMB", ""),
            due_date=scope.get("milestones", {}).get("AMB", ""),
        )
        tr.apply_readiness()
        out.append(tr)
    return out


def extract_amb_ane_wave2(all_wave_data: Dict[str, Any], scope: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = all_wave_data["ane_ambulatory"]["rows"]
    out: List[Dict[str, Any]] = []
    for rd in rows:
        wave = _norm_wave(rd.get("Wave"))
        if wave != 2:
            continue
        cyb_col = next((k for k in rd if "Cybernet" in k), None)
        qty = rd.get(cyb_col) if cyb_col else None
        try:
            qty_n = int(float(qty)) if qty not in (None, "") else 0
        except (TypeError, ValueError):
            qty_n = 0
        if qty_n <= 0:
            continue
        practice = str(rd.get("Practice Name") or "").strip()
        dep = str(rd.get("AMB DEP Name") or "").strip()
        out.append({
            "_row_num": rd.get("_row_num"),
            "practice": practice,
            "dep": dep,
            "cybernet_qty": qty_n,
            "group_key": _group_key_from_amb_dep(dep or practice),
        })
    return out


def group_ambulatory_targets(
    sprint_amb_rows: List[Dict[str, Any]],
    wave3_raw: List[TargetRow],
    ane_w2: List[Dict[str, Any]],
    scope: Dict[str, Any],
) -> List[TargetRow]:
    """Layer 3: sprint consolidated AMB rows drive grouped output."""
    milestones = scope.get("milestones", {})
    grouped: List[TargetRow] = []
    for rd in sprint_amb_rows:
        location = str(rd.get("Location") or "").strip()
        hostname = str(rd.get("Hostname (WBS)") or rd.get("Hostname") or "").strip()
        row_num = str(rd.get("_row_num", ""))
        tr = TargetRow(
            target_id=sprint_match_key("AMB", location),
            sprint_scope="AMB",
            wave="3",
            site="AMB",
            source_site="Sprint Dashboard AMB",
            location=location,
            source_workbook="sprint_dashboard",
            source_sheet="AMB",
            source_row=row_num,
            target_type="Cybernet",
            cybernet_count=1,
            hostname=hostname,
            status=str(rd.get("Status") or ""),
            imaged=str(rd.get("Imaged") or ""),
            labeled=str(rd.get("Labeled") or ""),
            boxed=str(rd.get("Boxed") or ""),
            ready_for_delivery=str(rd.get("Ready for Delivery") or ""),
            completed_date=str(rd.get("Completed Date") or ""),
            milestone="AMB",
            due_date=milestones.get("AMB", ""),
            amb_wave_bucket="sprint_consolidated",
        )
        tr.apply_readiness()
        grouped.append(tr)
    return grouped


def reconcile_amb(
    sprint_amb_rows: List[Dict[str, Any]],
    wave3_raw: List[TargetRow],
    ane_w2: List[Dict[str, Any]],
) -> List[AmbReconciliationRow]:
    sprint_keys: Set[str] = {_norm_text(r.get("Location", "")) for r in sprint_amb_rows}
    w3_keys: Set[str] = {_norm_text(r.location) for r in wave3_raw}
    w2_keys: Set[str] = {_group_key_from_amb_dep(d.get("dep") or d.get("practice", "")) for d in ane_w2}

    recon: List[AmbReconciliationRow] = []

    for r in sprint_amb_rows:
        loc = str(r.get("Location") or "")
        recon.append(AmbReconciliationRow(
            layer="sprint_consolidated",
            source_row=str(r.get("_row_num", "")),
            practice_location=loc,
            group_key=_norm_text(loc),
            in_sprint=True,
            in_wave3_cybernet=_norm_text(loc) in w3_keys or any(_norm_text(loc) in _norm_text(w.location) for w in wave3_raw),
            in_wave2_ane=False,
            action_needed="" if _norm_text(loc) in w3_keys else "Verify mapping to Wave 3 AMB source row",
        ))

    for tr in wave3_raw:
        recon.append(AmbReconciliationRow(
            layer="wave3_cybernet",
            source_row=tr.source_row,
            practice_location=tr.location,
            group_key=_norm_text(tr.location),
            in_sprint=_norm_text(tr.location) in sprint_keys or any(_norm_text(tr.location) in sk for sk in sprint_keys),
            in_wave3_cybernet=True,
            in_wave2_ane=False,
            action_needed="" if any(_norm_text(tr.location) in sk or sk in _norm_text(tr.location) for sk in sprint_keys) else "Not in sprint consolidated view",
        ))

    for d in ane_w2:
        gk = d.get("group_key", "")
        label = f"{d.get('practice', '')} | {d.get('dep', '')}"
        recon.append(AmbReconciliationRow(
            layer="ane_wave2_hardware",
            source_row=str(d.get("_row_num", "")),
            practice_location=label,
            group_key=gk,
            in_sprint=False,
            in_wave3_cybernet=False,
            in_wave2_ane=True,
            action_needed="Wave 2 hardware row — confirm sprint scope",
        ))

    return recon


def replace_ssuh_placeholders(
    wave3_targets: List[TargetRow],
    sprint_ssuh: List[Dict[str, Any]],
    scope: Dict[str, Any],
) -> List[TargetRow]:
    """Use All-Wave SSH rows for SSUH; merge sprint checklist by location match."""
    placeholder = scope.get("placeholder_ssuh_location", "Imaging Pipeline")
    milestones = scope.get("milestones", {})
    ssh_rows = [t for t in wave3_targets if t.site == "SSUH" and t.source_site.upper() in ("SSH", "SSUH")]
    sprint_by_key = {
        sprint_match_key("SSUH", str(r.get("Location") or "")): r
        for r in sprint_ssuh
    }

    if not ssh_rows:
        # Fall back to sprint rows only
        out: List[TargetRow] = []
        for rd in sprint_ssuh:
            loc = str(rd.get("Location") or "")
            host = str(rd.get("Hostname (WBS)") or rd.get("Hostname") or "").strip()
            tr = TargetRow(
                target_id=sprint_match_key("SSUH", loc),
                sprint_scope="SSUH",
                wave="3",
                site="SSUH",
                source_site="SSUH",
                location=loc,
                source_sheet="SSUH",
                source_row=str(rd.get("_row_num", "")),
                hostname=host,
                status=str(rd.get("Status") or ""),
                imaged=str(rd.get("Imaged") or ""),
                labeled=str(rd.get("Labeled") or ""),
                boxed=str(rd.get("Boxed") or ""),
                ready_for_delivery=str(rd.get("Ready for Delivery") or ""),
                completed_date=str(rd.get("Completed Date") or ""),
                milestone="SSUH_CONFIG_COMPLETE",
                due_date=milestones.get("SSUH_CONFIG_COMPLETE", ""),
                delivery_date=milestones.get("SSUH_DELIVERY", ""),
            )
            if _norm_text(loc) == _norm_text(placeholder):
                tr.action_needed = "Replace placeholder location with All-Wave SSH row"
            tr.apply_readiness()
            out.append(tr)
        return out

    out = []
    for tr in ssh_rows:
        key = sprint_match_key("SSUH", tr.location)
        prior = sprint_by_key.get(key)
        if prior:
            tr.status = str(prior.get("Status") or tr.status)
            tr.imaged = str(prior.get("Imaged") or tr.imaged)
            tr.labeled = str(prior.get("Labeled") or tr.labeled)
            tr.boxed = str(prior.get("Boxed") or tr.boxed)
            tr.ready_for_delivery = str(prior.get("Ready for Delivery") or tr.ready_for_delivery)
            tr.completed_date = str(prior.get("Completed Date") or tr.completed_date)
            sprint_host = str(prior.get("Hostname (WBS)") or prior.get("Hostname") or "").strip()
            if sprint_host and not sprint_host.upper().startswith("WBS-"):
                tr.hostname = sprint_host
        tr.milestone = "SSUH_CONFIG_COMPLETE"
        tr.due_date = milestones.get("SSUH_CONFIG_COMPLETE", "")
        tr.delivery_date = milestones.get("SSUH_DELIVERY", "")
        tr.apply_readiness()
        out.append(tr)
    return out


def resolve_sprint_targets(
    wave3_targets: List[TargetRow],
    all_wave_data: Dict[str, Any],
    sprint_data: Dict[str, List[Dict[str, Any]]],
    scope: Dict[str, Any] | None = None,
) -> ResolverReport:
    scope = scope or load_scope()
    rpt = ResolverReport()
    milestones = scope.get("milestones", {})
    carry_cols = scope.get("carry_forward_columns", [])

    # HH / JTM from wave3 with sprint carry
    for site in ("HH", "JTM"):
        site_targets = [t for t in wave3_targets if t.site == site]
        sprint_rows = sprint_data.get(site, [])
        sprint_by_loc = {sprint_match_key(site, str(r.get("Location") or "")): r for r in sprint_rows}
        for tr in site_targets:
            prior = sprint_by_loc.get(sprint_match_key(site, tr.location))
            if prior:
                tr.status = str(prior.get("Status") or tr.status)
                tr.imaged = str(prior.get("Imaged") or tr.imaged)
                tr.labeled = str(prior.get("Labeled") or tr.labeled)
                tr.boxed = str(prior.get("Boxed") or tr.boxed)
                tr.ready_for_delivery = str(prior.get("Ready for Delivery") or tr.ready_for_delivery)
                tr.completed_date = str(prior.get("Completed Date") or tr.completed_date)
            tr.due_date = milestones.get("PROTOTYPE_KITS", "")
            tr.milestone = site
            tr.apply_readiness()
        rpt.targets.extend(site_targets)

    # AMB three layers
    rpt.amb_raw = extract_amb_raw_from_neuron(all_wave_data, scope)
    ane_w2 = extract_amb_ane_wave2(all_wave_data, scope)
    sprint_amb = sprint_data.get("AMB", [])
    rpt.amb_grouped = group_ambulatory_targets(sprint_amb, rpt.amb_raw, ane_w2, scope)
    rpt.amb_reconciliation = reconcile_amb(sprint_amb, rpt.amb_raw, ane_w2)
    rpt.targets.extend(rpt.amb_grouped)

    counts = {
        "sprint_amb": len(sprint_amb),
        "wave3_amb": len(rpt.amb_raw),
        "ane_w2_cybernet": len(ane_w2),
    }
    if len(set(counts.values())) > 1:
        rpt.warnings.append(
            f"amb_count_mismatch:sprint={counts['sprint_amb']},wave3={counts['wave3_amb']},ane_w2={counts['ane_w2_cybernet']}"
        )

    # SSUH
    ssuh = replace_ssuh_placeholders(wave3_targets, sprint_data.get("SSUH", []), scope)
    rpt.targets.extend(ssuh)

    return rpt
