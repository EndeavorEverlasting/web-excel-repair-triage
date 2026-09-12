from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


SEED = load_module(
    "repository_ai_eval_baseline_seed",
    ROOT / "scripts/seed_repository_ai_eval_baseline.py",
)
RUNNER = load_module(
    "repository_ai_eval_runner_for_baseline_test",
    ROOT / "scripts/run_repository_ai_evals.py",
)
WORKFLOW = ROOT / ".github/workflows/repository-ai-evals.yml"


class RepositoryAIEvalBaselineSeedingTests(unittest.TestCase):
    def test_seed_report_requires_exact_passing_commit(self) -> None:
        sha = "a" * 40
        payload = {
            "schema_version": "repository-ai-eval-report/v1",
            "commit_sha": sha,
            "status": "PASS",
            "suites": [],
        }
        SEED.validate_baseline_report(payload, sha)

        wrong_sha = dict(payload, commit_sha="b" * 40)
        with self.assertRaisesRegex(SEED.BaselineSeedError, "commit does not match"):
            SEED.validate_baseline_report(wrong_sha, sha)

        degraded = dict(payload, status="FAIL")
        with self.assertRaisesRegex(SEED.BaselineSeedError, "degraded baseline"):
            SEED.validate_baseline_report(degraded, sha)

    def test_pass_to_fail_regression_sentinel(self) -> None:
        baseline = {
            "schema_version": "repository-ai-eval-report/v1",
            "commit_sha": "a" * 40,
            "status": "PASS",
            "suites": [
                {"id": "sentinel-pass-to-fail", "status": "PASS"},
                {"id": "unchanged-pass", "status": "PASS"},
            ],
        }
        candidate = [
            {"id": "sentinel-pass-to-fail", "status": "FAIL"},
            {"id": "unchanged-pass", "status": "PASS"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "baseline.json"
            path.write_text(json.dumps(baseline), encoding="utf-8")
            delta = RUNNER.baseline_delta(candidate, path)
        assert delta is not None
        self.assertEqual(
            delta["regressions"],
            [{"id": "sentinel-pass-to-fail", "baseline": "PASS", "candidate": "FAIL"}],
        )
        self.assertEqual(
            delta["changed"],
            [{"id": "sentinel-pass-to-fail", "baseline": "PASS", "candidate": "FAIL"}],
        )

    def test_workflow_refreshes_and_seeds_default_branch_baseline(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for marker in (
            "Resolve refreshed default-branch baseline",
            "git fetch --no-tags origin",
            "BASE_REF: ${{ github.base_ref }}",
            "PUSH_BEFORE: ${{ github.event.before }}",
            'REF="$PUSH_BEFORE"',
            "scripts/seed_repository_ai_eval_baseline.py",
            "--baseline-ref \"${{ steps.baseline.outputs.ref }}\"",
            "--baseline-report Outputs/repository-ai-eval-baseline.json",
            "Outputs/repository-ai-eval-baseline.json",
            "Verify PASS-to-FAIL comparator sentinel",
        ):
            self.assertIn(marker, workflow)
        self.assertNotIn('BASE_REF="${{ github.base_ref }}"', workflow)
        self.assertNotIn('REF="${{ github.event.before }}"', workflow)

    def test_seed_output_contract_stays_under_outputs(self) -> None:
        inside = SEED.resolve_output(Path("Outputs/repository-ai-eval-baseline.json"))
        self.assertTrue(inside.is_relative_to((ROOT / "Outputs").resolve()))
        with self.assertRaisesRegex(SEED.BaselineSeedError, "must remain under Outputs"):
            SEED.resolve_output(ROOT.parent / "baseline.json")

    def test_atomic_write_filesystem_errors_are_controlled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            blocker = Path(tmp) / "not-a-directory"
            blocker.write_text("occupied", encoding="utf-8")
            destination = blocker / "baseline.json"
            with self.assertRaisesRegex(SEED.BaselineSeedError, "failed to write baseline report atomically"):
                SEED.write_json_atomic(destination, {"status": "PASS"})


if __name__ == "__main__":
    unittest.main()
