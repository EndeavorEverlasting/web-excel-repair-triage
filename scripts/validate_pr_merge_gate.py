#!/usr/bin/env python3
"""Validate and evaluate the repository PR merge-gate contract."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness" / "contracts" / "pr-merge-gate.v1.json"
FIXTURES_PATH = ROOT / "harness" / "evals" / "fixtures" / "pr-merge-gate-cases.v1.json"


class PrMergeGateError(RuntimeError):
    """Raised when merge-gate inputs or repository contracts are invalid."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PrMergeGateError(f"missing JSON file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise PrMergeGateError(
            f"invalid JSON in {path.relative_to(ROOT)}: {exc}"
        ) from exc


def validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != "pr-merge-gate/v1":
        raise PrMergeGateError("unsupported PR merge-gate schema")
    if contract.get("contract_id") != "pr-merge-gate":
        raise PrMergeGateError("PR merge-gate contract ID drifted")
    if contract.get("workflow_id") != "pr-floor-integration":
        raise PrMergeGateError("PR merge-gate workflow owner drifted")

    required_fields = contract.get("required_state_fields")
    if not isinstance(required_fields, list) or not required_fields:
        raise PrMergeGateError("required_state_fields must be a non-empty array")
    expected_fields = {
        "pr_number",
        "state",
        "merged",
        "draft",
        "mergeable",
        "required_checks",
        "unresolved_review_findings",
        "head_sha",
        "expected_head_sha",
        "merge_intent",
        "merge_authorized",
        "default_branch",
        "head_branch",
    }
    if set(required_fields) != expected_fields:
        raise PrMergeGateError("required_state_fields drifted")

    if contract.get("passing_required_check_conclusions") != ["success"]:
        raise PrMergeGateError("required check success policy drifted")

    forbidden = contract.get("forbidden_outcomes")
    if not isinstance(forbidden, list) or len(forbidden) < 5:
        raise PrMergeGateError("forbidden_outcomes is incomplete")
    joined = "\n".join(str(item).lower() for item in forbidden)
    for phrase in (
        "green mergeable merge-authorized pr as a blocker",
        "feature branch after that work has been merged",
        "default branch advanced",
        "required checks",
        "expected-head",
    ):
        if phrase not in joined:
            raise PrMergeGateError(
                f"PR merge-gate forbidden outcomes missing required rule: {phrase}"
            )

    post_merge = contract.get("post_merge_consumption")
    if not isinstance(post_merge, dict):
        raise PrMergeGateError("post_merge_consumption contract is missing")
    if post_merge.get("canonical_default_branch") != "main":
        raise PrMergeGateError("canonical post-merge branch must be main")
    intents = post_merge.get("normal_consumer_intents")
    if not isinstance(intents, list) or not {"use", "update", "pull", "acquire"}.issubset(
        set(intents)
    ):
        raise PrMergeGateError("normal consumer intent set is incomplete")


def _require_state(state: dict[str, Any], contract: dict[str, Any]) -> None:
    missing = [field for field in contract["required_state_fields"] if field not in state]
    if missing:
        raise PrMergeGateError(f"PR state is missing required fields: {missing}")
    if not isinstance(state["pr_number"], int) or state["pr_number"] <= 0:
        raise PrMergeGateError("pr_number must be a positive integer")
    if state["state"] not in {"open", "closed"}:
        raise PrMergeGateError("state must be open or closed")
    for field in ("merged", "draft", "merge_intent", "merge_authorized"):
        if not isinstance(state[field], bool):
            raise PrMergeGateError(f"{field} must be boolean")
    if state["mergeable"] not in {True, False, None}:
        raise PrMergeGateError("mergeable must be true, false, or null")
    if not isinstance(state["required_checks"], list):
        raise PrMergeGateError("required_checks must be an array")
    if not isinstance(state["unresolved_review_findings"], int) or state[
        "unresolved_review_findings"
    ] < 0:
        raise PrMergeGateError("unresolved_review_findings must be a non-negative integer")
    for field in ("head_sha", "expected_head_sha", "default_branch", "head_branch"):
        if not isinstance(state[field], str) or not state[field].strip():
            raise PrMergeGateError(f"{field} must be a non-empty string")


def _result(decision: str, blocker: bool, reason: str | None, action: str) -> dict[str, Any]:
    return {
        "decision": decision,
        "blocker": blocker,
        "reason": reason,
        "required_action": action,
    }


def classify_pr_state(
    state: dict[str, Any], contract: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Classify PR state without performing a provider mutation."""
    contract = contract or load_json(CONTRACT_PATH)
    validate_contract(contract)
    _require_state(state, contract)

    if state["merged"]:
        return _result(
            "already_merged",
            False,
            None,
            "Verify the canonical default branch contains the merge and route normal consumers to that default branch or its registered artifact.",
        )
    if state["state"] != "open":
        return _result(
            "blocked",
            True,
            "closed_unmerged",
            "Preserve unique work and determine whether the closed PR should be reopened, superseded, or intentionally abandoned.",
        )
    if state["head_sha"] != state["expected_head_sha"]:
        return _result(
            "blocked",
            True,
            "head_moved",
            "Re-read the PR head and validations before any merge attempt; never merge against stale expected-head evidence.",
        )
    if state["draft"]:
        return _result(
            "blocked",
            True,
            "draft",
            "Resolve the draft/review gate before merging.",
        )
    if state["mergeable"] is None:
        return _result(
            "blocked",
            True,
            "mergeability_unresolved",
            "Resolve provider mergeability before merging.",
        )
    if state["mergeable"] is False:
        return _result(
            "blocked",
            True,
            "merge_conflict",
            "Repair the merge conflict without discarding unique work, then rerun the gate.",
        )

    passing = set(contract["passing_required_check_conclusions"])
    for check in state["required_checks"]:
        if not isinstance(check, dict):
            raise PrMergeGateError("required check entries must be objects")
        name = str(check.get("name", "")).strip()
        conclusion = str(check.get("conclusion", "")).strip().lower()
        if not name or not conclusion:
            raise PrMergeGateError("required check entries need name and conclusion")
        if conclusion not in passing:
            return _result(
                "blocked",
                True,
                "required_check_not_green",
                f"Repair or resolve required check {name!r} before merging.",
            )

    if state["unresolved_review_findings"]:
        return _result(
            "blocked",
            True,
            "unresolved_review_findings",
            "Resolve every required review finding before merging.",
        )
    if not state["merge_intent"]:
        return _result(
            "ready_for_review",
            False,
            None,
            "The PR is merge-ready, but integration intent is not established; preserve readiness without inventing merge authority.",
        )
    if not state["merge_authorized"]:
        return _result(
            "handoff_merge_authority",
            True,
            "merge_authority_unavailable",
            "Hand off the exact PR and expected head SHA to the merge-authorized owner; this authority gate is the blocker.",
        )

    return _result(
        "merge_now",
        False,
        None,
        "Merge immediately using expected-head protection; then verify the canonical default branch advanced before handoff.",
    )


def validate_post_merge_handoff(
    handoff: dict[str, Any], contract: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Reject branch-only consumer guidance after a merge has reached main."""
    contract = contract or load_json(CONTRACT_PATH)
    validate_contract(contract)
    for field in (
        "merged",
        "consumer_intent",
        "default_branch",
        "source_ref",
        "feature_branch",
        "default_branch_verified",
    ):
        if field not in handoff:
            raise PrMergeGateError(f"handoff is missing required field: {field}")
    if not isinstance(handoff["merged"], bool) or not isinstance(
        handoff["default_branch_verified"], bool
    ):
        raise PrMergeGateError("handoff merged/default_branch_verified must be boolean")

    if not handoff["merged"]:
        return {"valid": True, "reason": None}
    if not handoff["default_branch_verified"]:
        return {"valid": False, "reason": "default_branch_not_verified"}

    normal_intents = set(contract["post_merge_consumption"]["normal_consumer_intents"])
    if handoff["consumer_intent"] in normal_intents and handoff["source_ref"] != handoff[
        "default_branch"
    ]:
        return {
            "valid": False,
            "reason": "merged_work_must_route_normal_consumers_to_default_branch",
        }
    return {"valid": True, "reason": None}


def validate_fixtures(
    fixtures: dict[str, Any], contract: dict[str, Any]
) -> tuple[int, int]:
    if fixtures.get("schema_version") != "pr-merge-gate-fixtures/v1":
        raise PrMergeGateError("unsupported PR merge-gate fixture schema")
    state_cases = fixtures.get("state_cases")
    handoff_cases = fixtures.get("handoff_cases")
    if not isinstance(state_cases, list) or len(state_cases) < 8:
        raise PrMergeGateError("PR merge-gate state fixtures are incomplete")
    if not isinstance(handoff_cases, list) or len(handoff_cases) < 3:
        raise PrMergeGateError("PR merge-gate handoff fixtures are incomplete")

    seen: set[str] = set()
    for case in state_cases:
        case_id = str(case.get("id", "")).strip()
        if not case_id or case_id in seen:
            raise PrMergeGateError(f"duplicate or empty fixture id: {case_id}")
        seen.add(case_id)
        result = classify_pr_state(case["state"], contract)
        if result["decision"] != case["expected_decision"]:
            raise PrMergeGateError(
                f"fixture {case_id} decision drifted: {result['decision']} != {case['expected_decision']}"
            )
        if result["blocker"] is not case["expected_blocker"]:
            raise PrMergeGateError(f"fixture {case_id} blocker classification drifted")
        if "expected_reason" in case and result["reason"] != case["expected_reason"]:
            raise PrMergeGateError(f"fixture {case_id} reason drifted")

    for case in handoff_cases:
        case_id = str(case.get("id", "")).strip()
        if not case_id or case_id in seen:
            raise PrMergeGateError(f"duplicate or empty fixture id: {case_id}")
        seen.add(case_id)
        result = validate_post_merge_handoff(case["handoff"], contract)
        if result["valid"] is not case["expected_valid"]:
            raise PrMergeGateError(f"fixture {case_id} handoff validity drifted")
        if "expected_reason" in case and result["reason"] != case["expected_reason"]:
            raise PrMergeGateError(f"fixture {case_id} handoff reason drifted")
    return len(state_cases), len(handoff_cases)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    parser.add_argument("--fixtures", type=Path, default=FIXTURES_PATH)
    parser.add_argument("--state", type=Path, help="Optional JSON PR-state file to classify.")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    try:
        contract = load_json(args.contract)
        validate_contract(contract)
        state_count, handoff_count = validate_fixtures(load_json(args.fixtures), contract)
        if args.state:
            state = load_json(args.state)
            result = classify_pr_state(state, contract)
            print(json.dumps(result, indent=2, sort_keys=True))
        if args.summary:
            print(
                "PR merge-gate validation PASS: "
                f"state_cases={state_count} handoff_cases={handoff_count}"
            )
    except PrMergeGateError as exc:
        print(f"PR merge-gate validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
