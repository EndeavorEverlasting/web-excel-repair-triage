from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "harness" / "contracts" / "agent-capability-evidence.v1.json"
TIERING = ROOT / "harness" / "contracts" / "agent-execution-tiering.v1.json"


class AgentCapabilityEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.tiering = json.loads(TIERING.read_text(encoding="utf-8"))

    def test_deepswe_snapshot_is_scoped_and_pinned(self) -> None:
        source = self.evidence["benchmark_sources"][0]
        self.assertEqual(source["id"], "deepswe-v1.1-2026-09-02")
        self.assertEqual(source["tasks"], 113)
        self.assertEqual(source["harness"], "mini-swe-agent")
        self.assertEqual(source["metric"], "pass@1")
        self.assertIn("model + reasoning configuration", source["scope_note"])
        snapshot = {row["configuration"]: row for row in self.evidence["deepswe_frontier_snapshot"]}
        self.assertEqual(snapshot["gemini-3.8-flash[high]"]["pass_at_1_pct"], 74)
        self.assertEqual(snapshot["claude-opus-5[max]"]["pass_at_1_pct"], 74)
        self.assertEqual(snapshot["gpt-5.6-sol[max]"]["pass_at_1_pct"], 73)

    def test_product_agents_do_not_inherit_unproven_model_scores(self) -> None:
        identities = {row["agent_id"]: row for row in self.evidence["agent_identity_map"]}
        anti = identities["google-antigravity"]
        self.assertEqual(anti["model_mapping"], "UNKNOWN")
        self.assertIn("no DeepSWE score is inherited", anti["identity_note"])
        self.assertEqual(identities["auggie"]["product"], "Augment Code")
        self.assertIn("Do not conflate", identities["auggie"]["identity_note"])
        authority = self.evidence["authority"]
        self.assertTrue(authority["leaderboard_rank_alone_cannot_promote_agent"])
        self.assertTrue(authority["opaque_product_agent_must_not_inherit_underlying_model_score_without_proof"])

    def test_operator_observation_routes_antigravity_down_with_explicit_judgment_contract(self) -> None:
        observation = next(
            row for row in self.evidence["operator_observations"]
            if row["agent_id"] == "google-antigravity"
        )
        self.assertEqual(observation["evidence_class"], "operator-anecdotal")
        self.assertEqual(observation["routing_effect"], "route-down")
        self.assertEqual(observation["default_tier"], "bounded-application-executor")
        contract = "\n".join(observation["judgment_contract"])
        self.assertIn("material architecture and policy decisions must be settled", contract)
        self.assertIn("ambiguous or missing provider facts require STOP", contract)
        self.assertIn("no governance", contract)

    def test_execution_tiering_remains_authority_and_antigravity_is_not_strategic(self) -> None:
        self.assertEqual(
            self.tiering["evidence_registry"],
            "harness/contracts/agent-capability-evidence.v1.json",
        )
        tiers = {row["id"]: row for row in self.tiering["tiers"]}
        self.assertNotIn("google-antigravity", tiers["strategic-harness-owner"]["current_agents"])
        self.assertIn("google-antigravity", tiers["bounded-application-executor"]["current_agents"])
        self.assertEqual(
            self.tiering["agent_defaults"]["google-antigravity"],
            "bounded-application-executor",
        )
        self.assertTrue(self.tiering["rules"]["benchmark_rank_alone_cannot_promote_agent"])
        self.assertIn("Augment Code", self.tiering["identity_disambiguation"]["auggie"])
        self.assertIn("Google Anti-gravity", self.tiering["identity_disambiguation"]["google-antigravity"])


if __name__ == "__main__":
    unittest.main()
