"""Focused regressions for staged and tracked artifact hygiene."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from triage.artifact_hygiene_policy import classify_path, normalize_path, scan_paths
from triage.gitignore_hygiene import scan_tracked_artifacts

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_staged_artifacts.py"


class ArtifactHygienePolicyTests(unittest.TestCase):
    def test_runtime_secret_and_machine_local_paths_are_blocked(self) -> None:
        blocked = (
            "Outputs/live-audit.json",
            "billing_runs/run-42/evidence.xlsx",
            "logs/operator.log",
            "crash_dumps/python.dmp",
            ".venv/Lib/site-packages/local.py",
            "credentials.json",
        )
        findings = scan_paths(blocked)
        self.assertEqual(
            [item.path for item in findings],
            sorted(blocked, key=str.casefold),
        )

    def test_sanitized_fixtures_code_and_env_template_are_allowed(self) -> None:
        allowed = (
            "tests/fixtures/sanitized/sample.xlsx",
            "harness/fixtures/runtime-log/example.log",
            "docs/fixtures/example-output.json",
            "docs/operator-guide.md",
            "triage/service.py",
            ".env.example",
        )
        self.assertEqual(scan_paths(allowed), [])

    def test_secret_material_stays_blocked_under_fixture_prefix(self) -> None:
        finding = classify_path("tests/fixtures/example/private.key")
        self.assertIsNotNone(finding)
        assert finding is not None
        self.assertEqual(finding.reason, "secret_or_credential_material")

    def test_windows_paths_are_normalized_without_reading_contents(self) -> None:
        self.assertEqual(
            normalize_path(r".\Outputs\run\summary.json"),
            "Outputs/run/summary.json",
        )
        finding = classify_path(r"Outputs\run\summary.json")
        self.assertIsNotNone(finding)
        assert finding is not None
        self.assertEqual(finding.path, "Outputs/run/summary.json")


class TrackedArtifactAggregateTests(unittest.TestCase):
    def test_tracked_scan_reuses_path_policy(self) -> None:
        report = scan_tracked_artifacts(paths=["logs/run.log", "README.md"])
        self.assertFalse(report.ok)
        self.assertEqual(len(report.findings), 1)
        self.assertEqual(report.findings[0].path, "logs/run.log")
        self.assertEqual(
            report.findings[0].reason,
            "generated_or_runtime_artifact",
        )

    def test_existing_sanitized_binary_allowlist_still_passes(self) -> None:
        report = scan_tracked_artifacts(
            paths=["tests/fixtures/cybernet_targets/mini_all_wave.xlsx", "README.md"]
        )
        self.assertTrue(report.ok, report.findings)


class StagedValidatorCliTests(unittest.TestCase):
    def test_explicit_blocked_path_fails_closed(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "Outputs/private-evidence.json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("Outputs/private-evidence.json", result.stderr)
        self.assertIn("generated_or_runtime_artifact", result.stderr)

    def test_explicit_safe_path_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "docs/operator-guide.md"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("staged artifact hygiene: PASS", result.stdout)


class HookSourceSafetyTests(unittest.TestCase):
    def test_pre_commit_runs_path_gate_before_staged_tree_validation(self) -> None:
        hook = (ROOT / ".githooks" / "pre-commit").read_text(encoding="utf-8")
        gate = "python scripts/validate_staged_artifacts.py"
        checkout = "git checkout-index"
        self.assertIn(gate, hook)
        self.assertIn(checkout, hook)
        self.assertLess(hook.index(gate), hook.index(checkout))

    def test_validator_never_reads_staged_file_contents(self) -> None:
        validator = VALIDATOR.read_text(encoding="utf-8").lower()
        self.assertNotIn("git show", validator)
        self.assertNotIn("read_text(", validator)
        self.assertNotIn("open(", validator)

    def test_ignore_policy_covers_local_evidence_and_secret_material(self) -> None:
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for marker in (
            "/logs/",
            "/saves/",
            "/crash_dumps/",
            "/.local-tools/",
            "/.env",
            "*.pem",
            "*.key",
            "*.dmp",
        ):
            self.assertIn(marker, ignore)


if __name__ == "__main__":
    unittest.main()
