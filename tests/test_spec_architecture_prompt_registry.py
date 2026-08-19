from __future__ import annotations

import json
import unittest
from pathlib import Path

import build_prompt_kit
from scripts import build_prompt_kit_registry


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_REGISTRY = REPO_ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"


class SpecArchitecturePromptRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.operational = {
            prompt["id"]: prompt
            for prompt in build_prompt_kit_registry.load_prompt_registry()
        }
        cls.full = {
            prompt["id"]: prompt
            for prompt in build_prompt_kit_registry.load_prompt_kit_registry()
        }
        cls.policy = build_prompt_kit_registry.load_actionability_policy()
        raw_prompts = json.loads(RAW_REGISTRY.read_text(encoding="utf-8"))["prompts"]
        cls.raw = {prompt["id"]: prompt for prompt in raw_prompts}

    def test_p76_is_operational_and_distinct_from_general_context_engineering(self) -> None:
        prompt = self.operational["P76"]
        self.assertEqual(prompt["seq"], "76")
        self.assertEqual(prompt["profile"], "spec-architecture")
        self.assertEqual(prompt["color"], "Cyan")
        self.assertEqual(prompt["class"], "HARNESS / SPEC ARCHITECTURE")
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], prompt["copyContent"])
        self.assertEqual(self.operational["P68"]["class"], "AI ENGINEERING / CONTEXT")
        self.assertNotEqual(self.operational["P68"]["class"], prompt["class"])

    def test_prompt_encodes_three_zoom_levels_and_demand_loaded_ground_detail(self) -> None:
        content = self.full["P76"]["copyContent"]
        self.assertIn("50,000 FT — ORIENTATION", content)
        self.assertIn("30,000 FT — DOMAIN / CAPABILITY", content)
        self.assertIn("15,000 FT — WORKFLOW / SPEC", content)
        self.assertIn("Target <= 1,000 approximate tokens", content)
        self.assertIn("Target <= 2,000 additional approximate tokens", content)
        self.assertIn("Target <= 4,000 additional approximate tokens", content)
        self.assertIn("Large code files, historical reports, full schemas, fixtures", content)
        self.assertIn("remain on-demand", content)

    def test_prompt_factors_authority_instead_of_summarizing_everything(self) -> None:
        content = self.full["P76"]["copyContent"]
        self.assertIn("`AGENTS.md`: governance, precedence, universal safety/operating law", content)
        self.assertIn("skills: repeatable procedure and judgment only", content)
        self.assertIn("Preserve one canonical owner and lightweight references elsewhere", content)
        self.assertIn("Do not preload every skill, nested AGENTS file, tool schema", content)
        self.assertIn("IMPLEMENT, DON'T JUST RECOMMEND", content)
        self.assertIn("no unique rule or authority disappeared", content)

    def test_prompt_requires_measured_before_after_retrieval_cost(self) -> None:
        content = self.full["P76"]["copyContent"]
        self.assertIn("MEASURE BEFORE MODIFYING", content)
        self.assertIn("What is this app and how is it organized?", content)
        self.assertIn("Record which files and approximate tokens/bytes", content)
        self.assertIn("measured default context falls meaningfully", content)
        self.assertIn("representative tasks still succeed", content)

    def test_glossary_prompt_reduces_prose_without_creating_competing_truth(self) -> None:
        prompt = self.full["P78"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["seq"], "78")
        self.assertEqual(prompt["profile"], "spec-architecture")
        self.assertEqual(prompt["color"], "Cyan")
        self.assertEqual(prompt["class"], "HARNESS / KNOWLEDGE ARCHITECTURE")
        self.assertIn("DIET THE REPOSITORY DOCUMENTATION DOWN TO A LEAN GLOSSARY", content)
        self.assertIn("glossary may explain vocabulary", content)
        self.assertIn("must not become a second specification", content)
        self.assertIn("KEEP-AUTHORITY, KEEP-OPERATIONAL, COLLAPSE-INTO-GLOSSARY", content)
        self.assertIn("Do not create a new tutorial", content)
        self.assertIn("current code plus its contracts/tests/validators", content)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)

    def test_prompt_adder_consumes_preceding_context_and_executes_registry_work(self) -> None:
        prompt = self.full["P79"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["seq"], "79")
        self.assertEqual(prompt["profile"], "spec-architecture")
        self.assertEqual(prompt["color"], "Cyan")
        self.assertEqual(prompt["class"], "PROMPT KIT / REGISTRY OPERATIONS")
        self.assertIn("CONTEXT IMMEDIATELY ABOVE THIS INSTRUCTION", content)
        self.assertIn("DO NOT ASK ME TO RESTATE CONTEXT", content)
        self.assertIn("Assign the next valid unused `P##` identity", content)
        self.assertIn("Reuse the closest existing extension registry and profile", content)
        self.assertIn("registry record plus focused test is normally the documentation", content)
        self.assertIn("Regenerate the canonical website", content)
        self.assertIn("merge the exact green authorized head", content)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)

    def test_new_source_prompts_are_intentionally_bounded(self) -> None:
        for prompt_id in ("P78", "P79"):
            content = self.raw[prompt_id]["copyContent"]
            self.assertLess(len(content), 5000)
            self.assertGreater(len(content), 1800)

    def test_raw_p76_prompt_is_itself_bounded(self) -> None:
        content = self.raw["P76"]["copyContent"]
        self.assertLess(len(content), 7000)
        self.assertGreater(len(content), 2500)

    def test_discovery_aliases_route_spec_bloat_queries_to_p76(self) -> None:
        self.assertEqual(build_prompt_kit.SYNONYMS["spec driven development"], "P76")
        self.assertEqual(build_prompt_kit.SYNONYMS["progressive disclosure"], "P76")
        self.assertEqual(build_prompt_kit.SYNONYMS["harness bloat"], "P76")
        self.assertEqual(build_prompt_kit.SYNONYMS["50000 ft"], "P76")

    def test_render_contains_spec_profile_and_all_three_prompts(self) -> None:
        html = build_prompt_kit_registry.render()
        self.assertIn("prompt-kit-spec-architecture-styles", html)
        self.assertIn("spec-architecture", html)
        self.assertIn("◎ Spec Layers", html)
        self.assertIn("Progressive-Disclosure Spec & Harness Factorer", html)
        self.assertIn("Repository Glossary & Documentation Diet", html)
        self.assertIn("Prompt Registry Prompt Adder", html)


if __name__ == "__main__":
    unittest.main()
