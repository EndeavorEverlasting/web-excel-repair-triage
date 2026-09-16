from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry


class P13OwnerDisplacementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        payload = json.loads(
            (ROOT / "registry/prompts/prompt-overrides.v1.json").read_text(
                encoding="utf-8"
            )
        )
        cls.p13 = next(item for item in payload["overrides"] if item["id"] == "P13")
        effective = build_prompt_kit_registry.load_prompt_registry()
        cls.effective_p13 = next(item for item in effective if item["id"] == "P13")

    def test_p13_retires_superseded_writer_and_continues_from_current_owner(self) -> None:
        copy = self.p13["copyContent"]
        for phrase in (
            "OWNER DISPLACEMENT / STALE-LANE CONVERGENCE",
            "SUPERSEDED WRITER",
            "stop competing writes",
            "Do not rebase, spawn sidecars",
            "because authority remains",
            "retire the stale integration vehicle",
            "Rejoin the surviving owner",
            "Exhaustive compute/full authority apply there",
            "never as permission for a superseded writer to continue",
            "STALE_OWNER_COMPETITION",
            "owner displacement retires stale writers",
        ):
            self.assertIn(phrase, copy)

    def test_p13_owner_displacement_requires_overlapping_supersession(self) -> None:
        copy = self.p13["copyContent"]
        self.assertIn("newer overlapping work/ownership is a state transition", copy)
        self.assertIn("If it supersedes this lane", copy)
        self.assertIn("Rejoin the surviving owner", copy)

    def test_p13_handoff_preserves_actionable_evidence(self) -> None:
        copy = self.p13["copyContent"]
        for phrase in (
            "branch/PR/SHA",
            "reusable findings/tests",
            "passed/failed proof",
            "unsafe work",
            "existing PR/ledger/handoff",
        ):
            self.assertIn(phrase, copy)

    def test_p13_metadata_makes_owner_displacement_part_of_completion(self) -> None:
        self.assertIn("retire the stale writer", self.p13["sprintRole"])
        self.assertIn("prior agent lane continuing", self.p13["useWhen"])
        self.assertIn("current canonical owner", self.p13["inspectFirst"])
        self.assertIn("actionable evidence handoff", self.p13["expectedOutput"])
        self.assertIn("stop competing writes", self.p13["nextStep"])
        self.assertIn("no superseded writer continues mutation", self.p13["proofGate"])

    def test_effective_p13_keeps_global_exhaustive_compute_contract(self) -> None:
        copy = self.effective_p13["copyContent"]
        for phrase in (
            "OWNER DISPLACEMENT / STALE-LANE CONVERGENCE",
            "COMPUTE AUTHORITY / SCOPE-BOUNDARY CONTRACT",
            "EXHAUSTIVE AVAILABLE COMPUTE RULE",
            "Treat exhaustive available compute as authorized by default",
            "Exhaust the decision-relevant safe compute available",
            "dispatch them immediately and execute them concurrently",
            "END-STATE CONTRACT HORIZON",
        ):
            self.assertIn(phrase, copy)

    def test_p13_keeps_prompt_bounded(self) -> None:
        self.assertLess(len(self.p13["copyContent"]), 18000)


if __name__ == "__main__":
    unittest.main()
