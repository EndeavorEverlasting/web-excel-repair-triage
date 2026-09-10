from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import github_promotion_adapter as github_adapter
import validate_repository_promotion as promotion


class RepositoryPromotionTests(unittest.TestCase):
    def load(self, path: str) -> dict:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_contract_policy_and_negative_fixtures_pass(self) -> None:
        self.assertEqual(promotion.main([]), 0)

    def test_contract_is_provider_agnostic_but_runtime_is_bound_to_github(self) -> None:
        contract = self.load("harness/contracts/repository-promotion.v1.json")
        policy = self.load("harness/promotion/required-checks.v1.json")
        self.assertEqual(contract["provider_contract"]["interface_version"], "scm-ci-provider/v1")
        self.assertEqual(contract["github_actions_adapter"]["adapter_id"], "github-actions-v1")
        self.assertEqual(policy["provider_adapter"], "github-actions-v1")
        self.assertFalse(contract["authoring_boundary"]["pipeline_authors_source"])
        self.assertFalse(contract["provider_contract"]["local_git_merge_is_sufficient"])
        self.assertTrue(contract["provider_contract"]["provider_mutation_required_for_success"])
        self.assertEqual(contract["provider_contract"]["degraded_statuses"], ["PROVIDER_UNAVAILABLE", "PROVIDER_RATE_LIMITED", "PROVIDER_PARTIAL_TRUTH"])
        self.assertIn("provider_host", contract["receipt_schema"]["required_fields"])

    def test_required_checks_are_explicit_and_application_e2e_scope_is_bounded(self) -> None:
        main = self.load("harness/promotion/required-checks.v1.json")["destinations"]["main"]
        self.assertEqual(main["required_check_names"], ["Promotion / Contract", "Promotion / Harness E2E", "Promotion / Application E2E", "Promotion / Exact Candidate Gate"])
        self.assertEqual(main["allowed_change_paths"], ["harness/evals/fixtures/repository-promotion-canary.v1.json"])
        self.assertEqual(main["application_e2e"]["classification"], "INAPPLICABLE")
        self.assertEqual(main["merge_intent"]["head_prefix"], "promote/")
        self.assertEqual(main["merge_intent"]["pr_body_marker"], "[promotion:auto-main]")
        self.assertTrue(main["unresolved_review_threads_must_be_zero"])

    def test_candidate_workflow_is_read_only_and_exact_candidate_bound(self) -> None:
        text = (ROOT / ".github/workflows/promotion-candidate.yml").read_text(encoding="utf-8")
        for marker in ("pull_request:", "contents: read", "pull-requests: read", "ref: ${{ github.event.pull_request.head.sha }}", "persist-credentials: false", "harness/evals/fixtures/repository-promotion-*.v1.json", "Promotion / Contract", "Promotion / Harness E2E", "Promotion / Application E2E", "Promotion / Exact Candidate Gate"):
            self.assertIn(marker, text)
        self.assertNotIn("pull_request_target:", text)
        self.assertNotIn("contents: write", text)

    def test_executor_runs_trusted_default_branch_adapter_with_serialized_write_authority(self) -> None:
        text = (ROOT / ".github/workflows/promotion-executor.yml").read_text(encoding="utf-8")
        for marker in ("workflow_run:", "pull_request_target:", "pull_request_review:", "pull_request_review_comment:", "workflow_dispatch:", "actions: read", "checks: read", "contents: write", "pull-requests: write", "group: repository-promotion-main", "cancel-in-progress: false", "ref: ${{ github.event.repository.default_branch }}", "persist-credentials: false", "scripts/github_promotion_adapter.py", "repository-promotion-receipt"):
            self.assertIn(marker, text)
        self.assertNotIn("pull_request:\n", text)

    def test_github_adapter_is_host_parameterized_and_expected_head_guarded(self) -> None:
        text = (ROOT / "scripts/github_promotion_adapter.py").read_text(encoding="utf-8")
        for marker in ("GITHUB_SERVER_URL", "GITHUB_API_URL", "GITHUB_GRAPHQL_URL", "GITHUB_REPOSITORY", "reviewThreads", "/rulesets", "/actions/runs/", "/artifacts", '{"sha": head', "enqueuePullRequest", "/compare/", "PROVIDER_RATE_LIMITED", "PROVIDER_PARTIAL_TRUTH", "PROVIDER_UNAVAILABLE", "ALREADY_MERGED_VERIFIED", '"containment"', '"owner":"P115"'):
            self.assertIn(marker, text)
        self.assertNotIn("https://api.github.com", text)
        self.assertNotIn("PERSONAL_ACCESS_TOKEN", text)
        self.assertNotIn("git merge", text)

    def test_github_runtime_requires_explicit_server_identity(self) -> None:
        env = {
            "GITHUB_REPOSITORY": "EndeavorEverlasting/web-excel-repair-triage",
            "GITHUB_API_URL": "https://api.github.com",
            "GITHUB_GRAPHQL_URL": "https://api.github.com/graphql",
            "GITHUB_TOKEN": "token",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(github_adapter.ProviderError, "runtime identity"):
                github_adapter.GitHub()
        env["GITHUB_SERVER_URL"] = "https://github.com"
        with mock.patch.dict(os.environ, env, clear=True):
            gh = github_adapter.GitHub()
        self.assertEqual(gh.server_url, "https://github.com")

    def test_validation_run_accepts_exact_match_before_pagination_ceiling(self) -> None:
        exact = {
            "id": 9,
            "name": "Promotion Candidate Validation",
            "head_sha": "a" * 40,
            "created_at": "2026-09-10T00:00:00Z",
            "pull_requests": [{"number": 42}],
        }

        class FakeGitHub:
            repo = "EndeavorEverlasting/web-excel-repair-triage"

            def rest(self, method: str, path: str, body=None):
                self.last_path = path
                return {"total_count": 101, "workflow_runs": [exact]}

        result = github_adapter.validation_run(FakeGitHub(), 42, "a" * 40, None)
        self.assertEqual(result["id"], 9)

    def test_validation_run_fails_closed_when_match_may_be_on_older_page(self) -> None:
        class FakeGitHub:
            repo = "EndeavorEverlasting/web-excel-repair-triage"

            def rest(self, method: str, path: str, body=None):
                return {"total_count": 101, "workflow_runs": []}

        with self.assertRaisesRegex(github_adapter.ProviderError, "older provider pages remain"):
            github_adapter.validation_run(FakeGitHub(), 42, "a" * 40, None)

    def test_pr_floor_integration_registers_concrete_promotion_pipeline(self) -> None:
        owner = self.load("harness/contracts/pr-merge-gate.v1.json")
        registered = owner["promotion_pipeline"]
        self.assertEqual(owner["workflow_id"], "pr-floor-integration")
        self.assertEqual(registered["contract"], "harness/contracts/repository-promotion.v1.json")
        self.assertEqual(registered["github_adapter"], "scripts/github_promotion_adapter.py")
        self.assertEqual(registered["promotion_workflow"], ".github/workflows/promotion-executor.yml")
        self.assertEqual(registered["receipt"], "Outputs/repository-promotion-receipt.json")

    def test_ready_fixture_requires_mergeable_exact_head_and_complete_provider_truth(self) -> None:
        policy = self.load("harness/promotion/required-checks.v1.json")
        fixtures = self.load("harness/evals/fixtures/repository-promotion-cases.v1.json")
        ready = next(case for case in fixtures["cases"] if case["id"] == "ready_direct")
        snapshot = json.loads(json.dumps(ready["snapshot"]))
        self.assertEqual(promotion.evaluate_readiness(snapshot, policy)["decision"], "READY_DIRECT")
        snapshot["pr"]["mergeable"] = None
        self.assertEqual(promotion.evaluate_readiness(snapshot, policy)["reason"], "MERGEABILITY_UNRESOLVED_OR_CONFLICTED")

    def test_failed_candidate_proof_is_not_reused_by_promotion_contract(self) -> None:
        routing = self.load("harness/contracts/repository-promotion.v1.json")["failure_routing"]
        self.assertEqual(routing["repair_owner"], "P115")
        self.assertTrue(routing["repair_creates_new_candidate"])
        self.assertTrue(routing["failed_candidate_proof_reuse_forbidden"])


if __name__ == "__main__":
    unittest.main()
