from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import prompt_improvement_compiler as improvement
from scripts import prompt_language_compiler as compiler

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "harness" / "prompt-compilation" / "PROMPT_COMPILATION_ARCHITECTURE.md"
SPRINT = ROOT / "harness" / "prompt-compilation" / "PROMPT_COMPILATION_SPRINT_MAP.md"
JOURNEYS = ROOT / "harness" / "prompt-compilation" / "improvement-journeys"
IJ01 = JOURNEYS / "IJ01-modality-recurrence"
IJ02 = JOURNEYS / "IJ02-below-threshold"
CATALOG = ROOT / "harness" / "prompt-compilation" / "improvement-hypothesis-catalog.v1.json"


class ImprovementCompilerProgramDesignTests(unittest.TestCase):
    def test_architecture_reorders_ui_after_improvement_compiler(self) -> None:
        sprint = SPRINT.read_text(encoding="utf-8")
        self.assertIn("Sprint 3 — Improvement-Candidate Compiler", sprint)
        self.assertIn("Sprint 4 — Prompt Kit wiring + Compute Mode", sprint)
        self.assertIn("UI Compute Mode remains deferred", sprint)
        # UI must not be the immediate successor of Sprint 2.
        idx3 = sprint.index("Sprint 3 — Improvement-Candidate Compiler")
        idx4 = sprint.index("Sprint 4 — Prompt Kit wiring + Compute Mode")
        self.assertLess(idx3, idx4)

    def test_architecture_records_module_map_and_alternatives(self) -> None:
        text = ARCH.read_text(encoding="utf-8")
        for phrase in (
            "ImprovementCandidateCompiler",
            "reviewed_pr_only",
            "does **not** own lifecycle events",
            "Alternatives compared",
            "SUCCESS CALL STACK",
            "FAILURE CALL STACK",
            "auto_merge",
        ):
            self.assertIn(phrase, text)


class ImprovementCompilerCallStackTests(unittest.TestCase):
    def test_success_journey_emits_candidate_eval_and_pr_draft(self) -> None:
        finding = compiler.load_json(IJ01 / "finding.json")
        result = improvement.run_improvement_journey(finding)
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["stack"],
            [
                "normalize_finding",
                "recurrence_gate",
                "resolve_hypothesis",
                "compile_improvement_candidate",
                "evaluate_candidate_regressions",
                "build_pr_draft_package",
            ],
        )
        candidate = result["candidate"]
        self.assertEqual(candidate["failure_identity"], "parallel_dispatch.modality_weakened")
        self.assertEqual(candidate["promotion_authority"], "reviewed_pr_only")
        self.assertEqual(candidate["required_regressions"], ["TC06-parallelism-modality"])
        self.assertTrue(result["evaluation"]["ok"])
        draft = result["pr_draft"]
        self.assertFalse(draft["auto_merge"])
        self.assertFalse(draft["auto_mutate_source"])
        self.assertEqual(draft["operator_gate"], "human_review_required_before_git_apply")

    def test_failure_below_recurrence_threshold(self) -> None:
        finding = compiler.load_json(IJ02 / "finding.json")
        gate = improvement.recurrence_gate(finding)
        self.assertFalse(gate["admitted"])
        self.assertEqual(gate["reason"], "recurrence_threshold_not_met")
        with self.assertRaises(improvement.ImprovementCompilerError) as ctx:
            improvement.run_improvement_journey(finding)
        self.assertIn("recurrence_threshold_not_met", str(ctx.exception))

    def test_failure_missing_evidence_refs(self) -> None:
        finding = {
            "failure_identity": "parallel_dispatch.modality_weakened",
            "state": "confirmed_recurrence",
            "count": 3,
            "threshold": 2,
            "evidence_refs": [],
        }
        gate = improvement.recurrence_gate(finding)
        self.assertFalse(gate["admitted"])
        self.assertEqual(gate["reason"], "missing_evidence_refs")

    def test_failure_rejects_self_authorizing_promotion(self) -> None:
        finding = compiler.load_json(IJ01 / "finding.json")
        compiled = improvement.compile_candidate_from_finding(finding)
        bad = dict(compiled["candidate"])
        bad["promotion_authority"] = "auto_merge"
        with self.assertRaises(compiler.PromptCompilationError) as ctx_validate:
            compiler.validate_improvement_candidate(bad)
        self.assertIn("self-authorize", str(ctx_validate.exception))
        with self.assertRaises(improvement.ImprovementCompilerError) as ctx_draft:
            improvement.build_pr_draft_package(
                bad,
                {"ok": True, "regressions": []},
                fingerprint=compiled["fingerprint"],
            )
        self.assertIn("self-authorize", str(ctx_draft.exception))

    def test_failure_missing_regression_fixture(self) -> None:
        candidate = compiler.compile_improvement_candidate(
            failure_identity="unknown.failure",
            evidence_refs=["r1"],
            affected_authority="language-engine",
            rule="test",
            required_regressions=["TC-DOES-NOT-EXIST"],
            candidate_id="IC-missing-fixture",
        )
        with self.assertRaises(improvement.ImprovementCompilerError) as ctx:
            improvement.evaluate_candidate_regressions(candidate)
        self.assertIn("missing required regression fixture", str(ctx.exception))

    def test_hypothesis_catalog_is_deterministic(self) -> None:
        catalog = improvement.load_hypothesis_catalog(CATALOG)
        self.assertEqual(catalog["promotion_authority"], "reviewed_pr_only")
        hypo = improvement.resolve_hypothesis(
            "parallel_dispatch.modality_weakened",
            catalog=catalog,
        )
        self.assertEqual(hypo["required_regressions"], ["TC06-parallelism-modality"])

    def test_cli_success_and_gate_failure_exit_codes(self) -> None:
        self.assertEqual(
            improvement.main(
                [
                    "run-journey",
                    "--finding",
                    str(IJ01 / "finding.json"),
                    "--summary",
                ]
            ),
            0,
        )
        self.assertEqual(
            improvement.main(
                [
                    "recurrence-gate",
                    "--finding",
                    str(IJ02 / "finding.json"),
                    "--summary",
                ]
            ),
            2,
        )


if __name__ == "__main__":
    unittest.main()
