from __future__ import annotations

import copy
import unittest

from scripts import build_prompt_kit_registry as registry
from scripts import prompt_kit_tutorial_coverage as coverage


class PromptKitTutorialCoverageTests(unittest.TestCase):
    def test_every_canonical_prompt_has_a_tutorial_route(self) -> None:
        report = coverage.audit()
        self.assertTrue(report["ready"], report)
        self.assertEqual(report["prompt_count"], report["route_covered_count"])
        self.assertGreater(report["prompt_count"], 0)
        self.assertEqual(report["unknown_wired_prompt_ids"], [])
        self.assertEqual(report["route_errors"], [])

        routes = report["routes"]
        self.assertEqual(len(routes), report["prompt_count"])
        for route in routes:
            self.assertEqual(route["tutorial_route"][0], "Tutorial · Find My Prompt")
            self.assertEqual(route["tutorial_route"][1], route["classifier_section"])
            self.assertIn(route["prompt_id"], route["tutorial_route"][2])
            self.assertIn(
                route["wiring_status"],
                {"WIRED", "CLASSIFIER_FALLBACK_NEEDS_WIRING"},
            )

    def test_unwired_new_prompt_is_marked_immediately(self) -> None:
        policy = coverage._load_policy()
        prompt = {
            "id": "P999",
            "name": "Synthetic New Builder",
            "type": "BUILD",
        }
        route = coverage.coverage_for_prompt(prompt, policy)
        self.assertEqual(route["classifier_section"], "Build & Repair")
        self.assertEqual(route["wiring_status"], "CLASSIFIER_FALLBACK_NEEDS_WIRING")
        self.assertTrue(route["needs_wiring"])
        self.assertEqual(
            route["tutorial_route"],
            [
                "Tutorial · Find My Prompt",
                "Build & Repair",
                "P999 — Synthetic New Builder",
            ],
        )

    def test_curated_prompt_is_wired_but_keeps_classifier_route(self) -> None:
        prompts = {prompt["id"]: prompt for prompt in registry.load_prompt_kit_registry()}
        route = coverage.coverage_for_prompt(prompts["P65"])
        self.assertEqual(route["wiring_status"], "WIRED")
        self.assertFalse(route["needs_wiring"])
        self.assertEqual(route["wiring_source"], "explicit")
        self.assertEqual(route["tutorial_anchor"], "conversational-fallback")
        self.assertTrue(route["classifier_section"])

    def test_wired_status_fails_closed_when_tutorial_anchor_disappears(self) -> None:
        policy = copy.deepcopy(coverage._load_policy())
        policy["wired_prompts"][0]["tutorial_anchor"] = "missing-tutorial-anchor"
        tutorial_path = coverage.REPO_ROOT / policy["tutorial_document"]
        with self.assertRaisesRegex(SystemExit, "missing-tutorial-anchor"):
            coverage._validate_tutorial_anchors(
                policy,
                tutorial_path.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
