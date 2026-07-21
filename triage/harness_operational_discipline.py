"""Validate portable operational harness discipline and run context."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping, Optional, Sequence

DEFAULT_POLICY_PATH = Path(__file__).parents[1] / "configs/harness/operational_discipline_v1.json"
DEFAULT_MANIFEST_PATH = Path(__file__).parents[1] / "configs/harness/harness_manifest_v1.json"
_REQUIRED_HARNESS_COMPONENTS = (
    "repo_agent_rules", "codebase_map", "workflow_specs", "run_context", "artifact_registry",
    "validators", "local_hooks_where_useful", "scoped_skills", "read_only_code_intelligence_where_useful",
    "english_operator_reports", "final_handoff_compression",
)
_REQUIRED_MANIFEST_FIELDS = (
    "entrypoint", "agent_rules", "codebase_map", "workflow_specs", "run_context", "artifact_registry",
    "validators", "local_hooks", "scoped_skills", "read_only_code_intelligence", "operator_reports",
    "final_handoff_compression", "generated_output_policy",
)
_REQUIRED_CONTEXT = (
    "repo", "branch_or_worktree", "pr_or_sprint", "lane", "owned_scope", "forbidden_scope", "expected_artifacts"
)
_EXPECTED_LOOP = (
    "request", "evidence_review", "bounded_decision", "repo_git_github_mutation", "artifacts", "validation", "report", "next_decision"
)
_EXPECTED_PROMPTS = {
    "P03": "unknown repo intake and first action",
    "P06": "repo and PR cleanup",
    "P07": "general implementation",
    "P14": "broken PR",
    "P15": "merge or release",
    "P20": "selected Opportunity_Discovery row",
    "P12": "closeout",
}


def load_policy(path: str | Path = DEFAULT_POLICY_PATH) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("harness policy must be one JSON object")
    return payload


def validate_policy(policy: Mapping[str, object]) -> tuple[str, ...]:
    issues: list[str] = []
    if policy.get("schema_version") != 1:
        issues.append("schema_version must be 1")
    if policy.get("policy_id") != "portable-operational-harness-discipline":
        issues.append("policy_id drift")
    if policy.get("portable") is not True:
        issues.append("policy must remain portable")
    if tuple(policy.get("required_context_fields", ())) != _REQUIRED_CONTEXT:
        issues.append("required context fields drift")
    conditional = policy.get("conditional_context_fields")
    if not isinstance(conditional, Mapping) or "validation_order" not in conditional:
        issues.append("validation_order conditional requirement missing")
    if tuple(policy.get("operational_loop", ())) != _EXPECTED_LOOP:
        issues.append("executable operational loop drift")
    if policy.get("evidence_before_confidence") is not True:
        issues.append("evidence-before-confidence must be true")
    if tuple(policy.get("required_harness_components", ())) != _REQUIRED_HARNESS_COMPONENTS:
        issues.append("required harness component inventory drift")
    fallback = policy.get("connected_mutation_fallback")
    if not isinstance(fallback, Mapping):
        issues.append("connected mutation fallback missing")
    else:
        if fallback.get("mutation_surface") != "connected GitHub branch":
            issues.append("connected GitHub mutation surface drift")
        if fallback.get("local_reconstruction") != "only relevant generator, validator, and test files":
            issues.append("bounded local reconstruction rule drift")
    artifact = policy.get("artifact_policy")
    prompt_library = artifact.get("prompt_library") if isinstance(artifact, Mapping) else None
    if not isinstance(prompt_library, Mapping):
        issues.append("Prompt Library artifact policy missing")
    else:
        if prompt_library.get("whole_row_link_columns") != "B:O":
            issues.append("Prompt Library whole-row link columns must be B:O")
        if prompt_library.get("sparse_navigation_columns") != ["A", "P"]:
            issues.append("Prompt Library sparse navigation columns must be A and P")
        if prompt_library.get("allowed_sparse_cadences") != [10, 5, 2]:
            issues.append("sparse navigation cadences must be 10, 5, 2")
        if prompt_library.get("cadence_selection") != "largest evenly dividing cadence":
            issues.append("sparse navigation cadence selection drift")
    if policy.get("sequential_prompt_suite") != _EXPECTED_PROMPTS:
        issues.append("sequential prompt suite drift")
    if policy.get("task_specific_rules_override_generic_closeout") is not True:
        issues.append("task-specific closeout override missing")
    forbidden = set(policy.get("forbidden_substitutions", ()))
    for required in ("plan_only_for_requested_repo_work", "handoff_only_for_requested_repo_work", "acknowledgment_only_completion"):
        if required not in forbidden:
            issues.append(f"forbidden substitution missing: {required}")
    return tuple(issues)



def load_manifest(path: str | Path = DEFAULT_MANIFEST_PATH) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("harness manifest must be one JSON object")
    return payload


def _manifest_paths(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return tuple(value)
    return ()


def validate_repository(repo_root: str | Path, manifest_path: str | Path | None = None) -> tuple[str, ...]:
    root = Path(repo_root).resolve()
    path = Path(manifest_path).resolve() if manifest_path else root / "configs/harness/harness_manifest_v1.json"
    issues: list[str] = []
    try:
        manifest = load_manifest(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return (f"harness manifest unreadable: {exc}",)
    if manifest.get("schema_version") != 1:
        issues.append("harness manifest schema_version must be 1")
    if manifest.get("harness_id") != "web-excel-repair-triage-repo-harness":
        issues.append("harness manifest id drift")
    for field in _REQUIRED_MANIFEST_FIELDS:
        paths = _manifest_paths(manifest.get(field))
        if not paths:
            issues.append(f"harness manifest field missing or invalid: {field}")
            continue
        for relative in paths:
            if not (root / relative).exists():
                issues.append(f"harness surface missing: {relative}")
    sequence = manifest.get("required_fresh_agent_sequence")
    if not isinstance(sequence, list) or sequence[:4] != [
        "read_agent_rules", "read_harness_manifest", "load_run_context", "select_workflow"
    ]:
        issues.append("fresh-agent entry sequence drift")
    return tuple(issues)

def validate_run_context(context: Mapping[str, object], *, validation_order_specified: bool = False) -> tuple[str, ...]:
    issues = [f"missing or blank context field: {field}" for field in _REQUIRED_CONTEXT if not str(context.get(field, "")).strip()]
    if validation_order_specified and not str(context.get("validation_order", "")).strip():
        issues.append("missing or blank context field: validation_order")
    return tuple(issues)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY_PATH)
    parser.add_argument("--context", type=Path)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--validation-order-specified", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        policy = load_policy(args.policy)
        issues = list(validate_policy(policy))
        if args.repo_root:
            issues.extend(validate_repository(args.repo_root, args.manifest))
        if args.context:
            context = json.loads(args.context.read_text(encoding="utf-8"))
            if not isinstance(context, dict):
                raise ValueError("run context must be one JSON object")
            issues.extend(validate_run_context(context, validation_order_specified=args.validation_order_specified))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        issues = [str(exc)]
    result = {"valid": not issues, "policy": str(args.policy), "issues": issues}
    print(json.dumps(result, indent=2) if args.json or issues else "portable harness operational discipline: PASS")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
