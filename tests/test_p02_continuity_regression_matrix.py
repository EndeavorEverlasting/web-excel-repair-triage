from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "harness/evals/prompt-strength/p02-continuity-regression-matrix.v1.json"
RAW_BASE = ROOT / "docs/prompts.json"
TEST_FLOOR = ROOT / "harness/test-floor.v1.json"
TEST_PATH = "tests/test_p02_continuity_regression_matrix.py"


class P02ContinuityRegressionMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        cls.effective = {
            row["id"]: row for row in build_prompt_kit_registry.load_prompt_registry()
        }["P02"]
        cls.raw = {
            row["id"]: row for row in json.loads(RAW_BASE.read_text(encoding="utf-8"))
        }["P02"]

    def test_matrix_contract_and_mode_coverage(self) -> None:
        self.assertEqual(self.matrix["schema_version"], "p02-continuity-regression-matrix/v1")
        self.assertEqual(self.matrix["prompt_id"], "P02")
        self.assertEqual(
            set(self.matrix["required_modes"]),
            {"ORIENT", "SUMMARIZE", "CLOSEOUT", "CONTINUE"},
        )
        cases = self.matrix["cases"]
        self.assertGreaterEqual(len(cases), self.matrix["case_contract"]["minimum_cases"])
        self.assertEqual(len({case["case_id"] for case in cases}), len(cases))
        required = set(self.matrix["case_contract"]["required_fields"])
        for case in cases:
            self.assertFalse(required - set(case), case["case_id"])
            self.assertTrue(case["positive_assertions"], case["case_id"])
            self.assertTrue(case["negative_assertions"], case["case_id"])
            self.assertTrue(case["prompt_markers"], case["case_id"])
            ceiling = case["proof_ceiling"].lower()
            self.assertIn("model obedience", ceiling)
            self.assertIn("unproven", ceiling)

    def test_all_protected_capabilities_have_adversarial_cases(self) -> None:
        covered = {
            capability
            for case in self.matrix["cases"]
            for capability in case["capabilities"]
        }
        self.assertEqual(set(self.matrix["capability_ids"]), covered)

    def test_matrix_markers_bind_the_effective_p02_override(self) -> None:
        content = self.effective["copyContent"]
        for case in self.matrix["cases"]:
            for marker in case["prompt_markers"]:
                with self.subTest(case=case["case_id"], marker=marker):
                    self.assertIn(marker, content)

    def test_effective_override_not_raw_base_is_the_matrix_subject(self) -> None:
        self.assertEqual(
            self.matrix["effective_authority"],
            "registry/prompts/prompt-overrides.v1.json",
        )
        self.assertNotEqual(self.raw["copyContent"], self.effective["copyContent"])
        self.assertIn(
            "does not bind the effective P02 override body",
            self.matrix["semantic_coverage_boundary"]["known_gap"],
        )

    def test_mode_router_does_not_force_execution(self) -> None:
        content = self.effective["copyContent"]
        self.assertIn("MODE: AUTO | ORIENT | SUMMARIZE | CLOSEOUT | CONTINUE", content)
        self.assertIn("do not turn a request to orient, summarize, or close out into implementation", content)
        self.assertIn("No repository mutation merely to provide bearings.", content)
        self.assertIn("Do not execute work merely because open work exists.", content)
        self.assertIn("Do not start a new implementation slice merely because one is available.", content)
        self.assertNotIn(
            "CONTINUE THAT CHAT AS AN ACTIVE IMPLEMENTATION SPRINT. DO NOT MERELY SUMMARIZE IT OR RETURN A PLAN.",
            content,
        )

    def test_continue_mode_retains_execution_strength(self) -> None:
        content = self.effective["copyContent"]
        for marker in (
            "CONTINUE THAT CHAT AS AN ACTIVE IMPLEMENTATION SPRINT",
            "planning is subordinate to implementation",
            "SELECT THE FIRST UNFINISHED EXECUTION SLICE — CONTINUE ONLY",
            "IMPLEMENT NOW — CONTINUE ONLY",
            "VALIDATE AND DELIVER — CONTINUE ONLY",
            "Do not stop at a summary, TODO list, architecture discussion, branch listing, PR status, or plan while safe executable work remains.",
        ):
            self.assertIn(marker, content)

    def test_alignment_axes_remain_independent_before_reconciliation(self) -> None:
        content = self.effective["copyContent"]
        conversation = content.index("2. AXIS A — CONVERSATION FIDELITY")
        reality = content.index("3. AXIS B — CURRENT REALITY")
        reconcile = content.index("4. ALIGNMENT / RECONCILIATION")
        self.assertLess(conversation, reconcile)
        self.assertLess(reality, reconcile)
        self.assertIn("Do not infer present truth from conversation history", content)
        self.assertIn("do not infer operator intent from repository state", content)

    def test_words_matter_for_operator_alternatives(self) -> None:
        content = self.effective["copyContent"]
        self.assertIn("MODE ROUTING — WORDS MATTER", content)
        self.assertIn("such as 'closeout or review', preserve the OR relationship", content)
        self.assertIn("Do not silently rewrite alternatives as cumulative requirements.", content)

    def test_global_policy_cannot_promote_non_execution_dispositions(self) -> None:
        content = self.effective["copyContent"]
        marker = "DISPOSITION / MODE PRECEDENCE CONTRACT"
        self.assertGreater(content.index(marker), content.index("MODE: AUTO | ORIENT | SUMMARIZE | CLOSEOUT | CONTINUE"))
        for phrase in (
            "do not turn a request to orient, summarize, or close out into implementation.",
            marker,
            "For P02 specifically, ORIENT and SUMMARIZE do not authorize repository implementation",
            "CLOSEOUT may persist the mode-authorized checkpoint/handoff but must not start a new implementation slice",
            "CONTINUE is the execution-bearing disposition",
            "A later shared suffix does not override an earlier explicit disposition boundary",
        ):
            self.assertIn(phrase, content)

    def test_matrix_regression_runs_in_deterministic_floor(self) -> None:
        floor = json.loads(TEST_FLOOR.read_text(encoding="utf-8"))
        self.assertIn(TEST_PATH, floor["self_tests"])


if __name__ == "__main__":
    unittest.main()
