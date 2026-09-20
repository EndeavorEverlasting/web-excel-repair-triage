from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry as builder

ROOT = Path(__file__).resolve().parents[1]
PROMPT_KIT_JS = ROOT / "docs" / "prompt-kit.js"


class P07CanonicalCopyIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        operational = {prompt["id"]: prompt for prompt in builder.load_prompt_registry()}
        prompt_kit = {prompt["id"]: prompt for prompt in builder.load_prompt_kit_registry()}
        cls.base = operational["P07"]["copyContent"]
        cls.p07 = prompt_kit["P07"]

    def test_canonical_p07_retains_fixed_point_compute_and_integration_law(self) -> None:
        for phrase in (
            "ITERATIVE SPRINT FIXED-POINT",
            "The first green result is evidence, not an automatic stop signal",
            "EXHAUSTIVE AVAILABLE COMPUTE RULE",
            "Exhaust the decision-relevant safe compute available",
            "P07 MAINLINE CONVERGENCE OVERRIDE",
            "In P07, branch creation, worktree creation, a commit, a push, an open pull request, review-ready state, or green CI are intermediate evidence only",
            "PARALLEL EXECUTION IS AN EXECUTION REQUIREMENT",
            "REGRESSION SAFETY / RECURRING DEFECT CONTRACT",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.base)

    def test_compiled_profiles_remain_execution_metadata(self) -> None:
        compiled = self.p07["compiledEffectivePrompts"]
        self.assertIn("exhaustive", compiled)
        self.assertIn("efficient", compiled)
        self.assertIn("Execution profile: exhaustive", compiled["exhaustive"])
        self.assertIn("Execution profile: efficient", compiled["efficient"])

    def test_detail_panel_preserves_canonical_copy_content(self) -> None:
        source = PROMPT_KIT_JS.read_text(encoding="utf-8")
        self.assertIn("safeCopyContent=escapePromptHtml(p.copyContent||'')", source)
        self.assertNotIn('data-prompt-effective-content="true"', source)
        self.assertNotIn("function resolvePromptDetailContent(prompt)", source)

    def test_copy_resolver_requires_explicit_prompt_choice_for_efficient_variant(self) -> None:
        script = r'''
const api=require('./docs/prompt-kit-compute-mode.js');
const prompt={
  id:'P07',
  copyContent:'CANONICAL P07',
  compiledEffectivePrompts:{
    exhaustive:'COMPILED EXHAUSTIVE',
    efficient:'COMPILED EFFICIENT'
  }
};
for(const options of [
  {userDefault:'exhaustive'},
  {userDefault:'efficient'},
  {runOverride:'efficient',userDefault:'efficient'},
  {promptOverride:'exhaustive',userDefault:'efficient'}
]){
  const got=api.resolveCopyContent(prompt,options);
  if(got!==prompt.copyContent){
    console.error('silent shrink: '+JSON.stringify(options)+' => '+got);
    process.exit(1);
  }
}
const explicitEfficient=api.resolveCopyContent(prompt,{promptOverride:'efficient'});
if(explicitEfficient!=='COMPILED EFFICIENT'){
  console.error('explicit efficient: '+explicitEfficient);
  process.exit(2);
}
const variants=api.availablePromptVariants(prompt);
if(JSON.stringify(variants)!==JSON.stringify(['exhaustive','efficient'])){
  console.error('variants: '+JSON.stringify(variants));
  process.exit(3);
}
const fallback=api.resolveCopyContent(
  {id:'P07',compiledEffectivePrompts:{exhaustive:'COMPILED ONLY'}},
  {userDefault:'exhaustive'}
);
if(fallback!=='COMPILED ONLY'){
  console.error('fallback: '+fallback);
  process.exit(4);
}
process.stdout.write('explicit-variant-authority-preserved');
'''
        result = subprocess.run(
            ['node', '-e', script],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stdout, 'explicit-variant-authority-preserved')


if __name__ == "__main__":
    unittest.main()
