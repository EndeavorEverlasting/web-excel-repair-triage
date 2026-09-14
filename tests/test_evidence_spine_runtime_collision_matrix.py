from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "harness" / "prompt-topology" / "EVIDENCE_SPINE_RUNTIME_COLLISION_MATRIX.md"
ARCH = ROOT / "harness" / "prompt-topology" / "EVIDENCE_SPINE_ARCHITECTURE.md"


class EvidenceSpineRuntimeCollisionMatrixTests(unittest.TestCase):
    def test_matrix_and_architecture_exist(self) -> None:
        self.assertTrue(ARCH.is_file())
        self.assertTrue(MATRIX.is_file())
        text = MATRIX.read_text(encoding="utf-8")
        for phrase in (
            "Shared surfaces (coordinator-only writers)",
            "Lane A — routing reconciliation",
            "Lane B — bounded observation",
            "Lane C — recurrence",
            "Parallel safety verdict",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
