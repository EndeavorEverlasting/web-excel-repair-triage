from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_REGISTRY = REPO_ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TARGET_NAME = "Risk-Driven Test Floor Evolution Executor"


class TestFloorEvolutionPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.full = build_prompt_kit_registry.load_prompt_kit_registry()
        cls.by_id = {prompt["id"]: prompt for prompt in cls.full}
        matches = [prompt for prompt in cls.full if prompt.get("name") == TARGET_NAME]
        if len(matches) != 1:
            raise AssertionError(f"expected one {TARGET_NAME!r}, found {len(matches)}")
        cls.target = matches[0]
        raw_prompts = json.loads(RAW_REGISTRY.read_text(encoding="utf-8"))["prompts"]
        raw_matches = [prompt for prompt in raw_prompts if prompt.get("name") == TARGET_NAME]
        if len(raw_matches) != 1:
            raise AssertionError(f"expected one raw {TARGET_NAME!r}, found {len(raw_matches)}")
        cls.raw = raw_matches[0]
        cls.p112 = cls.by_id["P112"]

    def test_helper_owned_identity_and_profile(self) -> None:
        self.assertRegex(self.target["id"], r"^P\d+$")
        self.assertEqual(self.target["seq"], self.target["id"][1:])
        self.assertEqual(self.target["copySheet"], f"{self.target['id']}_COPY_SAFE")
        self.assertEqual(self.target["profile"], "spec-architecture")
        self.assertEqual(self.target["class"], "HARNESS / TEST EVOLUTION")
        self.assertEqual(self.raw["id"], self.target["id"])

    def test_trigger_is_existing_green_floor_not_bootstrap(self) -> None:
        trigger = self.target["useWhen"]
        self.assertIn("already has a canonical automated-test floor", trigger)
        self.assertIn("proactively and pragmatically deepen that floor", trigger)
        content = self.target["copyContent"]
        self.assertIn("if the repository does not yet have a trustworthy floor, use P112 first", content)
        self.assertIn("post-bootstrap test evolution", content)

    def test_risk_ranked_pragmatic_selection_beats_coverage_theater(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "BUILD A TEST-RISK LEDGER, NOT A COVERAGE WISHLIST",
            "percentage is evidence, not the objective",
            "Keep at most three active candidates",
            "cheapest maintainable test level",
            "Do not add trivial assertions merely to raise a number",
        ):
            self.assertIn(phrase, content)

    def test_iterative_prototype_and_sensitivity_proof(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "PROTOTYPE THE PROTECTION AND PROVE SENSITIVITY",
            "REFRESH -> SELECT RISK -> PROTOTYPE TEST/ORACLE -> RUN -> FALSIFY",
            "replay of a known historical regression",
            "smallest isolated mutation/controlled defect",
            "Never leave the deliberate defect in the durable branch",
            "SECOND-PASS FALSIFICATION",
            "BOUNDED FIXED POINT",
        ):
            self.assertIn(phrase, content)

    def test_stale_test_cannot_override_product_truth(self) -> None:
        content = self.target["copyContent"]
        self.assertIn("PRESERVE PRODUCT TRUTH; DO NOT MAKE TESTS THE SPEC BY ACCIDENT", content)
        self.assertIn("If the test is stale, repair the test instead of regressing correct product behavior", content)
        self.assertIn("Never weaken an assertion merely to make CI green", content)

    def test_skip_determinism_cost_and_provider_contracts(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "Unknown or newly introduced skips must not silently become green",
            "KEEP THE FLOOR DETERMINISTIC AND FAIL-CLOSED",
            "BE PRAGMATIC ABOUT SUITE COST",
            "REAL PROVIDER PROOF",
            "exact candidate revision",
            "PROVIDER-RUNTIME BLOCKED",
        ):
            self.assertIn(phrase, content)

    def test_neighbor_owners_remain_distinct_and_routed(self) -> None:
        self.assertEqual(self.by_id["P112"]["name"], "AFK Deterministic Automated Test Harness Builder")
        self.assertEqual(self.by_id["P32"]["name"], "GNHF Validation and CI Repair")
        self.assertEqual(self.by_id["P33"]["name"], "GNHF Harness Hardening")
        self.assertEqual(self.by_id["P67"]["name"], "Repository Eval Framework Builder")
        self.assertEqual(self.by_id["P105"]["name"], "Validated CI/CD Promotion Pipeline Builder")
        for owner_id in ("P112", "P32", "P33", "P67", "P105"):
            self.assertNotEqual(self.target["id"], owner_id)
        self.assertIn(self.target["id"], self.p112["nextStep"])
        self.assertIn(self.target["id"], self.p112["copyContent"])
        self.assertIn("P33: harden offline harness contracts", self.target["copyContent"])
        self.assertIn("P67: build AI/agent task-quality eval systems", self.target["copyContent"])

    def test_generated_site_contains_exact_prompt_identity(self) -> None:
        html = build_prompt_kit_registry.DEFAULT_OUTPUT.read_text(encoding="utf-8")
        self.assertEqual(html, build_prompt_kit_registry.render())
        self.assertIn(self.target["id"], html)
        self.assertIn(TARGET_NAME, html)

    def test_product_defect_feedback_routes_to_afk_development(self) -> None:
        matches = [p for p in self.full if p.get("name") == 'AFK Feedback-Driven Development Loop Executor']
        self.assertEqual(len(matches), 1)
        owner = matches[0]
        self.assertEqual(owner["id"], 'P115')
        self.assertIn(owner["id"], self.target["nextStep"])
        self.assertIn(owner["id"], self.target["copyContent"])
        content = self.target["copyContent"]
        self.assertIn("PRODUCT DEFECTS MUST ESCAPE THE TEST LANE", content)
        self.assertIn("Preserve the regression, bind the exact failure evidence", content)
        self.assertIn("route the bounded product repair through P115", content)
        self.assertIn("After the repair, rerun the regression and provider gate", content)
        self.assertIn("ingest the new feedback, and continue the next justified pass", content)
        self.assertIn("This prompt owns test evolution; it does not gain arbitrary product ownership", content)

if __name__ == "__main__":
    unittest.main()
