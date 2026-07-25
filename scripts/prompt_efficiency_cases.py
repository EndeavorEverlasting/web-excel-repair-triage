#!/usr/bin/env python3
"""Deterministic prompt/response checks and judge-packet construction."""
from __future__ import annotations
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable
from prompt_efficiency_contracts import PromptEfficiencyEvalError

def _finding(rule_id: str, severity: str, message: str, **metrics: Any) -> dict[str, Any]:
    return {"rule_id": rule_id, "severity": severity, "message": message, **metrics}

def _lines(text: str) -> list[str]:
    return [" ".join(line.lower().split()) for line in text.splitlines() if line.strip()]

def _duplicate_metrics(text: str) -> tuple[int, float]:
    lines = _lines(text)
    if not lines:
        return 0, 0.0
    count = sum(value - 1 for value in Counter(lines).values() if value > 1)
    return count, count / len(lines)

def _signal_groups(text: str, policy: dict[str, Any]) -> list[str]:
    lowered = text.lower()
    return sorted(
        group for group, markers in policy["weak_model_signal_groups"].items()
        if any(str(marker).lower() in lowered for marker in markers)
    )

def evaluate_prompt_code(prompt: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    prompt_id = str(prompt.get("id", ""))
    content = str(prompt.get("copyContent", ""))
    thresholds = policy["deterministic_thresholds"]
    findings: list[dict[str, Any]] = []
    required = (
        "id", "seq", "name", "type", "useWhen", "inspectFirst",
        "expectedOutput", "nextStep", "proofGate", "copyContent",
    )
    missing = [key for key in required if not str(prompt.get(key, "")).strip()]
    if missing:
        findings.append(_finding(
            "missing-required-prompt-metadata", "error",
            f"Empty required metadata: {missing}",
        ))
    if not content.strip():
        findings.append(_finding("empty-copy-content", "error", "Prompt copyContent is empty."))
    chars = len(content)
    tokens = math.ceil(chars / 4) if chars else 0
    duplicates, duplicate_ratio = _duplicate_metrics(content)
    max_line = max((len(line) for line in content.splitlines()), default=0)
    groups = _signal_groups(content, policy)
    checks = (
        (chars > int(thresholds["max_prompt_characters"]), "prompt-character-budget", chars, thresholds["max_prompt_characters"], "Prompt exceeds the character budget."),
        (tokens > int(thresholds["max_approx_prompt_tokens"]), "prompt-token-budget", tokens, thresholds["max_approx_prompt_tokens"], "Prompt exceeds the approximate token budget."),
        (duplicate_ratio > float(thresholds["max_duplicate_line_ratio"]), "duplicate-lines", round(duplicate_ratio, 4), thresholds["max_duplicate_line_ratio"], "Prompt repeats normalized lines beyond the allowed ratio."),
        (max_line > int(thresholds["max_line_characters"]), "oversized-line", max_line, thresholds["max_line_characters"], "Prompt contains an oversized line."),
        (len(groups) < int(thresholds["minimum_weak_model_signal_groups"]), "weak-model-structure", len(groups), thresholds["minimum_weak_model_signal_groups"], "Prompt lacks enough explicit weak-model structure signals."),
    )
    for failed, rule, metric, threshold, message in checks:
        if failed:
            findings.append(_finding(rule, "warning", message, metric=metric, threshold=threshold))
    return {
        "target_kind": "prompt-registry",
        "case_id": f"prompt:{prompt_id}",
        "prompt_id": prompt_id,
        "metrics": {
            "characters": chars,
            "approx_tokens": tokens,
            "nonempty_lines": len(_lines(content)),
            "duplicate_line_count": duplicates,
            "duplicate_line_ratio": round(duplicate_ratio, 4),
            "max_line_characters": max_line,
            "weak_model_signal_groups": groups,
            "weak_model_signal_group_count": len(groups),
        },
        "findings": findings,
        "code_safe": not any(item["severity"] == "error" for item in findings),
        "code_strict_ready": not findings,
    }

def evaluate_response_code(candidate: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    case_id = str(candidate.get("case_id", ""))
    prompt_id = str(candidate.get("prompt_id", ""))
    model_id = str(candidate.get("model_id", ""))
    response = str(candidate.get("response", ""))
    findings: list[dict[str, Any]] = []
    if not case_id or not prompt_id or not model_id:
        findings.append(_finding(
            "missing-response-identity", "error",
            "Candidate response lacks case_id, prompt_id, or model_id.",
        ))
    if not response.strip():
        findings.append(_finding("empty-model-response", "error", "Candidate response is empty."))
    nonempty = [line.strip() for line in response.splitlines() if line.strip()]
    if response.strip() and (not nonempty or not nonempty[0].startswith("OBJECTIVE:")):
        findings.append(_finding(
            "response-objective-canary", "warning",
            "First nonempty response line is not OBJECTIVE:.",
        ))
    if response.strip() and (len(nonempty) < 2 or not nonempty[1].startswith("REPOS:")):
        findings.append(_finding(
            "response-repos-canary", "warning",
            "Second nonempty response line is not REPOS:.",
        ))
    limit = int(policy["deterministic_thresholds"]["max_model_response_characters"])
    if len(response) > limit:
        findings.append(_finding(
            "model-response-character-budget", "warning",
            "Response exceeds the character budget.",
            metric=len(response), threshold=limit,
        ))
    return {
        "target_kind": "model-response",
        "case_id": case_id,
        "prompt_id": prompt_id,
        "model_id": model_id,
        "metrics": {
            "characters": len(response),
            "approx_tokens": math.ceil(len(response) / 4) if response else 0,
        },
        "findings": findings,
        "code_safe": not any(item["severity"] == "error" for item in findings),
        "code_strict_ready": not findings,
    }

def filter_prompts(prompts: list[dict[str, Any]], prompt_id: str | None) -> list[dict[str, Any]]:
    if not prompt_id:
        return prompts
    wanted = prompt_id.upper()
    selected = [prompt for prompt in prompts if str(prompt.get("id", "")).upper() == wanted]
    if not selected:
        raise PromptEfficiencyEvalError(f"unknown prompt ID: {prompt_id}")
    return selected

def build_prompt_cases(
    prompts: Iterable[dict[str, Any]],
    policy: dict[str, Any],
    prompt_id: str | None = None,
) -> list[dict[str, Any]]:
    rubric = policy["rubrics"]["prompt-registry"]
    cases = []
    for prompt in filter_prompts(list(prompts), prompt_id):
        current_id = str(prompt.get("id", ""))
        cases.append({
            "case_id": f"prompt:{current_id}",
            "target_kind": "prompt-registry",
            "prompt_id": current_id,
            "rubric_id": rubric["rubric_id"],
            "target": {key: prompt.get(key) for key in (
                "id", "seq", "name", "type", "class", "sprintRole",
                "useWhen", "inspectFirst", "expectedOutput", "nextStep",
                "proofGate", "keywords", "copyContent",
            )},
            "code_evaluation": evaluate_prompt_code(prompt, policy),
        })
    return cases

def build_response_cases(
    candidates: Iterable[dict[str, Any]],
    prompts: Iterable[dict[str, Any]],
    policy: dict[str, Any],
    prompt_id: str | None = None,
) -> list[dict[str, Any]]:
    selected = filter_prompts(list(prompts), prompt_id)
    prompt_by_id = {str(prompt.get("id", "")).upper(): prompt for prompt in selected}
    rubric = policy["rubrics"]["model-response"]
    cases = []
    for candidate in candidates:
        wanted = str(candidate.get("prompt_id", "")).upper()
        if wanted not in prompt_by_id:
            raise PromptEfficiencyEvalError(
                f"candidate response references unknown prompt ID: {wanted}"
            )
        prompt = prompt_by_id[wanted]
        cases.append({
            "case_id": str(candidate.get("case_id", "")),
            "target_kind": "model-response",
            "prompt_id": str(prompt.get("id", "")),
            "model_id": str(candidate.get("model_id", "")),
            "rubric_id": rubric["rubric_id"],
            "target": {
                "prompt": {key: prompt.get(key) for key in (
                    "id", "name", "type", "useWhen", "expectedOutput",
                    "proofGate", "copyContent",
                )},
                "candidate_response": str(candidate.get("response", "")),
                "expected_objective": candidate.get("expected_objective"),
                "expected_repos": candidate.get("expected_repos"),
            },
            "code_evaluation": evaluate_response_code(candidate, policy),
        })
    return cases

def load_candidate_responses(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise PromptEfficiencyEvalError(f"candidate response file missing: {path}") from exc
    results = []
    for number, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PromptEfficiencyEvalError(
                f"invalid candidate JSONL at line {number}: {exc}"
            ) from exc
        if not isinstance(item, dict):
            raise PromptEfficiencyEvalError(f"candidate line {number} is not an object")
        results.append(item)
    return results

def build_judge_packet_set(cases: list[dict[str, Any]], policy: dict[str, Any]) -> dict[str, Any]:
    used = sorted({case["target_kind"] for case in cases})
    judge = policy["judge"]
    return {
        "schema_version": judge["packet_schema_version"],
        "policy_id": policy["policy_id"],
        "instruction": judge["instruction"],
        "score_scale": judge["score_scale"],
        "result_schema_version": judge["result_schema_version"],
        "rubrics": {kind: policy["rubrics"][kind] for kind in used},
        "case_count": len(cases),
        "passage_mode": "one case at a time in listed order",
        "cases": cases,
    }
