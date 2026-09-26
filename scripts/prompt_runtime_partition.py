#!/usr/bin/env python3
"""Prototype shared runtime-partition seam for P04/P05 planning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


HOSTS = {
    "CURRENT_CHAT_RUNTIME",
    "LOCAL_AGENT_RUNTIME",
    "CI_OR_REMOTE_RUNNER",
    "OPERATOR_OR_PHYSICAL_RUNTIME",
    "UNKNOWN_RUNTIME",
}
AUTHORITY_STATES = {"VERIFIED", "AVAILABLE_UNVERIFIED", "BLOCKED", "UNKNOWN"}
VISIBILITY = {"PUBLIC_TRACKED", "SANITIZED_OPAQUE", "PROTECTED_EXTERNAL"}


class RuntimePartitionError(ValueError):
    pass


@dataclass(frozen=True)
class PartitionDecision:
    work_unit_id: str
    execution_environment: str
    provider_access: tuple[dict[str, Any], ...]
    required_capabilities: tuple[str, ...]
    evidence_inputs: tuple[dict[str, Any], ...]
    execute_now: bool
    already_executed_here: bool


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimePartitionError(f"{label} must be a non-empty string")
    return value.strip()


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise RuntimePartitionError(f"{label} must be an array of non-empty strings")
    return [x.strip() for x in value]


def _validate_provider_access(records: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(records, list):
        raise RuntimePartitionError("provider_access must be an array")
    out: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise RuntimePartitionError(f"provider_access[{index}] must be an object")
        provider_family = _nonempty(record.get("provider_family"), f"provider_access[{index}].provider_family")
        operation = _nonempty(record.get("operation"), f"provider_access[{index}].operation")
        authority_state = record.get("authority_state")
        if authority_state not in AUTHORITY_STATES:
            raise RuntimePartitionError(f"provider_access[{index}].authority_state is invalid")
        mutation_authority = record.get("mutation_authority")
        if not isinstance(mutation_authority, bool):
            raise RuntimePartitionError(f"provider_access[{index}].mutation_authority must be boolean")
        out.append({
            "provider_family": provider_family,
            "operation": operation,
            "authority_state": authority_state,
            "mutation_authority": mutation_authority,
        })
    return tuple(out)


def _validate_evidence(records: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(records, list):
        raise RuntimePartitionError("inherited_evidence must be an array")
    out: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise RuntimePartitionError(f"inherited_evidence[{index}] must be an object")
        evidence_type = _nonempty(record.get("evidence_type"), f"inherited_evidence[{index}].evidence_type")
        source_owner = _nonempty(record.get("source_owner"), f"inherited_evidence[{index}].source_owner")
        sanitized_ref = _nonempty(record.get("sanitized_ref"), f"inherited_evidence[{index}].sanitized_ref")
        revision = _nonempty(record.get("revision_or_freshness"), f"inherited_evidence[{index}].revision_or_freshness")
        visibility = record.get("visibility")
        if visibility not in VISIBILITY:
            raise RuntimePartitionError(f"inherited_evidence[{index}].visibility is invalid")
        proof_ceiling = _nonempty(record.get("proof_ceiling"), f"inherited_evidence[{index}].proof_ceiling")
        lowered = sanitized_ref.lower()
        if visibility == "PROTECTED_EXTERNAL":
            if not sanitized_ref.startswith("opaque:"):
                raise RuntimePartitionError("PROTECTED_EXTERNAL evidence must use an opaque: tracked alias")
            if "http://" in lowered or "https://" in lowered or "docs.google.com" in lowered or "drive.google.com" in lowered:
                raise RuntimePartitionError("PROTECTED_EXTERNAL evidence may not expose a raw provider URL")
        out.append({
            "evidence_type": evidence_type,
            "source_owner": source_owner,
            "sanitized_ref": sanitized_ref,
            "revision_or_freshness": revision,
            "visibility": visibility,
            "proof_ceiling": proof_ceiling,
        })
    return tuple(out)


def partition_work_unit(work_unit: dict[str, Any]) -> PartitionDecision:
    if not isinstance(work_unit, dict):
        raise RuntimePartitionError("work unit must be an object")
    work_unit_id = _nonempty(work_unit.get("work_unit_id"), "work_unit_id")
    required_capabilities = tuple(_string_list(work_unit.get("required_capabilities"), "required_capabilities"))
    facts = work_unit.get("capability_facts")
    if not isinstance(facts, dict):
        raise RuntimePartitionError("capability_facts must be an object")
    keys = (
        "current_runtime_available",
        "current_runtime_authorized",
        "local_runtime_required",
        "ci_remote_required",
        "operator_physical_required",
    )
    for key in keys:
        if not isinstance(facts.get(key), bool):
            raise RuntimePartitionError(f"capability_facts.{key} must be boolean")
    hard = [facts["local_runtime_required"], facts["ci_remote_required"], facts["operator_physical_required"]]
    if sum(bool(x) for x in hard) > 1:
        raise RuntimePartitionError("work unit has conflicting hard host requirements; split it before placement")

    if facts["operator_physical_required"]:
        host = "OPERATOR_OR_PHYSICAL_RUNTIME"
    elif facts["local_runtime_required"]:
        host = "LOCAL_AGENT_RUNTIME"
    elif facts["ci_remote_required"]:
        host = "CI_OR_REMOTE_RUNNER"
    elif facts["current_runtime_available"] and facts["current_runtime_authorized"]:
        host = "CURRENT_CHAT_RUNTIME"
    else:
        host = "UNKNOWN_RUNTIME"

    if host not in HOSTS:
        raise AssertionError(host)
    provider_access = _validate_provider_access(work_unit.get("provider_access"))
    evidence_inputs = _validate_evidence(work_unit.get("inherited_evidence"))
    already_executed = bool(work_unit.get("already_executed_here", False))
    return PartitionDecision(
        work_unit_id=work_unit_id,
        execution_environment=host,
        provider_access=provider_access,
        required_capabilities=required_capabilities,
        evidence_inputs=evidence_inputs,
        execute_now=(host == "CURRENT_CHAT_RUNTIME" and not already_executed),
        already_executed_here=already_executed,
    )


def project_p04(decision: PartitionDecision) -> dict[str, Any]:
    return {
        "execution_environment": decision.execution_environment,
        "provider_access": list(decision.provider_access),
        "required_capabilities": list(decision.required_capabilities),
        "evidence_inputs": list(decision.evidence_inputs),
        "execute_now": decision.execute_now,
    }


def project_p05(decision: PartitionDecision) -> dict[str, Any]:
    return {
        "EXECUTION ENVIRONMENT": decision.execution_environment,
        "PROVIDER / ACCESS ROUTE": list(decision.provider_access),
        "REQUIRED CAPABILITIES": list(decision.required_capabilities),
        "INHERITED EVIDENCE": list(decision.evidence_inputs),
        "ALREADY EXECUTED HERE": decision.already_executed_here,
        "RUNTIME HANDOFF": "none" if decision.already_executed_here else decision.execution_environment,
    }
