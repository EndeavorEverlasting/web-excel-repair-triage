from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import operant_version


class OperantReleaseAnchorTests(unittest.TestCase):
    def test_release_anchor_chooses_latest_matching_integrated_release_boundary(self) -> None:
        newest = "d" * 40
        older = "a" * 40
        history = "\n".join(
            [
                f"{newest}\tchore(operant): release v0.6.0",
                f"{older}\tchore(operant): release v0.6.0",
            ]
        )
        with mock.patch.object(operant_version, "_run_git", return_value=history):
            with mock.patch.object(
                operant_version,
                "_version_at_ref",
                return_value=operant_version.SemVer.parse("0.6.0"),
            ):
                self.assertEqual(
                    operant_version.release_anchor("0.6.0", head="HEAD"),
                    newest,
                )

    def test_release_anchor_skips_same_subject_with_wrong_version(self) -> None:
        newest = "d" * 40
        correct = "c" * 40
        history = "\n".join(
            [
                f"{newest}\tchore(operant): release v0.6.0",
                f"{correct}\tchore(operant): release v0.6.0",
            ]
        )
        with mock.patch.object(operant_version, "_run_git", return_value=history):
            with mock.patch.object(
                operant_version,
                "_version_at_ref",
                side_effect=[
                    operant_version.SemVer.parse("0.5.0"),
                    operant_version.SemVer.parse("0.6.0"),
                ],
            ):
                self.assertEqual(operant_version.release_anchor("0.6.0"), correct)

    def test_release_anchor_fails_closed_when_history_has_no_valid_boundary(self) -> None:
        history = f"{'f' * 40}\tfix(operant): ordinary change"
        with mock.patch.object(operant_version, "_run_git", return_value=history):
            with self.assertRaises(operant_version.VersioningError):
                operant_version.release_anchor("0.6.0")

    def test_require_tag_validation_targets_release_anchor_not_moving_head(self) -> None:
        source = inspect.getsource(operant_version.validate)
        self.assertIn("release_anchor(version)", source)
        self.assertNotIn("expected exact HEAD", source)

    def test_mainline_workflow_reconciles_tag_from_release_anchor(self) -> None:
        workflow = (ROOT / ".github/workflows/operant-versioning.yml").read_text(encoding="utf-8")
        self.assertIn("python scripts/operant_version.py release-anchor", workflow)
        self.assertIn('gh release create "$tag"', workflow)
        self.assertIn('--target "$anchor"', workflow)
        self.assertNotIn("git diff --quiet HEAD^ HEAD -- OPERANT_VERSION", workflow)
        self.assertIn("python scripts/operant_version.py validate --require-tag", workflow)


if __name__ == "__main__":
    unittest.main()
