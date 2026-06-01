"""Compare generated targets to prior sprint dashboard; carry forward manual status."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from triage.cybernet_targets.config import load_scope
from triage.cybernet_targets.models import TargetRow, sprint_match_key


@dataclass
class CarryoverEntry:
    target_id: str
    site: str
    location: str
    action: str
    columns_carried: List[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_id": self.target_id,
            "site": self.site,
            "location": self.location,
            "action": self.action,
            "columns_carried": self.columns_carried,
            "note": self.note,
        }


@dataclass
class CompareReport:
    targets: List[TargetRow] = field(default_factory=list)
    carryover_log: List[CarryoverEntry] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def carry_forward_manual_status(
    targets: List[TargetRow],
    sprint_data: Dict[str, List[Dict[str, Any]]],
    scope: Dict[str, Any] | None = None,
) -> CompareReport:
    scope = scope or load_scope()
    carry_cols = scope.get("carry_forward_columns", [])
    col_map = {
        "Status": "status",
        "Imaged": "imaged",
        "Labeled": "labeled",
        "Boxed": "boxed",
        "Ready for Delivery": "ready_for_delivery",
        "Completed Date": "completed_date",
    }
    rpt = CompareReport(targets=list(targets))

    prior_by_key: Dict[str, Dict[str, Any]] = {}
    for site, rows in sprint_data.items():
        for rd in rows:
            loc = str(rd.get("Location") or "")
            prior_by_key[sprint_match_key(site, loc)] = rd

    for tr in rpt.targets:
        key = sprint_match_key(tr.site, tr.location)
        prior = prior_by_key.get(key)
        if not prior:
            continue
        carried: List[str] = []
        for col, attr in col_map.items():
            if col not in carry_cols:
                continue
            val = prior.get(col)
            if val is None or str(val).strip() == "":
                continue
            current = getattr(tr, attr, "")
            if not str(current).strip():
                setattr(tr, attr, str(val))
                carried.append(col)
        if carried:
            rpt.carryover_log.append(CarryoverEntry(
                target_id=tr.target_id,
                site=tr.site,
                location=tr.location,
                action="carried_forward",
                columns_carried=carried,
            ))
        tr.apply_readiness()

    return rpt
