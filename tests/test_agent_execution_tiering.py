from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "harness" / "contracts" / "agent-execution-tiering.v1.json"
GOVERNANCE = ROOT / "AGENTS.md"


class AgentExecutionTieringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))
        cls.governance = GOVERNANCE.read_text(encoding="utf-8")

    def test_policy_is_machine_readable_and_evidence_earned(self) -> None:
        self.assertEqual(self.policy["schema_version"], "agent-execution-tiering/v1")
        self.assertEqual(
            self.policy["assignment_basis"],
            [
                "scope-specific",
                "evidence-earned",
                "environment-aware",
                "revocable",
                "operator-authorized",
            ],
        )
        rules = self.policy["rules"]
        self.assertTrue(rules["tool_or_model_label_is_not_authority"])
        self.assertTrue(rules["unknown_or_unproven_agent_routes_down"])
        self.assertTrue(rules["shared_contracts_before_parallel_consumers"])
        self.assertTrue(rules["promotion_requires_operator_approval"])
        self.assertTrue(rules["promotion_requires_evaluation_evidence"])

    def test_only_current_strategic_owners_receive_harness_authority(self) -> None:
        tiers = {item["id"]: item for item in self.policy["tiers"]}
        strategic = tiers["strategic-harness-owner"]
        self.assertEqual(strategic["current_agents"], ["chatgpt", "auggie"])
        for surface in (
            "governance",
            "harness-spine",
            "skills",
            "capabilities",
            "triggers",
            "routing",
            "validators-and-proof-gates",
            "cross-repository-architecture-and-migration-authority",
        ):
            self.assertIn(surface, strategic["owned_surfaces"])

    def test_desktop_and_opencode_are_bounded_by_default(self) -> None:
        tiers = {item["id"]: item for item in self.policy["tiers"]}
        bounded = tiers["bounded-application-executor"]
        self.assertIn("desktop-app", bounded["current_agents"])
        self.assertIn("opencode", bounded["current_agents"])
        self.assertIn("conventional-application-logic", bounded["owned_surfaces"])
        self.assertIn("ui", bounded["owned_surfaces"])
        for forbidden in (
            "governance mutation",
            "harness-spine mutation",
            "skill capability or trigger ownership changes",
            "validator or proof-gate weakening",
            "cross-repository authority changes",
        ):
            self.assertIn(forbidden, bounded["forbidden_without_promotion"])

    def test_governance_routes_to_the_machine_policy(self) -> None:
        for phrase in (
            "Parallelism is capability-earned, not equal-authority",
            "Strategic/harness owners are `ChatGPT` and `Auggie`",
            "`desktop-app` and `OpenCode` are executors",
            "harness/contracts/agent-execution-tiering.v1.json",
            "Promotion requires explicit operator approval and evaluation evidence",
            "Shared contracts precede parallel consumers",
        ):
            self.assertIn(phrase, self.governance)
        self.assertLessEqual(len(self.governance), 5200)


if __name__ == "__main__":
    unittest.main()
