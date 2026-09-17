from __future__ import annotations

import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry as builder
from scripts import prompt_compute_mode as compute_mode
from scripts import prompt_context_engine as context_engine

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "docs" / "prompt-kit-compute-mode.js"
BASE_RUNTIME = ROOT / "docs" / "prompt-kit.js"


class PromptComputeModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = compute_mode.load_policy()
        cls.manifest = compute_mode.build_product_manifest(cls.policy)

    def test_policy_reuses_context_engine_authority(self) -> None:
        self.assertEqual(self.policy["product_default"], context_engine.PRODUCT_DEFAULT_PROFILE)
        self.assertEqual(self.policy["profile_precedence"], list(context_engine.PROFILE_PRECEDENCE))

    def test_manifest_is_compiler_backed_for_both_profiles(self) -> None:
        self.assertEqual(self.manifest["schema_version"], "prompt-compute-mode-product/v1")
        self.assertEqual(set(self.manifest["profiles"]), {"exhaustive", "efficient"})
        for name, record in self.manifest["profiles"].items():
            self.assertIn("COMPILED EXECUTION PROFILE", record["overlay"])
            self.assertIn(f"Execution profile: {name}", record["overlay"])
            self.assertRegex(record["profile_sha256"], r"^[a-f0-9]{64}$")
            self.assertTrue(record["language_engine_revision"])

    def test_exhaustive_mode_preserves_legacy_rule_and_adds_overlay(self) -> None:
        canonical = (
            "BASE\n\nEXHAUSTIVE AVAILABLE COMPUTE RULE\n- preserve me\n\n"
            "NON-PROGRESS / QUIESCENCE CONTRACT\n- continue"
        )
        result = compute_mode.compose_effective_prompt(canonical, "exhaustive", policy=self.policy, manifest=self.manifest)
        self.assertIn("EXHAUSTIVE AVAILABLE COMPUTE RULE", result)
        self.assertIn("- preserve me", result)
        self.assertIn("COMPILED EXECUTION PROFILE", result)
        self.assertIn("Execution profile: exhaustive", result)

    def test_efficient_mode_removes_only_legacy_exhaustive_rule(self) -> None:
        canonical = (
            "COMPUTE AUTHORITY / SCOPE-BOUNDARY CONTRACT\n- keep authority\n\n"
            "EXHAUSTIVE AVAILABLE COMPUTE RULE\n- remove exhaustive-only behavior\n\n"
            "NON-PROGRESS / QUIESCENCE CONTRACT\n- keep quiescence\n\nTAIL"
        )
        result = compute_mode.compose_effective_prompt(canonical, "efficient", policy=self.policy, manifest=self.manifest)
        self.assertNotIn("EXHAUSTIVE AVAILABLE COMPUTE RULE", result)
        self.assertNotIn("remove exhaustive-only behavior", result)
        self.assertIn("COMPUTE AUTHORITY / SCOPE-BOUNDARY CONTRACT", result)
        self.assertIn("NON-PROGRESS / QUIESCENCE CONTRACT", result)
        self.assertIn("TAIL", result)
        self.assertIn("Execution profile: efficient", result)

    def test_missing_legacy_boundary_fails_closed_for_efficient_mode(self) -> None:
        with self.assertRaises(compute_mode.ComputeModeError):
            compute_mode.compose_effective_prompt("BASE", "efficient", policy=self.policy, manifest=self.manifest)

    def test_product_registry_operational_prompts_are_compute_mode_eligible(self) -> None:
        prompts = builder.load_prompt_kit_registry()
        operational = [item for item in prompts if item.get("actionabilityPolicy") == self.policy["eligible_actionability_policy"]]
        content_only = [item for item in prompts if item.get("actionabilityPolicy") == "not-applicable:content-only"]
        self.assertGreater(len(operational), 0)
        self.assertTrue(all(compute_mode.is_eligible_prompt(item, self.policy) for item in operational))
        self.assertTrue(all(not compute_mode.is_eligible_prompt(item, self.policy) for item in content_only))

    def test_builder_embeds_compute_mode_manifest_and_runtime(self) -> None:
        html = builder.render()
        self.assertIn("window.PROMPT_KIT_COMPUTE_MODE_MANIFEST", html)
        self.assertIn("prompt-compute-mode-product/v1", html)
        self.assertIn("PromptKitComputeMode", html)
        self.assertIn("promptKit.computeMode.v1", html)

    def test_copy_and_detail_paths_consume_effective_prompt(self) -> None:
        source = BASE_RUNTIME.read_text(encoding="utf-8")
        self.assertIn("PromptKitComputeMode.effectivePrompt", source)
        self.assertIn("PromptKitComputeMode.decorateDetail", source)
        self.assertIn("data-prompt-effective-content", source)
        runtime = RUNTIME.read_text(encoding="utf-8")
        self.assertIn("explicit_run_override", runtime)
        self.assertIn("prompt_override", runtime)
        self.assertIn("user_default", runtime)
        self.assertIn("product_default", runtime)
        self.assertIn("promptKit.computeModeOverrides.v1", runtime)


if __name__ == "__main__":
    unittest.main()
