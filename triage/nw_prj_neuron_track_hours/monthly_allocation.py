"""Sanitized month-specific task allocation for roster-derived Neuron shifts.

Policies distribute only heuristic/medium-confidence rows. Explicit high-confidence
roster evidence is preserved. Deployments are never invented by ratio allocation.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from triage.nw_prj_neuron_track_hours.bonita_resolver import BonitaResolution, BonitaShift

DEFAULT_POLICY_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "neuron_billing_evidence_pack"
    / "monthly_allocation_policies.json"
)


@dataclass(frozen=True)
class MonthlyPolicyStats:
    month_key: str
    policy_name: str
    applied_shift_count: int
    preserved_shift_count: int
    deployment_shift_count: int
    category_hours: Dict[str, float]
    policy_path: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "month_key": self.month_key,
            "policy_name": self.policy_name,
            "applied_shift_count": self.applied_shift_count,
            "preserved_shift_count": self.preserved_shift_count,
            "deployment_shift_count": self.deployment_shift_count,
            "category_hours": self.category_hours,
            "policy_path": self.policy_path,
        }


def _normal_name(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def load_monthly_policies(path: Optional[str] = None) -> Tuple[Path, Dict[str, Dict[str, Any]]]:
    policy_path = Path(path).resolve() if path else DEFAULT_POLICY_PATH.resolve()
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    policies = payload.get("policies")
    if not isinstance(policies, dict):
        raise ValueError(f"monthly allocation policy has no policies object: {policy_path}")
    return policy_path, policies


def _month_key(shift: BonitaShift) -> str:
    return f"{shift.date.year:04d}-{shift.date.month:02d}"


def _validate_policy(month_key: str, policy: Dict[str, Any]) -> Tuple[List[Tuple[str, float]], set[str], Dict[str, Any]]:
    raw_weights = policy.get("allocation_weights")
    if not isinstance(raw_weights, dict) or not raw_weights:
        raise ValueError(f"{month_key}: allocation_weights must be a non-empty object")
    weights: List[Tuple[str, float]] = []
    for category, value in raw_weights.items():
        weight = float(value)
        if weight <= 0:
            raise ValueError(f"{month_key}: weight for {category!r} must be positive")
        weights.append((str(category), weight))
    confidence = {
        str(value).strip().casefold()
        for value in policy.get("reallocate_confidence", ["low", "medium"])
    }
    if "high" in confidence:
        raise ValueError(
            f"{month_key}: high-confidence assignments are authoritative and may not be reallocated"
        )
    deployment = policy.get("deployment") or {}
    if not isinstance(deployment, dict):
        raise ValueError(f"{month_key}: deployment must be an object")
    explicit_only = deployment.get("explicit_only", False)
    if not isinstance(explicit_only, bool):
        raise ValueError(f"{month_key}: deployment.explicit_only must be a boolean")
    if explicit_only and any(
        _normal_name(category) == "deployments" for category, _ in weights
    ):
        raise ValueError(
            f"{month_key}: explicit-only Deployments cannot appear in allocation_weights"
        )
    return weights, confidence, deployment


def _choose_category(
    weights: Sequence[Tuple[str, float]],
    targets: Dict[str, float],
    assigned: Dict[str, float],
) -> str:
    order = {category: index for index, (category, _) in enumerate(weights)}
    return max(
        (category for category, _ in weights),
        key=lambda category: (targets[category] - assigned.get(category, 0.0), -order[category]),
    )


def apply_monthly_allocation_policies(
    resolution: BonitaResolution,
    months: Iterable[str],
    *,
    policy_path: Optional[str] = None,
) -> Tuple[BonitaResolution, List[MonthlyPolicyStats]]:
    """Apply configured ratios to heuristic shifts, preserving explicit evidence."""
    resolved_path, policies = load_monthly_policies(policy_path)
    requested = set(months)
    grouped: Dict[str, List[BonitaShift]] = defaultdict(list)
    untouched: List[BonitaShift] = []
    for shift in resolution.shifts:
        key = _month_key(shift)
        if key in requested and key in policies:
            grouped[key].append(shift)
        else:
            untouched.append(shift)

    rewritten: List[BonitaShift] = list(untouched)
    stats: List[MonthlyPolicyStats] = []
    warnings = list(resolution.warnings)

    for key in sorted(grouped):
        policy = policies[key]
        weights, reallocate_confidence, deployment = _validate_policy(key, policy)
        categories = {category for category, _ in weights}
        month_shifts = sorted(grouped[key], key=lambda s: (s.date, _normal_name(s.tech), s.clock_in))

        explicit_deployments = [
            shift
            for shift in month_shifts
            if shift.assignment_type == "Deployments"
            and shift.assignment_confidence.casefold() not in reallocate_confidence
        ]
        max_deployments = int(deployment.get("max_shift_count", 0))
        if len(explicit_deployments) > max_deployments:
            raise ValueError(
                f"{key}: explicit deployment shifts ({len(explicit_deployments)}) exceed "
                f"policy maximum ({max_deployments}); review roster evidence"
            )
        allowed = deployment.get("eligible_techs") or []
        allowed_names = {_normal_name(value) for value in allowed}
        if allowed_names:
            invalid = [shift.tech for shift in explicit_deployments if _normal_name(shift.tech) not in allowed_names]
            if invalid:
                raise ValueError(
                    f"{key}: explicit deployment tech is not allowed by local policy: "
                    + ", ".join(sorted(set(invalid)))
                )

        preserved: List[BonitaShift] = []
        allocatable: List[BonitaShift] = []
        for shift in month_shifts:
            confidence = shift.assignment_confidence.casefold()
            if confidence in reallocate_confidence and shift.assignment_type != "Deployments":
                allocatable.append(shift)
            elif confidence in reallocate_confidence and shift.assignment_type == "Deployments":
                allocatable.append(replace(shift, assignment_type="Configurations"))
            else:
                preserved.append(shift)

        assigned: Dict[str, float] = defaultdict(float)
        for shift in preserved:
            if shift.assignment_type in categories:
                assigned[shift.assignment_type] += float(shift.total_hours)
        weighted_pool = sum(float(shift.total_hours) for shift in allocatable) + sum(assigned.values())
        total_weight = sum(weight for _, weight in weights)
        targets = {
            category: weighted_pool * weight / total_weight
            for category, weight in weights
        }

        applied: List[BonitaShift] = []
        for shift in allocatable:
            category = _choose_category(weights, targets, assigned)
            assigned[category] += float(shift.total_hours)
            applied.append(replace(
                shift,
                assignment_type=category,
                assignment_rule=f"monthly-policy:{key}:{category}",
                assignment_confidence="medium",
            ))

        final = sorted(preserved + applied, key=lambda s: (s.date, _normal_name(s.tech), s.clock_in))
        rewritten.extend(final)
        category_hours: Dict[str, float] = defaultdict(float)
        for shift in final:
            category_hours[shift.assignment_type] += float(shift.total_hours)
        stats.append(MonthlyPolicyStats(
            month_key=key,
            policy_name=str(policy.get("name") or key),
            applied_shift_count=len(applied),
            preserved_shift_count=len(preserved),
            deployment_shift_count=sum(1 for shift in final if shift.assignment_type == "Deployments"),
            category_hours={category: round(hours, 2) for category, hours in category_hours.items()},
            policy_path=str(resolved_path),
        ))
        warnings.append(f"monthly_allocation_policy_applied:{key}:{len(applied)}")

    rewritten.sort(key=lambda s: (s.date, _normal_name(s.tech), s.clock_in))
    return BonitaResolution(
        shifts=rewritten,
        review=list(resolution.review),
        warnings=warnings,
    ), stats
