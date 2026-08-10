from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import validate_app_harness as validator

ROOT = Path(__file__).resolve().parents[1]


class AppHarnessValidatorTests(unittest.TestCase):
    def fake_runner(self, command, root):
        if command[:3] == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "test-branch\n", "")
        if command[:3] == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "a" * 40 + "\n", "")
        return subprocess.CompletedProcess(command, 0, "PASS\n", "")

    def test_matrix_has_honest_pass_skip_fail_summary(self):
        report = validator.validate(ROOT, runner=self.fake_runner, env={})
        self.assertEqual({"passed": 5, "skipped": 1, "failed": 0}, report["summary"])
        checks = [validator.Check(**item) for item in report["checks"]]
        text = validator.render_matrix(checks, report["branch"], report["commit"])
        self.assertIn("APP HARNESS VALIDATION", text)
        self.assertIn("[PASS] required files", text)
        self.assertIn("[SKIP] optional MCP symbol smoke: lsp_project_not_loaded", text)
        self.assertIn("Result: 5 passed / 1 skipped / 0 failed", text)
        self.assertIn("no live runtime, browser, launcher", text)

    def test_report_is_json_serializable(self):
        report = validator.validate(ROOT, runner=self.fake_runner, env={})
        encoded = json.dumps(report)
        decoded = json.loads(encoded)
        self.assertEqual("app-harness-validation/v1", decoded["schema_version"])
        self.assertEqual("test-branch", decoded["branch"])
        self.assertEqual("a" * 40, decoded["commit"])

    def test_required_validator_failure_is_blocking(self):
        def failing_runner(command, root):
            if command[:3] == ["git", "branch", "--show-current"]:
                return subprocess.CompletedProcess(command, 0, "test-branch\n", "")
            if command[:3] == ["git", "rev-parse", "HEAD"]:
                return subprocess.CompletedProcess(command, 0, "b" * 40 + "\n", "")
            if any(str(part).endswith("validate_harness.py") for part in command):
                return subprocess.CompletedProcess(command, 7, "", "broken root validator")
            return subprocess.CompletedProcess(command, 0, "PASS\n", "")

        report = validator.validate(ROOT, runner=failing_runner, env={})
        required = next(item for item in report["checks"] if item["name"] == "required files")
        self.assertEqual("FAIL", required["status"])
        self.assertEqual("required_harness_validator_failed", required["reason"])
        self.assertGreater(report["summary"]["failed"], 0)

    def test_missing_lsp_project_is_an_honest_skip(self):
        check = validator.check_optional_mcp(ROOT, {})
        self.assertEqual("SKIP", check.status)
        self.assertEqual("lsp_project_not_loaded", check.reason)

    def test_output_is_restricted_to_outputs(self):
        allowed = validator.output_path(ROOT, "Outputs/app-harness-validation.json")
        self.assertEqual(ROOT / "Outputs" / "app-harness-validation.json", allowed)
        with self.assertRaisesRegex(ValueError, "under Outputs"):
            validator.output_path(ROOT, "app-harness-validation.json")

    def test_previous_receipt_is_preserved_under_outputs_backups(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "Outputs" / "app-harness-validation.json"
            target.parent.mkdir(parents=True)
            target.write_text('{"old": true}\n', encoding="utf-8")
            backup = validator.preserve_existing_output(root, target)
            self.assertIsNotNone(backup)
            assert backup is not None
            self.assertTrue(backup.is_file())
            self.assertEqual(target.read_text(encoding="utf-8"), backup.read_text(encoding="utf-8"))
            self.assertIn("Outputs/backups/app-harness-validation/", backup.as_posix())

    def test_nested_harness_receipt_is_preserved_before_validator_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in validator.REQUIRED_FILES:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture\n", encoding="utf-8")
            nested = root / "Outputs" / "harness-completeness-report.json"
            nested.parent.mkdir(parents=True, exist_ok=True)
            nested.write_text('{"previous": true}\n', encoding="utf-8")
            check = validator.check_required_files(root, self.fake_runner)
            self.assertEqual("PASS", check.status)
            backups = list((root / "Outputs" / "backups" / "app-harness-validation").rglob("harness-completeness-report.json"))
            self.assertEqual(1, len(backups))
            self.assertEqual(nested.read_text(encoding="utf-8"), backups[0].read_text(encoding="utf-8"))

    def test_validator_and_receipt_are_registered_centrally(self):
        artifacts = json.loads((ROOT / "harness" / "artifacts.v1.json").read_text(encoding="utf-8"))
        artifact_ids = {item["id"] for item in artifacts["artifacts"]}
        self.assertIn("app-harness-validation-report", artifact_ids)

        validators = json.loads((ROOT / "harness" / "validators.v1.json").read_text(encoding="utf-8"))
        validator_ids = {item["id"] for item in validators["validators"]}
        self.assertIn("app-harness-validation", validator_ids)
        self.assertIn("app-harness-validation", validators["profiles"]["harness"])
        self.assertIn("app-harness-validation", validators["profiles"]["pre_push"])

    def test_offline_allowlist_rejects_launcher_and_network_commands(self):
        for command in (
            ["python", "app.py"],
            ["powershell", "Start-Process", "index.html"],
            ["curl", "https://example.invalid"],
            ["git", "clean", "-fd"],
        ):
            with self.subTest(command=command):
                with self.assertRaises(RuntimeError):
                    validator.safe_runner(command, ROOT)

    def test_cli_emits_matrix_and_json_without_runtime_lane(self):
        output = ROOT / "Outputs" / "test-app-harness-validation.json"
        output.unlink(missing_ok=True)
        try:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "validate_app_harness.py"), "--output", "Outputs/test-app-harness-validation.json"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("APP HARNESS VALIDATION", result.stdout)
            self.assertIn("Result: 5 passed / 1 skipped / 0 failed", result.stdout)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(0, payload["summary"]["failed"])
            self.assertIn("no live runtime, browser, launcher", payload["proof_ceiling"])
        finally:
            output.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
