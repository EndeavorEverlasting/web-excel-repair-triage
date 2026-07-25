from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry as registry
import evaluate_prompt_efficiency as cli
import prompt_efficiency_eval as efficiency


class PromptEfficiencyEvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = efficiency.load_policy()
        cls.fixtures = efficiency.load_fixtures()["cases"]
        cls.prompt_cases = {
            case["id"]: case["prompt"]
            for case in cls.fixtures
            if case["target_kind"] == "prompt-registry"
        }

    def test_policy_declares_code_llm_human_and_user_lanes(self) -> None:
        self.assertEqual(
            set(self.policy["evaluation_lanes"]),
            {"code_based", "llm_judge", "human", "user"},
        )
        self.assertTrue(
            self.policy["evaluation_lanes"]["llm_judge"]["required_for_strict_gate"]
        )
        self.assertEqual(
            set(self.policy["rubrics"]),
            {"prompt-registry", "model-response"},
        )

    def test_compact_explicit_fixture_is_code_safe(self) -> None:
        result = efficiency.evaluate_prompt_code(
            self.prompt_cases["compact-explicit-prompt"], self.policy
        )
        self.assertTrue(result["code_safe"])
        self.assertGreaterEqual(
            result["metrics"]["weak_model_signal_group_count"],
            self.policy["deterministic_thresholds"]["minimum_weak_model_signal_groups"],
        )

    def test_duplicate_fixture_produces_stable_rule(self) -> None:
        result = efficiency.evaluate_prompt_code(
            self.prompt_cases["duplicate-bloated-prompt"], self.policy
        )
        self.assertIn(
            "duplicate-lines",
            {item["rule_id"] for item in result["findings"]},
        )

    def test_judge_packet_is_one_case_at_a_time_contract(self) -> None:
        prompt = self.prompt_cases["compact-explicit-prompt"]
        cases = efficiency.build_prompt_cases([prompt], self.policy)
        packet = efficiency.build_judge_packet_set(cases, self.policy)
        self.assertEqual(packet["case_count"], 1)
        self.assertEqual(packet["passage_mode"], "one case at a time in listed order")
        self.assertIn("copyContent", packet["cases"][0]["target"])
        self.assertEqual(
            packet["result_schema_version"],
            "prompt-efficiency-judge-result/v1",
        )

    def test_valid_judge_result_can_pass_prompt_case(self) -> None:
        prompt = self.prompt_cases["compact-explicit-prompt"]
        cases = efficiency.build_prompt_cases([prompt], self.policy)
        rubric = self.policy["rubrics"]["prompt-registry"]
        result = {
            "schema_version": "prompt-efficiency-judge-result/v1",
            "case_id": cases[0]["case_id"],
            "target_kind": "prompt-registry",
            "judge_id": "judge-a",
            "rubric_id": rubric["rubric_id"],
            "verdict": "pass",
            "scores": {dimension: 4 for dimension in rubric["dimensions"]},
            "findings": [],
        }
        aggregate = efficiency.validate_and_aggregate_judge_results(
            [result], cases, self.policy
        )
        self.assertTrue(aggregate["coverage_complete"])
        self.assertTrue(aggregate["all_cases_pass"])

    def test_missing_judge_evidence_fails_strict_gate(self) -> None:
        prompt = self.prompt_cases["compact-explicit-prompt"]
        cases = efficiency.build_prompt_cases([prompt], self.policy)
        report = efficiency.build_report(cases, self.policy, strict=True)
        self.assertFalse(report["strict_ready"])
        self.assertFalse(report["judge"]["coverage_complete"])

    def test_malformed_judge_dimensions_fail_closed(self) -> None:
        prompt = self.prompt_cases["compact-explicit-prompt"]
        cases = efficiency.build_prompt_cases([prompt], self.policy)
        result = {
            "schema_version": "prompt-efficiency-judge-result/v1",
            "case_id": cases[0]["case_id"],
            "target_kind": "prompt-registry",
            "judge_id": "judge-a",
            "rubric_id": cases[0]["rubric_id"],
            "verdict": "pass",
            "scores": {"wrong": 4},
            "findings": [],
        }
        with self.assertRaises(efficiency.PromptEfficiencyEvalError):
            efficiency.validate_and_aggregate_judge_results(
                [result], cases, self.policy
            )

    def test_model_response_cases_enable_llm_on_llm_evaluation(self) -> None:
        prompt = self.prompt_cases["compact-explicit-prompt"]
        candidate = next(
            case["candidate"]
            for case in self.fixtures
            if case["id"] == "response-with-canary"
        )
        cases = efficiency.build_response_cases(
            [candidate], [prompt], self.policy
        )
        self.assertEqual(cases[0]["target_kind"], "model-response")
        self.assertIn("candidate_response", cases[0]["target"])
        self.assertTrue(cases[0]["code_evaluation"]["code_safe"])

    def test_empty_model_response_is_code_error(self) -> None:
        candidate = next(
            case["candidate"]
            for case in self.fixtures
            if case["id"] == "empty-response"
        )
        result = efficiency.evaluate_response_code(candidate, self.policy)
        self.assertFalse(result["code_safe"])
        self.assertIn(
            "empty-model-response",
            {item["rule_id"] for item in result["findings"]},
        )

    def test_cli_emits_report_and_packets_without_judge_claim(self) -> None:
        prompt = self.prompt_cases["compact-explicit-prompt"]
        with mock.patch.object(
            registry, "load_prompt_registry", return_value=[prompt]
        ):
            with tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp) / "report.json"
                packets = Path(tmp) / "packets.json"
                code = cli.main([
                    "--output", str(output),
                    "--emit-judge-packets", str(packets),
                    "--summary",
                ])
                self.assertEqual(code, 0)
                report = json.loads(output.read_text(encoding="utf-8"))
                self.assertFalse(report["judge"]["provided"])
                self.assertFalse(report["strict_ready"])
                self.assertEqual(
                    json.loads(packets.read_text(encoding="utf-8"))["case_count"],
                    1,
                )

    def test_repository_output_outside_outputs_is_rejected(self) -> None:
        with self.assertRaises(efficiency.PromptEfficiencyEvalError):
            efficiency.validate_output_path(ROOT / "docs" / "prompts.json")
        allowed = efficiency.validate_output_path(
            ROOT / "Outputs" / "prompt-efficiency-eval.json"
        )
        self.assertEqual(
            allowed,
            (ROOT / "Outputs" / "prompt-efficiency-eval.json").resolve(),
        )

    def test_protected_output_roots_are_rejected(self) -> None:
        for protected in efficiency.PROTECTED_OUTPUT_ROOTS:
            with self.assertRaises(efficiency.PromptEfficiencyEvalError):
                efficiency.validate_output_path(protected / "forbidden.json")


if __name__ == "__main__":
    unittest.main()
