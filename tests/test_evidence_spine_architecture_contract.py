from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "harness" / "prompt-topology" / "EVIDENCE_SPINE_ARCHITECTURE.md"


class EvidenceSpineArchitectureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = ARCH.read_text(encoding="utf-8")

    def test_architecture_artifact_exists(self) -> None:
        self.assertTrue(ARCH.is_file())

    def test_decision_prefers_adapter_only(self) -> None:
        self.assertIn("PREFER ADAPTER-ONLY / NO NEW SPINE", self.text)
        self.assertIn("Rejected", self.text)
        self.assertIn("Accepted", self.text)
        self.assertIn("No generic analytics/event bus", self.text)
        self.assertIn("Do **not** introduce a universal lifecycle envelope", self.text)

    def test_required_sections_and_traces(self) -> None:
        for phrase in (
            "State-owner matrix",
            "Identity and provenance model",
            "Trace 1 — Recommendation path",
            "Trace 2 — Autonomous repair path",
            "Trace 3 — Phase D candidate path",
            "Completion-candidate rule",
            "PR #450",
            "PR #431",
            "continuation resolver",
            "unknown",
        ):
            self.assertIn(phrase, self.text)

    def test_preserves_p99_p115_and_forbids_phase_d_implementation(self) -> None:
        self.assertIn("P99", self.text)
        self.assertIn("P115", self.text)
        self.assertIn("No Phase D topology mutation", self.text)
        self.assertIn("do not wholesale merge", self.text.lower())


if __name__ == "__main__":
    unittest.main()
