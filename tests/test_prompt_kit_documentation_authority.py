from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOSSARY = ROOT / "GLOSSARY.md"
INDEX = ROOT / "docs" / "README.md"
HISTORICAL_RELEASE = ROOT / "docs" / "PROMPT_KIT_WEB_MAINLINE_RELEASE.md"


class PromptKitDocumentationAuthorityTests(unittest.TestCase):
    def test_glossary_is_navigation_not_second_spec(self) -> None:
        text = GLOSSARY.read_text(encoding="utf-8")
        self.assertIn("Vocabulary and navigation only", text)
        for owner in (
            "AGENTS.md",
            "harness/specs/prompt-operations.md",
            "scripts/prompt_registry_ops.py",
            "scripts/build_prompt_kit_registry.py",
            "harness/contracts/prompt-kit-release-identity.v1.json",
            "harness/contracts/prompt-kit-portability.v1.json",
            "scripts/validate_observed_behavior_receipt.py",
        ):
            with self.subTest(owner=owner):
                self.assertIn(owner, text)
                self.assertTrue((ROOT / owner).exists(), f"glossary owner is missing: {owner}")

    def test_operator_index_routes_to_glossary(self) -> None:
        text = INDEX.read_text(encoding="utf-8")
        self.assertIn("../GLOSSARY.md", text)
        self.assertIn("does not restate product behavior", text)

    def test_stale_mainline_release_prose_is_removed(self) -> None:
        self.assertFalse(
            HISTORICAL_RELEASE.exists(),
            "obsolete release snapshot must not compete with current runtime/contracts",
        )


if __name__ == "__main__":
    unittest.main()
