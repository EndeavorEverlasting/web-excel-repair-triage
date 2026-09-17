from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_prompt_outcome_receipts as outcomes


class PromptOutcomeFieldReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.observations = cls.root / "harness/evals/observations/prompt-outcome"
        cls.paths = sorted(cls.observations.glob("*.json"))
        cls.receipts = [json.loads(path.read_text(encoding="utf-8")) for path in cls.paths]
        cls.by_id = {receipt["receipt_id"]: receipt for receipt in cls.receipts}

    def test_all_tracked_field_receipts_validate_and_have_unique_ids(self) -> None:
        self.assertGreaterEqual(len(self.receipts), 2)
        self.assertEqual(len(self.by_id), len(self.receipts))
        for receipt in self.receipts:
            with self.subTest(receipt_id=receipt["receipt_id"]):
                outcomes.validate_receipt(receipt)

    def test_p142_receipt_promotes_only_the_observed_drive_organizer_slice(self) -> None:
        receipt = self.by_id["field/20260916/p142-drive-organizer"]
        self.assertEqual(receipt["invocation"]["prompt_id"], "P142")
        self.assertEqual(receipt["result"], "SUCCESS")
        self.assertIsNone(receipt["classification"]["primary"])
        self.assertEqual(receipt["state_transition"], {"from": "INTEGRATED", "to": "OBSERVED"})
        self.assertIn("Same file IDs and URLs", receipt["observation"]["observed_state"])

    def test_p123_receipt_keeps_unobserved_gemini_export_blocked(self) -> None:
        receipt = self.by_id["field/20260916/p123-gemini-drive-title"]
        self.assertEqual(receipt["invocation"]["prompt_id"], "P123")
        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertEqual(receipt["classification"]["primary"], "environment")
        self.assertNotIn("state_transition", receipt)
        self.assertIn("Gemini export stage itself was not executed", receipt["observation"]["observed_state"])
        self.assertIn("Gemini", receipt["next_state"]["completion_gate"])

    def test_field_receipts_are_bounded_references_not_raw_provider_payloads(self) -> None:
        serialized = "\n".join(json.dumps(receipt, sort_keys=True) for receipt in self.receipts)
        for forbidden in ('"emailAddress":', '"permissions":', "drive.google.com", "docs.google.com"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
