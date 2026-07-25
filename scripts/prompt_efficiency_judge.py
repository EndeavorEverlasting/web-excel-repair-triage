#!/usr/bin/env python3
"""Judge-result validation, aggregation, and eval reporting."""
from __future__ import annotations
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from prompt_efficiency_contracts import PromptEfficiencyEvalError

def load_judge_results(path: Path) -> list[dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise PromptEfficiencyEvalError(f"judge result file missing: {path}") from exc
    if path.suffix.lower() == ".jsonl":
        results = []
        for number, raw in enumerate(text.splitlines(), 1):
            if not raw.strip():
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise PromptEfficiencyEvalError(
                    f"invalid judge JSONL at line {number}: {exc}"
                ) from exc
            if not isinstance(item, dict):
                raise PromptEfficiencyEvalError(
                    f"judge result line {number} is not an object"
                )
            results.append(item)
        return results
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PromptEfficiencyEvalError(f"invalid judge JSON: {exc}") from exc
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return payload["results"]
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]
    raise PromptEfficiencyEvalError(
        "judge result payload must be an object, list, or {results: []}"
    )

def _score_pass(scores: dict[str, float], rubric: dict[str, Any]) -> bool:
    if not scores or statistics.mean(scores.values()) < float(rubric["average_score_minimum"]):
        return False
    if any(score < float(rubric["dimension_floor"]) for score in scores.values()):
        return False
    return all(
        scores.get(dimension, -1) >= float(floor)
        for dimension, floor in rubric["required_dimension_floors"].items()
    )

def validate_and_aggregate_judge_results(
    results: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    policy: dict[str, Any],
) -> dict[str, Any]:
    case_by_id = {str(case["case_id"]): case for case in cases}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    judge = policy["judge"]
    for raw in results:
        if raw.get("schema_version") != judge["result_schema_version"]:
            raise PromptEfficiencyEvalError("judge result schema drifted")
        case_id = str(raw.get("case_id", ""))
        judge_id = str(raw.get("judge_id", ""))
        if case_id not in case_by_id:
            raise PromptEfficiencyEvalError(
                f"judge result references unknown case: {case_id}"
            )
        if not judge_id or (case_id, judge_id) in seen:
            raise PromptEfficiencyEvalError(
                f"missing or duplicate judge result: {case_id} / {judge_id}"
            )
        seen.add((case_id, judge_id))
        case = case_by_id[case_id]
        if raw.get("target_kind") != case["target_kind"]:
            raise PromptEfficiencyEvalError(f"judge target kind drifted: {case_id}")
        if raw.get("rubric_id") != case["rubric_id"]:
            raise PromptEfficiencyEvalError(f"judge rubric drifted: {case_id}")
        if raw.get("verdict") not in judge["allowed_verdicts"]:
            raise PromptEfficiencyEvalError(f"unsupported judge verdict: {case_id}")
        rubric = policy["rubrics"][case["target_kind"]]
        scores = raw.get("scores")
        if not isinstance(scores, dict) or set(scores) != set(rubric["dimensions"]):
            raise PromptEfficiencyEvalError(
                f"judge score dimensions drifted: {case_id}"
            )
        normalized = {}
        for dimension, value in scores.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise PromptEfficiencyEvalError(
                    f"judge score is not numeric: {case_id} / {dimension}"
                )
            if not 0 <= float(value) <= 4:
                raise PromptEfficiencyEvalError(
                    f"judge score outside 0..4: {case_id} / {dimension}"
                )
            normalized[dimension] = float(value)
        if not isinstance(raw.get("findings"), list):
            raise PromptEfficiencyEvalError(
                f"judge findings must be a list: {case_id}"
            )
        item = dict(raw)
        item["scores"] = normalized
        grouped[case_id].append(item)
    minimum = int(judge["minimum_judges_per_case"])
    summaries = []
    complete_count = 0
    pass_count = 0
    for case in cases:
        case_id = str(case["case_id"])
        items = grouped.get(case_id, [])
        complete = len(items) >= minimum
        complete_count += int(complete)
        rubric = policy["rubrics"][case["target_kind"]]
        aggregate = {
            dimension: round(float(statistics.median(
                item["scores"][dimension] for item in items
            )), 3)
            for dimension in rubric["dimensions"]
        } if items else {}
        passed = bool(
            complete
            and _score_pass(aggregate, rubric)
            and all(item["verdict"] == "pass" for item in items)
        )
        pass_count += int(passed)
        summaries.append({
            "case_id": case_id,
            "target_kind": case["target_kind"],
            "judge_count": len(items),
            "complete": complete,
            "aggregate_scores": aggregate,
            "judge_pass": passed,
            "verdicts": [item["verdict"] for item in items],
            "findings": [
                finding for item in items for finding in item["findings"]
            ],
        })
    return {
        "provided": bool(results),
        "result_count": len(results),
        "minimum_judges_per_case": minimum,
        "complete_case_count": complete_count,
        "pass_case_count": pass_count,
        "coverage_complete": complete_count == len(cases),
        "all_cases_pass": pass_count == len(cases) and bool(cases),
        "cases": summaries,
    }

def build_report(
    cases: list[dict[str, Any]],
    policy: dict[str, Any],
    *,
    judge_results: list[dict[str, Any]] | None = None,
    strict: bool = False,
) -> dict[str, Any]:
    findings = [
        dict(item, case_id=case["case_id"], target_kind=case["target_kind"])
        for case in cases
        for item in case["code_evaluation"]["findings"]
    ]
    errors = sum(item["severity"] == "error" for item in findings)
    warnings = sum(item["severity"] == "warning" for item in findings)
    judge = validate_and_aggregate_judge_results(
        judge_results or [], cases, policy
    )
    strict_ready = bool(
        errors == 0
        and warnings == 0
        and judge["coverage_complete"]
        and judge["all_cases_pass"]
    )
    return {
        "schema_version": "prompt-efficiency-eval-result/v1",
        "policy_id": policy["policy_id"],
        "strict": strict,
        "case_count": len(cases),
        "target_counts": dict(sorted(
            Counter(case["target_kind"] for case in cases).items()
        )),
        "code": {
            "safe": errors == 0,
            "strict_ready": errors == 0 and warnings == 0,
            "error_count": errors,
            "warning_count": warnings,
            "findings": findings,
        },
        "judge": judge,
        "strict_ready": strict_ready,
        "cases": cases,
        "proof_ceiling": policy["proof_ceiling"],
    }

def print_summary(
    report: dict[str, Any],
    *,
    output: Path | None = None,
    packets: Path | None = None,
) -> None:
    print("Prompt Efficiency Evaluation")
    print("=" * 28)
    print(f"Cases: {report['case_count']}")
    print(f"Targets: {report['target_counts']}")
    print(
        "Code findings: "
        f"{report['code']['error_count']} errors, "
        f"{report['code']['warning_count']} warnings"
    )
    print(f"Code strict ready: {report['code']['strict_ready']}")
    print(
        "Judge coverage: "
        f"{report['judge']['complete_case_count']} / {report['case_count']}"
    )
    print(
        "Judge pass: "
        f"{report['judge']['pass_case_count']} / {report['case_count']}"
    )
    print(f"Strict ready: {report['strict_ready']}")
    if output:
        print(f"Report: {output}")
    if packets:
        print(f"Judge packets: {packets}")
