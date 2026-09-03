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
            "Omit internal evidence mechanics",
            "private allocation logic",
            "singled-out edge cases",
            "defensive caveats",
            "invitation-to-question closings",
            "unless needed for recipient action",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
