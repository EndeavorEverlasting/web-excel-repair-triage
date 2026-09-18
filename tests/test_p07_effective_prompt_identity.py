from __future__ import annotations

import subprocess
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

    def test_detail_panel_preserves_canonical_copy_content(self) -> None:
        source = PROMPT_KIT_JS.read_text(encoding="utf-8")
        self.assertIn("safeCopyContent=escapePromptHtml(p.copyContent||'')", source)
        self.assertNotIn('data-prompt-effective-content="true"', source)
        self.assertNotIn("function resolvePromptDetailContent(prompt)", source)

    def test_copy_resolver_preserves_canonical_p07_across_compute_modes(self) -> None:
        script = r"""
const api=require('./docs/prompt-kit-compute-mode.js');
const prompt={
  id:'P07',
  copyContent:'CANONICAL P07',
  compiledEffectivePrompts:{
    exhaustive:'COMPILED EXHAUSTIVE',
    efficient:'COMPILED EFFICIENT'
  }
};
for(const profile of ['exhaustive','efficient']){
  const got=api.resolveCopyContent(prompt,{userDefault:profile});
  if(got!==prompt.copyContent){
    console.error(profile+': '+got);
    process.exit(1);
  }
}
const fallback=api.resolveCopyContent(
  {id:'P07',compiledEffectivePrompts:{exhaustive:'COMPILED ONLY'}},
  {userDefault:'exhaustive'}
);
if(fallback!=='COMPILED ONLY'){
  console.error('fallback: '+fallback);
  process.exit(2);
}
process.stdout.write('canonical-copy-preserved');
"""
        result = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stdout, "canonical-copy-preserved")


if __name__ == "__main__":
    unittest.main()
