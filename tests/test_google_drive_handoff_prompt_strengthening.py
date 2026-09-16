from __future__ import annotations

import unittest

from scripts import build_prompt_kit_registry


class GoogleDriveHandoffPromptStrengtheningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prompts = {item["id"]: item for item in build_prompt_kit_registry.load_prompt_kit_registry()}

    def test_p11_owns_drive_allocated_handoff_harness_semantics(self) -> None:
        body = self.prompts["P11"]["copyContent"]
        for phrase in (
            "GOOGLE DRIVE ALLOCATION / PRIMARY HANDOFF CONTRACT",
            "verified Google Drive URL is the PRIMARY user-facing artifact link",
            "`sandbox:/...` link",
            "supplemental only",
            "name the exact Drive gate",
            "Drive-primary handoff does not make Drive source control",
            "Regression hardening must fail",
        ):
            self.assertIn(phrase, body)

    def test_p140_specializes_drive_primary_handoff_without_making_drive_universal_authority(self) -> None:
        body = self.prompts["P140"]["copyContent"]
        for phrase in (
            "GOOGLE DRIVE ALLOCATION / PRIMARY HANDOFF",
            "Do not assume Google Drive is authoritative merely because it is connected",
            "return the verified Google Drive URL as the primary operator-facing artifact",
            "`sandbox:/...` links",
            "name the exact access/permission/identity gate",
            "this rule changes handoff/routing behavior, not which clinical or health-data source is canonical",
        ):
            self.assertIn(phrase, body)

    def test_strengthening_reuses_existing_prompt_ids(self) -> None:
        self.assertEqual("End-to-End Harness Validator", self.prompts["P11"]["name"])
        self.assertEqual("Connected Health Record Workspace Synchronizer", self.prompts["P140"]["name"])


if __name__ == "__main__":
    unittest.main()
