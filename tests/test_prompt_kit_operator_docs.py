from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPERATOR = ROOT / "docs" / "PROMPT_KIT_OPERATOR_GUIDE.md"
FINDER_TUTORIAL = ROOT / "docs" / "PROMPT_FINDER_QUESTIONNAIRE_TUTORIAL.md"
WEB_README = ROOT / "web" / "README.md"
GUIDED = ROOT / "docs" / "prompt-kit-guided-recommendations.js"
JOURNEY = ROOT / "docs" / "prompt-kit-journey.js"
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
P83_REGISTRY = ROOT / "registry" / "prompts" / "repository-work-ledger-prompts.v1.json"


class PromptKitOperatorDocumentationTests(unittest.TestCase):
    def test_operator_guide_tracks_current_four_question_finder(self) -> None:
        guide = OPERATOR.read_text(encoding="utf-8")
        tutorial = FINDER_TUTORIAL.read_text(encoding="utf-8")
        guided = GUIDED.read_text(encoding="utf-8")

        question_ids = ("startingPoint", "problemKnown", "goal", "shape")
        self.assertEqual(sum(guided.count(f"id:'{item}'") for item in question_ids), 4)
        self.assertIn("filterPromptsForQuery(PROMPTS,query)", guided)
        self.assertIn("slice(0,5)", guided)
        self.assertIn("slice(0,3)", guided)

        self.assertIn("Answer the **four** current questions", guide)
        self.assertIn("first five shared-search results", guide)
        self.assertIn("returns at most three recommendations", guide)
        self.assertIn("Answer the four current questions", tutorial)
        self.assertIn("first five shared-search results", tutorial)
        self.assertIn("returns at most three candidates", tutorial)

    def test_inherited_completion_documentation_points_to_canonical_p83(self) -> None:
        payload = json.loads(P83_REGISTRY.read_text(encoding="utf-8"))
        p83 = next(item for item in payload["prompts"] if item["id"] == "P83")
        guide = OPERATOR.read_text(encoding="utf-8")
        tutorial = FINDER_TUTORIAL.read_text(encoding="utf-8")

        self.assertEqual(p83["name"], "Agent Work Verifier & Iterative Advancer")
        self.assertIn("claims work is complete or partially complete", p83["useWhen"])
        self.assertIn("P83 — Agent Work Verifier & Iterative Advancer", guide)
        self.assertIn("search **`P83`**", guide)
        self.assertIn("P83 — Agent Work Verifier & Iterative Advancer", tutorial)
        self.assertIn("Another agent claims work is complete or partially complete", tutorial)

    def test_operator_docs_match_current_copy_reveal_shortcut_runtime(self) -> None:
        guide = OPERATOR.read_text(encoding="utf-8")
        web = WEB_README.read_text(encoding="utf-8")
        polish = POLISH.read_text(encoding="utf-8")

        start = polish.index("function activatePromptShortcutTarget")
        end = polish.index("\n\nfunction handleConfiguredPromptShortcutKey", start)
        activation = polish[start:end]

        self.assertIn("Copy + reveal '+promptId", polish)
        self.assertIn("revealPromptShortcutTarget(promptId)", activation)
        self.assertIn("copyPrompt(promptId)", activation)
        self.assertNotIn("showPromptDetail", activation)

        self.assertIn("**does not open prompt detail**", guide)
        self.assertIn("1.2 seconds", guide)
        self.assertIn("**without opening prompt detail**", web)
        self.assertIn("**Copy + reveal P##**", web)
        self.assertNotIn("open the canonical prompt detail immediately", web)

    def test_operator_docs_preserve_explicit_favorites_view(self) -> None:
        guide = OPERATOR.read_text(encoding="utf-8")
        web = WEB_README.read_text(encoding="utf-8")

        self.assertIn("Favorites do **not** reorder the normal library", guide)
        self.assertIn("explicit **Favorites** view", guide)
        self.assertIn("Favorites remain in the normal chronological/numeric library order by default", web)
        self.assertIn("explicit **Favorites** header view", web)
        self.assertNotIn(
            "Visible favorited prompts are promoted into one **Favorites** section before the normal sections.",
            web,
        )

    def test_journey_and_navigation_claims_are_repo_owned(self) -> None:
        guide = OPERATOR.read_text(encoding="utf-8")
        tutorial = FINDER_TUTORIAL.read_text(encoding="utf-8")
        web = WEB_README.read_text(encoding="utf-8")
        journey = JOURNEY.read_text(encoding="utf-8")

        for marker in (
            "NEXT-STEP CONTRACT",
            "READY TO CONTINUE WHEN",
            "sessionStorage",
            "Mark this step complete",
        ):
            self.assertIn(marker, journey)

        self.assertIn("NEXT-STEP CONTRACT", guide)
        self.assertIn("READY TO CONTINUE WHEN", guide)
        self.assertIn("sessionStorage", guide)
        self.assertIn("Marking a step complete is navigation state, not repository proof", guide)
        self.assertIn("PROMPT_KIT_OPERATOR_GUIDE.md", tutorial)
        self.assertIn("PROMPT_KIT_OPERATOR_GUIDE.md", web)

    def test_documented_validation_commands_reference_existing_owners(self) -> None:
        guide = OPERATOR.read_text(encoding="utf-8")
        tutorial = FINDER_TUTORIAL.read_text(encoding="utf-8")
        expected_paths = (
            ROOT / "scripts" / "build_prompt_kit_registry.py",
            ROOT / "scripts" / "validate_prompt_kit_discovery.py",
            ROOT / "tests" / "test_prompt_kit_hotkey_completion.py",
            ROOT / "tests" / "test_prompt_kit_discovery.py",
            ROOT / "tests" / "test_prompt_kit_guidance.py",
        )
        for path in expected_paths:
            self.assertTrue(path.is_file(), str(path))

        for text in (guide, tutorial):
            self.assertIn("scripts/build_prompt_kit_registry.py", text)
            self.assertIn("scripts/validate_prompt_kit_discovery.py", text)
        self.assertIn("tests.test_prompt_kit_operator_docs", guide)
        self.assertIn("tests.test_prompt_kit_operator_docs", tutorial)


if __name__ == "__main__":
    unittest.main()
