from __future__ import annotations

import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry as registry

ROOT = Path(__file__).resolve().parents[1]


class AgenticLoopPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.operational = {p["id"]: p for p in registry.load_prompt_registry()}
        cls.all_prompts = {p["id"]: p for p in registry.load_prompt_kit_registry()}

    def test_continuous_loop_prompt_encodes_progress_and_green_slice_convergence(self):
        prompt = next(p for p in self.all_prompts.values() if p["name"] == "Continuous Agentic Repo Loop Runner")
        content = prompt["copyContent"]
        self.assertIn("REFRESH -> ORIENT -> SELECT NEXT GATE -> EXECUTE -> VALIDATE -> CRITIQUE -> INTEGRATE -> REFRESH -> CONTINUE", content)
        self.assertIn("A pass is legitimate only if", content)
        self.assertIn("CONTINUOUS GREEN-SLICE INTEGRATION", content)
        self.assertIn("Do not keep a validated slice unmerged just because the larger mission has more work remaining.", content)
        self.assertIn("ANTI-SPIN AND RETRY DISCIPLINE", content)
        self.assertIn("RECOVERY AND INTERRUPTIBILITY", content)
        self.assertIn("FIXED POINT", content)
        self.assertEqual(prompt["actionabilityPolicy"], registry.load_actionability_policy()["policy_id"])

    def test_hardener_targets_early_stop_spin_recovery_and_merge_forward_failures(self):
        prompt = next(p for p in self.all_prompts.values() if p["name"] == "Agentic Loop Harness Hardener")
        content = prompt["copyContent"]
        for phrase in (
            "plan/status-only termination",
            "green branches/PRs stranded instead of integrated",
            "DEFINE A PROGRESS STATE MACHINE",
            "SEPARATE PROGRESS LOOPS FROM RETRY LOOPS",
            "ENFORCE CONTINUOUS GREEN-SLICE CONVERGENCE",
            "HARDEN RESUME / INTERRUPTION RECOVERY",
            "ADD EXECUTABLE REGRESSIONS",
            "ITERATE THE HARDENING ITSELF",
        ):
            self.assertIn(phrase, content)
        self.assertEqual(prompt["actionabilityPolicy"], registry.load_actionability_policy()["policy_id"])

    def test_p07_and_p83_have_direct_continuous_loop_invariants(self):
        p07 = self.operational["P07"]["copyContent"]
        p83 = self.operational["P83"]["copyContent"]
        for content in (p07, p83):
            self.assertIn("CONTINUOUS AGENTIC LOOP INVARIANT", content)
            self.assertIn("bounded green slice", content)
            self.assertIn("refresh", content.lower())
            self.assertIn("continue", content.lower())
        self.assertIn("do not strand it while broader mission work remains", p07.lower())
        self.assertIn("after integrating verified inherited work", p83.lower())

    def test_generated_site_is_exact_and_contains_agentic_loop_prompts(self):
        expected = registry.render()
        actual = (ROOT / "web" / "prompt-kit" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(actual, expected)
        self.assertIn("Continuous Agentic Repo Loop Runner", actual)
        self.assertIn("Agentic Loop Harness Hardener", actual)


if __name__ == "__main__":
    unittest.main()
