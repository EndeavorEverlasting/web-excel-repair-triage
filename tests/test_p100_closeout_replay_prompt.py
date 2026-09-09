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
import evaluate_p100_closeout_replay


class P100CloseoutReplayTests(unittest.TestCase):
    FIXTURE = ROOT / "tests" / "fixtures" / "p100_closeout_replay" / "opencode_p122_closeout_01ac559.v1.json"

    def _fixture(self) -> dict:
        return json.loads(self.FIXTURE.read_text(encoding="utf-8"))

    def test_preserved_opencode_closeout_contains_both_contradictions(self) -> None:
        fixture = self._fixture()
        self.assertEqual(fixture["candidate_sha"], "01ac559ac5ff774978a0cdedcb27f9b816bfb9d4")
        closeout = fixture["before"]["observed_closeout_text"]
        self.assertIn("none; no safe actionable work remains", closeout)
        self.assertIn("feat/gemini-youtube-ingestion-prompt-20260827", closeout)
        self.assertIn("will need rebase to P123 on merge", closeout)
        evidence = {item["id"]: item for item in fixture["authoritative_evidence"]}
        self.assertEqual(evidence["deterministic-test-floor-red"]["run_id"], 33086093122)
        self.assertEqual(evidence["deterministic-test-floor-red"]["status"], "failure")
        self.assertTrue(evidence["deterministic-test-floor-red"]["safe_action_available"])
        self.assertEqual(evidence["acknowledged-p122-identity-conflict"]["status"], "open")
        self.assertTrue(evidence["acknowledged-p122-identity-conflict"]["safe_action_available"])

    def test_current_p100_replay_rejects_terminal_none_and_preserves_before_after(self) -> None:
        fixture = self._fixture()
        p100 = {item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()}["P100"]
        report = evaluate_p100_closeout_replay.build_report(fixture, p100)

        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["p100"]["present"])
        self.assertEqual(report["p100"]["missing_markers"], [])
        self.assertTrue(report["before"]["accepted_terminal"])
        self.assertFalse(report["after"]["accepted_terminal"])
        self.assertEqual(report["after"]["classification"], "FAITHFULNESS_CONTEXT_IGNORED")
        self.assertEqual(
            report["after"]["contradiction_reasons"],
            ["required_gate_failure", "acknowledged_identity_conflict"],
        )
        self.assertTrue(report["after"]["context_identity"].startswith("effective-P100:"))
        self.assertIn("UNKNOWN", report["before"]["context_identity"])
        self.assertIsNone(report["escalation_owner"])
        self.assertTrue(report["expected_match"])

    def test_true_terminal_counterexample_remains_allowed(self) -> None:
        fixture = self._fixture()
        p100 = {item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()}["P100"]
        report = evaluate_p100_closeout_replay.build_report(fixture, p100)
        self.assertTrue(report["counterexample"]["accepted_terminal"])
        self.assertEqual(report["counterexample"]["classification"], "NONE")
        self.assertEqual(report["counterexample"]["contradiction_reasons"], [])

    def test_failed_replay_with_p100_present_routes_to_p67_not_wording_patch(self) -> None:
        fixture = self._fixture()
        p100 = {item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()}["P100"]
        broken = json.loads(json.dumps(fixture))
        broken["expected_after"]["classification"] = "FACTUALITY_MISSING_CONTEXT"
        report = evaluate_p100_closeout_replay.build_report(broken, p100)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(report["p100"]["present"])
        self.assertEqual(report["escalation_owner"], "P67")
        self.assertIn("source-faithfulness eval", report["escalation_reason"])
        self.assertNotIn("wording patch", report["escalation_reason"].split("rather than")[0])


if __name__ == "__main__":
    unittest.main()
