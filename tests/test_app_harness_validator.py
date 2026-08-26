from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from scripts import validate_app_harness as validator

ROOT = Path(__file__).resolve().parents[1]


class AppHarnessValidatorTests(unittest.TestCase):
    def fake_runner(self, command, root):
        if tuple(command) == ("git", "branch", "--show-current"):
            return subprocess.CompletedProcess(command, 0, "test-branch\n", "")
        if tuple(command) == ("git", "rev-parse", "HEAD"):
            return subprocess.CompletedProcess(command, 0, "a" * 40 + "\n", "")
        return subprocess.CompletedProcess(command, 0, "PASS\n", "")

    def test_matrix_and_receipt_are_exact_head_and_honest(self):
        report = validator.validate(ROOT, runner=self.fake_runner, env={})
        self.assertEqual("app-harness-validation/v2", report["schema_version"])
        self.assertEqual("offline_synthetic", report["proof_level"])
        self.assertFalse(report["runtime_proof"])
        self.assertEqual("a" * 40, report["head_sha"])
        self.assertEqual({"passed": 5, "skipped": 1, "failed": 0}, report["summary"])
        self.assertEqual("PASS", report["final_status"])
        checks = [validator.Check(**item) for item in report["checks"]]
        text = validator.render_matrix(checks, report["branch"], report["head_sha"])
        self.assertIn("APP HARNESS VALIDATION", text)
        self.assertIn("[PASS] required files", text)
        self.assertIn("[SKIP] optional MCP symbol smoke: lsp_project_not_loaded", text)
        self.assertIn("Result: 5 passed / 1 skipped / 0 failed", text)
        self.assertIn("Gate: PASS", text)
        self.assertIn("no live runtime, browser, launcher", text)

    def test_prompt_owner_always_carries_identifier_name_and_purpose(self):
        owner = validator.prompt_identity(ROOT)
        self.assertEqual("P11", owner["id"])
        self.assertEqual("End-to-End Harness Validator", owner["name"])
        self.assertTrue(owner["purpose"])
        rendered = f"{owner['id']} · {owner['name']} — {owner['purpose']}"
        self.assertIn("P11 · End-to-End Harness Validator —", rendered)

    def test_required_validator_failure_is_blocking(self):
        def failing_runner(command, root):
            if tuple(command) == ("git", "branch", "--show-current"):
                return subprocess.CompletedProcess(command, 0, "test-branch\n", "")
            if tuple(command) == ("git", "rev-parse", "HEAD"):
                return subprocess.CompletedProcess(command, 0, "b" * 40 + "\n", "")
            if any(str(part).endswith("validate_harness.py") for part in command):
                return subprocess.CompletedProcess(command, 7, "", "broken root validator")
            return subprocess.CompletedProcess(command, 0, "PASS\n", "")
        report = validator.validate(ROOT, runner=failing_runner, env={})
        check = next(item for item in report["checks"] if item["id"] == "required_files")
        self.assertEqual("FAIL", check["status"])
        self.assertEqual("FAIL", report["final_status"])

    def test_required_skip_fails_closed(self):
        checks = [validator.Check("required_probe", "required probe", "REQUIRED", "SKIP", "environment_missing", [])]
        self.assertEqual("FAIL", validator.final_status(checks))

    def test_optional_missing_dependency_is_honest_skip(self):
        check = validator.check_optional_mcp(ROOT, {})
        self.assertEqual("OPTIONAL", check.requirement)
        self.assertEqual("SKIP", check.status)
        self.assertEqual("lsp_project_not_loaded", check.reason)

    def test_receipt_is_json_serializable_and_has_ci_correlation_fields(self):
        report = validator.validate(ROOT, runner=self.fake_runner, env={})
        encoded = json.dumps(report)
        decoded = json.loads(encoded)
        self.assertEqual(".", decoded["repository_root"])
        self.assertEqual(6, len(decoded["validator_set"]))
        self.assertIn("required_files", decoded["required_checks"])
        self.assertEqual("optional_mcp_symbol_smoke", decoded["skipped_checks"][0]["id"])
        self.assertNotIn(str(ROOT), encoded)

    def test_output_is_restricted_to_outputs(self):
        self.assertEqual(ROOT / "Outputs" / "app-harness-validation.json", validator.output_path(ROOT, "Outputs/app-harness-validation.json"))
        with self.assertRaisesRegex(ValueError, "under Outputs"):
            validator.output_path(ROOT, "app-harness-validation.json")

    def test_offline_allowlist_rejects_runtime_network_and_mutation(self):
        forbidden = (
            ["python", "app.py"],
            ["python", "-m", "http.server"],
            ["powershell", "Start-Process", "index.html"],
            ["curl", "https://example.invalid"],
            ["git", "clean", "-fd"],
            ["git", "push"],
            ["playwright", "test"],
        )
        for command in forbidden:
            with self.subTest(command=command), self.assertRaises(RuntimeError):
                validator.safe_runner(command, ROOT)

    def test_canonical_command_is_the_single_ci_entrypoint(self):
        workflow = (ROOT / ".github" / "workflows" / "app-harness-validation.yml").read_text(encoding="utf-8")
        self.assertIn(validator.CANONICAL_COMMAND, workflow)
        self.assertEqual(1, workflow.count(validator.CANONICAL_COMMAND))
        self.assertNotIn("curl ", workflow)
        self.assertNotIn("playwright", workflow.lower())
        self.assertNotIn("start-process", workflow.lower())

    def test_ci_reruns_when_required_harness_dependencies_move(self):
        workflow = (ROOT / ".github" / "workflows" / "app-harness-validation.yml").read_text(encoding="utf-8")
        dependencies = (
            "AGENTS.md",
            "CODEBASE_MAP.md",
            "WORKFLOW.md",
            "ARTIFACT_REGISTRY.md",
            "scripts/validate_app_harness.py",
            "scripts/validate_harness.py",
            "tests/test_app_harness_validator.py",
            "harness/**",
            ".githooks/**",
            "triage/gitignore_hygiene.py",
            "docs/prompts.json",
            "mcp_server.py",
            ".github/workflows/app-harness-validation.yml",
        )
        for dependency in dependencies:
            with self.subTest(dependency=dependency):
                self.assertEqual(2, workflow.count(f"- '{dependency}'"))


if __name__ == "__main__":
    unittest.main()
