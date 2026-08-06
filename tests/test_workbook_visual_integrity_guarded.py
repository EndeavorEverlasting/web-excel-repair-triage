from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import validate_workbook_visual_integrity_guarded as guarded


class GuardedVisualIntegrityTests(unittest.TestCase):
    def test_style_only_profile_requires_runtime_baseline(self) -> None:
        profile = {"rules": [{"id": "STYLE", "type": "style_only_baseline", "preserve": ["cell_values"]}]}
        with self.assertRaises(guarded.GuardError):
            guarded.guard_profile(profile, baseline_supplied=False)
        guarded.guard_profile(profile, baseline_supplied=True)

    def test_unbounded_date_striping_fails(self) -> None:
        profile = {
            "rules": [
                {"id": "FORBID", "type": "forbid_unbounded_striping", "forbidden": ["date", "person"]},
                {
                    "id": "STRIPE",
                    "type": "same_key_style",
                    "sheet": "NTH",
                    "rows": [1, 20],
                    "key_semantic": "date",
                },
            ],
            "exceptions": [],
        }
        with self.assertRaises(guarded.GuardError):
            guarded.guard_profile_static(profile)

    def test_bounded_legacy_date_band_passes(self) -> None:
        profile = {
            "rules": [
                {"id": "FORBID", "type": "forbid_unbounded_striping", "forbidden": ["date", "person"]},
                {
                    "id": "STRIPE",
                    "type": "same_key_style",
                    "sheet": "NTH",
                    "rows": [9, 20],
                    "key_semantic": "date",
                },
            ],
            "exceptions": [
                {
                    "type": "legacy_date_band",
                    "bounded_sheet": "NTH",
                    "bounded_rows": [9, 20],
                }
            ],
        }
        guarded.guard_profile_static(profile)

    def test_report_inside_repo_must_be_under_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with mock.patch.object(guarded, "ROOT", root), mock.patch.object(
                guarded, "OUTPUT_ROOT", root / "Outputs"
            ):
                with self.assertRaises(guarded.GuardError):
                    guarded.guard_output(root / "Candidates" / "report.json", [])
                allowed = guarded.guard_output(root / "Outputs" / "report.json", [])
        self.assertEqual(allowed.name, "report.json")

    def test_report_cannot_overwrite_input(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            workbook = Path(folder) / "candidate.xlsx"
            with self.assertRaises(guarded.GuardError):
                guarded.guard_output(workbook, [workbook])

    def test_unknown_rule_type_fails_closed(self) -> None:
        with self.assertRaises(guarded.GuardError):
            guarded.guard_profile_static({"rules": [{"id": "UNKNOWN", "type": "magic"}]})


if __name__ == "__main__":
    unittest.main()
