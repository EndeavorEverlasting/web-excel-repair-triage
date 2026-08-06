from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry


class SkillPromptRegistryTests(unittest.TestCase):
    def test_combined_registry_contains_unique_skill_and_discovery_prompts(self) -> None:
        prompts = build_prompt_kit_registry.load_prompt_registry()
        by_id = {prompt["id"]: prompt for prompt in prompts}
        self.assertEqual(len(by_id), len(prompts))
        for prompt_id in ("P61", "P62", "P63", "P64", "P65"):
            self.assertIn(prompt_id, by_id)
        self.assertEqual(by_id["P63"]["skillPath"], ".ai/skills/skill-factoring/SKILL.md")
        self.assertEqual(by_id["P62"]["class"], "AGENT HARNESS / SKILL EVALS")
        self.assertNotEqual(by_id["P63"]["copyContent"], by_id["P62"]["copyContent"])
        self.assertEqual(by_id["P64"]["type"], "TUTORIAL PLAN")
        self.assertEqual(by_id["P65"]["type"], "SETUP")
        self.assertEqual(prompts[0]["id"], "P65")
        self.assertEqual(prompts[0]["discoveryRank"], 1)
        self.assertEqual(prompts[0]["displayOrderPolicy"], "prompt-kit-guided-discovery-order")

    def test_skill_eval_prompt_requires_correctness_weakness_and_efficiency_proof(self) -> None:
        prompts = build_prompt_kit_registry.load_prompt_registry()
        prompt = {item["id"]: item for item in prompts}["P62"]
        content = prompt["copyContent"]

        self.assertEqual(
            prompt["name"],
            "Skill Correctness and Efficiency Eval Implementer",
        )
        self.assertIn("bugs, missing functionality", prompt["useWhen"])
        self.assertIn("performance and token instrumentation", prompt["expectedOutput"])
        self.assertIn("open or print the canonical machine-readable report", prompt["nextStep"])
        self.assertIn("measured token/latency/cost improvements preserve quality", prompt["proofGate"])

        for phrase in (
            "IDENTIFY WEAKNESSES, NOT JUST FAILURES",
            "functional bugs and incorrect outputs",
            "missing functionality or unhandled conditions",
            "false-positive and false-negative skill selection",
            "unit tests for deterministic helpers",
            "integration tests across skill + trigger + capability + workflow + artifact",
            "test-driven development",
            "profiling or execution traces",
            "prompt, completion, cached, and total token usage",
            "context files/bytes loaded",
            "OPTIMIZE WITH SOUND FACTORING PRINCIPLES",
            "move deterministic work into code, schemas, registries, validators, and workflows",
            "load only the skill instructions and repository context required",
            "remove duplicate calls, unnecessary intermediate summaries",
            "performance or token change passes only when",
            "baseline/candidate deltas",
            "finding-to-repair ledger",
            "unit and integration tests",
            "one exact next command that runs the eval",
        ):
            self.assertIn(phrase, content)

        for forbidden_shortcut in (
            "DO NOT RETURN ONLY A RUBRIC",
            "Never weaken an assertion",
            "do not optimize a proxy while degrading the real task",
        ):
            self.assertIn(forbidden_shortcut, content)

    def test_tutorial_portfolio_prompt_preserves_uploaded_contract(self) -> None:
        prompt = {
            item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()
        }["P64"]
        content = prompt["copyContent"]
        for phrase in (
            "ANALYZE THE REPOSITORY AND RANK TUTORIAL PATHS WORTH SPRINTING",
            "Do not confuse a documentation gap with a tutorial opportunity",
            "TUTORIAL READINESS CLASSIFICATIONS",
            "READY_AFTER_PRODUCT_FIX",
            "CANDIDATE DISPOSITION LEDGER",
            "COPYABLE TUTORIAL SPRINT PANELS",
            "Use P18 when the sprint primarily creates durable tutorials",
            "one exact next command",
        ):
            self.assertIn(phrase, content)

    def test_guided_prompt_finder_is_bounded_and_registry_aware(self) -> None:
        prompt = {
            item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()
        }["P65"]
        content = prompt["copyContent"]
        for phrase in (
            "Ask one concise question at a time",
            "ask no more than four questions",
            "recommend exactly one primary prompt",
            "up to two optional follow-on prompts",
            "Do not invent prompt IDs",
            "P64 Repository Tutorial Portfolio Ranker",
        ):
            self.assertIn(phrase, content)

    def test_skill_factoring_file_has_required_contract_sections(self) -> None:
        path = REPO_ROOT / ".ai" / "skills" / "skill-factoring" / "SKILL.md"
        content = path.read_text(encoding="utf-8")
        for heading in (
            "## Trigger",
            "## Required inputs",
            "## Outputs",
            "## Procedure",
            "## Guardrails",
            "## Validation",
            "## Proof ceiling",
        ):
            self.assertIn(heading, content)

    def test_generator_manifest_routes_options_through_gui(self) -> None:
        path = REPO_ROOT / "configs" / "prompt_kit" / "generators.v1.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "prompt-kit-generators/v1")
        self.assertEqual(payload["gui_launcher"], "Run-PromptKitGenerator.cmd")
        generator = payload["generators"][0]
        self.assertEqual(generator["runner"], "scripts/build_prompt_kit_registry.py")
        option_types = {option["id"]: option["type"] for option in generator["options"]}
        self.assertEqual(option_types["output_path"], "file-save")
        self.assertEqual(option_types["validate_after_build"], "boolean")
        self.assertEqual(option_types["open_after_build"], "boolean")
        self.assertTrue((REPO_ROOT / payload["gui_launcher"]).is_file())
        self.assertTrue((REPO_ROOT / generator["direct_launcher"]).is_file())

    def test_gui_is_bounded_to_registered_builder(self) -> None:
        source = (SCRIPTS / "prompt_kit_generator_gui.py").read_text(encoding="utf-8")
        self.assertIn('ALLOWED_RUNNER = "scripts/build_prompt_kit_registry.py"', source)
        self.assertNotIn("subprocess", source)
        self.assertIn("build_prompt_kit_registry.build(output)", source)
        validation = source.index("build_prompt_kit_registry.validate_output_path(output)")
        thread_start = source.index("threading.Thread(")
        self.assertLess(validation, thread_start)

    def test_protected_operator_inputs_are_rejected_before_write(self) -> None:
        for root_name in ("Candidates", "Active"):
            output = REPO_ROOT / root_name / "nested" / "prompt-kit.html"
            with self.assertRaisesRegex(ValueError, "protected operator input"):
                build_prompt_kit_registry.validate_output_path(output)
            self.assertFalse(output.exists())

    def test_non_protected_output_is_allowed(self) -> None:
        output = REPO_ROOT / "Outputs" / "prompt-kit-preview.html"
        self.assertEqual(
            build_prompt_kit_registry.validate_output_path(output),
            output.resolve(),
        )

    def test_cmd_launchers_resolve_repository_root(self) -> None:
        for name in ("Run-PromptKitGenerator.cmd", "Build-PromptKitWebsite.cmd"):
            content = (REPO_ROOT / name).read_text(encoding="utf-8")
            self.assertIn('cd /d "%~dp0"', content)
        self.assertIn(
            "scripts\\prompt_kit_generator_gui.py",
            (REPO_ROOT / "Run-PromptKitGenerator.cmd").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "scripts\\build_prompt_kit_registry.py",
            (REPO_ROOT / "Build-PromptKitWebsite.cmd").read_text(encoding="utf-8"),
        )

    def test_combined_registry_build_contains_guided_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "prompt-kit.html"
            html = build_prompt_kit_registry.build(output)
            self.assertEqual(output.read_text(encoding="utf-8"), html)
            for prompt_id in ("P61", "P62", "P63", "P64", "P65"):
                self.assertIn(f'"id": "{prompt_id}"', html)
            self.assertIn("Skill Factoring and Boundary Refactorer", html)
            self.assertIn("Skill Correctness and Efficiency Eval Implementer", html)
            self.assertIn("Repository Tutorial Portfolio Ranker", html)
            self.assertIn("Guided Prompt Finder Questionnaire", html)
            self.assertIn("Find My Prompt", html)
            self.assertIn("prompt-kit-guided-recommendations.js", build_prompt_kit_registry.GUIDED_JS.as_posix())

    def test_checked_in_operator_site_is_exact_combined_build(self) -> None:
        deployed = REPO_ROOT / "web" / "prompt-kit" / "index.html"
        actual = deployed.read_text(encoding="utf-8")
        expected = build_prompt_kit_registry.render()
        self.assertEqual(actual, expected)
        for prompt_id in ("P61", "P62", "P63", "P64", "P65"):
            self.assertIn(f'"id": "{prompt_id}"', actual)
        self.assertIn("Skill Correctness and Efficiency Eval Implementer", actual)
        self.assertIn("Find My Prompt", actual)


if __name__ == "__main__":
    unittest.main()
