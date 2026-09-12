from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import prompt_kit_classifier_eval

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "Outputs"
POLICY = ROOT / "harness" / "evals" / "prompt-finder-classifier.v1.json"
CASES = ROOT / "harness" / "evals" / "fixtures" / "prompt-finder-classifier-cases.v1.json"
RUNNER = ROOT / "scripts" / "prompt_kit_classifier_eval.py"


class PromptKitClassifierEvalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = json.loads(POLICY.read_text(encoding="utf-8"))
        self.fixtures = json.loads(CASES.read_text(encoding="utf-8"))
        OUTPUTS.mkdir(parents=True, exist_ok=True)

    def test_contract_requires_quality_routing_and_failure_case_families(self) -> None:
        self.assertEqual(self.policy["schema_version"], "prompt-finder-classifier-eval/v1")
        self.assertEqual(self.policy["target"]["classifier_function"], "scorePromptFinderAnswers")
        self.assertEqual(self.policy["target"]["shared_search_runtime"], "docs/prompt-kit.js")
        self.assertEqual(self.policy["metrics"]["primary_accuracy_min"], 1.0)
        self.assertEqual(self.policy["metrics"]["required_recall_at_3_min"], 1.0)
        self.assertEqual(self.policy["metrics"]["case_pass_rate_min"], 1.0)
        self.assertEqual(
            set(self.policy["required_case_kinds"]),
            {"positive", "near_miss", "boundary", "malformed", "historical_risk"},
        )
        kinds = {case["kind"] for case in self.fixtures["cases"]}
        self.assertTrue(set(self.policy["required_case_kinds"]).issubset(kinds))

    def test_runner_reuses_canonical_search_and_classifier_sources(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        for marker in (
            'SEARCH_RUNTIME = ROOT / "docs" / "prompt-kit.js"',
            'GUIDED_RUNTIME = ROOT / "docs" / "prompt-kit-guided-recommendations.js"',
            '"function normalizeSearchText"',
            '"var PROMPT_FINDER_QUESTIONS="',
            '"function shell("',
            "build_prompt_kit_registry.load_prompt_kit_registry()",
        ):
            self.assertIn(marker, source)
        for duplicated_route in ("'P07'", '"P07"', "'P67'", '"P67"'):
            self.assertNotIn(duplicated_route, source)

    def test_policy_target_must_match_executed_runtime(self) -> None:
        mutated = copy.deepcopy(self.policy)
        mutated["target"]["runtime"] = "docs/not-the-runtime.js"
        with self.assertRaisesRegex(
            prompt_kit_classifier_eval.EvalError,
            "target does not match the executed canonical runtime",
        ):
            prompt_kit_classifier_eval.evaluate(mutated, self.fixtures)

    def test_cli_rejects_output_outside_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp) / "classifier-eval.json"
            completed = subprocess.run(
                [sys.executable, str(RUNNER), "--output", str(outside)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("output must be inside Outputs/", completed.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for canonical classifier execution")
    def test_cli_emits_passing_machine_readable_baseline(self) -> None:
        with tempfile.TemporaryDirectory(prefix="classifier-eval-test-", dir=OUTPUTS) as tmp:
            output = Path(tmp) / "classifier-eval.json"
            completed = subprocess.run(
                [sys.executable, str(RUNNER), "--output", str(output), "--summary"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn("PROMPT_FINDER_CLASSIFIER_EVAL_PASS", completed.stdout)
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["schema_version"], "prompt-finder-classifier-eval-result/v1")
        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["metrics"]["case_passes"], report["metrics"]["case_count"])
        self.assertEqual(report["metrics"]["primary_accuracy"], 1.0)
        self.assertEqual(report["metrics"]["required_recall_at_3"], 1.0)
        self.assertEqual(report["metrics"]["deterministic_rate"], 1.0)
        self.assertTrue(report["sources"]["classifier_runtime_sha256"])
        self.assertTrue(report["sources"]["shared_search_runtime_sha256"])
        self.assertTrue(report["sources"]["projected_registry_sha256"])
        self.assertGreater(report["sources"]["projected_registry_prompt_count"], 0)
        self.assertTrue(report["sources"]["registry_source_files"])
        self.assertEqual(
            report["proof_binding"]["projected_registry_sha256"],
            report["sources"]["projected_registry_sha256"],
        )
        self.assertEqual(report["proof_binding"]["validated_target"], report["target"])

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for canonical classifier execution")
    def test_wrong_gold_target_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.fixtures)
        target = next(case for case in mutated["cases"] if case["id"] == "goal-build-primary")
        target["expected_primary"] = "P12"
        report = prompt_kit_classifier_eval.evaluate(self.policy, mutated)
        self.assertEqual(report["verdict"], "fail")
        failed = {case["id"]: case for case in report["cases"]}
        self.assertEqual(failed["goal-build-primary"]["verdict"], "fail")
        self.assertIn("primary_expected:P12", failed["goal-build-primary"]["failures"])
        self.assertLess(report["metrics"]["primary_accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
