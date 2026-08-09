from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_prompt_kit_order_navigation as validator


class PromptKitOrderNavigationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(validator.CONTRACT.read_text(encoding="utf-8"))

    def test_contract_requires_chronological_default_and_five_prompt_navigation(self) -> None:
        payload = validator.validate_contract(self.contract)
        self.assertEqual(payload["navigation_interval"], 5)
        self.assertEqual(
            {item["id"] for item in payload["requirements"]},
            validator.REQUIRED_REQUIREMENT_IDS,
        )
        expected = {item["id"]: item["expected"] for item in payload["requirements"]}
        self.assertIn("ascending numeric sequence", expected["default_sequence_ascending"])
        self.assertIn("five visible prompt cards", expected["distributed_page_navigation"])
        self.assertIn("after every render", expected["filter_persistent_navigation"])
        self.assertIn("40px", expected["mobile_touch_accessibility"])

    def test_bad_static_sources_expose_order_and_navigation_gaps(self) -> None:
        report = validator.evaluate_source_payloads(
            self.contract,
            {"promoted_prompt_ids": ["P65", "P01"]},
            "return apply_display_order(strengthened_prompts, load_display_order_policy())",
            "window.promptSequenceValue=rank;render();",
            "appendSectionDivider(grid,group); page-jump min-height:40px",
        )
        self.assertEqual(report["implementation_status"], "needs-product-repair")
        rule_ids = {item["rule_id"] for item in report["findings"]}
        self.assertTrue({"PKON001", "PKON002", "PKON004", "PKON005"}.issubset(rule_ids))
        self.assertEqual(report["requirement_status"]["distributed_page_navigation"], "gap")
        self.assertEqual(report["navigation_interval"], 5)

    def test_good_static_sources_satisfy_contract(self) -> None:
        report = validator.evaluate_source_payloads(
            self.contract,
            {"promoted_prompt_ids": []},
            "def build():\n    return prompts",
            "function rankRecommendationOnly(){}",
            (
                "var PROMPT_NAVIGATION_INTERVAL=5; "
                "function appendDistributedPageNavigation(){} "
                "var visiblePromptIndex=0; "
                "page-jump min-height:40px"
            ),
        )
        self.assertEqual(report["implementation_status"], "pass")
        self.assertEqual(report["findings"], [])
        self.assertTrue(all(value == "pass" for value in report["requirement_status"].values()))

    def test_current_repository_matches_recorded_product_gap_until_product_lane_repairs_it(self) -> None:
        report = validator.evaluate_repository()
        self.assertEqual(self.contract["known_baseline"]["status"], "needs-product-repair")
        self.assertEqual(report["implementation_status"], "needs-product-repair")
        self.assertTrue(report["findings"])


if __name__ == "__main__":
    unittest.main()
