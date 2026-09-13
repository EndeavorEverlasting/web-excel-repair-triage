from __future__ import annotations

import copy
import unittest

from scripts import build_prompt_kit_registry as registry
from scripts import prompt_kit_tutorial_coverage as coverage
from scripts import prompt_registry_ops


class PromptKitTutorialCoverageTests(unittest.TestCase):
    def test_every_canonical_prompt_has_complete_tutorial_wiring(self) -> None:
        report = coverage.audit()
        self.assertTrue(report["ready"], report)
        self.assertEqual(report["prompt_count"], report["route_covered_count"])
        self.assertEqual(report["prompt_count"], report["wired_count"])
        self.assertGreater(report["prompt_count"], 0)
        self.assertEqual(report["needs_wiring_count"], 0)
        self.assertEqual(report["needs_wiring_prompt_ids"], [])
        self.assertEqual(report["unknown_wired_prompt_ids"], [])
        self.assertEqual(report["route_errors"], [])

        routes = report["routes"]
        self.assertEqual(len(routes), report["prompt_count"])
        for route in routes:
            self.assertEqual(route["tutorial_route"][0], "Tutorial · Find My Prompt")
            self.assertEqual(route["tutorial_route"][1], route["classifier_section"])
            self.assertIn(route["prompt_id"], route["tutorial_route"][2])
            self.assertFalse(route["needs_wiring"])
            self.assertIn(
                route["wiring_status"],
                {"CURATED_WIRED", "CLASSIFIER_WIRED"},
            )

    def test_new_prompt_is_classifier_wired_immediately(self) -> None:
        policy = coverage._load_policy()
        prompt = {
            "id": "P999",
            "name": "Synthetic New Builder",
            "type": "BUILD",
        }
        route = coverage.coverage_for_prompt(prompt, policy)
        self.assertEqual(route["classifier_section"], "Build & Repair")
        self.assertEqual(route["wiring_status"], "CLASSIFIER_WIRED")
        self.assertFalse(route["needs_wiring"])
        self.assertEqual(route["wiring_source"], "classifier")
        self.assertFalse(route["curated"])
        self.assertEqual(
            route["tutorial_route"],
            [
                "Tutorial · Find My Prompt",
                "Build & Repair",
                "P999 — Synthetic New Builder",
            ],
        )

    def test_curated_prompt_keeps_classifier_route_and_deeper_anchor(self) -> None:
        prompts = {prompt["id"]: prompt for prompt in registry.load_prompt_kit_registry()}
        route = coverage.coverage_for_prompt(prompts["P65"])
        self.assertEqual(route["wiring_status"], "CURATED_WIRED")
        self.assertFalse(route["needs_wiring"])
        self.assertEqual(route["wiring_source"], "curated")
        self.assertTrue(route["curated"])
        self.assertEqual(route["tutorial_anchor"], "conversational-fallback")
        self.assertTrue(route["classifier_section"])

    def test_recently_added_p140_is_complete_without_manual_curated_move(self) -> None:
        prompts = {prompt["id"]: prompt for prompt in registry.load_prompt_kit_registry()}
        route = coverage.coverage_for_prompt(prompts["P140"])
        self.assertEqual(route["wiring_status"], "CLASSIFIER_WIRED")
        self.assertFalse(route["needs_wiring"])
        self.assertEqual(route["wiring_source"], "classifier")
        self.assertIn("P140", route["tutorial_route"][2])

    def test_curated_status_fails_closed_when_tutorial_anchor_disappears(self) -> None:
        policy = copy.deepcopy(coverage._load_policy())
        policy["wired_prompts"][0]["tutorial_anchor"] = "missing-tutorial-anchor"
        tutorial_path = coverage.REPO_ROOT / policy["tutorial_document"]
        with self.assertRaisesRegex(SystemExit, "missing-tutorial-anchor"):
            coverage._validate_tutorial_anchors(
                policy,
                tutorial_path.read_text(encoding="utf-8"),
            )

    def test_registry_helper_receipt_proves_tutorial_wiring(self) -> None:
        receipt = prompt_registry_ops._tutorial_coverage_receipt("P140")
        self.assertEqual(receipt["prompt_id"], "P140")
        self.assertEqual(receipt["wiring_status"], "CLASSIFIER_WIRED")
        self.assertFalse(receipt["needs_wiring"])
        self.assertTrue(receipt["coverage_ready"])


if __name__ == "__main__":
    unittest.main()
