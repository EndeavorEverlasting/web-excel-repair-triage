from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry

POLICY = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
ROADMAP = ROOT / "harness" / "prompt-topology" / "PHASE_B_C_ROADMAP.md"
MARKER = "REPOSITORY PLAN DURABILITY CONTRACT"


class RepositoryPlanDurabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))
        raw = json.loads((ROOT / "docs" / "prompts.json").read_text(encoding="utf-8"))
        cls.raw = {p["id"]: p for p in raw}
        cls.prompts = {p["id"]: p for p in build_prompt_kit_registry.load_prompt_registry()}
        cls.roadmap = ROADMAP.read_text(encoding="utf-8")

    def test_shared_policy_makes_chat_only_repo_plans_noncanonical(self) -> None:
        appendix = self.policy["copy_content_appendix"]
        self.assertIn(MARKER, appendix)
        for phrase in (
            "chat alone is not a canonical planning surface",
            "persist the complete plan",
            "active pull request",
            "plan approved in chat triggers synchronization",
            "Multi-phase repository work must persist the whole phase map",
            "Closeout is invalid",
        ):
            self.assertIn(phrase, appendix)

    def test_next_step_contract_requires_durable_plan_before_handoff(self) -> None:
        suffix = self.policy["next_step_suffix"]
        self.assertIn("chat text is provisional rather than canonical repository state", suffix)
        self.assertIn("active pull request", suffix)

    def test_p02_and_p04_raw_owners_no_longer_treat_chat_as_durable_owner(self) -> None:
        self.assertIn("DURABLE REPOSITORY PLAN HANDOFF", self.raw["P02"]["copyContent"])
        self.assertIn("DURABLE PLAN OUTPUT", self.raw["P04"]["copyContent"])
        self.assertIn("canonical tracked plan", self.raw["P02"]["expectedOutput"])
        self.assertIn("canonical", self.raw["P04"]["expectedOutput"])
        self.assertIn("active PR", self.raw["P04"]["proofGate"])

    def test_representative_planning_and_execution_prompts_receive_contract(self) -> None:
        for prompt_id in ("P02", "P04", "P07", "P95", "P141"):
            self.assertIn(prompt_id, self.prompts)
            self.assertIn(MARKER, self.prompts[prompt_id]["copyContent"])
            self.assertIn("chat alone is not a canonical planning surface", self.prompts[prompt_id]["copyContent"])

    def test_topology_successor_plan_is_durable_and_complete_enough_to_sprint(self) -> None:
        self.assertTrue(ROADMAP.is_file())
        for phrase in (
            "Phase A COMPLETE",
            "Phase B — Deterministic 3D projection + spatial stability",
            "Phase C — Read-only interactive topology viewer",
            "Behavioral telemetry channels",
            "Vector database",
            "Prompt identity / ontology rewrites",
            "Execution order",
            "Acceptance gates",
        ):
            self.assertIn(phrase, self.roadmap)

    def test_roadmap_preserves_semantic_visualization_boundary(self) -> None:
        for phrase in (
            "projection/viewer output cannot influence clustering",
            "projection remains visualization-only",
            "visual proximity as classification truth",
        ):
            self.assertIn(phrase, self.roadmap)


if __name__ == "__main__":
    unittest.main()
