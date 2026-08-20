from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

import sys

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry


class RepositoryWorkLedgerPromptTests(unittest.TestCase):
    def prompts_by_id(self) -> dict[str, dict]:
        prompts = build_prompt_kit_registry.load_prompt_registry()
        return {item["id"]: item for item in prompts}

    def prompt(self) -> dict:
        return self.prompts_by_id()["P66"]

    def test_p66_is_registered_with_stable_identity_and_discovery_rank(self) -> None:
        prompt = self.prompt()
        self.assertEqual(prompt["seq"], "66")
        self.assertEqual(prompt["name"], "Repository Work Ledger Steward")
        self.assertEqual(prompt["type"], "SETUP")
        self.assertEqual(prompt["class"], "AGENT HARNESS / WORK LEDGER")
        self.assertEqual(prompt["discoveryRank"], 4)
        self.assertEqual(prompt["displayOrderPolicy"], "prompt-kit-guided-discovery-order")
        self.assertIn("repository ledger", prompt["keywords"])
        self.assertIn("weak model", prompt["keywords"])

    def test_p66_preserves_authority_and_weak_model_safety_contract(self) -> None:
        content = self.prompt()["copyContent"]
        for phrase in (
            "DO NOT CREATE A COMPETING SOURCE OF TRUTH",
            "MODE DECISION — CHOOSE ONE BEFORE MUTATION",
            "ESTABLISH: no usable repository ledger exists",
            "ADOPT: a family/shared ledger contract exists",
            "CONTRIBUTE: the canonical local ledger exists",
            "REPAIR: a ledger exists but has ambiguous state",
            "WEAK-MODEL-SAFE LEDGER CONTRACT",
            "READY — unclaimed and executable now",
            "CLAIMED — one identified agent/session",
            "DONE — acceptance gate satisfied",
            "commit:<git-sha>",
            "none; no safe actionable work remains",
            "One writer owns one task block at a time",
            "Reconcile queue conflicts semantically",
            "Seed only real current tasks",
            "Do not weaken a check to make the ledger pass",
        ):
            self.assertIn(phrase, content)

    def test_p66_requires_local_validation_and_rejects_remote_authority_duplication(self) -> None:
        content = self.prompt()["copyContent"]
        for phrase in (
            "The consumer owns its validator and tests",
            "do not execute a remote validator",
            "duplicate task and duplicate-field rejection",
            "concrete claimed owners",
            "exact BLOCKED/OPERATOR gates",
            "durable DONE proof",
            "stale-reference handling",
            "concurrent-task preservation",
        ):
            self.assertIn(phrase, content)

    def test_p83_is_registered_as_distinct_cross_agent_verification_workflow(self) -> None:
        prompt = self.prompts_by_id()["P83"]
        self.assertEqual(prompt["seq"], "83")
        self.assertEqual(prompt["name"], "Agent Work Verifier & Iterative Advancer")
        self.assertEqual(prompt["type"], "VERIFY + ADVANCE")
        self.assertEqual(prompt["class"], "AGENT HARNESS / ITERATIVE REVIEW")
        self.assertEqual(prompt["color"], "Teal")
        self.assertEqual(prompt["category"], "standard")
        self.assertIn("verify another agent", prompt["keywords"])
        self.assertIn("claim to evidence", prompt["keywords"])
        self.assertNotEqual(prompt["class"], self.prompts_by_id()["P07"]["class"])

    def test_p83_verifies_inherited_claims_then_repairs_advances_and_rechecks(self) -> None:
        content = self.prompts_by_id()["P83"]["copyContent"]
        for phrase in (
            "DO NOT TREAT THE HANDOFF OR COMPLETION CLAIM AS PROOF",
            "TREAT CLAIMS AS HYPOTHESES",
            "VERIFIED, STALE, PARTIAL, CONTRADICTED, or UNPROVEN",
            "VERIFY -> CRITIQUE -> REPAIR OR ADVANCE -> VALIDATE -> INSPECT NEW EVIDENCE",
            "Pass 2: deliberately review",
            "Continue until a bounded fixed point",
            "CORRECT WITHOUT REGRESSING GOOD WORK",
            "ADVANCE BEYOND REVIEW",
            "EXPAND ONLY WHEN EVIDENCE EARNS IT",
            "KEEP AGENT-CAPABLE WORK WITH THE AGENT",
            "USER-ONLY GATE",
            "REPORT PROGRESS AS EVIDENCE, NOT NARRATION",
            "STOP ONLY AT THE REAL FIXED POINT",
        ):
            self.assertIn(phrase, content)

    def test_p83_limits_user_escalation_and_preserves_proof_boundaries(self) -> None:
        prompt = self.prompts_by_id()["P83"]
        content = prompt["copyContent"]
        for phrase in (
            "do not ask the user to repeat information that is available to the agent",
            "Do not ask the user to inspect files, run tests, collect logs",
            "watch CI, merge routine green work",
            "Ask the user only when the next material step truly requires",
            "advance every other safe owned action first",
            "Never claim runtime, deployment, physical-device, or human acceptance proof",
        ):
            self.assertIn(phrase, content)
        policy = build_prompt_kit_registry.load_actionability_policy()
        self.assertEqual(prompt["actionabilityPolicy"], policy["policy_id"])
        self.assertIn(policy["marker"], content)
        self.assertGreater(len(content), 3000)
        self.assertLess(len(content), 12000)

    def test_guided_questionnaire_exposes_repository_ledger_intent(self) -> None:
        guided = (ROOT / "docs" / "prompt-kit-guided-recommendations.js").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "Keep human and agent work continuous in a repository ledger",
            "'repository ledger'",
            "'work ledger'",
            "'agent queue'",
            "'shared work state'",
        ):
            self.assertIn(phrase, guided)

    def test_copyable_p65_finder_can_recommend_p66_without_inventing_it(self) -> None:
        p65 = self.prompts_by_id()["P65"]["copyContent"]
        self.assertIn(
            "P66 Repository Work Ledger Steward: establish, adopt, contribute to, or repair",
            p65,
        )
        self.assertLess(
            p65.index("P66 Repository Work Ledger Steward"),
            p65.index("RECOMMENDATION CONTRACT"),
        )

    def test_generated_preview_contains_p66_and_p83(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "prompt-kit.html"
            html = build_prompt_kit_registry.build(output)
        self.assertIn('"id": "P66"', html)
        self.assertIn("Repository Work Ledger Steward", html)
        self.assertIn("WEAK-MODEL-SAFE LEDGER CONTRACT", html)
        self.assertIn('"id": "P83"', html)
        self.assertIn("Agent Work Verifier & Iterative Advancer", html)
        self.assertIn("TREAT CLAIMS AS HYPOTHESES", html)

    def test_checked_in_site_contains_repository_continuity_routes_and_p83(self) -> None:
        deployed = (ROOT / "web" / "prompt-kit" / "index.html").read_text(
            encoding="utf-8"
        )
        self.assertEqual(deployed, build_prompt_kit_registry.render())
        self.assertIn('"id": "P66"', deployed)
        self.assertIn(
            "P66 Repository Work Ledger Steward: establish, adopt, contribute to, or repair",
            deployed,
        )
        self.assertIn(
            "Keep human and agent work continuous in a repository ledger",
            deployed,
        )
        self.assertIn('"id": "P83"', deployed)
        self.assertIn("Agent Work Verifier & Iterative Advancer", deployed)


if __name__ == "__main__":
    unittest.main()
