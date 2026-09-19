#!/usr/bin/env python3
"""Evaluate typed delivery-signoff routing predicates with deny precedence."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "triggers" / "delivery-signoff-generation.json"


def _predicate_matches(predicate: dict[str, Any], request: dict[str, Any]) -> bool:
    field = predicate.get("field")
    operator = predicate.get("operator")
    actual = request.get(field, "")
    if operator == "equals":
        return actual == predicate.get("value")
    if operator == "not_equals":
        return actual != predicate.get("value")
    if operator == "equals_any":
        return actual in predicate.get("values", [])
    if operator == "contains_any":
        if not isinstance(actual, str):
            return False
        lowered = actual.casefold()
        return any(isinstance(value, str) and value.casefold() in lowered for value in predicate.get("values", []))
    raise ValueError(f"unsupported trigger operator: {operator}")


def _rule_matches(rule: dict[str, Any], request: dict[str, Any]) -> bool:
    predicates = rule.get("predicates", [])
    mode = rule.get("match", "all")
    if not isinstance(predicates, list) or not predicates:
        return False
    results = [_predicate_matches(predicate, request) for predicate in predicates]
    if mode == "all":
        return all(results)
    if mode == "any":
        return any(results)
    raise ValueError(f"unsupported trigger match mode: {mode}")


def evaluate_trigger(config: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    if config.get("schema") != "triage-trigger/v1":
        raise ValueError("trigger schema must be triage-trigger/v1")
    evaluation = config.get("evaluation", {})
    if evaluation.get("predicate_schema") != "triage-trigger-predicate/v1":
        raise ValueError("trigger predicate schema must be triage-trigger-predicate/v1")
    ordered_sets = [
        ("deny", config.get("deny_rules", [])),
        ("allow", config.get("allow_rules", [])),
    ]
    if evaluation.get("deny_precedence") is not True:
        ordered_sets.reverse()
    for rule_class, rules in ordered_sets:
        if not isinstance(rules, list):
            raise ValueError(f"{rule_class}_rules must be a list")
        for rule in rules:
            if not isinstance(rule, dict):
                raise ValueError(f"{rule_class} rule must be an object")
            if _rule_matches(rule, request):
                route_name = rule.get("route")
                routes = config.get("routes", {})
                if route_name not in routes:
                    raise ValueError(f"trigger route is not registered: {route_name}")
                return {
                    "schema": "triage-trigger-decision/v1",
                    "decision": rule_class,
                    "rule_id": rule.get("id"),
                    "route": route_name,
                    "target": routes[route_name],
                }
    return {
        "schema": "triage-trigger-decision/v1",
        "decision": evaluation.get("default_decision", "no_match"),
        "rule_id": None,
        "route": None,
        "target": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("request", type=Path, help="JSON routing request")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        request = json.loads(args.request.read_text(encoding="utf-8"))
        result = evaluate_trigger(config, request)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: trigger evaluation: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
