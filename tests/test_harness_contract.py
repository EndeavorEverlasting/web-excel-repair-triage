from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import evaluate_prompt_language
import validate_harness


class HarnessContractTests(unittest.TestCase):
    def load(self, relative_path: str) -> dict:
        return json.loads(
            (ROOT / relative_path).read_text(encoding="utf-8")
        )

    def test_full_harness_validator_passes(self) -> None:
        self.assertEqual(validate_harness.main([]), 0)

    def test_harness_report_is_written_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "harness-report.json"
            self.assertEqual(
                validate_harness.main(
                    ["--report", str(report_path)]
                ),
                0,
            )
            report = json.loads(
                report_path.read_text(encoding="utf-8")
            )
        self.assertEqual(
            report["schema_version"],
            "harness-completeness-report/v1",
        )
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["failure_count"], 0)
        self.assertTrue(report["checks"])
        self.assertTrue(
            all(item["status"] == "PASS" for item in report["checks"])
        )
        self.assertEqual(
            report["counts"]["components"],
            len(validate_harness.REQUIRED_COMPONENT_IDS),
        )
        self.assertEqual(
            report["counts"]["workflows"],
            len(validate_harness.REQUIRED_WORKFLOW_IDS),
        )
        self.assertEqual(
            report["counts"]["artifacts"],
            len(validate_harness.REQUIRED_ARTIFACT_IDS),
        )
        self.assertEqual(
            report["counts"]["validators"],
            len(validate_harness.REQUIRED_VALIDATOR_IDS),
        )

    def test_manifest_registers_every_required_harness_surface(self) -> None:
        manifest = self.load("harness/manifest.v1.json")
        self.assertEqual(
            manifest["schema_version"], "web-excel-harness/v1"
        )
        self.assertEqual(manifest["default_branch"], "main")
        self.assertEqual(
            set(manifest["components"]),
            validate_harness.REQUIRED_COMPONENT_IDS,
        )
        for path in manifest["components"].values():
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertEqual(
            set(manifest["skills"]),
            {
                capability["skill"]
                for capability in self.load(
                    "harness/capabilities.v1.json"
                )["capabilities"]
            },
        )

    def test_machine_registries_are_complete_and_connected(self) -> None:
        manifest = self.load("harness/manifest.v1.json")
        workflows = self.load("harness/workflows.v1.json")
        artifacts = self.load("harness/artifacts.v1.json")
        validators = self.load("harness/validators.v1.json")

        self.assertEqual(
            {item["id"] for item in workflows["workflows"]},
            validate_harness.REQUIRED_WORKFLOW_IDS,
        )
        self.assertEqual(
            {item["id"] for item in artifacts["artifacts"]},
            validate_harness.REQUIRED_ARTIFACT_IDS,
        )
        validator_by_id = {
            item["id"]: item for item in validators["validators"]
        }
        self.assertEqual(
            set(validator_by_id),
            validate_harness.REQUIRED_VALIDATOR_IDS,
        )
        self.assertEqual(
            [
                validator_by_id[validator_id]["command"]
                for validator_id in validators["profiles"]["harness"]
            ],
            manifest["validation_order"],
        )
        self.assertEqual(
            validators["profiles"]["pre_push"],
            validators["profiles"]["harness"],
        )

    def test_workflows_have_scope_failure_and_handoff_contracts(self) -> None:
        workflows = self.load("harness/workflows.v1.json")[
            "workflows"
        ]
        for workflow in workflows:
            self.assertTrue(workflow["document"].startswith("WORKFLOW.md#"))
            self.assertTrue(workflow["trigger"])
            self.assertTrue(workflow["owned_scope"])
            self.assertTrue(workflow["forbidden_scope"])
            self.assertTrue(workflow["entry_points"])
            self.assertTrue(workflow["failure_policy"])
            self.assertTrue(workflow["handoff_fields"])

    def test_artifact_registry_protects_inputs_and_resolves_outputs(self) -> None:
        payload = self.load("harness/artifacts.v1.json")
        self.assertEqual(
            payload["protected_paths"], ["Candidates/", "Active/"]
        )
        kinds = {artifact["kind"] for artifact in payload["artifacts"]}
        self.assertEqual(kinds, {"tracked", "runtime"})
        for artifact in payload["artifacts"]:
            path = artifact["canonical_path"]
            self.assertFalse(path.startswith("Candidates/"))
            self.assertFalse(path.startswith("Active/"))
            if artifact["kind"] == "runtime":
                self.assertTrue(path.startswith("Outputs/"))

    def test_capabilities_and_triggers_have_unique_connected_owners(self) -> None:
        capabilities = self.load(
            "harness/capabilities.v1.json"
        )["capabilities"]
        triggers = self.load(
            "harness/triggers.v1.json"
        )["triggers"]
        capability_by_id = {item["id"]: item for item in capabilities}
        self.assertEqual(
            set(capability_by_id),
            validate_harness.REQUIRED_CAPABILITY_IDS,
        )
        self.assertEqual(
            {item["id"] for item in triggers},
            validate_harness.REQUIRED_TRIGGER_IDS,
        )
        for trigger in triggers:
            capability = capability_by_id[trigger["capability_id"]]
            self.assertEqual(trigger["skill"], capability["skill"])
            self.assertIn(trigger["id"], capability["trigger_ids"])

    def test_every_active_skill_is_indexed_and_structured(self) -> None:
        manifest = self.load("harness/manifest.v1.json")
        index = (ROOT / "SKILLS.md").read_text(encoding="utf-8")
        for skill_path in manifest["skills"]:
            self.assertIn(skill_path, index)
            skill = (ROOT / skill_path).read_text(encoding="utf-8")
            for section in validate_harness.REQUIRED_SKILL_SECTIONS:
                self.assertIn(section, skill)

    def test_prompt_language_audit_covers_every_effective_prompt(self) -> None:
        report = evaluate_prompt_language.evaluate_registry()
        self.assertTrue(report["coverage_complete"])
        self.assertEqual(
            report["prompt_count"], report["effective_prompt_count"]
        )
        self.assertEqual(
            report["prompt_count"], report["disposition_count"]
        )
        self.assertEqual(report["error_count"], 0)
        self.assertIn(
            "P62", {item["prompt_id"] for item in report["prompts"]}
        )

    def test_acquisition_contract_is_preservation_first(self) -> None:
        manifest = self.load("harness/manifest.v1.json")
        safety = manifest["technician_acquisition"]["safety"]
        self.assertTrue(safety["clone_when_absent"])
        self.assertTrue(safety["fast_forward_only"])
        self.assertTrue(safety["refuse_dirty_worktree"])
        self.assertTrue(safety["refuse_divergence"])
        self.assertFalse(safety["force_push"])
        self.assertFalse(safety["destructive_reset"])
        self.assertFalse(safety["embedded_credentials"])

    def test_hooks_use_registered_profiles_and_staged_tree(self) -> None:
        validators = self.load("harness/validators.v1.json")
        self.assertEqual(
            validators["hooks"]["pre_commit"]["index_mode"],
            "staged-tree",
        )
        pre_commit = (ROOT / ".githooks" / "pre-commit").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "git checkout-index --all --prefix=",
            'cd "$staged_tree"',
            'python scripts/validate_harness.py --report "$HARNESS_REPORT"',
            "git diff --cached --check",
        ):
            self.assertIn(phrase, pre_commit)

        pre_push = (ROOT / ".githooks" / "pre-push").read_text(
            encoding="utf-8"
        )
        for validator_id in validators["profiles"]["pre_push"]:
            command = {
                item["id"]: item["command"]
                for item in validators["validators"]
            }[validator_id]
            if validator_id == "harness-completeness":
                self.assertIn(
                    'python scripts/validate_harness.py --report "$HARNESS_REPORT"',
                    pre_push,
                )
            elif validator_id == "prompt-kit-interaction-audit":
                self.assertIn(
                    "python scripts/validate_prompt_kit_interactions.py",
                    pre_push,
                )
            elif validator_id == "prompt-language-audit":
                self.assertIn(
                    "python scripts/evaluate_prompt_language.py",
                    pre_push,
                )
            else:
                self.assertIn(command, pre_push)


if __name__ == "__main__":
    unittest.main()
