"""Tests for git-tracked artifact hygiene."""
from __future__ import annotations

import unittest

from triage.gitignore_hygiene import scan_tracked_binaries


class GitignoreHygieneTests(unittest.TestCase):
    def test_attached_assets_not_tracked_on_clean_tip(self) -> None:
        report = scan_tracked_binaries()
        attached = [
            finding
            for finding in report.findings
            if finding.path.startswith("attached_assets/")
        ]
        self.assertEqual(attached, [])

    def test_fixture_allowlist_passes(self) -> None:
        report = scan_tracked_binaries(
            paths=[
                "tests/fixtures/cybernet_targets/mini_all_wave.xlsx",
                "tests/fixtures/sanitized/operator.log",
                "README.md",
            ]
        )
        self.assertTrue(report.ok)

    def test_runtime_and_secret_paths_fail(self) -> None:
        report = scan_tracked_binaries(
            paths=[
                "Outputs/live-report.json",
                "logs/operator.log",
                "private.key",
            ]
        )
        self.assertFalse(report.ok)
        self.assertEqual(
            {finding.path for finding in report.findings},
            {
                "Outputs/live-report.json",
                "logs/operator.log",
                "private.key",
            },
        )


if __name__ == "__main__":
    unittest.main()
