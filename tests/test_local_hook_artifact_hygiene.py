"""Focused tests for local hook installation and path-only artifact hygiene."""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.install_local_hooks import HookInstallError, install_local_hooks
from triage.artifact_hygiene_policy import (
    REMEDIATION,
    classify_path,
    render_findings,
    scan_paths,
)

ROOT = Path(__file__).resolve().parents[1]


class ArtifactHygienePolicyTests(unittest.TestCase):
    def test_obvious_generated_runtime_paths_are_blocked(self) -> None:
        blocked = (
            "Outputs/live-audit.json",
            "billing_runs/run-42/evidence.xlsx",
            "logs/operator.log",
            "crash_dumps/python.dmp",
            ".venv/Lib/site-packages/local.py",
            "credentials.json",
        )
        findings = scan_paths(blocked)
        self.assertEqual([item.path for item in findings], sorted(blocked, key=str.casefold))

    def test_remediation_guidance_is_path_only(self) -> None:
        secret_excerpt = "DO_NOT_PRINT_THIS_SECRET"
        findings = scan_paths(["Outputs/private-evidence.json"])
        rendered = render_findings(findings)
        self.assertIn(
            "[harness] refusing staged generated/runtime artifact: "
            "Outputs/private-evidence.json",
            rendered,
        )
        self.assertIn(REMEDIATION, rendered)
        self.assertNotIn(secret_excerpt, rendered)

    def test_sanitized_fixtures_are_allowed(self) -> None:
        allowed = (
            "tests/fixtures/sanitized/sample.xlsx",
            "harness/fixtures/runtime-log/example.log",
            "docs/fixtures/example-output.json",
        )
        self.assertEqual(scan_paths(allowed), [])

    def test_docs_and_code_are_not_broadly_blocked(self) -> None:
        allowed = (
            "README.md",
            "docs/operator-guide.md",
            "triage/service.py",
            "tests/test_service.py",
            "configs/runtime_contract.json",
        )
        self.assertEqual(scan_paths(allowed), [])

    def test_secret_material_stays_blocked_even_under_fixture_prefix(self) -> None:
        finding = classify_path("tests/fixtures/example/private.key")
        self.assertIsNotNone(finding)
        self.assertEqual(finding.reason, "secret_or_credential_material")


class LocalHookInstallerTests(unittest.TestCase):
    def test_installer_configures_only_local_hooks_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            subprocess.run(
                ["git", "init"],
                cwd=repo,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            hooks = repo / ".githooks"
            hooks.mkdir()
            for name in ("pre-commit", "pre-push"):
                (hooks / name).write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

            configured = install_local_hooks(repo)
            self.assertEqual(configured, ".githooks")

            local_value = subprocess.run(
                ["git", "config", "--local", "--get", "core.hooksPath"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(local_value, ".githooks")

            global_value = subprocess.run(
                ["git", "config", "--global", "--get", "core.hooksPath"],
                cwd=repo,
                check=False,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertNotEqual(global_value, ".githooks")

    def test_installer_preserves_a_different_local_hook_setup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            subprocess.run(
                ["git", "init"],
                cwd=repo,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            hooks = repo / ".githooks"
            hooks.mkdir()
            for name in ("pre-commit", "pre-push"):
                (hooks / name).write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            subprocess.run(
                ["git", "config", "--local", "core.hooksPath", ".custom-hooks"],
                cwd=repo,
                check=True,
            )

            with self.assertRaises(HookInstallError):
                install_local_hooks(repo)

            value = subprocess.run(
                ["git", "config", "--local", "--get", "core.hooksPath"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(value, ".custom-hooks")


class HookSourceSafetyTests(unittest.TestCase):
    def test_pre_commit_runs_path_gate_before_staged_tree_validation(self) -> None:
        hook = (ROOT / ".githooks" / "pre-commit").read_text(encoding="utf-8")
        gate = "python scripts/validate_staged_artifacts.py"
        checkout = "git checkout-index"
        self.assertIn(gate, hook)
        self.assertIn(checkout, hook)
        self.assertLess(hook.index(gate), hook.index(checkout))

    def test_hooks_do_not_launch_runtime_or_network_activity(self) -> None:
        combined = "\n".join(
            (ROOT / ".githooks" / name).read_text(encoding="utf-8")
            for name in ("pre-commit", "pre-push")
        ).lower()
        forbidden = (
            "curl ",
            "wget ",
            "invoke-webrequest",
            "start-process",
            "streamlit run",
            "acquire-latest",
            "run-promptkitgenerator",
            "http://",
            "https://",
        )
        for marker in forbidden:
            self.assertNotIn(marker, combined)

    def test_hook_and_validator_never_read_staged_file_contents(self) -> None:
        hook = (ROOT / ".githooks" / "pre-commit").read_text(encoding="utf-8")
        validator = (
            ROOT / "scripts" / "validate_staged_artifacts.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("git show", hook.lower())
        self.assertNotIn("read_text(", validator)
        self.assertNotIn("open(", validator)


if __name__ == "__main__":
    unittest.main()
