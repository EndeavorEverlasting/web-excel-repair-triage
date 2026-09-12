from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "repository_ai_evals",
    ROOT / "scripts/run_repository_ai_evals.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)

REGISTRY = ROOT / "harness/evals/repository-ai-evals.v1.json"
OBSERVED = ROOT / "harness/evals/fixtures/repository-ai-eval-observed-candidates.v1.json"


class RepositoryAIEvalFrameworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = MOD.load_json(REGISTRY)
        cls.suites = MOD.validate_registry(cls.registry)
        cls.by_id = {item["id"]: item for item in cls.suites}

    def test_registry_builds_full_eval_pyramid_without_model_tokens_for_exact_oracles(self) -> None:
        self.assertEqual(
            set(self.registry["layers"]),
            {"deterministic", "synthetic", "model_runtime", "human_review"},
        )
        self.assertEqual(self.by_id["prompt-finder-routing"]["layer"], "deterministic")
        self.assertEqual(self.by_id["prompt-language-actionability"]["layer"], "deterministic")
        self.assertEqual(self.by_id["p123-source-proof-boundary"]["layer"], "synthetic")
        self.assertEqual(self.by_id["p67-hallucination-diagnosis"]["layer"], "model_runtime")
        self.assertTrue(self.by_id["prompt-finder-routing"]["blocking"])
        self.assertTrue(self.by_id["p123-source-proof-boundary"]["blocking"])
        self.assertFalse(self.by_id["p67-hallucination-diagnosis"]["blocking"])

    def test_hallucination_suite_pairs_missing_truth_with_ignored_truth_and_correct_repairs(self) -> None:
        pair = self.by_id["p67-hallucination-diagnosis"]["required_pair"]
        self.assertEqual(pair["missing_context"]["classification"], "FACTUALITY_CONTEXT_MISSING")
        self.assertEqual(pair["missing_context"]["remediation"], "TARGETED_GROUNDING")
        self.assertEqual(pair["present_but_ignored"]["classification"], "FAITHFULNESS_CONTEXT_IGNORED")
        self.assertEqual(pair["present_but_ignored"]["remediation"], "REANCHOR_EXISTING_CONTEXT")

    def test_observed_usage_fixture_is_candidate_only_and_sanitized(self) -> None:
        summary = MOD.validate_observed_candidates(OBSERVED, self.registry)
        self.assertEqual(summary["candidate_count"], 1)
        self.assertEqual(summary["authority"], "candidate_only")
        self.assertFalse(summary["gold_eval_authority"])
        self.assertFalse(summary["mutation_authority"])

    def test_observed_usage_cannot_promote_itself_or_smuggle_raw_query_text(self) -> None:
        payload = json.loads(OBSERVED.read_text(encoding="utf-8"))
        payload["eval_sample_candidates"][0]["gold_eval_authority"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-authority.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(MOD.EvalFrameworkError, "gold_eval_authority"):
                MOD.validate_observed_candidates(path, self.registry)

        payload = json.loads(OBSERVED.read_text(encoding="utf-8"))
        payload["eval_sample_candidates"][0]["query_text"] = "private user text must not enter candidate corpus"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-query.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(MOD.EvalFrameworkError, "forbidden fields"):
                MOD.validate_observed_candidates(path, self.registry)

    def test_baseline_comparison_attributes_regressions_by_suite(self) -> None:
        baseline = {
            "schema_version": "repository-ai-eval-report/v1",
            "suites": [
                {"id": "prompt-finder-routing", "status": "PASS"},
                {"id": "p123-source-proof-boundary", "status": "PASS"},
            ],
        }
        candidate = [
            {"id": "prompt-finder-routing", "status": "FAIL"},
            {"id": "p123-source-proof-boundary", "status": "PASS"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "baseline.json"
            path.write_text(json.dumps(baseline), encoding="utf-8")
            delta = MOD.baseline_delta(candidate, path)
        assert delta is not None
        self.assertEqual(delta["regressions"], [
            {"id": "prompt-finder-routing", "baseline": "PASS", "candidate": "FAIL"}
        ])

    def test_model_runtime_defaults_to_unproven_after_contract_pass(self) -> None:
        suite = self.by_id["p67-hallucination-diagnosis"]
        original = MOD.run_command
        try:
            MOD.run_command = lambda command, timeout_seconds: {
                "exit_code": 0,
                "timed_out": False,
                "stdout_sha256": "0" * 64,
                "stderr_sha256": "0" * 64,
                "stdout_tail": "",
                "stderr_tail": "",
            }
            result = MOD.run_suite(suite, include_model_runtime=False, timeout_seconds=1)
        finally:
            MOD.run_command = original
        self.assertEqual(result["contract"]["status"], "PASS")
        self.assertEqual(result["status"], "UNPROVEN_RUNTIME")
        self.assertFalse(result["blocking"])

    def test_framework_is_registered_in_deterministic_floor_and_ci(self) -> None:
        floor = json.loads((ROOT / "harness/test-floor.v1.json").read_text(encoding="utf-8"))
        self.assertIn("tests/test_repository_ai_eval_framework.py", floor["self_tests"])
        workflow = (ROOT / ".github/workflows/repository-ai-evals.yml").read_text(encoding="utf-8")
        for marker in (
            "scripts/run_repository_ai_evals.py",
            "Outputs/repository-ai-eval-report.json",
            "tests.test_repository_ai_eval_framework",
            "repository-ai-eval-report",
        ):
            self.assertIn(marker, workflow)


if __name__ == "__main__":
    unittest.main()
