from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "Invoke-HarnessProfile.ps1"
CONTRACT = ROOT / "harness" / "contracts" / "powershell-command-envelope.v1.json"
MANIFEST = ROOT / "harness" / "manifest.v1.json"
VALIDATORS = ROOT / "harness" / "validators.v1.json"
PRE_COMMIT = ROOT / ".githooks" / "pre-commit"
PRE_PUSH = ROOT / ".githooks" / "pre-push"


class PowerShellCommandEnvelopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = RUNNER.read_text(encoding="utf-8")
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_contract_is_versioned_and_points_to_runner(self) -> None:
        self.assertEqual(
            self.contract["schema_version"],
            "powershell-command-envelope/v1",
        )
        self.assertEqual(
            self.contract["runner"],
            "scripts/Invoke-HarnessProfile.ps1",
        )
        requirements = self.contract["requirements"]
        self.assertTrue(requirements["caller_terminal_survives"])
        self.assertTrue(requirements["standalone_exit_forbidden"])
        self.assertTrue(requirements["summary_finalized_on_failure"])
        self.assertFalse(requirements["automatic_dependency_installation"])
        self.assertFalse(requirements["destructive_cleanup"])

    def test_runner_never_terminates_the_caller(self) -> None:
        forbidden = {
            "standalone exit": r"(?im)^\s*exit(?:\s+[-+]?\d+)?\s*(?:#.*)?$",
            "environment exit": r"(?i)\[\s*Environment\s*\]::Exit\s*\(",
            "stop process": r"(?i)\bStop-Process\b",
            "kill process": r"(?i)\.Kill\s*\(",
        }
        for label, pattern in forbidden.items():
            with self.subTest(label=label):
                self.assertIsNone(re.search(pattern, self.runner), label)
        self.assertIn("throw", self.runner)
        self.assertIn("finally", self.runner)

    def test_runner_writes_durable_evidence(self) -> None:
        required_markers = (
            "run.log",
            "summary.json",
            ".stdout.log",
            ".stderr.log",
            "Write-AtomicJson",
            "RUNNING",
            "PASS",
            "FAIL",
            "durable summary",
            "durable run log",
        )
        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.runner)

    def test_evidence_exists_before_repository_root_gate(self) -> None:
        summary_write = self.runner.index(
            "Write-AtomicJson -Value $summary -Path $summaryPath"
        )
        root_resolve = self.runner.index(
            "$resolvedRoot = (Resolve-Path -LiteralPath $RepositoryRoot).Path"
        )
        self.assertLess(summary_write, root_resolve)
        self.assertIn("repository_root_requested", self.runner)

    def test_runner_uses_child_process_and_preserves_exit_code(self) -> None:
        self.assertIn("System.Diagnostics.ProcessStartInfo", self.runner)
        self.assertIn("System.Diagnostics.Process", self.runner)
        self.assertIn("$env:ComSpec", self.runner)
        self.assertIn("RedirectStandardOutput", self.runner)
        self.assertIn("RedirectStandardError", self.runner)
        self.assertIn("ReadToEndAsync", self.runner)
        self.assertIn("$process.ExitCode", self.runner)
        self.assertIn("call exit /b", self.runner)

    def test_command_file_path_is_quoted_for_spaces(self) -> None:
        self.assertIn("$escapedCommandPath", self.runner)
        self.assertIn('/d /s /c call `"$escapedCommandPath`"', self.runner)

    def test_runner_gates_repository_and_expected_head(self) -> None:
        self.assertIn("harness\\manifest.v1.json", self.runner)
        self.assertIn("harness\\validators.v1.json", self.runner)
        self.assertIn("git rev-parse HEAD", self.runner)
        self.assertIn("ExpectedHead", self.runner)
        self.assertIn("Expected HEAD", self.runner)

    def test_runner_does_not_install_dependencies_or_clean_work(self) -> None:
        forbidden = (
            "winget install",
            "choco install",
            "scoop install",
            "git reset --hard",
            "git clean -",
            "Remove-Item -Recurse",
        )
        lowered = self.runner.lower()
        for marker in forbidden:
            with self.subTest(marker=marker):
                self.assertNotIn(marker.lower(), lowered)

    def test_manifest_and_validator_profile_register_the_contract(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        contract = manifest["domain_contracts"]["powershell_command_envelope"]
        self.assertEqual(
            contract["contract"],
            "harness/contracts/powershell-command-envelope.v1.json",
        )
        self.assertEqual(
            contract["validator"],
            "tests/test_powershell_command_envelope.py",
        )
        validators = json.loads(VALIDATORS.read_text(encoding="utf-8"))
        harness_tests = next(
            item
            for item in validators["validators"]
            if item["id"] == "harness-contract-tests"
        )
        self.assertIn(
            "tests.test_powershell_command_envelope",
            harness_tests["command"],
        )
        self.assertEqual(
            manifest["validation_order"][1],
            harness_tests["command"],
        )

    def test_hooks_execute_the_command_envelope_contract_tests(self) -> None:
        expected = "tests.test_powershell_command_envelope"
        self.assertIn(expected, PRE_COMMIT.read_text(encoding="utf-8"))
        self.assertIn(expected, PRE_PUSH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
