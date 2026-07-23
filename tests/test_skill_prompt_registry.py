from __future__ import annotations

import json
import re
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

    def test_prompt_nextstep_is_actionable_when_artifact_exists(self) -> None:
        """Prompts that produce artifacts must have an actionable nextStep that consumes the artifact."""
        prompts = build_prompt_kit_registry.load_prompt_registry()

        # Only flag truly passive patterns like PR viewing, status checking
        # "Use P" transitions are legitimate pipeline handoffs
        passive_patterns = [
            r"gh pr view.*--web",
            r"gh pr checks",
            r"git status",
            r"git branch",
            r"git log",
            r"show workflow logs",
            r"open.*pr page",
            r"view.*pr",
            r"check status",
        ]

        actionable_pattern = re.compile(r"git worktree add|git clone|python.*-m unittest|python scripts/|start .*\.html|start .*\.json|cat .*\.txt|Open.*artifact|open.*website|launch.*generator|validate.*output|run.*validator", re.IGNORECASE)

        for prompt in prompts:
            prompt_type = prompt.get("type", "")
            next_step = prompt.get("nextStep", "")

            if prompt_type in {"BUILD", "REPAIR", "BUILD + MUTATE", "BUILD + ARTIFACT",
                               "BUILD + FACTOR", "BUILD + BOOTSTRAP", "BUILD + SAFETY",
                               "BUILD + ARTIFACT", "REVIEW + BUILD",
                               "ANALYZE + FACTOR", "ANALYZE + TEST",
                               "ENABLEMENT + BUILD", "OPERATE",
                               "AUTONOMY + VALIDATE", "AUTONOMY + BUILD", "AUTONOMY + PLAN",
                               "AUTONOMY + PREFLIGHT", "AUTONOMY + QUEUE", "RECOVER + BUILD",
                               "RECOVER + COMMIT", "HARNESS + BUILD", "HARNESS + EXECUTE",
                               "CURSOR + LIVE CERT", "ENVIRONMENT + CONFIGURE",
                               "CONTEXT-TO-ARTIFACT", "SPRINT / BUILD + MUTATE"}:
                has_passive = any(re.search(pattern, next_step, re.IGNORECASE) for pattern in passive_patterns)
                has_actionable = bool(actionable_pattern.search(next_step))
                # Fail only if there's a passive pattern AND no actionable pattern
                if has_passive and not has_actionable:
                    self.fail(f"Prompt {prompt['id']} ({prompt['name']}) has passive nextStep: {next_step[:200]}")

    def test_prompt_nextstep_contains_artifact_consumption_pattern(self) -> None:
        """Actionable prompts should contain artifact consumption patterns in nextStep."""
        prompts = build_prompt_kit_registry.load_prompt_registry()

        must_have_artifact_consumption = {"P03", "P07", "P26", "P28", "P29", "P30", "P32", "P33",
                                          "P35", "P37", "P38", "P39", "P40", "P41", "P47", "P48",
                                          "P52", "P53", "P55", "P56", "P58", "P59", "P60"}

        artifact_patterns = [
            r"git worktree add",
            r"git clone",
            r"python.*-m unittest",
            r"python scripts/",
            r"start .*\\.html",
            r"start .*\\.json",
            r"cat .*\\.txt",
            r"open.*artifact",
            r"launch.*generator",
            r"validate.*output",
            r"run.*validator",
            r"tee .*\\.txt",
        ]

        for prompt in prompts:
            if prompt["id"] in must_have_artifact_consumption:
                next_step = prompt.get("nextStep", "")
                has_pattern = any(re.search(pattern, next_step, re.IGNORECASE) for pattern in artifact_patterns)
                self.assertTrue(has_pattern,
                    f"Prompt {prompt['id']} ({prompt['name']}) lacks artifact consumption pattern in nextStep")

    def test_prompt_nextstep_preserves_dirty_work(self) -> None:
        """Actionable prompts should preserve dirty work through worktree isolation."""
        prompts = build_prompt_kit_registry.load_prompt_registry()

        must_preserve_dirty = {"P03", "P07", "P26", "P28", "P29", "P30", "P32", "P33",
                               "P35", "P37", "P38", "P39", "P40", "P41", "P47", "P48",
                               "P52", "P53", "P55", "P56", "P58", "P59", "P60"}

        for prompt in prompts:
            if prompt["id"] in must_preserve_dirty:
                next_step = prompt.get("nextStep", "")
                self.assertIn("git worktree add", next_step,
                    f"Prompt {prompt['id']} should use worktree for isolation")
                self.assertNotIn("git reset --hard", next_step)
                self.assertNotIn("git clean -fd", next_step)
                self.assertNotIn("git push --force", next_step)
                self.assertNotIn("git checkout -f", next_step)

    def test_prompt_nextstep_propagates_exit_code(self) -> None:
        """Actionable prompts should propagate command failures and exit codes."""
        prompts = build_prompt_kit_registry.load_prompt_registry()

        must_propagate = {"P03", "P07", "P26", "P28", "P29", "P30", "P32", "P33",
                          "P35", "P37", "P38", "P39", "P40", "P41", "P47", "P48",
                          "P52", "P53", "P55", "P56", "P58", "P59", "P60"}

        for prompt in prompts:
            if prompt["id"] in must_propagate:
                next_step = prompt.get("nextStep", "")
                self.assertNotIn("|| true", next_step)
                self.assertNotIn("2>nul", next_step.lower())
                self.assertNotIn("2>/dev/null", next_step)

    def test_prompt_registry_no_gh_pr_view_as_sole_nextstep(self) -> None:
        """No prompt should have 'gh pr view --web' as its only actionable nextStep."""
        prompts = build_prompt_kit_registry.load_prompt_registry()

        for prompt in prompts:
            next_step = prompt.get("nextStep", "")
            if "gh pr view" in next_step and "--web" in next_step:
                has_artifact = bool(re.search(r"git worktree add|python.*-m unittest|start .*\\.html|cat .*\\.txt|tee .*\\.txt", next_step))
                self.assertTrue(has_artifact,
                    f"Prompt {prompt['id']} uses 'gh pr view --web' without artifact consumption")

    def test_prompt_registry_validates_panel_chat_equivalence(self) -> None:
        """Verify panel/chat contract is preserved in prompt metadata."""
        prompts = build_prompt_kit_registry.load_prompt_registry()

        parallel_prompts = {"P59"}
        for prompt in prompts:
            if prompt["id"] in parallel_prompts:
                next_step = prompt.get("nextStep", "")
                self.assertTrue("parallel" in next_step.lower() or "worktree" in next_step.lower(),
                    f"Parallel prompt {prompt['id']} should mention parallel/worktree execution")

        serialized_prompts = {"P60"}
        for prompt in prompts:
            if prompt["id"] in serialized_prompts:
                next_step = prompt.get("nextStep", "")
                self.assertTrue("handoff" in next_step.lower() or "step" in next_step.lower(),
                    f"Serialized prompt {prompt['id']} should mention handoff/step")


if __name__ == "__main__":
    unittest.main()