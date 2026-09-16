#!/usr/bin/env python3
"""Thin read-only Context Engine adapters for Prompt Compilation Sprint 2.

Consumes owner-native artifacts. Does not own lifecycle events or introduce a bus.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import prompt_language_compiler as compiler

PROFILE_PRECEDENCE = (
    "explicit_run_override",
    "prompt_override",
    "user_default",
    "product_default",
)

PRODUCT_DEFAULT_PROFILE = "exhaustive"

EXHAUSTIVE_PROFILE = {
    "schema_version": "prompt-execution-profile/v1",
    "profile": "exhaustive",
    "compute_policy": "maximize_useful_compute_until_fixed_point",
    "parallel_policy": "dispatch_when_safe_parallel_width_exists",
    "hypothesis_policy": "falsify_material_alternatives",
    "validation_policy": "advance_all_executable_contracts",
    "stop_policy": "evidence_defined_fixed_point",
    "non_weakenable_constraints": sorted(compiler.REQUIRED_NON_WEAKENABLE),
}

EFFICIENT_PROFILE = {
    "schema_version": "prompt-execution-profile/v1",
    "profile": "efficient",
    "compute_policy": "minimum_sufficient_compute",
    "parallel_policy": "parallelize_when_expected_gain_exceeds_coordination_cost",
    "hypothesis_policy": "test_alternatives_only_when_materially_ambiguous",
    "validation_policy": "minimum_authoritative_acceptance_set",
    "stop_policy": "sufficient_proof_for_requested_scope",
    "non_weakenable_constraints": sorted(compiler.REQUIRED_NON_WEAKENABLE),
}

PROFILE_LIBRARY = {
    "exhaustive": EXHAUSTIVE_PROFILE,
    "efficient": EFFICIENT_PROFILE,
}


class ContextEngineError(ValueError):
    """Raised when context projection or profile resolution fails closed."""


def _as_dict(value: Any, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ContextEngineError(f"{label} must be an object when provided")
    return value


def resolve_execution_profile(
    *,
    explicit_run_override: str | None = None,
    prompt_override: str | None = None,
    user_default: str | None = None,
    product_default: str = PRODUCT_DEFAULT_PROFILE,
) -> dict[str, Any]:
    """Resolve compute mode with run > prompt > user > product precedence."""
    candidates = {
        "explicit_run_override": explicit_run_override,
        "prompt_override": prompt_override,
        "user_default": user_default,
        "product_default": product_default,
    }
    chosen_source = "product_default"
    chosen_name = product_default
    for source in PROFILE_PRECEDENCE:
        value = candidates.get(source)
        if isinstance(value, str) and value.strip():
            chosen_source = source
            chosen_name = value.strip().lower()
            break
    if chosen_name not in PROFILE_LIBRARY:
        raise ContextEngineError(f"unknown execution profile: {chosen_name}")
    profile = dict(PROFILE_LIBRARY[chosen_name])
    meta = {
        "resolved_from": chosen_source,
        "precedence": list(PROFILE_PRECEDENCE),
        "profile": chosen_name,
    }
    return {"profile": compiler.validate_profile(profile), "resolution": meta}


def adapt_dispatch_receipt(receipt: dict[str, Any] | None) -> dict[str, Any]:
    """Read-only projection from prompt-parallel-dispatch receipt fields."""
    receipt = _as_dict(receipt, "dispatch_receipt")
    lanes = receipt.get("lanes") if isinstance(receipt.get("lanes"), list) else []
    observed = bool(receipt.get("observed_parallelism"))
    width = int(receipt.get("graph_width") or receipt.get("parallel_width") or len(lanes) or 0)
    safe_capacity = int(receipt.get("safe_capacity") or receipt.get("usable_capacity") or width)
    return {
        "adapter": "dispatch_receipt_read",
        "execution": {
            "parallel_width": max(width, 0),
            "safe_capacity": max(safe_capacity, 0),
            "dependency_ready_width": max(
                int(receipt.get("dependency_ready_width") or width),
                0,
            ),
            "available_capabilities": list(receipt.get("adapters_probed") or receipt.get("capability_rungs") or []),
        },
        "evidence_bits": {
            "dispatch_observed_parallelism": observed,
        },
    }


def adapt_continuation_disposition(disposition: dict[str, Any] | None) -> dict[str, Any]:
    """Read-only projection from Evidence Spine continuation disposition."""
    disposition = _as_dict(disposition, "continuation_disposition")
    open_recovery = disposition.get("disposition") == "recover"
    return {
        "adapter": "continuation_disposition_read",
        "evidence_bits": {
            "open_recovery": open_recovery,
            "continuation_disposition": disposition.get("disposition"),
        },
    }


def adapt_outcome_receipts(receipts: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Read-only projection from P99 outcome receipts (identity only)."""
    if receipts is None:
        receipts = []
    if not isinstance(receipts, list):
        raise ContextEngineError("outcome_receipts must be a list")
    gates: list[str] = []
    for item in receipts:
        if not isinstance(item, dict):
            raise ContextEngineError("outcome receipt must be an object")
        result = item.get("result")
        if result:
            gates.append(f"outcome:{result}")
        classification = item.get("classification") if isinstance(item.get("classification"), dict) else {}
        primary = classification.get("primary")
        if primary:
            gates.append(f"failure_class:{primary}")
    return {
        "adapter": "p99_outcome_receipt_read",
        "evidence_bits": {
            "known_acceptance_gates": sorted(set(gates)),
            "outcome_receipt_count": len(receipts),
        },
    }


def adapt_recurrence_findings(findings: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Read-only projection from recurrence findings."""
    if findings is None:
        findings = []
    if not isinstance(findings, list):
        raise ContextEngineError("recurrence findings must be a list")
    relevant = []
    for item in findings:
        if not isinstance(item, dict):
            raise ContextEngineError("finding must be an object")
        state = item.get("state")
        failure_id = item.get("contract_failure_id")
        if state in {"confirmed_recurrence", "monitoring_reopened", "suspected_recurrence"} and failure_id:
            relevant.append(str(failure_id))
    return {
        "adapter": "recurrence_finding_read",
        "history_bits": {"relevant_recurrences": sorted(set(relevant))},
    }


def project_prompt_context(
    *,
    repository_head: str,
    owned_scope: list[str],
    active_contracts: list[str] | None = None,
    dispatch_receipt: dict[str, Any] | None = None,
    continuation_disposition: dict[str, Any] | None = None,
    outcome_receipts: list[dict[str, Any]] | None = None,
    recurrence_findings: list[dict[str, Any]] | None = None,
    effective_prompt_identity: str | None = None,
) -> dict[str, Any]:
    """Compose a temporary prompt-context/v1 from owner-native artifacts."""
    if not isinstance(repository_head, str) or len(repository_head.strip()) < 7:
        raise ContextEngineError("repository_head must be a git SHA")
    if not isinstance(owned_scope, list) or not owned_scope:
        raise ContextEngineError("owned_scope must be a non-empty list")

    dispatch = adapt_dispatch_receipt(dispatch_receipt)
    continuation = adapt_continuation_disposition(continuation_disposition)
    outcomes = adapt_outcome_receipts(outcome_receipts)
    recurrence = adapt_recurrence_findings(recurrence_findings)

    execution = {
        "available_capabilities": list(dispatch["execution"]["available_capabilities"]),
        "parallel_width": int(dispatch["execution"]["parallel_width"]),
        "safe_capacity": int(dispatch["execution"]["safe_capacity"]),
        "dependency_ready_width": int(dispatch["execution"]["dependency_ready_width"]),
    }
    gates = list(outcomes["evidence_bits"]["known_acceptance_gates"])
    if dispatch["evidence_bits"].get("dispatch_observed_parallelism"):
        gates.append("observed_parallelism")
    open_recovery = bool(continuation["evidence_bits"].get("open_recovery"))

    context = {
        "schema_version": "prompt-context/v1",
        "repository": {
            "head": repository_head.strip(),
            "active_contracts": list(active_contracts or []),
            "owned_scope": list(owned_scope),
        },
        "execution": execution,
        "history": {
            "relevant_recurrences": list(recurrence["history_bits"]["relevant_recurrences"]),
        },
        "evidence": {
            "open_recovery": open_recovery,
            "known_acceptance_gates": sorted(set(gates)),
            "effective_prompt_identity": effective_prompt_identity,
        },
        "source_adapters": [
            dispatch["adapter"],
            continuation["adapter"],
            outcomes["adapter"],
            recurrence["adapter"],
        ],
    }
    # Fail closed if adapters accidentally introduced event ownership fields.
    return compiler.validate_context(context)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    resolve_cmd = sub.add_parser("resolve-profile", help="Resolve execution profile by precedence")
    resolve_cmd.add_argument("--run-override")
    resolve_cmd.add_argument("--prompt-override")
    resolve_cmd.add_argument("--user-default")
    resolve_cmd.add_argument("--product-default", default=PRODUCT_DEFAULT_PROFILE)
    resolve_cmd.add_argument("--summary", action="store_true")

    project_cmd = sub.add_parser("project-context", help="Project owner artifacts into prompt-context/v1")
    project_cmd.add_argument("--repository-head", required=True)
    project_cmd.add_argument("--owned-scope", action="append", required=True)
    project_cmd.add_argument("--active-contract", action="append", default=[])
    project_cmd.add_argument("--dispatch-receipt", type=Path)
    project_cmd.add_argument("--continuation", type=Path)
    project_cmd.add_argument("--outcome-receipts", type=Path)
    project_cmd.add_argument("--recurrence-findings", type=Path)
    project_cmd.add_argument("--effective-prompt-identity")
    project_cmd.add_argument("--output", type=Path)
    project_cmd.add_argument("--summary", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "resolve-profile":
            result = resolve_execution_profile(
                explicit_run_override=args.run_override,
                prompt_override=args.prompt_override,
                user_default=args.user_default,
                product_default=args.product_default,
            )
            print(json.dumps(result if args.summary else result["resolution"], indent=2))
            return 0
        if args.command == "project-context":
            dispatch = compiler.load_json(args.dispatch_receipt) if args.dispatch_receipt else None
            continuation = compiler.load_json(args.continuation) if args.continuation else None
            outcomes = compiler.load_json(args.outcome_receipts) if args.outcome_receipts else []
            findings = compiler.load_json(args.recurrence_findings) if args.recurrence_findings else []
            if args.outcome_receipts and not isinstance(outcomes, list):
                raise ContextEngineError("outcome-receipts JSON must be an array")
            if args.recurrence_findings and not isinstance(findings, list):
                raise ContextEngineError("recurrence-findings JSON must be an array")
            context = project_prompt_context(
                repository_head=args.repository_head,
                owned_scope=args.owned_scope,
                active_contracts=args.active_contract,
                dispatch_receipt=dispatch,
                continuation_disposition=continuation,
                outcome_receipts=outcomes,
                recurrence_findings=findings,
                effective_prompt_identity=args.effective_prompt_identity,
            )
            if args.output:
                args.output.write_text(json.dumps(context, indent=2) + "\n", encoding="utf-8")
            if args.summary or not args.output:
                print(json.dumps(context, indent=2))
            return 0
        parser.error(f"unknown command: {args.command}")
        return 2
    except (ContextEngineError, compiler.PromptCompilationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
