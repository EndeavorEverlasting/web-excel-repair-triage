from __future__ import annotations

import unittest

from scripts import build_prompt_kit_registry


class CorrespondencePromptRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.operational_prompts = {
            prompt["id"]: prompt
            for prompt in build_prompt_kit_registry.load_prompt_registry()
        }
        cls.content_prompts = {
            prompt["id"]: prompt
            for prompt in build_prompt_kit_registry.load_content_prompt_registry()
        }
        cls.prompts = {
            prompt["id"]: prompt
            for prompt in build_prompt_kit_registry.load_prompt_kit_registry()
        }

    def test_correspondence_prompts_are_content_only_with_stable_identity(self) -> None:
        self.assertNotIn("P72", self.operational_prompts)
        self.assertNotIn("P73", self.operational_prompts)
        self.assertEqual(set(self.content_prompts), {"P72", "P73"})
        self.assertEqual(self.prompts["P72"]["seq"], "72")
        self.assertEqual(self.prompts["P73"]["seq"], "73")
        for prompt_id in ("P72", "P73"):
            prompt = self.prompts[prompt_id]
            self.assertEqual(prompt["profile"], "correspondence")
            self.assertEqual(prompt["category"], "standard")
            self.assertEqual(prompt["color"], "Magenta")
            self.assertEqual(
                prompt["actionabilityPolicy"], "not-applicable:content-only"
            )

    def test_operational_prompts_keep_global_actionability_policy(self) -> None:
        policy = build_prompt_kit_registry.load_actionability_policy()
        for prompt in self.operational_prompts.values():
            with self.subTest(prompt=prompt["id"]):
                self.assertEqual(prompt["actionabilityPolicy"], policy["policy_id"])
                self.assertIn(policy["marker"], prompt["copyContent"])
                self.assertIn(policy["next_step_suffix"], prompt["nextStep"])

    def test_message_polisher_preserves_fidelity_and_does_not_invent_action(self) -> None:
        content = self.prompts["P72"]["copyContent"]
        self.assertIn("concise, confident, actionable, and cordial", content)
        self.assertIn("Do not invent a deadline, owner, promise", content)
        self.assertIn("Do not soften away an important disagreement", content)
        self.assertIn("Return only the send-ready message", content)
        self.assertNotIn("ACTIONABLE NEXT COMMAND AND NEXT STEPS CONTRACT", content)

    def test_client_facing_refiner_removes_process_without_hiding_material_truth(self) -> None:
        content = self.prompts["P73"]["copyContent"]
        self.assertIn("REMOVE OR TRANSLATE INTERNAL MACHINERY", content)
        self.assertIn("repository, branch, pull request, commit, worktree, harness", content)
        self.assertIn("DO NOT SANITIZE AWAY BAD NEWS", content)
        self.assertIn("Never turn an unresolved issue into `complete`", content)
        self.assertNotIn("ACTIONABLE NEXT COMMAND AND NEXT STEPS CONTRACT", content)

    def test_render_includes_correspondence_runtime_and_profile_tokens(self) -> None:
        html = build_prompt_kit_registry.render()
        self.assertIn("prompt-kit-correspondence-styles", html)
        self.assertIn("COLORS.magenta=ACCENT", html)
        self.assertIn("data-profile", html)
        self.assertIn("Concise Confident Message Polisher", html)
        self.assertIn("Client-Facing Correspondence Refiner", html)

    def test_correspondence_prompts_bind_role_source_done_and_self_check(self) -> None:
        for prompt_id in ("P72", "P73"):
            content = self.prompts[prompt_id]["copyContent"]
            with self.subTest(prompt=prompt_id):
                self.assertIn("ROLE / SOURCE / DONE / SELF-CHECK", content)
                self.assertIn("- ROLE:", content)
                self.assertIn("- SOURCE:", content)
                self.assertIn("- DEFINITION OF DONE:", content)
                self.assertIn("- SELF-CHECK:", content)
        self.assertIn("senior correspondence editor", self.prompts["P72"]["copyContent"])
        self.assertIn("compare the final message back to the source", self.prompts["P72"]["copyContent"])
        self.assertIn("senior client-communications editor", self.prompts["P73"]["copyContent"])
        self.assertIn("preserve that uncertainty instead of manufacturing confidence", self.prompts["P73"]["copyContent"])

if __name__ == "__main__":
    unittest.main()
