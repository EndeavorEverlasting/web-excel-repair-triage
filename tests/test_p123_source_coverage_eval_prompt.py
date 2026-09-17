from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "p123_source_coverage_eval",
    ROOT / "scripts" / "evaluate_p123_source_coverage.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)

FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "p123_source_coverage"
    / "drive_7UyhyhxdFsQ_20260910.v1.json"
)
QUALITY = (
    ROOT
    / "tests"
    / "fixtures"
    / "p123_source_document_quality"
    / "drive_7UyhyhxdFsQ_20260910.v1.json"
)
CONTRACT = ROOT / "harness" / "contracts" / "p123-source-coverage-proof.v1.json"
PLAN = ROOT / "harness" / "evals" / "P123_SOURCE_COVERAGE_PROOF_PLAN.md"
IDENTITY_RECEIPT = (
    ROOT
    / "harness"
    / "evals"
    / "observations"
    / "prompt-outcome"
    / "2026-09-16-p123-gemini-drive-title.json"
)
REGISTRY = ROOT / "registry" / "prompts" / "ai-engineering-level-up-prompts.v1.json"


class P123SourceCoverageEvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = MOD.load_fixture(FIXTURE)
        cls.contract = MOD.load_contract(CONTRACT)
        cls.quality = json.loads(QUALITY.read_text(encoding="utf-8"))
        cls.identity = json.loads(IDENTITY_RECEIPT.read_text(encoding="utf-8"))
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.prompt = next(item for item in payload["prompts"] if item["id"] == "P123")

    def test_plan_and_contract_bind_the_same_owned_surfaces(self) -> None:
        plan = PLAN.read_text(encoding="utf-8")
        self.assertIn("Phase A — Deterministic coverage harness", plan)
        self.assertIn("field `OBSERVED` remains UNPROVEN", plan)
        self.assertEqual(self.contract["fixture"], "tests/fixtures/p123_source_coverage/drive_7UyhyhxdFsQ_20260910.v1.json")
        self.assertEqual(self.contract["scorer"], "scripts/evaluate_p123_source_coverage.py")
        self.assertEqual(
            set(self.contract["failure_classes"]),
            MOD.FAILURE_CLASSES,
        )

    def test_fixture_preserves_quality_regression_without_inventing_tail_content(self) -> None:
        source = self.fixture["source"]
        baseline = self.fixture["baseline_coverage_receipt"]
        self.assertEqual(source["identity"], "7UyhyhxdFsQ")
        self.assertEqual(source["duration_seconds"], self.quality["source"]["duration_seconds"])
        self.assertEqual(
            baseline["last_inspected_position_seconds"],
            self.quality["observed_output"]["last_timestamped_finding_seconds"],
        )
        self.assertFalse(baseline["explicit_end_coverage_receipt"])
        self.assertFalse(baseline["claims_specific_unrepresented_tail_facts"])
        self.assertIn("without inventing", self.fixture["proof_ceiling"])
        self.assertTrue(self.fixture["candidate_coverage_receipt"]["synthetic"])

    def test_identity_receipt_still_refuses_to_promote_tail_coverage(self) -> None:
        self.assertEqual(self.identity["invocation"]["prompt_id"], "P123")
        self.assertIn("does not promote", self.identity["classification"]["rationale"])
        self.assertIn("How WhatsApp Video Sharing Works?", self.identity["observation"]["observed_state"])

    def test_prompt_still_owns_full_source_coverage_contract_language(self) -> None:
        content = self.prompt["copyContent"]
        for marker in (
            "FULL-SOURCE COVERAGE / TAIL-CHECK CONTRACT",
            "COVERAGE_LEDGER",
            "LAST_INSPECTED_POSITION",
            "UNACCOUNTED_SPANS",
            "FULL_SOURCE_COVERAGE",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, content)

    def test_baseline_partial_receipt_fails_expected_coverage_classes(self) -> None:
        result = MOD.score_coverage_receipt(self.fixture, self.fixture["baseline_coverage_receipt"])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(
            set(result["failure_classes"]),
            set(self.fixture["expected"]["baseline_failure_classes"]),
        )

    def test_synthetic_complete_candidate_passes_and_stays_synthetic(self) -> None:
        result = MOD.score_coverage_receipt(self.fixture, self.fixture["candidate_coverage_receipt"])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["failure_classes"], [])
        self.assertTrue(result["synthetic"])

    def test_complete_overclaim_without_tail_accounting_fails(self) -> None:
        receipt = copy.deepcopy(self.fixture["baseline_coverage_receipt"])
        receipt["full_source_coverage"] = "COMPLETE"
        receipt["explicit_end_coverage_receipt"] = True
        receipt["unaccounted_spans"] = [{"start_seconds": 97, "end_seconds": 128}]
        result = MOD.score_coverage_receipt(self.fixture, receipt)
        self.assertIn("COMPLETE_WITHOUT_FULL_ACCOUNTING", result["failure_classes"])

    def test_fabricated_unrepresented_tail_facts_fail_closed(self) -> None:
        receipt = copy.deepcopy(self.fixture["candidate_coverage_receipt"])
        receipt["claims_specific_unrepresented_tail_facts"] = True
        result = MOD.score_coverage_receipt(self.fixture, receipt)
        self.assertIn("FABRICATED_UNREPRESENTED_TAIL_FACTS", result["failure_classes"])

    def test_source_extent_mismatch_fails_closed(self) -> None:
        receipt = copy.deepcopy(self.fixture["candidate_coverage_receipt"])
        receipt["source_extent_seconds"] = 999
        result = MOD.score_coverage_receipt(self.fixture, receipt)
        self.assertIn("SOURCE_EXTENT_MISMATCH", result["failure_classes"])

    def test_compare_fixture_passes_and_rejects_nonsynthetic_pass(self) -> None:
        comparison = MOD.compare_fixture(self.fixture)
        self.assertEqual(comparison["status"], "PASS")

        broken = copy.deepcopy(self.fixture)
        broken["candidate_coverage_receipt"] = copy.deepcopy(self.fixture["candidate_coverage_receipt"])
        broken["candidate_coverage_receipt"]["synthetic"] = False
        bad = MOD.compare_fixture(broken)
        self.assertEqual(bad["status"], "FAIL")
        self.assertTrue(any("synthetic" in error for error in bad["errors"]))

    def test_cli_writes_report_under_outputs_and_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # Route Outputs through a temp workspace by invoking main with absolute Outputs path.
            out = ROOT / "Outputs" / "p123-source-coverage-unittest-report.json"
            code = MOD.main(["--output", str(out), "--summary"])
            self.assertEqual(code, 0)
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["baseline"]["status"], "FAIL")
            self.assertEqual(report["candidate"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
