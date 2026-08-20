from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_pr_merge_gate


class PrMergeGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            validate_pr_merge_gate.CONTRACT_PATH.read_text(encoding="utf-8")
        )
        cls.fixtures = json.loads(
            validate_pr_merge_gate.FIXTURES_PATH.read_text(encoding="utf-8")
        )

    def case(self, case_id: str) -> dict:
        return next(
            case for case in self.fixtures["state_cases"] if case["id"] == case_id
        )

    def handoff_case(self, case_id: str) -> dict:
        return next(
            case for case in self.fixtures["handoff_cases"] if case["id"] == case_id
        )

    def test_contract_and_fixture_validator_passes(self) -> None:
        self.assertEqual(validate_pr_merge_gate.main(["--summary"]), 0)

    def test_green_mergeable_authorized_pr_is_merge_now_not_blocker(self) -> None:
        result = validate_pr_merge_gate.classify_pr_state(
            self.case("green-authorized-pr-merges-now")["state"], self.contract
        )
        self.assertEqual(result["decision"], "merge_now")
        self.assertFalse(result["blocker"])
        self.assertIsNone(result["reason"])
        self.assertIn("Merge immediately", result["required_action"])
        self.assertIn("expected-head", result["required_action"])
        self.assertIn("default branch", result["required_action"])

    def test_missing_merge_authority_is_the_actual_gate(self) -> None:
        result = validate_pr_merge_gate.classify_pr_state(
            self.case("green-pr-without-authority-hands-off-authority")["state"],
            self.contract,
        )
        self.assertEqual(result["decision"], "handoff_merge_authority")
        self.assertTrue(result["blocker"])
        self.assertEqual(result["reason"], "merge_authority_unavailable")

    def test_required_check_review_conflict_and_head_move_are_real_blockers(self) -> None:
        cases = {
            "failed-required-check-blocks": "required_check_not_green",
            "unresolved-review-blocks": "unresolved_review_findings",
            "conflict-blocks": "merge_conflict",
            "unknown-mergeability-blocks-until-resolved": "mergeability_unresolved",
            "head-move-blocks-stale-merge": "head_moved",
            "draft-blocks-merge": "draft",
        }
        for case_id, reason in cases.items():
            with self.subTest(case=case_id):
                result = validate_pr_merge_gate.classify_pr_state(
                    self.case(case_id)["state"], self.contract
                )
                self.assertEqual(result["decision"], "blocked")
                self.assertTrue(result["blocker"])
                self.assertEqual(result["reason"], reason)

    def test_already_merged_is_complete_not_blocked(self) -> None:
        result = validate_pr_merge_gate.classify_pr_state(
            self.case("already-merged-is-complete-not-blocked")["state"], self.contract
        )
        self.assertEqual(result["decision"], "already_merged")
        self.assertFalse(result["blocker"])
        self.assertIn("default branch", result["required_action"])

    def test_post_merge_normal_consumers_must_use_main(self) -> None:
        good = validate_pr_merge_gate.validate_post_merge_handoff(
            self.handoff_case("merged-normal-consumer-uses-main")["handoff"],
            self.contract,
        )
        bad = validate_pr_merge_gate.validate_post_merge_handoff(
            self.handoff_case(
                "merged-normal-consumer-must-not-use-feature-branch"
            )["handoff"],
            self.contract,
        )
        self.assertTrue(good["valid"])
        self.assertFalse(bad["valid"])
        self.assertEqual(
            bad["reason"],
            "merged_work_must_route_normal_consumers_to_default_branch",
        )

    def test_post_merge_handoff_requires_default_branch_verification(self) -> None:
        result = validate_pr_merge_gate.validate_post_merge_handoff(
            self.handoff_case("merged-handoff-requires-default-branch-proof")[
                "handoff"
            ],
            self.contract,
        )
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "default_branch_not_verified")

    def test_historical_branch_debugging_remains_allowed(self) -> None:
        result = validate_pr_merge_gate.validate_post_merge_handoff(
            self.handoff_case("historical-feature-branch-intent-is-allowed")[
                "handoff"
            ],
            self.contract,
        )
        self.assertTrue(result["valid"])

    def test_incomplete_state_fails_closed(self) -> None:
        state = dict(self.case("green-authorized-pr-merges-now")["state"])
        state.pop("expected_head_sha")
        with self.assertRaisesRegex(
            validate_pr_merge_gate.PrMergeGateError, "missing required fields"
        ):
            validate_pr_merge_gate.classify_pr_state(state, self.contract)


if __name__ == "__main__":
    unittest.main()
