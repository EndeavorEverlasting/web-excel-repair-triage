from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import evaluate_prompt_language
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
        self.assertEqual(set(manifest["components"]), validate_harness.REQUIRED_COMPONENT_IDS)
        for path in manifest["components"].values():
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertEqual(len(manifest["skills"]), 4)

    def test_nth_domain_overlay_is_registered_and_tracked_by_the_root_manifest(self) -> None:
        manifest = json.loads(
            (ROOT / "harness" / "manifest.v1.json").read_text(encoding="utf-8")
        )
        overlay = manifest["domain_overlays"]["neuron_track_hours"]
        expected = {
            "manifest": "harness/nth/manifest.v1.json",
            "rule_pack_registry": "harness/nth/monthly-rule-packs.v1.json",
            "trigger_registry": "harness/nth/triggers.v1.json",
            "skill": ".ai/skills/neuron-track-hours-monthly-artifact/SKILL.md",
            "validator": "scripts/validate_nth_harness.py",
            "tests": "tests/test_nth_harness_contract.py",
        }
        self.assertEqual(overlay, expected)
        for path in overlay.values():
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertIn(
            "python scripts/validate_nth_harness.py", manifest["validation_order"]
        )
        self.assertIn(
            "python -m unittest tests.test_nth_harness_contract -v",
            manifest["validation_order"],
        )

    def test_capabilities_and_triggers_have_unique_connected_owners(self) -> None:
        capabilities = json.loads(
            (ROOT / "harness" / "capabilities.v1.json").read_text(encoding="utf-8")
        )["capabilities"]
        triggers = json.loads(
            (ROOT / "harness" / "triggers.v1.json").read_text(encoding="utf-8")
        )["triggers"]
        capability_by_id = {item["id"]: item for item in capabilities}
        self.assertEqual(set(capability_by_id), validate_harness.REQUIRED_CAPABILITY_IDS)
        self.assertEqual({item["id"] for item in triggers}, validate_harness.REQUIRED_TRIGGER_IDS)
        for trigger in triggers:
            capability = capability_by_id[trigger["capability_id"]]
            self.assertEqual(trigger["skill"], capability["skill"])
            self.assertIn(trigger["id"], capability["trigger_ids"])

    def test_every_active_skill_is_indexed_and_structured(self) -> None:
        manifest = json.loads(
            (ROOT / "harness" / "manifest.v1.json").read_text(encoding="utf-8")
        )
        index = (ROOT / "SKILLS.md").read_text(encoding="utf-8")
        for skill_path in manifest["skills"]:
            self.assertIn(skill_path, index)
            skill = (ROOT / skill_path).read_text(encoding="utf-8")
            for section in validate_harness.REQUIRED_SKILL_SECTIONS:
                self.assertIn(section, skill)

    def test_prompt_language_audit_covers_every_effective_prompt(self) -> None:
        report = evaluate_prompt_language.evaluate_registry()
        self.assertTrue(report["coverage_complete"])
        self.assertEqual(report["prompt_count"], report["effective_prompt_count"])
        self.assertEqual(report["prompt_count"], report["disposition_count"])
        self.assertEqual(report["error_count"], 0)
        self.assertIn("P62", {item["prompt_id"] for item in report["prompts"]})

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

    def test_gui_uses_only_clone_or_fast_forward_update(self) -> None:
        gui = (ROOT / "scripts" / "Acquire-LatestPromptKit.ps1").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "'clone', '--branch', $DefaultBranch, '--single-branch'",
            "'status', '--porcelain'",
            "'branch', '--show-current'",
            "'fetch', 'origin', $DefaultBranch, '--prune'",
            "'rev-list', '--left-right', '--count'",
            "'merge', '--ff-only'",
            "Test-RequiredFiles",
        ):
            self.assertIn(phrase, gui)
        lowered = gui.lower()
        for forbidden in validate_harness.FORBIDDEN_ACQUISITION_PATTERNS:
            self.assertNotIn(forbidden.lower(), lowered)

    def test_hooks_run_focused_and_exhaustive_harness_gates(self) -> None:
        pre_commit = (ROOT / ".githooks" / "pre-commit").read_text(encoding="utf-8")
        self.assertIn("python scripts/validate_harness.py", pre_commit)
        self.assertIn("python scripts/validate_nth_harness.py", pre_commit)
        self.assertIn("git diff --cached --check", pre_commit)
        pre_push = (ROOT / ".githooks" / "pre-push").read_text(encoding="utf-8")
        for phrase in (
            "python scripts/validate_harness.py",
            "python scripts/validate_nth_harness.py",
            "python -m unittest tests.test_nth_harness_contract -v",
            "python -m unittest tests.test_prompt_language_audit -v",
            "python scripts/evaluate_prompt_language.py",
            "python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check",
            "git diff --check",
        ):
            self.assertIn(phrase, pre_push)


if __name__ == "__main__":
    unittest.main()
