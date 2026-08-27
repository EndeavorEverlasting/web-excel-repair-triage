from __future__ import annotations

import unittest

import build_prompt_kit as prompt_site
from scripts import build_prompt_kit_registry as prompt_registry


TARGET_ID = "P103"
TARGET_NAME = "Prompt Registry Classification Refiner"


class PromptClassificationRefinerPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prompts = prompt_registry.load_prompt_kit_registry()
        matches = [prompt for prompt in cls.prompts if prompt.get("name") == TARGET_NAME]
        if len(matches) != 1:
            raise AssertionError(f"expected exactly one {TARGET_NAME!r}, found {len(matches)}")
        cls.prompt = matches[0]
        cls.copy = cls.prompt["copyContent"]

    def test_identity_is_distinct_and_helper_allocated(self) -> None:
        self.assertEqual(TARGET_ID, self.prompt["id"])
        self.assertEqual("103", self.prompt["seq"])
        self.assertEqual("P103_COPY_SAFE", self.prompt["copySheet"])
        self.assertEqual("MAINTENANCE + HARNESS", self.prompt["type"])
        self.assertEqual("PROMPT KIT / CLASSIFICATION ARCHITECTURE", self.prompt["class"])
        self.assertEqual("spec-architecture", self.prompt["profile"])

    def test_iteration_is_prototype_driven_and_mainline_convergent(self) -> None:
        for marker in (
            "BASELINE -> HYPOTHESIS -> SMALLEST PROTOTYPE -> REBUILD -> USE/FALSIFY -> HOOK -> MIGRATE NEXT SLICE -> REFRESH -> CONTINUE",
            "A prototype is evidence; it is not automatically the final taxonomy.",
            "SECOND-PASS FALSIFICATION",
            "CONVERGE TO MAIN",
            "prove containment of the integrated SHA",
        ):
            self.assertIn(marker, self.copy)

    def test_hooks_are_created_from_proven_invariants_not_subjective_judgment(self) -> None:
        self.assertIn("IMPLEMENT HOOKS AS YOU LEARN THE RULES", self.copy)
        self.assertIn("Whenever an iteration establishes a deterministic invariant, enforce it immediately", self.copy)
        self.assertIn("Do not add a hook for subjective judgment that cannot be checked reliably.", self.copy)
        self.assertIn("pre-commit/pre-push hooks", self.copy)
        self.assertIn("CI path triggers", self.copy)

    def test_classification_does_not_conflate_identity_aliases_or_synonyms(self) -> None:
        self.assertIn("KEEP IDENTITY, TAXONOMY, PRESENTATION, AND DISCOVERY DISTINCT", self.copy)
        self.assertIn("Preserve canonical prompt IDs and useful prompt names", self.copy)
        self.assertIn("human aliases/display titles are presentation identity, not canonical taxonomy", self.copy)
        self.assertIn("keywords, triggers, and intent synonyms primarily serve discovery/routing", self.copy)
        self.assertIn("Classification cleanup must not silently break search/discovery or turn synonyms into taxonomy.", self.copy)

    def test_classification_compares_behavior_and_closure_not_title_alone(self) -> None:
        self.assertIn("CLASSIFY BY BEHAVIOR AND CLOSURE, NOT TITLE ALONE", self.copy)
        for field in ("trigger", "mission", "owned scope", "expected output", "proof gate", "closure condition"):
            self.assertIn(field, self.copy.casefold())

    def test_prompt_has_actionable_classification_keywords(self) -> None:
        keywords = {item.casefold() for item in self.prompt["keywords"]}
        for expected in (
            "prompt classification",
            "prompt taxonomy",
            "classification hooks",
            "classification prototype",
            "registry taxonomy",
        ):
            self.assertIn(expected, keywords)

    def test_generated_prompt_kit_exposes_helper_allocated_prompt(self) -> None:
        html = prompt_registry.render()
        self.assertIn(TARGET_ID, html)
        self.assertIn(TARGET_NAME, html)
        self.assertIn("PROMPT KIT / CLASSIFICATION ARCHITECTURE", html)
        self.assertIn("classification prototype", html.casefold())

    def test_every_effective_type_has_one_lifecycle_section(self) -> None:
        memberships: dict[str, list[str]] = {}
        for section in prompt_site.SECTIONS:
            section_name = section["name"]
            for prompt_type in section["types"]:
                memberships.setdefault(prompt_type, []).append(section_name)

        effective_types = {str(prompt["type"]).strip() for prompt in self.prompts}
        unmapped = sorted(prompt_type for prompt_type in effective_types if prompt_type not in memberships)
        unmapped_usages = {
            prompt_type: [
                f"{prompt['id']}:{prompt['name']} [{prompt['class']}]"
                for prompt in self.prompts
                if str(prompt["type"]).strip() == prompt_type
            ]
            for prompt_type in unmapped
        }
        multiply_mapped = {
            prompt_type: sections
            for prompt_type, sections in sorted(memberships.items())
            if len(sections) != 1
        }
        self.assertEqual({}, unmapped_usages, f"effective prompt types without lifecycle section: {unmapped_usages}")
        self.assertEqual({}, multiply_mapped, f"prompt types mapped to multiple lifecycle sections: {multiply_mapped}")


if __name__ == "__main__":
    unittest.main()
