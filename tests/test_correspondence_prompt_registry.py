from __future__ import annotations

import unittest

from scripts import build_prompt_kit_registry


class CorrespondencePromptRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prompts = {
            prompt["id"]: prompt for prompt in build_prompt_kit_registry.load_prompt_registry()
        }

    def test_correspondence_prompts_are_registered_with_stable_identity(self) -> None:
        self.assertIn("P72", self.prompts)
        self.assertIn("P73", self.prompts)
        self.assertEqual(self.prompts["P72"]["seq"], "72")
        self.assertEqual(self.prompts["P73"]["seq"], "73")
        for prompt_id in ("P72", "P73"):
            prompt = self.prompts[prompt_id]
            self.assertEqual(prompt["profile"], "correspondence")
            self.assertEqual(prompt["category"], "standard")
            self.assertEqual(prompt["color"], "Magenta")
            self.assertEqual(
                prompt["actionabilityPolicy"], "profile-exempt:correspondence"
            )

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


if __name__ == "__main__":
    unittest.main()
