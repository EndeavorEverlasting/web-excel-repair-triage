from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE = ROOT / "AGENTS.md"


class GovernanceClientDeliveryTests(unittest.TestCase):
    def test_governance_exists_and_client_delivery_is_minimum_sufficient(self) -> None:
        self.assertTrue(GOVERNANCE.is_file())
        text = GOVERNANCE.read_text(encoding="utf-8")
        for phrase in (
            "single repository governance authority",
            "minimum sufficient explanation",
            "purpose, period, totals, attachment, consequence",
            "Do not narrate internal evidence mechanics",
            "private allocation logic",
            "singled-out edge cases unless needed to act",
            "Do not add defensive caveats or invitation-to-question closings",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
