from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_REGISTRY = REPO_ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TARGET_NAME = "AFK Deterministic Automated Test Harness Builder"


class AfkDeterministicTestingPromptTests(unittest.TestCase):
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

    def test_helper_owned_identity_and_profile(self) -> None:
        self.assertRegex(self.target["id"], r"^P\d+$")
        self.assertEqual(self.target["seq"], self.target["id"][1:])
        self.assertEqual(self.target["copySheet"], f"{self.target['id']}_COPY_SAFE")
        self.assertEqual(self.target["profile"], "spec-architecture")
        self.assertEqual(self.target["class"], "HARNESS / AUTOMATED TESTING")
        self.assertEqual(self.raw["id"], self.target["id"])
        self.assertEqual(self.raw["copySheet"], self.target["copySheet"])

    def test_low_context_repo_first_entry(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "LOW-CONTEXT, REPO-FIRST ENTRY",
            "Detect the project's language/framework/test tooling",
            "Do not ask the user to choose Jest vs Pytest vs Go test",
            "genuinely user-only preference",
        ):
            self.assertIn(phrase, content)

    def test_iterative_prototype_and_falsification_loop(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "ITERATIVE PROTOTYPING LOOP",
            "BASELINE -> PROTOTYPE -> RUN -> INJECT OR SELECT A REPRESENTATIVE FAILURE",
            "CRITIQUE -> REVISE",
            "bounded fixed point",
            "negative canary",
            "SECOND PASS",
        ):
            self.assertIn(phrase, content)

    def test_deterministic_test_floor_and_false_green_guards(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "Fail closed on false-green states",
            "discovers zero required tests",
            "random seeds",
            "clocks, timezone/locale",
            "external-network tests",
            "Do not add retries that turn assertion failures into green",
        ):
            self.assertIn(phrase, content)

    def test_github_actions_afk_contract(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "CANONICAL COMMAND FIRST, CI YAML SECOND",
            "`push` and `pull_request` triggers",
            "`schedule`/cron trigger only when unattended periodic revalidation has real value",
            "best-effort",
            "least-privilege workflow permissions",
            "exact candidate revision",
        ):
            self.assertIn(phrase, content)
        self.assertIn("GitHub Actions should orchestrate those commands", content)

    def test_provider_runtime_requires_real_positive_and_negative_proof(self) -> None:
        content = self.target["copyContent"]
        self.assertIn("Trigger the actual GitHub Actions workflow", content)
        self.assertIn("observe the target gate fail for the right reason", content)
        self.assertIn("observe the exact final head pass", content)
        self.assertIn("PROVIDER-RUNTIME BLOCKED", content)
        self.assertIn("Do not call test automation complete merely because a workflow file exists", content)

    def test_neighbor_owners_remain_distinct(self) -> None:
        self.assertEqual(self.by_id["P51"]["name"], "Zero-Token Local Test Planner")
        self.assertEqual(self.by_id["P32"]["name"], "GNHF Validation and CI Repair")
        self.assertEqual(self.by_id["P105"]["name"], "Validated CI/CD Promotion Pipeline Builder")
        self.assertNotEqual(self.target["id"], "P51")
        self.assertNotEqual(self.target["id"], "P32")
        self.assertNotEqual(self.target["id"], "P105")
        self.assertIn("P105 owns validated promotion after that floor exists", self.target["copyContent"])
        self.assertIn("Route a failing established CI lane to P32", self.target["nextStep"])
        evolution = [
            prompt for prompt in self.full
            if prompt.get("name") == "Risk-Driven Test Floor Evolution Executor"
        ]
        self.assertEqual(len(evolution), 1)
        self.assertIn(evolution[0]["id"], self.target["nextStep"])
        self.assertIn(evolution[0]["id"], self.target["copyContent"])

    def test_generated_site_contains_exact_prompt_identity(self) -> None:
        html = build_prompt_kit_registry.DEFAULT_OUTPUT.read_text(encoding="utf-8")
        self.assertIn(self.target["id"], html)
        self.assertIn(TARGET_NAME, html)


if __name__ == "__main__":
    unittest.main()
