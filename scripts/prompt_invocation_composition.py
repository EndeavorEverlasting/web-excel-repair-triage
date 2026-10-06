#!/usr/bin/env python3
"""Deterministically compose explicit Prompt Kit invocations."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "harness/contracts/prompt-invocation-composition.v1.json"


class CompositionError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CompositionError(f"{path} must contain a JSON object")
    return value


def _prompt_number(prompt_id: str) -> int:
    match = re.fullmatch(r"P(\d+)", prompt_id)
    if not match:
        raise CompositionError(f"invalid prompt id: {prompt_id}")
    return int(match.group(1))


def _pair_rule(contract: dict[str, Any], left: str, right: str) -> dict[str, Any] | None:
    wanted = {left, right}
    for rule in contract.get("pair_rules", []):
        if set(rule.get("prompts", [])) == wanted:
            return rule
    return None


def _stable_toposort(nodes: set[str], edges: set[tuple[str, str]]) -> list[str]:
    incoming = {node: set() for node in nodes}
    outgoing = {node: set() for node in nodes}
    for left, right in edges:
        if left not in nodes or right not in nodes:
            continue
        outgoing[left].add(right)
        incoming[right].add(left)
    ready = sorted((n for n in nodes if not incoming[n]), key=_prompt_number)
    result: list[str] = []
    while ready:
        node = ready.pop(0)
        result.append(node)
        for target in sorted(outgoing[node], key=_prompt_number):
            incoming[target].discard(node)
            if not incoming[target] and target not in result and target not in ready:
                ready.append(target)
                ready.sort(key=_prompt_number)
    if len(result) != len(nodes):
        raise CompositionError("precedence graph contains a cycle")
    return result


def _canonical_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _receipt(
    state: str,
    invocations: list[str],
    task_set: set[str],
    edges: list[tuple[str, str]],
    projected: dict[str, set[str]],
    residual: dict[str, set[str]],
    inherited: dict[str, set[str]],
    suppressed: list[dict[str, Any]],
    pushback: list[dict[str, Any]],
    contract: dict[str, Any],
    *,
    linearization: list[str] | None = None,
) -> dict[str, Any]:
    order = linearization or []
    selected = [
        {
            "prompt_id": pid,
            "projected_facets": sorted(projected[pid]),
            "residual_facets": sorted(residual.get(pid, set())),
            "inherited_facets": sorted(inherited.get(pid, set())),
        }
        for pid in order
    ]
    result = {
        "schema_version": "prompt-invocation-composition-receipt/v1",
        "state": state,
        "requested_invocations": list(invocations),
        "task_facets": sorted(task_set),
        "linearization": order,
        "precedence_edges": [list(x) for x in edges],
        "selected": selected,
        "suppressed": suppressed,
        "pushback": pushback,
        "authority_effect": "NO_AUTHORITY_EXPANSION",
        "authority_rule": contract["mathematical_model"]["authority_source_invariant"],
        "proof_ceiling": contract["proof_ceiling"],
    }
    result["composition_sha256"] = _canonical_hash(result)
    return result


def compose(request: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    if request.get("schema_version") != "prompt-invocation-request/v1":
        raise CompositionError("schema_version must be prompt-invocation-request/v1")
    invocations = request.get("invocations")
    task_facets = request.get("task_facets")
    facts = request.get("facts", {})
    explicit_precedence = request.get("explicit_precedence", [])
    if not isinstance(invocations, list) or not invocations or any(not isinstance(x, str) for x in invocations):
        raise CompositionError("invocations must be a non-empty array of prompt ids")
    if len(set(invocations)) != len(invocations):
        raise CompositionError("invocations must not contain duplicate prompt ids")
    if not isinstance(task_facets, list) or not task_facets or any(not isinstance(x, str) or not x for x in task_facets):
        raise CompositionError("task_facets must be a non-empty array of strings")
    if not isinstance(facts, dict):
        raise CompositionError("facts must be an object")
    if not isinstance(explicit_precedence, list):
        raise CompositionError("explicit_precedence must be an array")

    facet_map = contract.get("prompt_facets")
    if not isinstance(facet_map, dict):
        raise CompositionError("contract prompt_facets must be an object")

    task_set = set(task_facets)
    projected: dict[str, set[str]] = {}
    suppressed: list[dict[str, Any]] = []
    for prompt_id in invocations:
        facets = facet_map.get(prompt_id)
        if not isinstance(facets, list):
            raise CompositionError(f"prompt {prompt_id} has no declared invocation facets")
        applicable = set(facets) & task_set
        if applicable:
            projected[prompt_id] = applicable
        else:
            suppressed.append({
                "prompt_id": prompt_id,
                "state": "INVOKED_NO_APPLICABLE_RESIDUAL",
                "reason": "none of the prompt's declared facets intersect task_facets",
            })

    if not projected:
        return _receipt(
            "NO_APPLICABLE_FACETS", invocations, task_set, [], {}, {}, {},
            suppressed, [], contract
        )

    edges: set[tuple[str, str]] = set()
    pushback: list[dict[str, Any]] = []
    inherited: dict[str, set[str]] = {p: set() for p in projected}
    residual: dict[str, set[str]] = {p: set(v) for p, v in projected.items()}

    if "P05" in projected:
        state = facts.get("p04_factoring_artifact_state")
        allowed = {"ABSENT", "ACCEPTED_CURRENT", "STALE", "CONTRADICTED"}
        if state not in allowed:
            return _receipt(
                "INSUFFICIENT_CONTEXT", invocations, task_set, [], projected,
                residual, inherited, suppressed,
                [{"code": "P04_ARTIFACT_STATE_REQUIRED", "route": "SUPPLY_TYPED_FACT"}],
                contract,
            )

        shared_facet = "planning.runtime_partition"
        if state == "ACCEPTED_CURRENT":
            if shared_facet in projected["P05"]:
                inherited["P05"].add(shared_facet)
                residual["P05"].discard(shared_facet)
            if "P04" in projected and shared_facet in projected["P04"]:
                inherited["P04"].add(shared_facet)
                residual["P04"].discard(shared_facet)
            pushback.append({
                "code": "P05_CONSUME_P04_ARTIFACT",
                "state": state,
                "message": "Consume the accepted current P04 factoring artifact; do not recompute its accepted overlap.",
            })
        elif "planning.factor" in task_set:
            if "P04" not in projected:
                p04_facets = set(facet_map["P04"]) & task_set
                if not p04_facets:
                    raise CompositionError("planning.factor requires a projected P04 facet")
                projected["P04"] = p04_facets
                residual["P04"] = set(p04_facets)
                inherited["P04"] = set()
            edges.add(("P04", "P05"))
            shared = projected["P04"] & projected["P05"] & {shared_facet}
            inherited["P05"].update(shared)
            residual["P05"].difference_update(shared)
            pushback.append({
                "code": "ROUTE_P04_THEN_P05",
                "state": state,
                "message": "The task explicitly requires full factoring, so P04 owns that prerequisite before P05 packing.",
            })
        else:
            # Canonical P05 owns bounded recovery factoring when no usable
            # P04 artifact exists. Do not steal that fallback by routing to P04.
            if "P04" in projected:
                shared = projected["P04"] & projected["P05"] & {shared_facet}
                inherited["P04"].update(shared)
                residual["P04"].difference_update(shared)
            pushback.append({
                "code": "P05_BOUNDED_RECOVERY_FACTORING",
                "state": state,
                "message": "No usable P04 artifact exists; preserve P05's canonical bounded recovery factoring authority.",
            })

    active = set(projected)
    active_list = sorted(active, key=_prompt_number)
    for index, left in enumerate(active_list):
        for right in active_list[index + 1:]:
            overlap = projected[left] & projected[right]
            if not overlap:
                continue
            rule = _pair_rule(contract, left, right)
            if rule is None:
                return _receipt(
                    "INCOHERENT_INVOCATION", invocations, task_set, [], projected,
                    residual, inherited, suppressed,
                    pushback + [{
                        "code": "UNRESOLVED_OVERLAP",
                        "prompts": [left, right],
                        "facets": sorted(overlap),
                    }],
                    contract,
                )
            declared_shared = set(rule.get("shared_facets", []))
            uncovered_overlap = overlap - declared_shared
            if uncovered_overlap:
                return _receipt(
                    "INCOHERENT_INVOCATION", invocations, task_set, [], projected,
                    residual, inherited, suppressed,
                    pushback + [{
                        "code": "UNDECLARED_PAIR_OVERLAP",
                        "prompts": [left, right],
                        "facets": sorted(uncovered_overlap),
                    }],
                    contract,
                )
            relation = rule.get("relation")
            if relation == "CONFLICT":
                return _receipt(
                    "INCOHERENT_INVOCATION", invocations, task_set, [], projected,
                    residual, inherited, suppressed,
                    pushback + [{
                        "code": "DECLARED_CONFLICT",
                        "prompts": [left, right],
                        "facets": sorted(overlap),
                    }],
                    contract,
                )
            if relation == "DUPLICATE":
                owner = rule.get("canonical_prompt_owner")
                if owner not in {left, right}:
                    raise CompositionError(f"duplicate rule for {left}/{right} lacks canonical_prompt_owner")
                loser = right if owner == left else left
                residual[loser].difference_update(overlap)
                inherited[loser].update(overlap)
            elif relation == "ORDERED_OVERLAP":
                before = rule.get("before")
                after = rule.get("after")
                if before and after:
                    edges.add((before, after))
            elif relation == "CONSTRAINING_OVERLAP":
                pass
            elif relation != "DISJOINT":
                raise CompositionError(f"unsupported relation {relation!r}")

    # An invoked prompt whose applicable contribution is fully satisfied by
    # canonicalized overlap has no executable residual. Preserve the fact in
    # the receipt, but do not execute it merely because it was named.
    fully_residualized = sorted(
        (p for p in active if not residual.get(p)),
        key=_prompt_number,
    )
    for prompt_id in fully_residualized:
        suppressed.append({
            "prompt_id": prompt_id,
            "state": "INVOKED_NO_APPLICABLE_RESIDUAL",
            "reason": "all applicable facets were satisfied by canonicalized overlap",
            "inherited_facets": sorted(inherited.get(prompt_id, set())),
        })
        active.remove(prompt_id)

    for edge in contract.get("lifecycle_edges", []):
        left, right = edge.get("from"), edge.get("to")
        required = set(edge.get("when_facets", []))
        if left in active and right in active and required <= task_set:
            edges.add((left, right))

    for row in explicit_precedence:
        if not isinstance(row, list) or len(row) != 2 or any(not isinstance(x, str) for x in row):
            raise CompositionError("explicit_precedence rows must be [before, after]")
        if row[0] in active and row[1] in active:
            edges.add((row[0], row[1]))

    try:
        linearization = _stable_toposort(active, edges)
    except CompositionError:
        return _receipt(
            "INCOHERENT_INVOCATION", invocations, task_set, sorted(edges),
            projected, residual, inherited, suppressed,
            pushback + [{"code": "PRECEDENCE_CYCLE"}],
            contract,
        )

    state = "ROUTE_REQUIRED" if any(x.get("code") == "ROUTE_P04_THEN_P05" for x in pushback) else "COMPOSED"
    return _receipt(
        state, invocations, task_set, sorted(edges), projected, residual,
        inherited, suppressed, pushback, contract, linearization=linearization,
    )


def _read_request(location: str) -> dict[str, Any]:
    raw = sys.stdin.read() if location == "-" else Path(location).read_text(encoding="utf-8")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise CompositionError("request input must be a JSON object")
    return value


def validate_contract(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if contract.get("schema_version") != "prompt-invocation-composition/v1":
        errors.append("schema_version mismatch")

    relation_kinds = contract.get("relation_kinds")
    if not isinstance(relation_kinds, dict) or not relation_kinds:
        errors.append("relation_kinds must be a non-empty object")

    mathematical_model = contract.get("mathematical_model")
    if not isinstance(mathematical_model, dict):
        errors.append("mathematical_model must be an object")
    elif not isinstance(mathematical_model.get("authority_source_invariant"), str) or not mathematical_model.get("authority_source_invariant", "").strip():
        errors.append("mathematical_model.authority_source_invariant must be a non-empty string")

    if not isinstance(contract.get("proof_ceiling"), str) or not contract.get("proof_ceiling", "").strip():
        errors.append("proof_ceiling must be a non-empty string")

    prompt_facets = contract.get("prompt_facets")
    if not isinstance(prompt_facets, dict) or not prompt_facets:
        errors.append("prompt_facets must be a non-empty object")
        prompt_facets = {}

    for pid, facets in prompt_facets.items():
        try:
            _prompt_number(pid)
        except CompositionError as exc:
            errors.append(str(exc))
        if not isinstance(facets, list) or not facets or len(facets) != len(set(facets)):
            errors.append(f"{pid} facets must be a non-empty unique list")

    for rule in contract.get("pair_rules", []):
        rule_id = rule.get("id")
        prompts = rule.get("prompts")
        if not isinstance(prompts, list) or len(prompts) != 2:
            errors.append(f"pair rule {rule_id} must name exactly two prompts")
            continue
        if any(prompt_id not in prompt_facets for prompt_id in prompts):
            errors.append(f"pair rule {rule_id} references an unknown prompt")
        if rule.get("relation") not in (relation_kinds or {}):
            errors.append(f"pair rule {rule_id} relation is unsupported")
        shared = rule.get("shared_facets")
        if not isinstance(shared, list) or not shared or len(shared) != len(set(shared)):
            errors.append(f"pair rule {rule_id} shared_facets must be a non-empty unique list")
        elif all(prompt_id in prompt_facets for prompt_id in prompts):
            common = set(prompt_facets[prompts[0]]) & set(prompt_facets[prompts[1]])
            if not set(shared) <= common:
                errors.append(f"pair rule {rule_id} declares facets not shared by both prompts")

    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate-contract")
    validate.add_argument("--summary", action="store_true")
    compile_cmd = sub.add_parser("compose")
    compile_cmd.add_argument("--input", required=True, help="request JSON path or - for stdin")
    args = parser.parse_args(argv)

    try:
        contract = _load_json(args.contract)
        errors = validate_contract(contract)
        if errors:
            for error in errors:
                print(f"FAIL {error}", file=sys.stderr)
            return 2
        if args.command == "validate-contract":
            if args.summary:
                print(json.dumps({
                    "state": "PASS",
                    "contract": contract["contract_id"],
                    "prompt_count": len(contract["prompt_facets"]),
                    "pair_rule_count": len(contract["pair_rules"]),
                    "prior_art_count": len(contract.get("p97_prior_art", [])),
                }, sort_keys=True))
            else:
                print("PASS")
            return 0
        receipt = compose(_read_request(args.input), contract)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0 if receipt["state"] in {"COMPOSED", "ROUTE_REQUIRED", "NO_APPLICABLE_FACETS"} else 2
    except (OSError, UnicodeError, json.JSONDecodeError, CompositionError) as exc:
        print(f"prompt-invocation-composition error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
