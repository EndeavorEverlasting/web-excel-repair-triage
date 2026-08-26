from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_REGISTRY = REPO_ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TARGET_NAME = 'AFK Feedback-Driven Development Loop Executor'


class AfkFeedbackDevelopmentPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.full_list = build_prompt_kit_registry.load_prompt_kit_registry()
        cls.full = {p["id"]: p for p in cls.full_list}
        matches = [p for p in cls.full_list if p.get("name") == TARGET_NAME]
        if len(matches) != 1:
            raise AssertionError(f"expected one {TARGET_NAME!r}, found {len(matches)}")
        cls.target = matches[0]
        raw = json.loads(RAW_REGISTRY.read_text(encoding="utf-8"))["prompts"]
        raw_matches = [p for p in raw if p.get("name") == TARGET_NAME]
        if len(raw_matches) != 1:
            raise AssertionError(f"expected one raw {TARGET_NAME!r}, found {len(raw_matches)}")
        cls.raw = raw_matches[0]

    def test_helper_owns_identity_and_profile(self) -> None:
        self.assertEqual(self.target["id"], 'P115')
        self.assertEqual(self.target["seq"], self.target["id"][1:])
        self.assertEqual(self.target["copySheet"], f"{self.target['id']}_COPY_SAFE")
        self.assertEqual(self.target["profile"], "spec-architecture")
        self.assertEqual(self.target["class"], "HARNESS / AFK DEVELOPMENT")
        self.assertEqual(self.raw["id"], self.target["id"])

    def test_nonterminal_loop_requires_real_work(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "P07-STYLE NONTERMINAL WORK LOOP",
            "REFRESH -> INGEST SIGNALS -> SELECT SAFE HIGHEST-VALUE WORK -> EXECUTE -> VALIDATE -> INGEST NEW FEEDBACK -> CRITIQUE -> IMPROVE -> INTEGRATE -> REFRESH -> REPEAT",
            "A status-only pass is a failed pass when safe agent-capable work exists",
            "Every ACTIONABLE_REPAIR must become either a concrete repository mutation",
            "COERCE REAL WORK, NOT STATUS THEATER",
            "If a safe mutation is available",
            "An open PR, green CI, generated report",
        ):
            self.assertIn(phrase, content)

    def test_feedback_reaches_capable_workers_with_provenance(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "provider run/job/check ID and candidate SHA",
            "PR review thread/comment/path/line",
            "developers, scripts, agents, models, PRs",
            "exact target, owned surface, evidence, acceptance condition",
            "Do not force the operator to shuttle CI logs",
            "Deduplicate already-consumed signal identities",
        ):
            self.assertIn(phrase, content)

    def test_existing_owner_boundaries_are_reused_not_collapsed(self) -> None:
        content = self.target["copyContent"]
        expected = {
            "P07": "Repo Sprint Executor",
            "P32": "GNHF Validation and CI Repair",
            "P104": "Repository-Native Code Update Harness Builder",
            "P105": "Validated CI/CD Promotion Pipeline Builder",
            "P112": "AFK Deterministic Automated Test Harness Builder",
            "P113": "Risk-Driven Test Floor Evolution Executor",
        }
        for prompt_id, name in expected.items():
            self.assertEqual(self.full[prompt_id]["name"], name)
            self.assertIn(prompt_id, content)
            self.assertNotEqual(self.target["id"], prompt_id)
        self.assertIn("Use existing specialized owners rather than teaching this loop to impersonate every subsystem", content)

    def test_p112_p113_and_p105_feed_the_new_loop(self) -> None:
        for prompt_id in ("P112", "P113", "P105"):
            self.assertIn(self.target["id"], self.full[prompt_id]["nextStep"])
            self.assertIn(self.target["id"], self.full[prompt_id]["copyContent"])
        self.assertIn("This pipeline remains promotion-only", self.full["P105"]["copyContent"])
        self.assertIn("This prompt still owns test-floor bootstrap", self.full["P112"]["copyContent"])
        self.assertIn("This prompt owns test evolution", self.full["P113"]["copyContent"])

    def test_generated_site_contains_exact_prompt_and_parity(self) -> None:
        html = build_prompt_kit_registry.DEFAULT_OUTPUT.read_text(encoding="utf-8")
        self.assertEqual(html, build_prompt_kit_registry.render())
        self.assertIn(self.target["id"], html)
        self.assertIn(TARGET_NAME, html)


if __name__ == "__main__":
    unittest.main()
