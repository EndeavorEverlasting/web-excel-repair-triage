from __future__ import annotations

import unittest

import build_prompt_kit as prompt_site
from scripts import build_prompt_kit_registry as prompt_registry
from scripts import prompt_classification
from scripts import prompt_registry_ops

TARGET_ID = "P103"
TARGET_NAME = "Prompt Registry Classification Refiner"


class PromptClassificationRefinerPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prompts = prompt_registry.load_prompt_kit_registry()
        matches = [prompt for prompt in cls.prompts if prompt.get("name") == TARGET_NAME]
        if len(matches) != 1:
            raise AssertionError(
                f"expected exactly one {TARGET_NAME!r}, found {len(matches)}"
            )
        cls.prompt = matches[0]
        cls.copy = cls.prompt["copyContent"]

    def test_identity_is_distinct_and_helper_allocated(self) -> None:
        self.assertEqual(TARGET_ID, self.prompt["id"])
        self.assertEqual("103", self.prompt["seq"])
        self.assertEqual("P103_COPY_SAFE", self.prompt["copySheet"])
        self.assertEqual("MAINTENANCE + HARNESS", self.prompt["type"])
        self.assertEqual(
            "PROMPT KIT / CLASSIFICATION ARCHITECTURE", self.prompt["class"]
        )
        self.assertEqual("spec-architecture", self.prompt["profile"])

    def test_iteration_contract_remains_prototype_driven(self) -> None:
        for marker in (
            "BASELINE -> HYPOTHESIS -> SMALLEST PROTOTYPE -> REBUILD -> USE/FALSIFY -> HOOK -> MIGRATE NEXT SLICE -> REFRESH -> CONTINUE",
            "A prototype is evidence; it is not automatically the final taxonomy.",
            "SECOND-PASS FALSIFICATION",
            "CONVERGE TO MAIN",
            "prove containment of the integrated SHA",
        ):
            self.assertIn(marker, self.copy)

    def test_identity_taxonomy_presentation_and_discovery_remain_distinct(self) -> None:
        self.assertIn(
            "KEEP IDENTITY, TAXONOMY, PRESENTATION, AND DISCOVERY DISTINCT",
            self.copy,
        )
        self.assertIn("Preserve canonical prompt IDs and useful prompt names", self.copy)
        self.assertIn(
            "human aliases/display titles are presentation identity, not canonical taxonomy",
            self.copy,
        )
        self.assertIn(
            "keywords, triggers, and intent synonyms primarily serve discovery/routing",
            self.copy,
        )

    def test_every_effective_type_has_one_lifecycle_section(self) -> None:
        prompt_classification.validate_prompt_classification(self.prompts)
        self.assertEqual(prompt_site.SECTIONS, prompt_classification.site_sections())
        effective_types = {str(prompt["type"]).strip() for prompt in self.prompts}
        self.assertTrue(
            effective_types <= set(prompt_classification.type_to_section())
        )

    def test_representative_boundary_prompts_land_by_behavior(self) -> None:
        expected = {
            "P77": "Integrate & Ship",
            "P79": "Integrate & Ship",
            "P83": "Validate & Protect",
            "P96": "Foundation",
            "P97": "Discover & Plan",
            "P103": "Integrate & Ship",
            "P115": "Autonomy & Night Shift",
            "P122": "Build & Repair",
        }
        by_id = {prompt["id"]: prompt for prompt in self.prompts}
        mapping = prompt_classification.type_to_section()
        for prompt_id, section in expected.items():
            self.assertEqual(section, mapping[by_id[prompt_id]["type"]], prompt_id)

    def test_registry_helper_rejects_unclassified_new_type(self) -> None:
        draft = {
            "name": "Synthetic classification canary",
            "type": "UNMAPPED + TYPE",
            "class": "TEST / CANARY",
            "sprintRole": "test",
            "useWhen": "test",
            "inspectFirst": "test",
            "expectedOutput": "test",
            "nextStep": "test",
            "proofGate": "test",
            "copyContent": "x" * 301,
            "keywords": ["classification canary"],
        }
        with self.assertRaisesRegex(SystemExit, "Unclassified prompt type"):
            prompt_registry_ops._validate_draft(draft)


if __name__ == "__main__":
    unittest.main()
