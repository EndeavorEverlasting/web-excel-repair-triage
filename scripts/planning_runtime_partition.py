#!/usr/bin/env python3
"""Compatibility shim over the canonical prompt_runtime_partition owner."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "prompt_runtime_partition",
    ROOT / "scripts/prompt_runtime_partition.py",
)
_MOD = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
sys.modules[_SPEC.name] = _MOD
_SPEC.loader.exec_module(_MOD)

HOSTS = _MOD.HOSTS
PartitionDecision = _MOD.PartitionDecision
RuntimePartitionError = _MOD.RuntimePartitionError
partition_work_unit = _MOD.partition_work_unit
project_p04 = _MOD.project_p04
project_p05 = _MOD.project_p05
place_work_unit = partition_work_unit
project_p04_dispatch_lane = project_p04
project_p05_panel = project_p05


def validate_lane_runtime_metadata(lane: dict[str, Any], *, lane_id: str) -> dict[str, Any]:
    """Validate required parallel-dispatch lane runtime-placement fields."""
    host = lane.get("execution_environment")
    if host not in HOSTS:
        raise RuntimePartitionError(
            f"lane {lane_id} has invalid execution_environment: {host!r}"
        )
    provider_access = lane.get("provider_access")
    if not isinstance(provider_access, list):
        raise RuntimePartitionError(f"lane {lane_id} provider_access must be an array")
    required = lane.get("required_capabilities")
    evidence = lane.get("evidence_inputs")
    if evidence is None:
        evidence = lane.get("inherited_evidence")
    if not isinstance(evidence, list):
        raise RuntimePartitionError(f"lane {lane_id} evidence_inputs must be an array")

    normalized_providers: list[dict[str, Any]] = []
    for index, item in enumerate(provider_access):
        if isinstance(item, str) and item.strip():
            normalized_providers.append(
                {
                    "provider_family": item.strip(),
                    "operation": "access",
                    "authority_state": "AVAILABLE_UNVERIFIED",
                    "mutation_authority": False,
                }
            )
        elif isinstance(item, dict):
            normalized_providers.append(item)
        else:
            raise RuntimePartitionError(
                f"lane {lane_id} provider_access[{index}] must be a string or object"
            )

    normalized_evidence: list[dict[str, Any]] = []
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            raise RuntimePartitionError(
                f"lane {lane_id} evidence_inputs[{index}] must be an object"
            )
        record = dict(item)
        if "sanitized_ref" not in record and "durable_ref" in record:
            record["sanitized_ref"] = record.pop("durable_ref")
        if "source_owner" not in record and "source_owner_class" in record:
            record["source_owner"] = record.pop("source_owner_class")
        visibility = record.get("visibility")
        if isinstance(visibility, str) and visibility.islower():
            mapping = {
                "public_tracked": "PUBLIC_TRACKED",
                "protected_provider": "PROTECTED_EXTERNAL",
                "ephemeral_runtime": "SANITIZED_OPAQUE",
            }
            record["visibility"] = mapping.get(visibility, visibility.upper())
        if record.get("visibility") == "PROTECTED_EXTERNAL":
            ref = str(record.get("sanitized_ref") or "")
            if not ref.startswith("opaque:"):
                record["sanitized_ref"] = f"opaque:{ref}" if ref else "opaque:protected"
        if record.get("visibility") == "PUBLIC_TRACKED" and "public_provider_ref_verified" not in record:
            record["public_provider_ref_verified"] = False
        normalized_evidence.append(record)

    decision = partition_work_unit(
        {
            "work_unit_id": lane_id,
            "required_capabilities": required,
            "capability_facts": {
                "current_runtime_available": host == "CURRENT_CHAT_RUNTIME",
                "current_runtime_authorized": host == "CURRENT_CHAT_RUNTIME",
                "local_runtime_required": host == "LOCAL_AGENT_RUNTIME",
                "ci_remote_required": host == "CI_OR_REMOTE_RUNNER",
                "operator_physical_required": host == "OPERATOR_OR_PHYSICAL_RUNTIME",
            },
            "provider_access": normalized_providers,
            "inherited_evidence": normalized_evidence,
            "already_executed_here": bool(lane.get("already_executed_here", False))
            and host == "CURRENT_CHAT_RUNTIME",
        }
    )
    return {
        "execution_environment": host,
        "provider_access": [dict(record) for record in decision.provider_access],
        "required_capabilities": list(decision.required_capabilities),
        "evidence_inputs": [dict(record) for record in decision.evidence_inputs],
    }
