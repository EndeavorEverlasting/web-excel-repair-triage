from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE = ROOT / "AGENTS.md"


class PromptKitNavigationGovernanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = GOVERNANCE.read_text(encoding="utf-8")

    def test_distributed_top_bottom_navigation_is_governed(self) -> None:
        heading = "### Prompt Kit web top/bottom navigation invariant"
        self.assertIn(heading, self.text)
        section = self.text.split(heading, 1)[1].split("## 8.", 1)[0]

        for phrase in (
            "operator-facing Prompt Kit website",
            "every repeated prompt-group header row",
            "`Top` anchor/control on the left side",
            "`Bottom` anchor/control on the right side",
            "distributed throughout the rendered prompt surface",
            "one canonical page-top anchor",
            "one canonical page-bottom anchor",
            "All / Standard / GNHF / Doctrine",
            "section, type, and search filtering",
            "any header that remains visible must retain both controls",
            "stable, unique same-document targets",
            "pointer and keyboard activation",
            "canonical builder or generator",
            "generated HTML must not be hand-edited",
            "enumerate the repeated headers in the canonical generated page",
            "Workbook-only navigation does not satisfy this web-page contract",
            "separately declared Prompt Kit product sprint",
        ):
            self.assertIn(phrase, section)


if __name__ == "__main__":
    unittest.main()
