"""Target row model and identity keys for Cybernet sprint automation."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from triage.cybernet_targets.config import targets_schema


def _norm_loc(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().upper())


def target_key(site: str, location: str, source_sheet: str = "", source_row: str = "") -> str:
    return f"{site}|{_norm_loc(location)}|{source_sheet}|{source_row}"


def sprint_match_key(site: str, location: str) -> str:
    return f"{site}|{_norm_loc(location)}"


@dataclass
class TargetRow:
    target_id: str = ""
    sprint_scope: str = ""
    wave: str = ""
    site: str = ""
    source_site: str = ""
    location: str = ""
    source_workbook: str = ""
    source_sheet: str = ""
    source_row: str = ""
    target_type: str = ""
    kit_required: str = ""
    cybernet_count: int = 0
    neuron_count: int = 0
    arm_required: str = ""
    ethernet_dim_required: str = ""
    breakaway_required: str = ""
    hostname: str = ""
    asset_assignment_status: str = "unassigned"
    status: str = ""
    imaged: str = ""
    labeled: str = ""
    boxed: str = ""
    ready_for_delivery: str = ""
    completed_date: str = ""
    due_date: str = ""
    delivery_date: str = ""
    milestone: str = ""
    readiness_gate: str = "blocked"
    review_status: str = ""
    action_needed: str = ""
    amb_wave_bucket: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "TargetRow":
        cols = targets_schema()["target_columns"]
        kw: Dict[str, Any] = {}
        field_map = {
            "Target ID": "target_id",
            "Sprint Scope": "sprint_scope",
            "Wave": "wave",
            "Site": "site",
            "Source Site": "source_site",
            "Location": "location",
            "Source Workbook": "source_workbook",
            "Source Sheet": "source_sheet",
            "Source Row": "source_row",
            "Target Type": "target_type",
            "Kit Required": "kit_required",
            "Cybernet Count": "cybernet_count",
            "Neuron Count": "neuron_count",
            "Arm Required": "arm_required",
            "Ethernet DIM Required": "ethernet_dim_required",
            "Breakaway Required": "breakaway_required",
            "Hostname": "hostname",
            "Asset Assignment Status": "asset_assignment_status",
            "Status": "status",
            "Imaged": "imaged",
            "Labeled": "labeled",
            "Boxed": "boxed",
            "Ready for Delivery": "ready_for_delivery",
            "Due Date": "due_date",
            "Delivery Date": "delivery_date",
            "Milestone": "milestone",
            "Readiness Gate": "readiness_gate",
            "Review Status": "review_status",
            "Action Needed": "action_needed",
        }
        for col in cols:
            attr = field_map.get(col)
            if attr and col in d:
                val = d[col]
                if attr in ("cybernet_count", "neuron_count"):
                    try:
                        kw[attr] = int(float(val)) if val not in (None, "") else 0
                    except (TypeError, ValueError):
                        kw[attr] = 0
                else:
                    kw[attr] = "" if val is None else str(val)
        row = TargetRow(**kw)
        row.amb_wave_bucket = str(d.get("Ambulatory Wave Bucket", d.get("amb_wave_bucket", "")) or "")
        return row

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "Target ID": self.target_id,
            "Sprint Scope": self.sprint_scope,
            "Wave": self.wave,
            "Site": self.site,
            "Source Site": self.source_site,
            "Location": self.location,
            "Source Workbook": self.source_workbook,
            "Source Sheet": self.source_sheet,
            "Source Row": self.source_row,
            "Target Type": self.target_type,
            "Kit Required": self.kit_required,
            "Cybernet Count": self.cybernet_count,
            "Neuron Count": self.neuron_count,
            "Arm Required": self.arm_required,
            "Ethernet DIM Required": self.ethernet_dim_required,
            "Breakaway Required": self.breakaway_required,
            "Hostname": self.hostname,
            "Asset Assignment Status": self.asset_assignment_status,
            "Status": self.status,
            "Imaged": self.imaged,
            "Labeled": self.labeled,
            "Boxed": self.boxed,
            "Ready for Delivery": self.ready_for_delivery,
            "Completed Date": self.completed_date,
            "Due Date": self.due_date,
            "Delivery Date": self.delivery_date,
            "Milestone": self.milestone,
            "Readiness Gate": self.readiness_gate,
            "Review Status": self.review_status,
            "Action Needed": self.action_needed,
        }
        if self.amb_wave_bucket:
            d["Ambulatory Wave Bucket"] = self.amb_wave_bucket
        return d

    def apply_readiness(self) -> None:
        host = (self.hostname or "").strip()
        if not host or host.upper() in ("X", "TBD", "WBS"):
            self.asset_assignment_status = self.asset_assignment_status or "unassigned"
            if not self.imaged and not self.labeled:
                self.readiness_gate = "blocked"
                if not self.action_needed:
                    self.action_needed = "Assign hostname before delivery"
        else:
            if self.asset_assignment_status == "unassigned":
                self.asset_assignment_status = "assigned"
            if self.imaged and self.labeled and self.boxed:
                self.readiness_gate = "ready" if self.ready_for_delivery else "staged"
            else:
                self.readiness_gate = "in_progress"


def rows_to_dicts(rows: List[TargetRow]) -> List[Dict[str, Any]]:
    return [r.to_dict() for r in rows]
