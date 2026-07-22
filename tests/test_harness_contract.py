from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_harness


class HarnessContractTests(unittest.TestCase):
    def test_full_harness_validator_passes(self) -> None:
        self.assertEqual(validate_harness.main(), 0)

    def test_manifest_registers_every_required_harness_surface(self) -> None:
        manifest = json.loads(
            (ROOT / "harness" / "manifest.v1.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["schema_version"], "web-excel-harness/v1")
        self.assertEqual(manifest["default_branch"], "main")
        expected_components = {
            "codebase_map",
            "workflow_spec",
            "artifact_registry",
            "skill_index",
            "validator",
            "contract_tests",
            "hook",
            "operator_report",
        }
        self.assertEqual(set(manifest["components"]), expected_components)
        for path in manifest["components"].values():
            self.assertTrue((ROOT / path).is_file(), path)

    def test_acquisition_contract_is_preservation_first(self) -> None:
        manifest = json.loads(
            (ROOT / "harness" / "manifest.v1.json").read_text(encoding="utf-8")
        )
        safety = manifest["technician_acquisition"]["safety"]
        self.assertTrue(safety["clone_when_absent"])
        self.assertTrue(safety["fast_forward_only"])
        self.assertTrue(safety["refuse_dirty_worktree"])
        self.assertTrue(safety["refuse_divergence"])
        self.assertFalse(safety["force_push"])
        self.assertFalse(safety["destructive_reset"])
        self.assertFalse(safety["embedded_credentials"])

    def test_cmd_can_bootstrap_the_gui_when_repo_is_absent(self) -> None:
        launcher = (ROOT / "Acquire-Latest-PromptKit.cmd").read_text(encoding="utf-8")
        self.assertIn("raw.githubusercontent.com", launcher)
        self.assertIn("Invoke-WebRequest", launcher)
        self.assertIn("Acquire-LatestPromptKit.ps1", launcher)
        self.assertIn("%TEMP%", launcher)
        self.assertNotIn("C:\\Users\\", launcher)

    def test_gui_uses_only_clone_or_fast_forward_update(self) -> None:
        gui = (ROOT / "scripts" / "Acquire-LatestPromptKit.ps1").read_text(
            encoding="utf-8"
        )
        required = (
            "'clone', '--branch', $DefaultBranch, '--single-branch'",
            "'status', '--porcelain'",
            "'branch', '--show-current'",
            "'fetch', 'origin', $DefaultBranch, '--prune'",
            "'rev-list', '--left-right', '--count'",
            "'merge', '--ff-only'",
            "Test-RequiredFiles",
        )
        for phrase in required:
            self.assertIn(phrase, gui)
        lowered = gui.lower()
        for forbidden in validate_harness.FORBIDDEN_ACQUISITION_PATTERNS:
            self.assertNotIn(forbidden.lower(), lowered)

    def test_gui_refuses_wrong_origin_dirty_branch_and_divergence(self) -> None:
        gui = (ROOT / "scripts" / "Acquire-LatestPromptKit.ps1").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "unexpected origin",
            "local modifications or untracked files",
            "not '$DefaultBranch'",
            "Local main contains $localAhead commit(s)",
            "No reset or overwrite was attempted",
        ):
            self.assertIn(phrase, gui)

    def test_gui_validates_then_opens_mouse_selected_surface(self) -> None:
        gui = (ROOT / "scripts" / "Acquire-LatestPromptKit.ps1").read_text(
            encoding="utf-8"
        )
        self.assertIn("Open Prompt Kit website", gui)
        self.assertIn("Open generator selection GUI", gui)
        self.assertIn("Prompt Kit exact-output validation failed", gui)
        validation_position = gui.index("Test-RequiredFiles -RepositoryRoot")
        website_open_position = gui.index("Opening Prompt Kit website")
        generator_open_position = gui.index("Opening generator selection GUI")
        self.assertLess(validation_position, website_open_position)
        self.assertLess(validation_position, generator_open_position)

    def test_skill_index_and_skill_contract_are_connected(self) -> None:
        index = (ROOT / "SKILLS.md").read_text(encoding="utf-8")
        skill_path = ".ai/skills/technician-prompt-kit-acquisition/SKILL.md"
        self.assertIn(skill_path, index)
        skill = (ROOT / skill_path).read_text(encoding="utf-8")
        for section in validate_harness.REQUIRED_SKILL_SECTIONS:
            self.assertIn(section, skill)

    def test_pre_commit_hook_runs_focused_harness_gates(self) -> None:
        hook = (ROOT / ".githooks" / "pre-commit").read_text(encoding="utf-8")
        self.assertIn("python scripts/validate_harness.py", hook)
        self.assertIn("python -m unittest tests.test_harness_contract -v", hook)
        self.assertIn("git diff --cached --check", hook)


if __name__ == "__main__":
    unittest.main()
