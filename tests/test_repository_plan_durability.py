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
BASE = ROOT / "docs" / "prompts.json"
AI = ROOT / "registry" / "prompts" / "ai-engineering-level-up-prompts.v1.json"
PLAN_MARKER = "REPOSITORY PLAN DURABILITY CONTRACT"
STATE_MARKER = "EVIDENCE STATE / NO PROMOTION CONTRACT"


class RepositoryPlanDurabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))
        cls.raw = {p["id"]: p for p in json.loads(BASE.read_text(encoding="utf-8"))}
        ai_payload = json.loads(AI.read_text(encoding="utf-8"))
        cls.ai_raw = {p["id"]: p for p in ai_payload["prompts"]}
        cls.effective = {p["id"]: p for p in build_prompt_kit_registry.load_prompt_registry()}

    def test_shared_policy_makes_chat_only_repository_plans_noncanonical(self) -> None:
        appendix = self.policy["copy_content_appendix"]
        self.assertIn(PLAN_MARKER, appendix)
        for phrase in (
            "chat alone is not a canonical planning surface",
            "active pull request",
            "approved in chat triggers synchronization",
            "Multi-phase repository work must persist the whole phase map",
            "P66",
            "Closeout is invalid",
        ):
            self.assertIn(phrase, appendix)
        self.assertTrue(any("exists only in chat" in item for item in self.policy["forbidden_solo_actions"]))

    def test_shared_policy_forbids_evidence_state_promotion(self) -> None:
        appendix = self.policy["copy_content_appendix"]
        self.assertIn(STATE_MARKER, appendix)
        for phrase in (
            "PLANNED/DESIGNED",
            "IMPLEMENTED",
            "WIRED/REACHABLE",
            "INTEGRATED",
            "different chat, agent, worktree, branch, or PR",
            "named future phase",
            "strongest proven state",
        ):
            self.assertIn(phrase, appendix)
        self.assertIn("Do not promote evidence states", self.policy["next_step_suffix"])

    def test_p02_and_p04_persist_actionable_repository_plans(self) -> None:
        self.assertIn("DURABLE REPOSITORY PLAN HANDOFF", self.raw["P02"]["copyContent"])
        self.assertIn("DURABLE PLAN OUTPUT", self.raw["P04"]["copyContent"])
        self.assertIn("P66", self.raw["P02"]["copyContent"])
        self.assertIn("P66", self.raw["P04"]["copyContent"])
        self.assertIn("canonical tracked plan", self.raw["P02"]["expectedOutput"])
        self.assertIn("active PR", self.raw["P04"]["proofGate"])
        self.assertIn("no canonical plan owner or active PR exists", self.raw["P02"]["nextStep"])
        self.assertIn("If none exists and there is no active PR", self.raw["P04"]["nextStep"])
        self.assertIn("smallest tracked plan artifact", self.policy["copy_content_appendix"])

    def test_p12_refuses_chat_only_or_state_promoted_closeout(self) -> None:
        p12 = self.raw["P12"]
        self.assertIn("DURABLE CLOSEOUT GATE", p12["copyContent"])
        self.assertIn("phase-local", p12["copyContent"].lower())
        self.assertIn("PLANNED/DESIGNED/TRACKED", p12["copyContent"])
        self.assertIn("actionable repository plan or successor phase exists only in chat", p12["proofGate"])

    def test_p07_phase_continuity_repair_remains_present(self) -> None:
        p07 = self.raw["P07"]["copyContent"]
        for phrase in (
            "PHASE-LOCAL OUT OF SCOPE",
            "USER/REPO FORBIDDEN",
            "do not by themselves forbid a later successor phase",
        ):
            self.assertIn(phrase, p07)

    def test_p100_names_state_promotion_without_breaking_prompt_budget(self) -> None:
        p100 = self.ai_raw["P100"]
        self.assertIn("DESIGNED is not WIRED", p100["proofGate"])
        self.assertIn("concurrent chat/branch/PR activity", p100["proofGate"])
        self.assertIn("evidence-state promotion", p100["keywords"])
        self.assertIn("designed vs implemented", p100["keywords"])
        self.assertLess(len(p100["copyContent"]), 8000)

    def test_shared_contract_reaches_plan_build_closeout_ledger_and_diagnosis(self) -> None:
        for prompt_id in ("P02", "P04", "P07", "P12", "P66", "P83", "P95", "P100", "P141"):
            self.assertIn(prompt_id, self.effective)
            copy = self.effective[prompt_id]["copyContent"]
            self.assertIn(PLAN_MARKER, copy)
            self.assertIn(STATE_MARKER, copy)


if __name__ == "__main__":
    unittest.main()
