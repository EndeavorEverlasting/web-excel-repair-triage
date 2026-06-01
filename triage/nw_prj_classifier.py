"""
NW PRJ Classifier — resolve authority hierarchy and apply Rich Guard.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from triage.nw_prj_admin_reader import AdminRecord
from triage.nw_prj_roster_reader import RosterRecord

@dataclass
class ClassificationResult:
    tech: str
    date: str
    resolved_hours: float
    status: str  # RED, AMBER, GREEN, BLUE, GRAY
    reason_code: str
    action_needed: str = ""
    is_blocker: bool = False
    notes: str = ""
    admin_ref: Optional[AdminRecord] = None
    roster_refs: List[RosterRecord] = field(default_factory=list)

class NwPrjClassifier:
    def __init__(self, protected_names: List[str] = None):
        self.protected_names = protected_names or ["Rich Perez", "Richard Perez"]

    def classify(
        self, 
        admin_records: List[AdminRecord], 
        roster_records: List[RosterRecord]
    ) -> List[ClassificationResult]:
        # Index roster by (tech, date)
        roster_map: Dict[tuple[str, str], List[RosterRecord]] = {}
        for r in roster_records:
            # Normalize names if possible? For now exact match.
            key = (r.tech, r.date)
            if key not in roster_map:
                roster_map[key] = []
            roster_map[key].append(r)

        results: List[ClassificationResult] = []
        
        # Process admin records (primary authority for hours)
        processed_roster_keys: Set[tuple[str, str]] = set()
        
        for admin in admin_records:
            key = (admin.tech, admin.date)
            rosters = roster_map.get(key, [])
            processed_roster_keys.add(key)
            
            roster_hours = sum(r.hours for r in rosters)
            
            res = ClassificationResult(
                tech=admin.tech,
                date=admin.date,
                resolved_hours=admin.hours,
                admin_ref=admin,
                roster_refs=rosters,
                status="GREEN",
                reason_code="RECONCILED"
            )

            # Apply Rich Guard
            if admin.tech in self.protected_names:
                # Rich afternoon clock-out check
                has_afternoon_clockout = any(r.punch_out and "12:" not in r.punch_out and "1:" in r.punch_out or "2:" in r.punch_out or "3:" in r.punch_out for r in rosters)
                
                if admin.hours >= 8 and roster_hours < admin.hours:
                    res.status = "AMBER"
                    res.reason_code = "RICH_GUARD"
                    res.action_needed = "Preserve admin full day; roster under-reports (afternoon clockout suspected)."
                    res.resolved_hours = admin.hours # Authority: Admin wins
                elif admin.hours > 0 and roster_hours == 0:
                    res.status = "AMBER"
                    res.reason_code = "RICH_MISSING_ROSTER"
                    res.action_needed = "Rich worked according to Admin, but roster is empty."
                    res.resolved_hours = admin.hours
            
            elif abs(admin.hours - roster_hours) > 0.01:
                res.status = "RED"
                res.reason_code = "MISMATCH"
                res.action_needed = f"Admin({admin.hours}) != Roster({roster_hours})"
                res.is_blocker = True
            
            results.append(res)
            
        # Check for roster records not in admin (lingering admin rows or new roster entries)
        for key, rosters in roster_map.items():
            if key not in processed_roster_keys:
                roster_hours = sum(r.hours for r in rosters)
                if roster_hours > 0:
                    res = ClassificationResult(
                        tech=key[0],
                        date=key[1],
                        resolved_hours=roster_hours,
                        roster_refs=rosters,
                        status="BLUE",
                        reason_code="ROSTER_ONLY",
                        action_needed="Roster entry missing from Admin summary."
                    )
                    results.append(res)
                
        return results
