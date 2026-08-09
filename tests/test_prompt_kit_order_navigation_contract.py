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
        self.valid_prompts = [
            {"id": "P00", "seq": "00"},
            {"id": "P01", "seq": "01"},
            {"id": "P02", "seq": "02"},
        ]

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
        self.assertIn("canonical render path", expected["filter_persistent_navigation"])
        self.assertIn("40px", expected["mobile_touch_accessibility"])
        self.assertIn("unique P-number ID", expected["stable_prompt_identity"])
        self.assertIn("exactly matches", expected["canonical_site_parity"])

    def test_bad_static_sources_expose_order_and_navigation_gaps(self) -> None:
        report = validator.evaluate_source_payloads(
            self.contract,
            {"promoted_prompt_ids": ["P65", "P01"]},
            "return apply_display_order(strengthened_prompts, load_display_order_policy())",
            "window.promptSequenceValue=rank;render();",
            "appendSectionDivider(grid,group); page-jump min-height:40px",
            raw_prompts=self.valid_prompts,
        )
        self.assertEqual(report["implementation_status"], "needs-product-repair")
        rule_ids = {item["rule_id"] for item in report["findings"]}
        self.assertTrue(
            {"PKON001", "PKON002", "PKON003", "PKON004", "PKON005", "PKON006"}.issubset(rule_ids)
        )
        self.assertEqual(report["requirement_status"]["distributed_page_navigation"], "gap")
        self.assertEqual(report["navigation_interval"], 5)

    def test_marker_strings_outside_render_do_not_fake_filter_persistence(self) -> None:
        base = (
            "var PROMPT_NAVIGATION_INTERVAL=5;"
            "function appendDistributedPageNavigation(grid,visiblePromptIndex){"
            "var nav=document.createElement('nav');nav.className='distributed-page-navigation';"
            "var a=document.createElement('a');a.className='page-jump';a.href='#page-top';"
            "var b=document.createElement('a');b.className='page-jump';b.href='#page-bottom';}"
            "var visiblePromptIndex=0;appendDistributedPageNavigation(grid,visiblePromptIndex);"
            "function render(){var f=[];}"
            "var css='.distributed-page-navigation .page-jump{min-height:40px}';"
        )
        report = validator.evaluate_source_payloads(
            self.contract,
            {"promoted_prompt_ids": []},
            "def build():\n    return prompts",
            "function rankRecommendationOnly(){}",
            base,
            raw_prompts=self.valid_prompts,
        )
        self.assertIn("PKON005", {item["rule_id"] for item in report["findings"]})
        self.assertEqual(report["requirement_status"]["filter_persistent_navigation"], "gap")

    def test_unassociated_mobile_tokens_do_not_fake_accessibility(self) -> None:
        base = (
            "var PROMPT_NAVIGATION_INTERVAL=5;"
            "function appendDistributedPageNavigation(grid,visiblePromptIndex){return;}"
            "function render(){var visiblePromptIndex=0;"
            "appendDistributedPageNavigation(grid,visiblePromptIndex);}"
            "var unrelated='page-jump min-height:40px #page-top #page-bottom';"
        )
        report = validator.evaluate_source_payloads(
            self.contract,
            {"promoted_prompt_ids": []},
            "def build():\n    return prompts",
            "function rankRecommendationOnly(){}",
            base,
            raw_prompts=self.valid_prompts,
        )
        self.assertIn("PKON006", {item["rule_id"] for item in report["findings"]})
        self.assertEqual(report["requirement_status"]["mobile_touch_accessibility"], "gap")

    def test_prompt_identity_mismatch_is_reported(self) -> None:
        report = validator.evaluate_source_payloads(
            self.contract,
            {"promoted_prompt_ids": []},
            "def build():\n    return prompts",
            "function rankRecommendationOnly(){}",
            self._good_base_source(),
            raw_prompts=[{"id": "P01", "seq": "02"}, {"id": "P02", "seq": "02"}],
        )
        self.assertIn("PKON008", {item["rule_id"] for item in report["findings"]})
        self.assertEqual(report["requirement_status"]["stable_prompt_identity"], "gap")

    def test_stale_canonical_site_is_reported(self) -> None:
        report = validator.evaluate_source_payloads(
            self.contract,
            {"promoted_prompt_ids": []},
            "def build():\n    return prompts",
            "function rankRecommendationOnly(){}",
            self._good_base_source(),
            raw_prompts=self.valid_prompts,
            canonical_site_matches=False,
        )
        self.assertIn("PKON007", {item["rule_id"] for item in report["findings"]})
        self.assertEqual(report["requirement_status"]["canonical_site_parity"], "gap")

    def _good_base_source(self) -> str:
        return (
            "var PROMPT_NAVIGATION_INTERVAL=5;"
            "function appendDistributedPageNavigation(grid,visiblePromptIndex){"
            "var nav=document.createElement('nav');nav.className='distributed-page-navigation';"
            "var top=document.createElement('a');top.className='page-jump';top.href='#page-top';"
            "var bottom=document.createElement('a');bottom.className='page-jump';bottom.href='#page-bottom';}"
            "function render(){var visiblePromptIndex=0;"
            "appendDistributedPageNavigation(grid,visiblePromptIndex);}"
            "var css='.distributed-page-navigation .page-jump{min-height:40px}';"
        )

    def test_recommendation_only_p65_promotion_is_allowed(self) -> None:
        report = validator.evaluate_source_payloads(
            self.contract,
            {"promoted_prompt_ids": ["P65", "P01"]},
            "def build():\n    return prompts",
            "function rankRecommendationOnly(){return 65}",
            self._good_base_source(),
            raw_prompts=self.valid_prompts,
            canonical_site_matches=True,
        )
        self.assertNotIn("PKON003", {item["rule_id"] for item in report["findings"]})
        self.assertEqual(report["implementation_status"], "pass")

    def test_good_static_sources_satisfy_contract(self) -> None:
        report = validator.evaluate_source_payloads(
            self.contract,
            {"promoted_prompt_ids": ["P65"]},
            "def build():\n    return prompts",
            "function rankRecommendationOnly(){}",
            self._good_base_source(),
            raw_prompts=self.valid_prompts,
            canonical_site_matches=True,
        )
        self.assertEqual(report["implementation_status"], "pass")
        self.assertEqual(report["findings"], [])
        self.assertTrue(all(value == "pass" for value in report["requirement_status"].values()))

    def test_current_repository_matches_recorded_product_gap_until_product_lane_repairs_it(self) -> None:
        report = validator.evaluate_repository()
        self.assertEqual(self.contract["known_baseline"]["status"], "needs-product-repair")
        self.assertEqual(report["implementation_status"], "needs-product-repair")
        self.assertTrue(report["findings"])
        self.assertEqual(report["requirement_status"]["stable_prompt_identity"], "pass")
        self.assertEqual(report["requirement_status"]["canonical_site_parity"], "pass")


if __name__ == "__main__":
    unittest.main()
