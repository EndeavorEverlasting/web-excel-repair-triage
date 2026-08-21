from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_prompt_kit_registry  # noqa: E402


class P77QuantitativeEvidenceEnvelopeTests(unittest.TestCase):
    def test_effective_p77_enforces_date_attendance_envelope(self) -> None:
        prompts = {
            str(prompt["id"]): prompt
            for prompt in build_prompt_kit_registry.load_prompt_registry()
        }
        p77 = prompts["P77"]
        text = "\n".join(
            str(p77[field])
            for field in ("inspectFirst", "expectedOutput", "proofGate", "copyContent")
        ).lower()

        for phrase in (
            "exact dates consumed",
            "attendance envelope",
            "team/date context",
            "role identity",
            "round-number",
            "silently redistribute",
            "unresolved workstream allocation",
        ):
            self.assertIn(phrase, text)

        self.assertEqual(p77["profile"], "triage-management")
        self.assertEqual(p77["color"], "Emerald")


if __name__ == "__main__":
    unittest.main()
