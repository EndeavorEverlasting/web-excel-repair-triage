from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "p123_youtube_ingestion_behavior_eval",
    ROOT / "scripts" / "evaluate_p123_youtube_ingestion_behavior.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)

FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "p123_youtube_ingestion_behavior"
    / "drive_ud64uounlw_20260831.v1.json"
)


class P123YouTubeIngestionBehaviorEvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = MOD.load_fixture(FIXTURE)

    def test_fixture_preserves_real_single_short_context_and_eval_ownership(self):
        self.assertEqual(self.fixture["owner"], "P123")
        self.assertEqual(self.fixture["eval_owner"], "P67")
        self.assertEqual(self.fixture["source"]["kind"], "youtube_short")
        self.assertEqual(self.fixture["source"]["identity"], "Ud-64UOUNlw")
        self.assertFalse(self.fixture["source"]["repository_access"])
        self.assertFalse(self.fixture["source"]["playlist_corpus_supplied"])
        self.assertFalse(self.fixture["source"]["donor_pins_supplied"])
        self.assertFalse(self.fixture["source"]["live_ytdlp_execution_evidence"])
        self.assertFalse(self.fixture["source"]["execution_trace_preserved"])

    def test_observed_baseline_fails_all_expected_proof_and_source_classes(self):
        result = MOD.score_response(self.fixture, self.fixture["baseline_response"])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["classification"], "FAITHFULNESS_CONTEXT_IGNORED")
        self.assertEqual(result["remediation"], "REANCHOR_EXISTING_CONTEXT")
        self.assertEqual(
            set(result["failure_classes"]),
            set(self.fixture["expected"]["baseline_failure_classes"]),
        )

    def test_candidate_that_reanchors_existing_context_passes(self):
        result = MOD.score_response(self.fixture, self.fixture["candidate_response"])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["classification"], "NONE")
        self.assertEqual(result["remediation"], "NONE")
        self.assertEqual(result["failure_classes"], [])

    def test_25_23_regression_fixture_is_allowed_only_when_explicitly_labeled_synthetic(self):
        bad = "SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\nCanonical result: 25 occurrences / 23 unique IDs"
        bad_result = MOD.score_response(self.fixture, bad)
        self.assertIn("SOURCE_CONTEXT_REPLACED", bad_result["failure_classes"])

        good = (
            "SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\n"
            "SYNTHETIC REGRESSION FIXTURE ONLY: 25 occurrences / 23 unique IDs"
        )
        good_result = MOD.score_response(self.fixture, good)
        self.assertNotIn("SOURCE_CONTEXT_REPLACED", good_result["failure_classes"])

    def test_multiline_25_23_claim_cannot_evade_source_context_gate(self):
        bad = (
            "SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\n"
            "playlist_occurrence_count: 25\n"
            "unique_source_identities: 23"
        )
        result = MOD.score_response(self.fixture, bad)
        self.assertIn("SOURCE_CONTEXT_REPLACED", result["failure_classes"])

        good = (
            "SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\n"
            "SYNTHETIC REGRESSION FIXTURE ONLY\n"
            "playlist_occurrence_count: 25\n"
            "unique_source_identities: 23"
        )
        good_result = MOD.score_response(self.fixture, good)
        self.assertNotIn("SOURCE_CONTEXT_REPLACED", good_result["failure_classes"])

    def test_donor_pins_fail_closed_when_no_pin_evidence_was_supplied(self):
        response = 'SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\n"pinned_version": "v9.9.9"'
        result = MOD.score_response(self.fixture, response)
        self.assertIn("UNSUPPORTED_DONOR_PIN", result["failure_classes"])

        prose = "SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\npinned yt-dlp version v9.9.9"
        prose_result = MOD.score_response(self.fixture, prose)
        self.assertIn("UNSUPPORTED_DONOR_PIN", prose_result["failure_classes"])

        response_unknown = 'SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\n"pinned_version": "NOT_SUPPLIED"'
        result_unknown = MOD.score_response(self.fixture, response_unknown)
        self.assertNotIn("UNSUPPORTED_DONOR_PIN", result_unknown["failure_classes"])

    def test_fixture_or_metadata_tool_claim_cannot_be_promoted_to_live_ytdlp_proof(self):
        response = (
            "SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\n"
            "Live YouTube metadata access | PROVEN | metadata retrieved"
        )
        result = MOD.score_response(self.fixture, response)
        self.assertIn("UNSUPPORTED_LIVE_PROOF", result["failure_classes"])

        bounded = (
            "SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\n"
            "Live yt-dlp metadata extraction: UNPROVEN because no runtime evidence is supplied"
        )
        bounded_result = MOD.score_response(self.fixture, bounded)
        self.assertNotIn("UNSUPPORTED_LIVE_PROOF", bounded_result["failure_classes"])

    def test_unproven_disclaimer_cannot_mask_separate_live_proof_claim(self):
        response = (
            "SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\n"
            "Live yt-dlp metadata: UNPROVEN | Live YouTube metadata: PROVEN"
        )
        result = MOD.score_response(self.fixture, response)
        self.assertIn("UNSUPPORTED_LIVE_PROOF", result["failure_classes"])

    def test_negated_live_proof_wording_is_not_misclassified_as_proof(self):
        for wording in (
            "Live YouTube metadata was not verified",
            "live yt-dlp was not proven",
            "Current YouTube behavior was not retrieved",
        ):
            with self.subTest(wording=wording):
                result = MOD.score_response(
                    self.fixture,
                    f"SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\n{wording}",
                )
                self.assertNotIn("UNSUPPORTED_LIVE_PROOF", result["failure_classes"])

    def test_unbound_exact_test_pass_claim_fails_but_unproven_wording_does_not(self):
        response = (
            "SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\n"
            "Verified all 6 deterministic tests passing (0.284s)"
        )
        result = MOD.score_response(self.fixture, response)
        self.assertIn("UNBOUND_EXECUTION_PROOF", result["failure_classes"])

        words = (
            "SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\n"
            "all six deterministic tests passed"
        )
        words_result = MOD.score_response(self.fixture, words)
        self.assertIn("UNBOUND_EXECUTION_PROOF", words_result["failure_classes"])

        bounded = (
            "SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\n"
            "Deterministic tests: UNPROVEN in this preserved artifact; execution trace not supplied"
        )
        bounded_result = MOD.score_response(self.fixture, bounded)
        self.assertNotIn("UNBOUND_EXECUTION_PROOF", bounded_result["failure_classes"])

    def test_malformed_fixture_boolean_fails_closed_instead_of_becoming_truthy(self):
        malformed = copy.deepcopy(self.fixture)
        malformed["source"]["donor_pins_supplied"] = "false"
        with self.assertRaisesRegex(ValueError, "donor_pins_supplied must be boolean"):
            MOD.score_response(
                malformed,
                'SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\n"pinned_version": "v9.9.9"',
            )

    def test_zero_proven_risk_language_is_rejected_when_asserted_not_when_rejected(self):
        response = "SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\nFormula injection risk | ZERO_PROVEN"
        result = MOD.score_response(self.fixture, response)
        self.assertIn("ABSOLUTE_RISK_OVERCLAIM", result["failure_classes"])

        bounded = (
            "SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\n"
            "`ZERO_PROVEN` is unsupported and is not claimed here"
        )
        bounded_result = MOD.score_response(self.fixture, bounded)
        self.assertNotIn("ABSOLUTE_RISK_OVERCLAIM", bounded_result["failure_classes"])

    def test_repository_boundary_stays_independent_from_other_failures(self):
        safe = "SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\nTarget repo path: UNKNOWN_REQUIRES_REPO_INSPECTION"
        safe_result = MOD.score_response(self.fixture, safe)
        self.assertNotIn("REPOSITORY_BOUNDARY_BREACH", safe_result["failure_classes"])

        bad = "SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\nTarget repository tests passed"
        bad_result = MOD.score_response(self.fixture, bad)
        self.assertIn("REPOSITORY_BOUNDARY_BREACH", bad_result["failure_classes"])

    def test_repository_boundary_allows_explicit_denials(self):
        for wording in (
            "Target repository tests passed: NOT OBSERVED",
            "No repository patch applied",
            "Committed to target repo: UNKNOWN",
            "Merged into target repo: UNPROVEN",
        ):
            with self.subTest(wording=wording):
                result = MOD.score_response(
                    self.fixture,
                    f"SOURCE_INPUT_IDENTITY: Ud-64UOUNlw\n{wording}",
                )
                self.assertNotIn("REPOSITORY_BOUNDARY_BREACH", result["failure_classes"])

    def test_baseline_candidate_comparison_is_reproducible(self):
        comparison = MOD.compare_fixture(self.fixture)
        self.assertEqual(comparison["status"], "PASS")
        self.assertEqual(comparison["baseline"]["status"], "FAIL")
        self.assertEqual(comparison["candidate"]["status"], "PASS")
        self.assertIn("false_positive_risk", comparison)
        self.assertIn("false_negative_risk", comparison)

    def test_cli_writes_machine_readable_report_and_returns_green_for_expected_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            rc = MOD.main(["--fixture", str(FIXTURE), "--output", str(out)])
            self.assertEqual(rc, 0)
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(report["schema_version"], "p123-youtube-ingestion-behavior-comparison/v1")
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["baseline"]["status"], "FAIL")
            self.assertEqual(report["candidate"]["status"], "PASS")

    def test_existing_p67_pair_remains_the_model_runtime_hallucination_layer(self):
        floor = json.loads((ROOT / "harness" / "test-floor.v1.json").read_text(encoding="utf-8"))
        self.assertIn("tests/test_p67_source_faithfulness_eval_prompt.py", floor["self_tests"])
        self.assertIn("tests/test_p123_youtube_ingestion_behavior_eval_prompt.py", floor["self_tests"])


if __name__ == "__main__":
    unittest.main()
