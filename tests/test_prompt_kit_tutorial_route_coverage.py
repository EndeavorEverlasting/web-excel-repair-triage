from __future__ import annotations

import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry
from scripts import validate_prompt_kit_tutorial_routes as route_validator

ROOT = Path(__file__).resolve().parents[1]
GUIDED = ROOT / "docs" / "prompt-kit-guided-recommendations.js"


class PromptKitTutorialRouteCoverageTests(unittest.TestCase):
    def test_every_current_prompt_is_reachable(self) -> None:
        report = route_validator.audit()
        prompts = build_prompt_kit_registry.load_prompt_kit_registry()
        self.assertTrue(report["ready"], report)
        self.assertEqual(report["prompt_count"], len(prompts))
        self.assertEqual(report["reachable_count"], len(prompts))
        self.assertEqual(report["unreachable"], [])

    def test_default_path_is_four_questions_with_optional_fifth(self) -> None:
        report = route_validator.audit()
        self.assertEqual(report["fixed_questions"], 3)
        self.assertEqual(report["default_questions"], 4)
        self.assertEqual(report["max_questions"], 5)
        guided = GUIDED.read_text(encoding="utf-8")
        self.assertEqual(guided.count("{id:'startingPoint'"), 1)
        self.assertEqual(guided.count("{id:'goal'"), 1)
        self.assertEqual(guided.count("{id:'proofNeed'"), 1)
        self.assertIn("renderAdaptiveQuestion", guided)
        self.assertIn("optional specialist finder", guided)

    def test_specialist_fallback_uses_live_registry_not_prompt_id_table(self) -> None:
        guided = GUIDED.read_text(encoding="utf-8")
        self.assertIn("if(!q)return PROMPTS.slice().sort", guided)
        self.assertIn("return sharedSearch(q)", guided)
        self.assertIn("Something else — show every prompt", guided)
        self.assertNotIn("var R=", guided)
        self.assertNotIn("NEXT_PROMPT_MAP", guided)

    def test_generic_query_candidates_are_not_truncated_per_query(self) -> None:
        guided = GUIDED.read_text(encoding="utf-8")
        self.assertNotIn("sharedSearch(query).slice(0,5)", guided)
        self.assertIn("var perQuestion={}", guided)
        self.assertIn("Math.max(perQuestion[prompt.id]||0,points)", guided)


if __name__ == "__main__":
    unittest.main()
