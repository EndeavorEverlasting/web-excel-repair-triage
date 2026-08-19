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

    def test_client_prompt_pack_builds_local_overlay_without_global_mutation(self) -> None:
        prompt = self.full["P80"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["seq"], "80")
        self.assertEqual(prompt["profile"], "spec-architecture")
        self.assertEqual(prompt["class"], "PROMPT KIT / LOCAL PROFILE")
        self.assertIn("GLOBAL VS LOCAL BOUNDARY", content)
        self.assertIn("JSON file upload", content)
        self.assertIn("paste-JSON/text area", content)
        self.assertIn("type/color chips", content)
        self.assertIn("local:<profile_id>:<prompt_id>", content)
        self.assertIn("same search index", content)
        self.assertIn("Favorites", content)
        self.assertIn("export -> clear -> re-import", content)
        self.assertIn("Treat uploaded/pasted JSON as hostile input", content)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)

    def test_cache_prompt_covers_invalidation_and_production_failure_modes(self) -> None:
        prompt = self.full["P81"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["seq"], "81")
        self.assertEqual(prompt["class"], "SOFTWARE ARCHITECTURE / CACHING")
        self.assertIn("Client browser", content)
        self.assertIn("Distributed L2", content)
        self.assertIn("TTL / PASSIVE INVALIDATION", content)
        self.assertIn("EVENT-DRIVEN / ACTIVE INVALIDATION", content)
        self.assertIn("CACHE VERSIONING / KEY NAMESPACING", content)
        self.assertIn("CACHE STAMPEDE / THUNDERING HERD", content)
        self.assertIn("CACHE PENETRATION", content)
        self.assertIn("CACHE AVALANCHE", content)
        self.assertIn("TTL jitter", content)
        self.assertIn("Bloom filter", content)
        self.assertIn("negative caching", content)
        self.assertIn("probabilistic early expiration", content)
        self.assertIn("REDIS VS MEMCACHED", content)
        self.assertIn("L1 + L2 COHERENCE", content)
        self.assertIn("benchmark the actual runtime", content)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])

    def test_prototyping_prompt_enforces_measured_iteration_to_final(self) -> None:
        prompt = self.full["P82"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["seq"], "82")
        self.assertEqual(prompt["class"], "ENGINEERING / PROTOTYPING")
        self.assertIn("PROTOTYPE LADDER", content)
        self.assertIn("HYPOTHESIS -> BUILD -> MEASURE -> CRITIQUE -> DECIDE", content)
        self.assertIn("Do not present a prototype as final", content)
        self.assertIn("Preserve the last known-good candidate", content)
        self.assertIn("SAME acceptance rubric", content)
        self.assertIn("USE FEEDBACK WITHOUT TURNING THE USER INTO THE TEST RUNNER", content)
        self.assertIn("REMOVE PROTOTYPE DEBT BEFORE FINAL", content)
        self.assertIn("FINAL PROOF IS STRICTER THAN PROTOTYPE PROOF", content)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])

    def test_new_source_prompts_are_intentionally_bounded(self) -> None:
        for prompt_id in ("P78", "P79", "P80", "P81", "P82"):
            content = self.raw[prompt_id]["copyContent"]
            self.assertLess(len(content), 8000)
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

    def test_render_contains_spec_profile_and_extended_architecture_prompts(self) -> None:
        html = build_prompt_kit_registry.render()
        self.assertIn("prompt-kit-spec-architecture-styles", html)
        self.assertIn("spec-architecture", html)
        self.assertIn("◎ Spec Layers", html)
        self.assertIn("Progressive-Disclosure Spec & Harness Factorer", html)
        self.assertIn("Repository Glossary & Documentation Diet", html)
        self.assertIn("Prompt Registry Prompt Adder", html)
        self.assertIn("Client Prompt Pack & Local Profile Builder", html)
        self.assertIn("Multi-Tier Cache Architecture & Invalidation Hardener", html)
        self.assertIn("Prototype-Measure-Refine Delivery Loop", html)


if __name__ == "__main__":
    unittest.main()
