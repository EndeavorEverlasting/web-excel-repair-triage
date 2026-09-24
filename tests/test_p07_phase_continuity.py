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

MARKER = "P07 PHASE CONTINUITY CONTRACT"


class P07PhaseContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        raw = json.loads((ROOT / "docs" / "prompts.json").read_text(encoding="utf-8"))
        cls.raw_p07 = next(prompt for prompt in raw if prompt["id"] == "P07")
        effective = {prompt["id"]: prompt for prompt in build_prompt_kit_registry.load_prompt_registry()}
        cls.effective_p07 = effective["P07"]

    def test_p07_distinguishes_phase_local_scope_from_true_prohibition(self) -> None:
        content = self.raw_p07["copyContent"]
        self.assertIn(MARKER, content)
        self.assertIn("PHASE-LOCAL OUT OF SCOPE", content)
        self.assertIn("USER/REPO FORBIDDEN", content)
        self.assertIn(
            "do not by themselves forbid a later successor phase",
            content,
        )

    def test_p07_continues_into_evidence_backed_successor_without_operator_nudge(self) -> None:
        content = self.raw_p07["copyContent"]
        for phrase in (
            "same execution thread",
            "evidence-backed successor phase",
            "refresh current repository/provider truth",
            "issue a new bounded sprint declaration",
            "without waiting for the operator to restate or re-authorize work already covered by the mission",
        ):
            self.assertIn(phrase, content)

    def test_phase_crossing_redeclares_scope_proof_and_authority(self) -> None:
        content = self.raw_p07["copyContent"]
        for phrase in (
            "successor owned scope",
            "successor forbidden scope",
            "dependencies and collision risks",
            "expected artifacts and validation",
            "proof ceiling",
            "mutation authority",
        ):
            self.assertIn(phrase, content)

    def test_none_is_invalid_when_safe_successor_phase_is_evident(self) -> None:
        content = self.raw_p07["copyContent"]
        self.assertIn(
            "`none; no safe actionable work remains` is invalid merely because the active phase is complete",
            content,
        )
        self.assertIn("safe, dependency-ready successor work", content)

    def test_true_phase_stop_conditions_remain_explicit(self) -> None:
        content = self.raw_p07["copyContent"]
        for phrase in (
            "operator explicitly limited the mission to the completed phase",
            "repository or user policy forbids the successor",
            "successor is unsafe or BLOCKED",
            "required dependency is unresolved",
            "no evidence-backed successor exists",
        ):
            self.assertIn(phrase, content)

    def test_next_step_and_proof_gate_encode_continuity(self) -> None:
        self.assertIn("phase-local exclusions", self.raw_p07["nextStep"])
        self.assertIn("successor sprint", self.raw_p07["nextStep"])
        self.assertIn(
            "Phase-local forbidden scope alone is not a terminal condition",
            self.raw_p07["proofGate"],
        )

    def test_effective_p07_preserves_raw_phase_continuity_contract(self) -> None:
        content = self.effective_p07["copyContent"]
        self.assertEqual(content.count(MARKER), 1)
        self.assertIn("P07 MAINLINE CONVERGENCE OVERRIDE", content)
        self.assertIn("OPERATIONAL CLOSEOUT / GAP-RISK CONTRACT", content)


if __name__ == "__main__":
    unittest.main()
