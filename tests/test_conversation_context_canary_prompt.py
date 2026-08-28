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

    def test_identity_and_profile_remain_stable(self) -> None:
        self.assertEqual(self.target["id"], "P114")
        self.assertEqual(self.target["seq"], "114")
        self.assertEqual(self.target["copySheet"], "P114_COPY_SAFE")
        self.assertEqual(self.target["profile"], "spec-architecture")
        self.assertEqual(self.target["class"], "CONTEXT / CONTINUITY")
        self.assertEqual(self.raw["id"], self.target["id"])

    def test_canary_requires_profile_and_required_network_every_response(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "MANDATORY FIRST LINE",
            "CANARY | PROFILE=<canonical computer profile> | NETWORK=<WAB|Guest|Hardwire|Local|Arbitrary/N/A>",
            "Do not expand the normal Canary into scope narration",
            "Keep the normal Canary to one line",
        ):
            self.assertIn(phrase, content)
        for network in ("WAB", "Guest", "Hardwire", "Local", "Arbitrary/N/A"):
            self.assertIn(network, content)

    def test_network_is_required_posture_not_observed_connectivity(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "REQUIRED NETWORK SEMANTICS",
            "network the user should be on for the current task",
            "not, by itself, a claim that the agent has observed the user's live connection",
            "It must never be used as a synonym for unknown",
            "NETWORK=UNKNOWN",
        ):
            self.assertIn(phrase, content)

    def test_execution_context_is_conditional_and_distinguishes_terminal_shell_kernel(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "EXECUTION CONTEXT SEMANTICS",
            "EXEC=<shell>@<kernel/runtime>",
            "EXEC=UNKNOWN",
            "terminal application only as a host surface",
            "Windows Terminal, for example, can host PowerShell, `cmd.exe`, WSL shells",
            "do not guess a shell-specific mutation command or shell-bound agent runtime",
            "When execution context is irrelevant, omit EXEC",
        ):
            self.assertIn(phrase, content)

    def test_unknown_material_context_fails_closed_and_reanchors(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "PROFILE=UNKNOWN",
            "NETWORK=UNKNOWN",
            "command-sensitive `EXEC=UNKNOWN`",
            "RE-ANCHOR ONCE",
            "Do not ask the operator to repeat recoverable context",
        ):
            self.assertIn(phrase, content)

    def test_handoff_preserves_network_and_material_execution_context(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "HANDOFF ON REPEATED OR UNRECOVERABLE DRIFT",
            "required network (`WAB`, `Guest`, `Hardwire`, `Local`, `Arbitrary/N/A`)",
            "material execution context (`<shell>@<kernel/runtime>` plus target detail when needed)",
            "current mission and forbidden scope",
            "last proven artifacts, SHAs, checks, or other evidence",
            "first executable next action",
        ):
            self.assertIn(phrase, content)

    def test_lightweight_stub_preserves_owner_boundaries(self) -> None:
        content = self.target["copyContent"]
        self.assertIn("ONE CANONICAL CONTRACT, LIGHTWEIGHT EMBEDDING", content)
        self.assertIn("do not paste this entire contract into every prompt", content)
        self.assertIn("Append ` | EXEC=<shell>@<kernel/runtime>` only when command/agent choice materially depends", content)
        self.assertIn("P92 Canonical Path Prompt", content)
        self.assertIn("must not create a competing profile or network registry", content)

    def test_semantic_falsification_order_covers_exec_context(self) -> None:
        content = self.target["copyContent"]
        ordered = ("1. STABLE BASELINE", "2. RECOVERY CASE", "3. LEGITIMATE CHANGE", "4. REPEATED DRIFT", "5. UNRECOVERABLE STATE")
        positions = [content.index(marker) for marker in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("wrong material shell/kernel execution context", content)
        self.assertIn("shell/kernel runtime, or execution target", content)
        self.assertIn("command-sensitive execution context unrecoverable", content)

    def test_neighbor_owners_remain_distinct(self) -> None:
        self.assertEqual(self.by_id["P02"]["name"], "Previous Chat → Active Sprint Executor")
        self.assertEqual(self.by_id["P76"]["name"], "Progressive-Disclosure Spec & Harness Factorer")
        self.assertNotEqual(self.target["id"], "P02")
        self.assertNotEqual(self.target["id"], "P76")

    def test_registered_in_deterministic_test_floor(self) -> None:
        floor = json.loads(TEST_FLOOR.read_text(encoding="utf-8"))
        self.assertEqual(floor["self_tests"].count(TEST_PATH), 1)
        self.assertIn("tests/test_*_prompt.py", floor["prompt_semantic_test_globs"])

    def test_generated_site_is_exact_and_contains_canary(self) -> None:
        html = build_prompt_kit_registry.DEFAULT_OUTPUT.read_text(encoding="utf-8")
        self.assertEqual(html, build_prompt_kit_registry.render())
        self.assertIn("P114", html)
        self.assertIn(TARGET_NAME, html)
        self.assertIn("kernel/runtime", html)
        self.assertIn("EXEC=", html)


if __name__ == "__main__":
    unittest.main()
