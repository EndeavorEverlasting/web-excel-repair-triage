from __future__ import annotations

import unittest

from scripts import build_prompt_kit_registry as prompt_registry


class P77DatasetComponentArtifactHookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        prompts = prompt_registry.load_prompt_kit_registry()
        matches = [prompt for prompt in prompts if prompt.get("id") == "P77"]
        if len(matches) != 1:
            raise AssertionError(f"expected one P77, found {len(matches)}")
        cls.prompt = matches[0]

    def test_identity_and_existing_taxonomy_are_unchanged(self) -> None:
        self.assertEqual("P77", self.prompt["id"])
        self.assertEqual("Triage + FUN + Drive Context Synchronizer", self.prompt["name"])
        self.assertEqual("MAINTENANCE + CROSS-REPO", self.prompt["type"])
        self.assertEqual(
            "TRIAGE / BILLING / MANAGEMENT OPERATIONS", self.prompt["class"]
        )

    def test_dataset_component_client_artifact_hook_contract_is_explicit(self) -> None:
        copy = self.prompt["copyContent"]
        for marker in (
            "DATASET -> COMPONENT -> CLIENT ARTIFACT HOOK CONTRACT",
            "per-claim dependency map",
            "source or component change invalidates downstream claims",
            "component-versus-complete-solution semantics",
            "mark CONFLICT and preserve both truths",
            "fail-closed stale-state handling",
        ):
            self.assertIn(marker, copy)

    def test_discovery_routes_the_new_truth_propagation_use_case_to_p77(self) -> None:
        keywords = {item.casefold() for item in self.prompt["keywords"]}
        for expected in (
            "dataset artifact synchronization",
            "client artifact state",
            "application state synchronization",
            "component state hooks",
            "truth propagation hooks",
        ):
            self.assertIn(expected, keywords)
        html = prompt_registry.render().casefold()
        self.assertIn("truth propagation hooks", html)
        self.assertIn("dataset artifact synchronization", html)


if __name__ == "__main__":
    unittest.main()
