#!/usr/bin/env python3
"""Validate the provider-agnostic repository promotion contract and decision model."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness" / "contracts" / "repository-promotion.v1.json"
POLICY_PATH = ROOT / "harness" / "promotion" / "required-checks.v1.json"
FIXTURES_PATH = ROOT / "harness" / "evals" / "fixtures" / "repository-promotion-cases.v1.json"
CANDIDATE_WORKFLOW = ROOT / ".github" / "workflows" / "promotion-candidate.yml"
EXECUTOR_WORKFLOW = ROOT / ".github" / "workflows" / "promotion-executor.yml"
PR_MERGE_CONTRACT = ROOT / "harness" / "contracts" / "pr-merge-gate.v1.json"


class PromotionContractError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PromotionContractError(f"missing JSON file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise PromotionContractError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc


def validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != "repository-promotion/v1":
        raise PromotionContractError("unsupported repository promotion contract schema")
    if contract.get("contract_id") != "repository-promotion":
        raise PromotionContractError("repository promotion contract ID drifted")
    if contract.get("workflow_id") != "pr-floor-integration":
        raise PromotionContractError("promotion workflow owner must remain pr-floor-integration")
    boundary = contract.get("authoring_boundary", {})
    if boundary.get("pipeline_authors_source") is not False:
        raise PromotionContractError("promotion pipeline must not author source")
    if boundary.get("provider_yaml_orchestrates_repository_owned_commands") is not True:
        raise PromotionContractError("provider YAML must orchestrate repository-owned commands")
    if boundary.get("local_git_merge_is_provider_promotion") is not False:
        raise PromotionContractError("local git merge must not count as provider promotion")
    provider = contract.get("provider_contract", {})
    expected = {"resolve_host_identity","resolve_default_branch","query_candidate_state","query_explicit_required_checks","query_review_decision","query_unresolved_review_threads","query_branch_protection_and_rulesets","expected_head_merge_or_merge_queue","artifact_identity","post_promotion_containment"}
    required_capabilities = provider.get("required_capabilities")
    if not isinstance(required_capabilities, list) or set(required_capabilities) != expected:
        raise PromotionContractError("provider capability contract drifted")
    if provider.get("promotion_requires_complete_provider_truth") is not True:
        raise PromotionContractError("provider truth must fail closed")
    if provider.get("provider_mutation_required_for_success") is not True:
        raise PromotionContractError("provider mutation must be required for promotion success")
    if provider.get("local_git_merge_is_sufficient") is not False:
        raise PromotionContractError("local merge must remain insufficient")
    if provider.get("degraded_statuses") != ["PROVIDER_UNAVAILABLE","PROVIDER_RATE_LIMITED","PROVIDER_PARTIAL_TRUTH"]:
        raise PromotionContractError("degraded provider statuses drifted")
    adapter = contract.get("github_actions_adapter", {})
    if adapter.get("adapter_id") != "github-actions-v1":
        raise PromotionContractError("GitHub Actions adapter identity drifted")
    for field in ("runtime_script","candidate_workflow","promotion_workflow","required_check_policy"):
        value = adapter.get(field)
        if not isinstance(value, str) or not value:
            raise PromotionContractError(f"GitHub adapter missing {field}")
        if not (ROOT / value).is_file():
            raise PromotionContractError(f"GitHub adapter path missing: {value}")
    if adapter.get("long_lived_pat_forbidden") is not True:
        raise PromotionContractError("long-lived PAT must remain forbidden")


def validate_owner_registration(contract: dict[str, Any]) -> None:
    owner = load_json(PR_MERGE_CONTRACT)
    if owner.get("workflow_id") != "pr-floor-integration":
        raise PromotionContractError("repository promotion must remain under pr-floor-integration")
    registered = owner.get("promotion_pipeline")
    if not isinstance(registered, dict):
        raise PromotionContractError("pr-merge-gate does not register the promotion pipeline")
    expected = {"contract":"harness/contracts/repository-promotion.v1.json","policy":"harness/promotion/required-checks.v1.json","contract_validator":"scripts/validate_repository_promotion.py","candidate_gate_runner":"scripts/run_repository_promotion_gate.py","github_adapter":"scripts/github_promotion_adapter.py","candidate_workflow":".github/workflows/promotion-candidate.yml","promotion_workflow":".github/workflows/promotion-executor.yml","receipt":"github-actions-artifact://repository-promotion-receipt/repository-promotion-receipt.json"}
    for key, value in expected.items():
        if registered.get(key) != value:
            raise PromotionContractError(f"pr-merge-gate promotion registration drifted: {key}")
    for key in ("contract","policy","contract_validator","candidate_gate_runner","github_adapter","candidate_workflow","promotion_workflow"):
        if not (ROOT / registered[key]).is_file():
            raise PromotionContractError(f"registered promotion owner path is missing: {registered[key]}")
    if contract.get("workflow_id") != owner.get("workflow_id"):
        raise PromotionContractError("promotion contract workflow owner diverged from pr-merge-gate")


def validate_policy(policy: dict[str, Any]) -> dict[str, Any]:
    if policy.get("schema_version") != "repository-promotion-policy/v1":
        raise PromotionContractError("unsupported promotion policy schema")
    if policy.get("provider_adapter") != "github-actions-v1":
        raise PromotionContractError("policy must bind the current runtime to github-actions-v1")
    if policy.get("repository") != "EndeavorEverlasting/web-excel-repair-triage":
        raise PromotionContractError("promotion policy repository is not canonical")
    if not isinstance(policy.get("policy_version"), str) or not policy["policy_version"]:
        raise PromotionContractError("policy_version is required")
    destinations = policy.get("destinations")
    if not isinstance(destinations, dict) or not destinations:
        raise PromotionContractError("promotion policy needs at least one destination")
    main = destinations.get("main")
    if not isinstance(main, dict) or main.get("enabled") is not True:
        raise PromotionContractError("main promotion destination must be explicitly enabled")
    if main.get("merge_method") not in {"merge","squash","rebase"}:
        raise PromotionContractError("unsupported merge method")
    checks = main.get("required_check_names")
    if not isinstance(checks, list) or len(checks) < 3 or len(checks) != len(set(checks)):
        raise PromotionContractError("required_check_names must contain unique explicit names")
    artifacts = main.get("required_validation_artifacts")
    if not isinstance(artifacts, list) or len(artifacts) < 3 or len(artifacts) != len(set(artifacts)):
        raise PromotionContractError("required validation artifacts are incomplete")
    allowed = main.get("allowed_change_paths")
    if not isinstance(allowed, list) or not allowed:
        raise PromotionContractError("bounded v1 promotion scope is missing")
    e2e = main.get("application_e2e")
    if not isinstance(e2e, dict) or e2e.get("classification") != "INAPPLICABLE":
        raise PromotionContractError("bounded v1 application E2E must be explicitly INAPPLICABLE")
    if not main.get("merge_intent", {}).get("pr_body_marker") or not main.get("merge_intent", {}).get("head_prefix"):
        raise PromotionContractError("explicit merge intent contract is incomplete")
    if main.get("unresolved_review_threads_must_be_zero") is not True:
        raise PromotionContractError("unresolved review threads must block promotion")
    return main


def _blocked(reason: str, *, action: str) -> dict[str, Any]:
    return {"decision":"BLOCKED","blocker":True,"reason":reason,"required_action":action}


def evaluate_readiness(snapshot: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    main = validate_policy(policy)
    provider_status = snapshot.get("provider_status")
    if provider_status != "AVAILABLE":
        if provider_status not in policy.get("provider_degraded_statuses", []):
            return _blocked("PROVIDER_PARTIAL_TRUTH", action="Re-read complete provider truth.")
        return _blocked(str(provider_status), action="Retry only after authoritative provider truth is complete.")
    if snapshot.get("target") != "main":
        return _blocked("UNAUTHORIZED_TARGET", action="Use an explicitly enabled promotion destination.")
    pr, validation, reviews, branch_policy = snapshot.get("pr"), snapshot.get("validation"), snapshot.get("reviews"), snapshot.get("branch_policy")
    if not all(isinstance(item, dict) for item in (pr, validation, reviews, branch_policy)):
        return _blocked("PROVIDER_PARTIAL_TRUTH", action="Reconstruct the full provider snapshot.")
    if pr.get("merged") is True:
        return {"decision":"ALREADY_MERGED","blocker":False,"reason":None,"required_action":"Verify integration containment and reuse the existing-success receipt."}
    if pr.get("state") != "open":
        return _blocked("CLOSED_UNMERGED", action="Reopen, supersede, or intentionally abandon the candidate.")
    if pr.get("draft") is not False:
        return _blocked("DRAFT", action="Move the pull request to ready-for-review state.")
    if pr.get("mergeable") is not True:
        return _blocked("MERGEABILITY_UNRESOLVED_OR_CONFLICTED", action="Wait for authoritative mergeability or repair the conflict before promotion.")
    expected = snapshot.get("expected_head_sha")
    if not isinstance(expected, str) or pr.get("head_sha") != expected:
        return _blocked("HEAD_MOVED", action="Validate the new exact head from the beginning.")
    if validation.get("head_sha") != pr.get("head_sha"):
        return _blocked("STALE_VALIDATION_HEAD", action="Rerun validation for the current exact head.")
    if validation.get("base_sha") != pr.get("base_sha"):
        return _blocked("BASE_MOVED", action="Rerun validation against the current base.")
    if validation.get("policy_version") != policy.get("policy_version"):
        return _blocked("STALE_POLICY", action="Rerun validation against the current promotion policy.")
    if validation.get("conclusion") != "success":
        return _blocked("VALIDATION_RUN_NOT_GREEN", action="Repair the failing validation run.")
    if main.get("head_repository_must_equal_base_repository") and pr.get("head_repository") != policy.get("repository"):
        return _blocked("UNAUTHORIZED_HEAD_REPOSITORY", action="Use a same-repository candidate for v1 promotion.")
    if pr.get("author_association") not in set(main.get("authorized_author_associations", [])):
        return _blocked("UNAUTHORIZED_AUTHOR", action="Use a candidate authored by an allowed repository association.")
    intent = main["merge_intent"]
    if not str(pr.get("head_ref", "")).startswith(intent["head_prefix"]):
        return _blocked("MERGE_INTENT_MISSING", action=f"Use the required head prefix {intent['head_prefix']!r}.")
    if intent["pr_body_marker"] not in str(pr.get("body", "")):
        return _blocked("MERGE_INTENT_MISSING", action="Add the tracked promotion intent marker when opening the candidate.")
    changed_paths = validation.get("changed_paths")
    if not isinstance(changed_paths, list) or not changed_paths:
        return _blocked("PROVIDER_PARTIAL_TRUTH", action="Provide the exact changed-path set.")
    out_of_scope = sorted(set(changed_paths) - set(main["allowed_change_paths"]))
    if out_of_scope:
        return _blocked(
            "UNAUTHORIZED_CHANGE_SCOPE",
            action=(
                "Register a real application-E2E profile before widening auto-promotion scope; "
                f"out-of-scope paths: {out_of_scope}"
            ),
        )
    checks = validation.get("checks")
    if not isinstance(checks, list):
        return _blocked("PROVIDER_PARTIAL_TRUTH", action="Query the named validation checks.")
    by_name = {str(item.get("name")):str(item.get("conclusion")) for item in checks if isinstance(item, dict)}
    for name in main["required_check_names"]:
        conclusion = by_name.get(name)
        if conclusion is None:
            return _blocked("REQUIRED_CHECK_MISSING", action=f"Restore the explicitly required check {name!r}.")
        if conclusion != "success":
            return _blocked("REQUIRED_CHECK_NOT_GREEN", action=f"Repair required check {name!r}; {conclusion!r} is not green.")
    artifacts = validation.get("artifacts")
    if not isinstance(artifacts, list):
        return _blocked("PROVIDER_PARTIAL_TRUTH", action="Query validation artifact identities.")
    required_artifacts = main["required_validation_artifacts"]
    available = {
        str(item.get("name")): item
        for item in artifacts
        if isinstance(item, dict) and item.get("expired") is False
    }
    missing = [name for name in required_artifacts if name not in available]
    if missing:
        return _blocked("VALIDATION_ARTIFACT_MISSING", action=f"Recreate validation artifacts: {missing}")
    invalid_ids = [
        name
        for name in required_artifacts
        if (
            isinstance(available[name].get("id"), bool)
            or not isinstance(available[name].get("id"), int)
            or available[name]["id"] <= 0
        )
    ]
    if invalid_ids:
        return _blocked(
            "PROVIDER_PARTIAL_TRUTH",
            action=f"Re-read positive numeric provider artifact IDs for required artifacts: {invalid_ids}",
        )
    if branch_policy.get("complete") is not True:
        return _blocked("PROVIDER_PARTIAL_TRUTH", action="Read branch protection and ruleset truth before promotion.")
    if main.get("unresolved_review_threads_must_be_zero") and reviews.get("unresolved_threads") != 0:
        return _blocked("UNRESOLVED_REVIEW_THREADS", action="Resolve every review thread before promotion.")
    if int(main.get("required_approvals", 0)) and reviews.get("decision") != "APPROVED":
        return _blocked("REQUIRED_APPROVAL_MISSING", action="Satisfy the provider review-decision gate.")
    if branch_policy.get("merge_queue_required") is True:
        return {"decision":"READY_QUEUE","blocker":False,"reason":None,"required_action":"Re-read provider truth, then enqueue this exact pull request through the provider merge queue."}
    return {"decision":"READY_DIRECT","blocker":False,"reason":None,"required_action":"Re-read provider truth, then merge through the provider API with expected-head compare-and-set."}


def validate_workflow_contract(policy: dict[str, Any]) -> None:
    main = validate_policy(policy)
    candidate = CANDIDATE_WORKFLOW.read_text(encoding="utf-8")
    executor = EXECUTOR_WORKFLOW.read_text(encoding="utf-8")
    for name in main["required_check_names"]:
        if f"name: {name}" not in candidate:
            raise PromotionContractError(f"candidate workflow does not expose required check name: {name}")
    for marker in ("pull_request:","permissions:","contents: read","pull-requests: read","scripts/run_repository_promotion_gate.py","actions/upload-artifact@v7"):
        if marker not in candidate:
            raise PromotionContractError(f"candidate workflow missing safety marker: {marker}")
    for marker in ("workflow_run:","pull_request_target:","pull_request_review:","pull_request_review_comment:","workflow_dispatch:","concurrency:","actions: read","checks: read","contents: write","pull-requests: write","scripts/github_promotion_adapter.py","persist-credentials: false"):
        if marker not in executor:
            raise PromotionContractError(f"promotion executor missing safety marker: {marker}")
    if any(line.strip() == "pull_request:" for line in executor.splitlines()):
        raise PromotionContractError("privileged promotion workflow must not execute from untrusted pull_request YAML")


def validate_fixtures(fixtures: dict[str, Any], policy: dict[str, Any]) -> int:
    if fixtures.get("schema_version") != "repository-promotion-fixtures/v1":
        raise PromotionContractError("unsupported promotion fixture schema")
    cases = fixtures.get("cases")
    if not isinstance(cases, list) or len(cases) < 10:
        raise PromotionContractError("promotion fixture coverage is incomplete")
    seen: set[str] = set()
    for case in cases:
        case_id = str(case.get("id", ""))
        if not case_id or case_id in seen:
            raise PromotionContractError(f"duplicate or empty promotion fixture id: {case_id}")
        seen.add(case_id)
        result = evaluate_readiness(case["snapshot"], policy)
        if result["decision"] != case["expected_decision"]:
            raise PromotionContractError(f"fixture {case_id} decision drifted: {result['decision']} != {case['expected_decision']}")
        if result["blocker"] is not case["expected_blocker"]:
            raise PromotionContractError(f"fixture {case_id} blocker classification drifted")
    return len(cases)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    try:
        contract = load_json(CONTRACT_PATH)
        policy = load_json(POLICY_PATH)
        validate_contract(contract)
        validate_owner_registration(contract)
        validate_policy(policy)
        validate_workflow_contract(policy)
        count = validate_fixtures(load_json(FIXTURES_PATH), policy)
        if args.summary:
            print(f"Repository promotion validation PASS: fixtures={count} adapter={policy['provider_adapter']} policy={policy['policy_version']}")
    except PromotionContractError as exc:
        print(f"Repository promotion validation failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
