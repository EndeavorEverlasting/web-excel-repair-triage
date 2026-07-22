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
    def test_combined_registry_contains_unique_skill_prompts(self) -> None:
        prompts = build_prompt_kit_registry.load_prompt_registry()
        by_id = {prompt["id"]: prompt for prompt in prompts}
        self.assertEqual(len(by_id), len(prompts))
        self.assertIn("P61", by_id)
        self.assertIn("P62", by_id)
        self.assertEqual(by_id["P61"]["skillPath"], ".ai/skills/skill-factoring/SKILL.md")
        self.assertEqual(by_id["P62"]["class"], "AGENT HARNESS / SKILL EVALS")
        self.assertNotEqual(by_id["P61"]["copyContent"], by_id["P62"]["copyContent"])

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

    def test_combined_registry_build_contains_both_new_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "prompt-kit.html"
            html = build_prompt_kit_registry.build(output)
            self.assertEqual(output.read_text(encoding="utf-8"), html)
            self.assertIn('"id": "P61"', html)
            self.assertIn('"id": "P62"', html)
            self.assertIn("Skill Factoring and Boundary Refactorer", html)
            self.assertIn("Skill Evaluation Harness Implementer", html)

    def test_checked_in_operator_site_is_exact_combined_build(self) -> None:
        deployed = REPO_ROOT / "web" / "prompt-kit" / "index.html"
        actual = deployed.read_text(encoding="utf-8")
        expected = build_prompt_kit_registry.render()
        self.assertEqual(actual, expected)
        self.assertIn('"id": "P61"', actual)
        self.assertIn('"id": "P62"', actual)


if __name__ == "__main__":
    unittest.main()
