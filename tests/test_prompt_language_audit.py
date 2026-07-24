from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import evaluate_prompt_language


class PromptLanguageAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = evaluate_prompt_language.load_policy()
        fixture_path = (
            ROOT
            / "harness"
            / "evals"
            / "fixtures"
            / "prompt-language-cases.v1.json"
        )
        self.fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))["cases"]

    def test_fixture_rules_detect_expected_language_defects(self) -> None:
        for case in self.fixtures:
            with self.subTest(case=case["id"]):
                result = evaluate_prompt_language.evaluate_prompt(
                    case["raw_prompt"], case["effective_prompt"], self.policy
                )
                actual = {finding["rule_id"] for finding in result["findings"]}
                self.assertEqual(actual, set(case["expected_rule_ids"]))

    def test_combined_registry_is_exhaustively_covered_without_errors(self) -> None:
        report = evaluate_prompt_language.evaluate_registry(policy=self.policy)
        self.assertTrue(report["coverage_complete"])
        self.assertEqual(report["prompt_count"], report["disposition_count"])
        self.assertEqual(report["prompt_count"], report["effective_prompt_count"])
        self.assertEqual(report["error_count"], 0)
        self.assertIn("P62", {item["prompt_id"] for item in report["prompts"]})

    def test_strict_mode_fails_warning_only_registry(self) -> None:
        case = next(item for item in self.fixtures if item["id"] == "lazy-pr-only")
        report = evaluate_prompt_language.evaluate_registry(
            [case["raw_prompt"]],
            [case["effective_prompt"]],
            policy=self.policy,
            strict=True,
        )
        self.assertEqual(report["warning_count"], 1)
        self.assertEqual(report["verdict"], "fail")


if __name__ == "__main__":
    unittest.main()
