from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "harness/evals/prompt-strength/p65-staged-routing-regression-matrix.v1.json"
TEST_FLOOR = ROOT / "harness/test-floor.v1.json"
TEST_PATH = "tests/test_p65_staged_routing_prompt.py"


class P65StagedRoutingPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        cls.effective = {
            row["id"]: row for row in build_prompt_kit_registry.load_prompt_kit_registry()
        }["P65"]

    def test_staged_routing_schema_separates_actor_disposition_axes(self) -> None:
        self.assertEqual(
            self.matrix["schema_version"],
            "p65-staged-routing-regression-matrix/v1",
        )
        self.assertEqual(self.matrix["prompt_id"], "P65")
        schema = self.matrix["staged_routing_schema"]
        self.assertEqual(schema["schema_version"], "p65-staged-routing/v1")
        fields = schema["fields"]
        self.assertEqual(
            set(fields),
            {
                "starting_state",
                "user_outcome",
                "current_agent_disposition",
                "requested_output",
                "downstream_actor",
                "downstream_disposition",
                "work_shape",
                "proof_need",
                "material_constraints",
            },
        )
        self.assertTrue(fields["current_agent_disposition"]["required"])
        self.assertTrue(fields["requested_output"]["required"])
        self.assertEqual(fields["downstream_actor"]["required"], "conditional")
        self.assertEqual(fields["downstream_disposition"]["required"], "conditional")
        self.assertIn(
            "plan_design",
            fields["current_agent_disposition"]["values"],
        )
        self.assertIn("handoff", fields["requested_output"]["values"])
        self.assertIn(
            "execute_bounded_sprint",
            fields["downstream_disposition"]["values"],
        )
        self.assertEqual(
            schema["resolved_need_model_order"],
            [
                "starting_state",
                "user_outcome",
                "current_agent_disposition",
                "requested_output",
                "downstream_disposition_if_any",
                "work_shape",
                "proof_need",
                "material_constraints",
            ],
        )

    def test_regression_matrix_has_all_required_deterministic_routes(self) -> None:
        cases = self.matrix["cases"]
        self.assertGreaterEqual(
            len(cases),
            self.matrix["case_contract"]["minimum_cases"],
        )
        self.assertEqual(
            {case["case_id"] for case in cases},
            {
                "P65R-001",
                "P65R-002",
                "P65R-003",
                "P65R-004",
                "P65R-005",
                "P65R-006",
                "P65R-007",
            },
        )
        required = set(self.matrix["case_contract"]["required_fields"])
        for case in cases:
            with self.subTest(case=case["case_id"]):
                self.assertFalse(required - set(case))
                self.assertTrue(case["positive_assertions"])
                self.assertTrue(case["negative_assertions"])
                self.assertTrue(case["prompt_markers"])
                ceiling = case["proof_ceiling"].lower()
                self.assertIn("model obedience", ceiling)
                self.assertIn("unproven", ceiling)

        by_id = {case["case_id"]: case for case in cases}
        self.assertEqual(by_id["P65R-001"]["expected_primary"], "P04")
        self.assertEqual(by_id["P65R-001"]["expected_follow_ons"], ["P12"])
        self.assertEqual(by_id["P65R-002"]["expected_primary"], "P06")
        self.assertEqual(by_id["P65R-003"]["expected_primary"], "P12")
        self.assertEqual(by_id["P65R-004"]["expected_primary"], "P04")
        self.assertEqual(by_id["P65R-005"]["expected_primary"], "P56")
        self.assertEqual(by_id["P65R-006"]["expected_primary"], "P04")
        self.assertEqual(by_id["P65R-006"]["expected_follow_ons"], ["P12"])
        self.assertEqual(by_id["P65R-007"]["expected_primary"], "P04")
        self.assertEqual(by_id["P65R-007"]["expected_follow_ons"], ["P12"])

    def test_all_protected_capabilities_have_regression_cases(self) -> None:
        covered = {
            capability
            for case in self.matrix["cases"]
            for capability in case["capabilities"]
        }
        self.assertEqual(set(self.matrix["capability_ids"]), covered)

    def test_matrix_markers_bind_effective_p65(self) -> None:
        content = self.effective["copyContent"]
        for case in self.matrix["cases"]:
            for marker in case["prompt_markers"]:
                with self.subTest(case=case["case_id"], marker=marker):
                    self.assertIn(marker, content)

    def test_effective_p65_models_stages_and_rejects_false_binary(self) -> None:
        p65 = self.effective
        content = p65["copyContent"]
        for marker in (
            "STAGED ROUTING / ACTOR BOUNDARY",
            "Current-agent disposition:",
            "Requested output:",
            "Downstream disposition:",
            "Actor/disposition boundaries are facts when the user has already specified them.",
            "Explicit actor/stage boundaries are facts once the user states them.",
            "Do not force a false binary whose alternatives omit the user's stated desired state.",
            "never reduce plan→handoff to “execute the repo work now” versus “only tell me what you found.”",
            "starting state | user outcome | current-agent disposition | requested output | downstream disposition if any | work shape | proof need | material constraints",
        ):
            self.assertIn(marker, content)
        self.assertIn("current-agent disposition", p65["expectedOutput"])
        self.assertIn("downstream-agent disposition", p65["expectedOutput"])
        self.assertIn("false binaries", p65["proofGate"])
        self.assertIn("actor/stage boundaries", p65["proofGate"])

    def test_composite_route_examples_preserve_primary_owner_boundaries(self) -> None:
        content = self.effective["copyContent"]
        for marker in (
            "Known repository + inaccessible/interrupted local residue + inspect provider evidence + form a preservation/convergence plan + hand off to the local executor → P04 primary, P12 follow-on.",
            "Dirty local repository + preserve useful work + reconcile/clean/merge when safe → P06 primary.",
            "Work is already complete + compress proven state for the next agent → P12 primary.",
            "Inspect repository evidence and decide reconciliation order without executing it → P04 primary.",
            "Recover prior decisions and create/update the canonical tracked handoff/document as the deliverable → P56 primary.",
            "Determine sprint decomposition now, then produce an executor handoff → planning owner primary; P12 packages the handoff; downstream executor behavior must not cause premature P07 routing.",
        ):
            self.assertIn(marker, content)
        self.assertIn(
            "Do not route to a downstream execution prompt merely because the handoff recipient may eventually execute.",
            content,
        )
        self.assertIn(
            "Do not route to P56 merely because a plan or handoff is an artifact",
            content,
        )

    def test_regression_is_registered_in_deterministic_floor(self) -> None:
        floor = json.loads(TEST_FLOOR.read_text(encoding="utf-8"))
        self.assertIn(TEST_PATH, floor["self_tests"])


if __name__ == "__main__":
    unittest.main()
