from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from scripts import build_prompt_kit_registry
from scripts import prompt_registry_ops

ROOT = Path(__file__).resolve().parents[1]
STRENGTHENINGS = ROOT / "registry" / "prompts" / "prompt-strengthenings.v1.json"
TUTORIAL_FRESHNESS = ROOT / "registry" / "prompts" / "tutorial-freshness.v1.json"
TUTORIAL = ROOT / "docs" / "PROMPT_FINDER_QUESTIONNAIRE_TUTORIAL.md"


class LocalFirstPromotionAndTutorialFreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prompts = {
            prompt["id"]: prompt for prompt in build_prompt_kit_registry.load_prompt_registry()
        }
        cls.strengthenings = json.loads(STRENGTHENINGS.read_text(encoding="utf-8"))
        cls.tutorial_freshness = json.loads(TUTORIAL_FRESHNESS.read_text(encoding="utf-8"))
        cls.tutorial = TUTORIAL.read_text(encoding="utf-8")

    def test_p105_prefers_local_first_provider_minimal_execution(self) -> None:
        prompt = self.prompts["P105"]
        content = prompt["copyContent"]
        for phrase in (
            "LOCAL-FIRST / PROVIDER-MINIMAL CONTROL PLANE",
            "LOCAL_ONLY",
            "GIT_REMOTE_MINIMAL",
            "PROVIDER_GOVERNED",
            "Prefer plain Git transport",
            "Use the provider API only for facts Git cannot prove",
            "GitHub Actions remains a thin adapter",
            "PROVIDER REQUEST BUDGET / RATE-LIMIT ECONOMY",
            "event-driven wakeups over status polling",
            "Retry-After",
            "bounded exponential backoff with jitter",
            "preserve the locally complete candidate receipt",
            "without rerunning unchanged local work",
            "PORTABLE CORE / THIN ADAPTER PROOF",
            "same canonical repo-owned commands",
        ):
            self.assertIn(phrase, content)
        for keyword in (
            "local-first CI/CD",
            "provider-minimal promotion",
            "provider request budget",
            "thin CI adapter",
        ):
            self.assertIn(keyword, prompt["keywords"])
        self.assertEqual(
            prompt["tutorialFreshness"]["disposition"], "UPDATE_EXISTING_TUTORIAL"
        )

    def test_p79_makes_tutorial_freshness_part_of_prompt_contribution(self) -> None:
        prompt = self.prompts["P79"]
        content = prompt["copyContent"]
        for phrase in (
            "PROMPT -> TUTORIAL FRESHNESS CONTRACT",
            "Every ADD must update tutorial coverage",
            "REFERENCE_ONLY_WITH_REASON",
            "canonical prompt-add helper must fail closed",
            "mutation/rollback boundary must include the tutorial freshness ledger",
            "Recycle work",
            "Raw ordinary prompt_usage",
            "privacy-bounded operant_friction",
            "P64 Repository Tutorial Portfolio Ranker",
            "normal repository behavior as reusable tutorial evidence",
        ):
            self.assertIn(phrase, content)
        self.assertIn("tutorial freshness", prompt["keywords"])

    def test_p64_consumes_lifecycle_and_privacy_bounded_refresh_signals(self) -> None:
        prompt = self.prompts["P64"]
        content = prompt["copyContent"]
        for phrase in (
            "TUTORIAL FRESHNESS / RECYCLING LOOP",
            "prompt ADD or material STRENGTHEN",
            "REFERENCE_ONLY_WITH_REASON",
            "raw ordinary prompt_usage remains local/information-only",
            "privacy-bounded operant_friction",
            "Recycle proven work instead of re-performing discovery",
            "current commits, tests, launchers, help text, and support evidence",
        ):
            self.assertIn(phrase, content)
        self.assertIn("tutorial freshness ledger", prompt["keywords"])

    def test_strengthening_registry_requires_tutorial_disposition_for_each_target(self) -> None:
        self.assertEqual(
            self.strengthenings["schema_version"], "prompt-registry-strengthenings/v1"
        )
        records = self.strengthenings["strengthenings"]
        self.assertEqual({record["id"] for record in records}, {"P64", "P79", "P105"})
        for record in records:
            tutorial = record["tutorial"]
            self.assertIn(
                tutorial["disposition"],
                {
                    "UPDATE_EXISTING_TUTORIAL",
                    "ADD_TUTORIAL",
                    "REFERENCE_ONLY_WITH_REASON",
                },
            )
            self.assertTrue(tutorial["reason"])
            for relative in tutorial["paths"]:
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_prompt_add_helper_fails_closed_without_tutorial_plan_for_real_write(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            prompt_registry_ops._validate_tutorial_plan({"name": "Example"}, require=True)
        self.assertIn("requires draft.tutorial", str(caught.exception))

    def test_prompt_add_helper_accepts_current_tutorial_coverage(self) -> None:
        plan = prompt_registry_ops._validate_tutorial_plan(
            {
                "name": "P105",
                "tutorial": {
                    "disposition": "UPDATE_EXISTING_TUTORIAL",
                    "tutorial_paths": ["docs/PROMPT_FINDER_QUESTIONNAIRE_TUTORIAL.md"],
                    "reason": "Focused unit proof of the coverage gate.",
                },
            },
            require=True,
        )
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan["coverage_paths"], ["docs/PROMPT_FINDER_QUESTIONNAIRE_TUTORIAL.md"])

    def test_prompt_add_helper_accepts_reference_only_without_tutorial_paths(self) -> None:
        plan = prompt_registry_ops._validate_tutorial_plan(
            {
                "name": "Reference-only example",
                "tutorial": {
                    "disposition": "REFERENCE_ONLY_WITH_REASON",
                    "tutorial_paths": [],
                    "reason": "Existing reference material already owns the operator explanation.",
                },
            },
            require=True,
        )
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan["tutorial_paths"], [])
        self.assertEqual(plan["coverage_paths"], [])

    def test_tutorial_freshness_ledger_requires_policy_identity(self) -> None:
        invalid = dict(self.tutorial_freshness)
        invalid.pop("policy_id", None)
        with mock.patch.object(prompt_registry_ops.registry, "_load_json", return_value=invalid):
            with self.assertRaisesRegex(SystemExit, "policy_id"):
                prompt_registry_ops._load_tutorial_freshness()

    def test_tutorial_freshness_ledger_reuses_existing_privacy_contract(self) -> None:
        ledger = self.tutorial_freshness
        self.assertEqual(ledger["schema_version"], "prompt-tutorial-freshness/v1")
        self.assertEqual(ledger["tutorial_owner_prompt"], "P64")
        self.assertEqual(ledger["contribution_owner_prompt"], "P79")
        self.assertFalse(ledger["privacy"]["raw_prompt_usage_is_durable_input"])
        self.assertFalse(ledger["privacy"]["prompt_body_is_durable_input"])
        self.assertTrue(
            ledger["privacy"]["accepted_operant_friction_receipts_may_inform_tutorial_priority"]
        )
        self.assertEqual(
            ledger["privacy"]["source_contract"],
            "harness/contracts/prompt-kit-feedback-afk-routing.v1.json",
        )
        self.assertEqual({record["prompt_id"] for record in ledger["records"]}, {"P64", "P79", "P105"})

    def test_tutorial_documents_local_first_and_contribution_freshness(self) -> None:
        for phrase in (
            "## Local-first CI/CD with P105",
            "GIT_REMOTE_MINIMAL",
            "PROVIDER_ONLY",
            "Provider calls are a budgeted dependency",
            "## Keeping tutorials current as prompts evolve",
            "tutorial-freshness.v1.json",
            "Before the canonical `prompt_registry_ops.py add` command may write a new identity",
            "At least one declared tutorial path must already mention the new prompt's **name**",
            "raw ordinary usage local and information-only",
            "Recycle proven work",
        ):
            self.assertIn(phrase, self.tutorial)


if __name__ == "__main__":
    unittest.main()
