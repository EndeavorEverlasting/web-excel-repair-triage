from __future__ import annotations

import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry as builder

ROOT = Path(__file__).resolve().parents[1]
PROMPT_KIT_JS = ROOT / "docs" / "prompt-kit.js"
COMPUTE_MODE_JS = ROOT / "docs" / "prompt-kit-compute-mode.js"


class P07EffectivePromptIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        operational = {prompt["id"]: prompt for prompt in builder.load_prompt_registry()}
        prompt_kit = {prompt["id"]: prompt for prompt in builder.load_prompt_kit_registry()}
        cls.base = operational["P07"]["copyContent"]
        cls.p07 = prompt_kit["P07"]

    def test_compiled_profiles_preserve_the_canonical_p07_contract(self) -> None:
        compiled = self.p07["compiledEffectivePrompts"]
        for profile in ("exhaustive", "efficient"):
            with self.subTest(profile=profile):
                self.assertIn(self.base, compiled[profile])
                self.assertIn("EXECUTION PROFILE OVERLAY", compiled[profile])
                self.assertIn(f"Execution profile: {profile}", compiled[profile])

    def test_exhaustive_identity_retains_fixed_point_compute_and_integration_law(self) -> None:
        exhaustive = self.p07["compiledEffectivePrompts"]["exhaustive"]
        for phrase in (
            "ITERATIVE SPRINT FIXED-POINT",
            "The first green result is evidence, not an automatic stop signal",
            "EXHAUSTIVE AVAILABLE COMPUTE RULE",
            "Exhaust the decision-relevant safe compute available",
            "P07 MAINLINE CONVERGENCE OVERRIDE",
            "In P07, branch creation, worktree creation, a commit, a push, an open pull request, review-ready state, or green CI are intermediate evidence only",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, exhaustive)

    def test_efficient_profile_is_an_overlay_not_a_replacement_prompt(self) -> None:
        efficient = self.p07["compiledEffectivePrompts"]["efficient"]
        self.assertIn("Compute policy: minimum_sufficient_compute", efficient)
        self.assertIn("Stop policy: sufficient_proof_for_requested_scope", efficient)
        self.assertIn("canonical prompt obligations remain in force", efficient.lower())

    def test_detail_panel_resolves_the_same_effective_identity_as_copy(self) -> None:
        source = PROMPT_KIT_JS.read_text(encoding="utf-8")
        self.assertIn("function resolvePromptDetailContent(prompt)", source)
        self.assertIn("PromptKitComputeMode.resolveCopyContent(prompt)", source)
        self.assertIn('data-prompt-effective-content="true"', source)
        self.assertNotIn("safeCopyContent=escapePromptHtml(p.copyContent||'')", source)

    def test_compute_mode_refresh_updates_open_panel_effective_content(self) -> None:
        source = COMPUTE_MODE_JS.read_text(encoding="utf-8")
        self.assertIn("function refreshDetail(doc,storage,promptId,promptCatalog)", source)
        self.assertIn("data-prompt-effective-content", source)
        self.assertIn("contentNode.textContent=resolveCopyContent(prompt,{storage:storage})", source)



def test_canonical_p07_forbids_premature_terminal_states(self) -> None:
    required = (
        "NON-SILENT CONTINUATION / TERMINATION CONTRACT (MANDATORY)",
        "CHECKPOINTS ARE NOT STOP CONDITIONS",
        "If any item is SAFE & EXECUTABLE and progress-bearing, execute it now.",
        "If progress stops because of a boundary, name the boundary immediately; never go silent at an unexplained edge.",
        "A terminal response is allowed only when no SAFE & EXECUTABLE progress-bearing item remains",
        "Any response that ends while SAFE & EXECUTABLE progress-bearing work remains is a P07 contract failure.",
        "Repeated premature stopping is itself a system defect.",
    )
    for phrase in required:
        with self.subTest(phrase=phrase):
            self.assertIn(phrase, self.base)
    for profile in ("exhaustive", "efficient"):
        rendered = self.p07["compiledEffectivePrompts"][profile]
        with self.subTest(profile=profile):
            for phrase in required:
                self.assertIn(phrase, rendered)

if __name__ == "__main__":
    unittest.main()
