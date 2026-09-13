from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry
from scripts import prompt_registry_product_boundaries as boundaries

ROOT = Path(__file__).resolve().parents[1]
MANAGEMENT_REGISTRY = ROOT / "registry" / "prompts" / "management-operations-prompts.v1.json"


class PromptRegistryProductBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = boundaries.load_contract()
        cls.summary = boundaries.validate_product_boundaries(cls.contract)
        cls.management = json.loads(MANAGEMENT_REGISTRY.read_text(encoding="utf-8"))

    def test_every_legacy_extension_has_exactly_one_product_owner(self) -> None:
        legacy = {
            path.resolve().relative_to(ROOT).as_posix()
            for path in build_prompt_kit_registry.EXTENSION_REGISTRIES
        }
        afk = {
            path.relative_to(ROOT).as_posix()
            for path in boundaries.extension_registries_for_product(
                boundaries.AFK_PRODUCT, self.contract
            )
        }
        triage = {
            path.relative_to(ROOT).as_posix()
            for path in boundaries.extension_registries_for_product(
                boundaries.TRIAGE_PRODUCT, self.contract
            )
        }
        self.assertFalse(afk & triage)
        self.assertEqual(legacy, afk | triage)

    def test_afk_product_boundary_excludes_triage_management_registry(self) -> None:
        afk = {
            path.relative_to(ROOT).as_posix()
            for path in boundaries.extension_registries_for_product(
                boundaries.AFK_PRODUCT, self.contract
            )
        }
        self.assertNotIn(boundaries.MANAGEMENT_REGISTRY, afk)
        self.assertIn(
            boundaries.MANAGEMENT_REGISTRY,
            self.contract["products"][boundaries.AFK_PRODUCT]["must_not_include"],
        )

    def test_nth_remains_owned_and_available_in_triage(self) -> None:
        triage = {
            path.relative_to(ROOT).as_posix()
            for path in boundaries.extension_registries_for_product(
                boundaries.TRIAGE_PRODUCT, self.contract
            )
        }
        self.assertEqual(triage, {boundaries.MANAGEMENT_REGISTRY})
        prompts = {prompt["id"]: prompt for prompt in self.management["prompts"]}
        self.assertIn("P74", prompts)
        self.assertEqual(prompts["P74"]["profile"], "billing-management")
        self.assertIn("Neuron Track Hours", prompts["P74"]["name"])

    def test_legacy_combined_prompt_kit_behavior_is_preserved(self) -> None:
        legacy = {
            path.resolve().relative_to(ROOT).as_posix()
            for path in build_prompt_kit_registry.EXTENSION_REGISTRIES
        }
        self.assertIn(boundaries.MANAGEMENT_REGISTRY, legacy)
        self.assertTrue(self.summary["legacy_behavior_preserved"])
        self.assertEqual(
            self.contract["legacy_combined_surface"]["site"],
            "web/prompt-kit/index.html",
        )

    def test_maintenance_question_has_one_obvious_owner(self) -> None:
        afk = boundaries.extension_registries_for_product(
            boundaries.AFK_PRODUCT, self.contract
        )
        triage = boundaries.extension_registries_for_product(
            boundaries.TRIAGE_PRODUCT, self.contract
        )
        self.assertEqual(len(afk), 5)
        self.assertEqual(len(triage), 1)
        self.assertEqual(self.summary["legacy_extension_count"], 6)


if __name__ == "__main__":
    unittest.main()
