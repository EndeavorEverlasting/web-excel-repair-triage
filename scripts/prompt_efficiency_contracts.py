#!/usr/bin/env python3
"""Contracts and safe I/O for prompt-efficiency evaluation."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "harness/prompt-registry/prompt-efficiency-eval.v1.json"
FIXTURES_PATH = ROOT / "harness/prompt-registry/fixtures/prompt-efficiency-cases.v1.json"
PROTECTED_OUTPUT_ROOTS = (ROOT / "Candidates", ROOT / "Active")

class PromptEfficiencyEvalError(RuntimeError):
    pass

def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PromptEfficiencyEvalError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PromptEfficiencyEvalError(f"invalid JSON in {path}: {exc}") from exc

def validate_output_path(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    for protected in PROTECTED_OUTPUT_ROOTS:
        try:
            resolved.relative_to(protected.resolve())
        except ValueError:
            continue
        raise PromptEfficiencyEvalError(
            f"output path is inside protected input root: {protected.relative_to(ROOT)}"
        )
    return resolved

def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    policy = load_json(path)
    if policy.get("schema_version") != "prompt-efficiency-eval-policy/v1":
        raise PromptEfficiencyEvalError("unsupported prompt-efficiency policy schema")
    if policy.get("policy_id") != "prompt-efficiency-weak-model-readiness":
        raise PromptEfficiencyEvalError("prompt-efficiency policy ID drifted")
    if policy.get("target_kinds") != ["prompt-registry", "model-response"]:
        raise PromptEfficiencyEvalError("prompt-efficiency target kinds drifted")
    thresholds = policy.get("deterministic_thresholds")
    required_thresholds = {
        "max_prompt_characters", "max_approx_prompt_tokens",
        "max_duplicate_line_ratio", "max_line_characters",
        "minimum_weak_model_signal_groups", "max_model_response_characters",
    }
    if not isinstance(thresholds, dict) or not required_thresholds <= set(thresholds):
        raise PromptEfficiencyEvalError("deterministic thresholds are incomplete")
    signals = policy.get("weak_model_signal_groups")
    if not isinstance(signals, dict) or len(signals) < 6 or any(
        not isinstance(values, list) or not values for values in signals.values()
    ):
        raise PromptEfficiencyEvalError("weak-model signal groups are incomplete")
    rubrics = policy.get("rubrics")
    if not isinstance(rubrics, dict) or set(rubrics) != set(policy["target_kinds"]):
        raise PromptEfficiencyEvalError("rubric target coverage drifted")
    for target, rubric in rubrics.items():
        dimensions = rubric.get("dimensions")
        if not isinstance(dimensions, list) or len(dimensions) < 5:
            raise PromptEfficiencyEvalError(f"rubric dimensions incomplete: {target}")
        if len(dimensions) != len(set(dimensions)):
            raise PromptEfficiencyEvalError(f"duplicate rubric dimensions: {target}")
        if not isinstance(rubric.get("required_dimension_floors"), dict):
            raise PromptEfficiencyEvalError(f"rubric floors missing: {target}")
    judge = policy.get("judge")
    if not isinstance(judge, dict) or int(judge.get("minimum_judges_per_case", 0)) < 1:
        raise PromptEfficiencyEvalError("judge contract is incomplete")
    if not str(judge.get("instruction", "")).strip():
        raise PromptEfficiencyEvalError("judge instruction is empty")
    return policy

def load_fixtures(path: Path = FIXTURES_PATH) -> dict[str, Any]:
    payload = load_json(path)
    if payload.get("schema_version") != "prompt-efficiency-fixtures/v1":
        raise PromptEfficiencyEvalError("unsupported prompt-efficiency fixture schema")
    cases = payload.get("cases")
    ids = [str(case.get("id", "")) for case in cases or []]
    if not isinstance(cases, list) or len(cases) < 4:
        raise PromptEfficiencyEvalError("prompt-efficiency fixtures are incomplete")
    if any(not item for item in ids) or len(ids) != len(set(ids)):
        raise PromptEfficiencyEvalError("prompt-efficiency fixture IDs are duplicate")
    return payload

def write_json(payload: dict[str, Any], output: Path) -> Path:
    resolved = validate_output_path(output)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return resolved
