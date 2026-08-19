from __future__ import annotations

import unittest

import build_prompt_kit
from scripts import build_prompt_kit_registry


class ManagementOperationsPromptRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.operational = {
            prompt["id"]: prompt
            for prompt in build_prompt_kit_registry.load_prompt_registry()
        }
        cls.full = {
            prompt["id"]: prompt
            for prompt in build_prompt_kit_registry.load_prompt_kit_registry()
        }
        cls.policy = build_prompt_kit_registry.load_actionability_policy()

    def test_management_prompts_are_operational_with_stable_profiles(self) -> None:
        self.assertEqual(self.operational["P74"]["seq"], "74")
        self.assertEqual(self.operational["P75"]["seq"], "75")
        self.assertEqual(self.operational["P77"]["seq"], "77")
        self.assertEqual(self.operational["P74"]["profile"], "billing-management")
        self.assertEqual(self.operational["P75"]["profile"], "fun-management")
        self.assertEqual(self.operational["P77"]["profile"], "triage-management")
        self.assertEqual(self.operational["P74"]["color"], "Emerald")
        self.assertEqual(self.operational["P75"]["color"], "Indigo")
        self.assertEqual(self.operational["P77"]["color"], "Emerald")
        for prompt_id in ("P74", "P75", "P77"):
            prompt = self.operational[prompt_id]
            self.assertEqual(prompt["category"], "standard")
            self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
            self.assertIn(self.policy["marker"], prompt["copyContent"])
            self.assertIn(self.policy["next_step_suffix"], prompt["nextStep"])

    def test_neuron_track_hours_prompt_is_artifact_execution_not_prose(self) -> None:
        prompt = self.full["P74"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["type"], "BUILD + ARTIFACT")
        self.assertIn("GENERATE THE NEURON TRACK HOURS BILLING ARTIFACT NOW", content)
        self.assertIn("EndeavorEverlasting/web-excel-repair-triage", content)
        self.assertIn("EndeavorEverlasting/FUN", content)
        self.assertIn("registered `Outputs/` family", content)
        self.assertIn("do not substitute an older remembered precedence rule", content)
        self.assertIn("Do not invent sites, rooms, hostnames", content)
        self.assertIn("Do not answer with instructions for how someone else could build the sheet", content)

    def test_fun_update_prompt_targets_canonical_repo_and_stays_blue(self) -> None:
        prompt = self.full["P75"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["type"], "MAINTENANCE")
        self.assertEqual(prompt["profile"], "fun-management")
        self.assertEqual(prompt["color"], "Indigo")
        self.assertIn("`EndeavorEverlasting/FUN`", content)
        self.assertIn("Reuse or repair an existing branch/PR", content)
        self.assertIn("CROSS-REPO CONTRACT CHECK", content)
        self.assertIn("web-excel-repair-triage", content)
        self.assertIn("merge it in the same sprint", content)
        self.assertIn("Do not make the operator pull a merged feature branch", content)

    def test_cross_repo_sync_prompt_covers_forgotten_work_and_green_triage_semantics(self) -> None:
        prompt = self.full["P77"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["type"], "MAINTENANCE + CROSS-REPO")
        self.assertEqual(prompt["profile"], "triage-management")
        self.assertEqual(prompt["color"], "Emerald")
        self.assertIn("SYNCHRONIZE THE CURRENT MANAGEMENT CONTEXT", content)
        self.assertIn("MATERIAL DEPENDENCY MAP", content)
        self.assertIn("MUST UPDATE, CHECKED/NO CHANGE, or BLOCKED BY EXTERNAL PROOF", content)
        self.assertIn("Cover the secondary work", content)
        self.assertIn("green Triage/product lane", content)
        self.assertIn("blue/indigo FUN evidence-management lane", content)
        self.assertIn("Do not recolor FUN prompts green", content)
        self.assertIn("Drive File Map or audience route", content)
        self.assertIn("generated canonical website", content)
        self.assertIn("merge every exact green authorized head", content)

    def test_management_profile_runtime_is_rendered(self) -> None:
        html = build_prompt_kit_registry.render()
        self.assertIn("prompt-kit-management-styles", html)
        self.assertIn("billing-management", html)
        self.assertIn("fun-management", html)
        self.assertIn("triage-management", html)
        self.assertIn("▦ NTH Billing", html)
        self.assertIn("◆ FUN Management", html)
        self.assertIn("▣ Triage Ops", html)
        self.assertIn("Neuron Track Hours Billing Artifact Builder", html)
        self.assertIn("FUN Repository Management & Evidence Updater", html)
        self.assertIn("Triage + FUN + Drive Context Synchronizer", html)

    def test_base_palette_supports_management_accents(self) -> None:
        self.assertEqual(build_prompt_kit.COLOR_HEX["emerald"], "#10b981")
        self.assertEqual(build_prompt_kit.COLOR_HEX["indigo"], "#6366f1")


if __name__ == "__main__":
    unittest.main()
