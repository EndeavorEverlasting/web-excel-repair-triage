from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_REGISTRY = REPO_ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TEST_FLOOR = REPO_ROOT / "harness" / "test-floor.v1.json"
TARGET_NAME = "Conversation Context Canary & Handoff Guard"
TEST_PATH = "tests/test_conversation_context_canary_prompt.py"


class ConversationContextCanaryPromptTests(unittest.TestCase):
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

    def test_helper_owns_identity_and_profile(self) -> None:
        self.assertRegex(self.target["id"], r"^P\d+$")
        self.assertEqual(self.target["seq"], self.target["id"][1:])
        self.assertEqual(self.target["copySheet"], f"{self.target['id']}_COPY_SAFE")
        self.assertEqual(self.target["profile"], "spec-architecture")
        self.assertEqual(self.target["class"], "CONTEXT / CONTINUITY")
        self.assertEqual(self.raw["id"], self.target["id"])

    def test_canary_requires_small_computer_profile_signal_every_response(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "MANDATORY FIRST LINE",
            "Before every response, emit one compact first line",
            "CANARY | PROFILE=<canonical computer profile>",
            "Do not expand the normal Canary into scope narration",
            "Keep the normal Canary to one line",
        ):
            self.assertIn(phrase, content)

    def test_unknown_profile_fails_closed_and_reanchors_from_evidence(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "CANARY | PROFILE=UNKNOWN",
            "Never invent a machine, profile, path, repo, branch, or lane",
            "RE-ANCHOR ONCE",
            "Do not ask the operator to repeat recoverable context",
        ):
            self.assertIn(phrase, content)

    def test_canary_is_signal_not_fake_context_telemetry(self) -> None:
        content = self.target["copyContent"]
        self.assertIn("CANARY IS A SENSOR, NOT PROOF", content)
        self.assertIn("not mathematical proof that the context window is exhausted", content)
        self.assertIn("Do not claim a token count, context percentage, or remaining-window estimate", content)
        self.assertIn("Do not treat harmless wording changes as drift", content)

    def test_repeated_drift_crosses_to_evidence_bearing_handoff(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "HANDOFF ON REPEATED OR UNRECOVERABLE DRIFT",
            "fails again after a re-anchor",
            "current mission and forbidden scope",
            "last proven artifacts, SHAs, checks, or other evidence",
            "first executable next action",
            "Do not pretend that the agent can terminate the current chat or open the next one itself",
        ):
            self.assertIn(phrase, content)

    def test_one_canonical_contract_exports_only_a_lightweight_stub(self) -> None:
        content = self.target["copyContent"]
        self.assertIn("ONE CANONICAL CONTRACT, LIGHTWEIGHT EMBEDDING", content)
        self.assertIn("do not paste this entire contract into every prompt", content)
        self.assertIn(
            "CANARY STUB — Before every response emit CANARY | PROFILE=<canonical computer profile>",
            content,
        )
        self.assertIn("The host prompt still owns its mission, scope, proof, and closure", content)

    def test_neighbor_owners_remain_distinct(self) -> None:
        self.assertEqual(
            self.by_id["P02"]["name"],
            "Previous Chat → Active Sprint Executor",
        )
        self.assertEqual(
            self.by_id["P76"]["name"],
            "Progressive-Disclosure Spec & Harness Factorer",
        )
        self.assertNotEqual(self.target["id"], "P02")
        self.assertNotEqual(self.target["id"], "P76")
        self.assertIn("P02 owns previous-chat recovery and active sprint execution", self.target["copyContent"])
        self.assertIn("P76 owns repository spec/harness progressive disclosure", self.target["copyContent"])

    def test_semantic_falsification_cases_are_explicit(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "SEMANTIC FALSIFICATION",
            "stable profile across several responses",
            "one seeded omission",
            "one seeded wrong profile",
            "a legitimate profile change backed by new evidence",
            "repeated drift after re-anchor",
            "unrecoverable profile state",
        ):
            self.assertIn(phrase, content)

    def test_registered_in_deterministic_test_floor(self) -> None:
        floor = json.loads(TEST_FLOOR.read_text(encoding="utf-8"))
        self.assertEqual(floor["self_tests"].count(TEST_PATH), 1)
        self.assertIn("tests/test_*_prompt.py", floor["prompt_semantic_test_globs"])

    def test_generated_site_is_exact_and_contains_canary(self) -> None:
        html = build_prompt_kit_registry.DEFAULT_OUTPUT.read_text(encoding="utf-8")
        self.assertEqual(html, build_prompt_kit_registry.render())
        self.assertIn(self.target["id"], html)
        self.assertIn(TARGET_NAME, html)


if __name__ == "__main__":
    unittest.main()
