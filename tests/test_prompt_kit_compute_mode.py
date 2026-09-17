from __future__ import annotations

import unittest
from pathlib import Path

import build_prompt_kit
from scripts import build_prompt_kit_registry as builder
from scripts import prompt_context_engine as engine
from scripts import prompt_language_compiler as compiler

ROOT = Path(__file__).resolve().parents[1]
BUILDER_SOURCE = ROOT / "scripts" / "build_prompt_kit_registry.py"
COMPUTE_MODE_JS = ROOT / "docs" / "prompt-kit-compute-mode.js"
SEMANTICS_P07 = ROOT / "harness" / "prompt-compilation" / "semantics" / "P07.json"
BUILD_CONTEXT = (
    ROOT / "harness" / "prompt-compilation" / "build-context" / "default.v1.json"
)
MUST_DISPATCH_PHRASE = "MUST dispatch independent lanes in parallel"


class PromptKitComputeModeTests(unittest.TestCase):
    def test_builder_wires_compute_mode_after_storage_lifecycle(self) -> None:
        source = BUILDER_SOURCE.read_text(encoding="utf-8")
        self.assertIn(
            'COMPUTE_MODE_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-compute-mode.js"',
            source,
        )
        self.assertLess(
            source.index("storage_lifecycle_script = _read_runtime"),
            source.index("compute_mode_script = _read_runtime"),
        )
        self.assertLess(
            source.index('f"<script>\\n{storage_lifecycle_script}\\n</script>\\n"'),
            source.index('f"<script>\\n{compute_mode_script}\\n</script>\\n"'),
        )
        self.assertLess(
            source.index('f"<script>\\n{compute_mode_script}\\n</script>\\n"'),
            source.index('f"<script>\\n{profile_script}\\n</script>\\n"'),
        )

    def test_builder_render_embeds_compute_mode_when_runtime_exists(self) -> None:
        if not COMPUTE_MODE_JS.is_file():
            self.skipTest("docs/prompt-kit-compute-mode.js not yet delivered by Lane A")
        html = builder.render()
        runtime_text = COMPUTE_MODE_JS.read_text(encoding="utf-8")
        marker = (
            "PromptKitComputeMode"
            if "PromptKitComputeMode" in runtime_text
            else "compute-mode"
        )
        self.assertIn(marker, html)
        self.assertIn("compiledEffectivePrompts", html)
        self.assertIn(MUST_DISPATCH_PHRASE, html)

    def test_p07_registry_includes_compiled_effective_prompts(self) -> None:
        self.assertTrue(SEMANTICS_P07.is_file())
        self.assertTrue(BUILD_CONTEXT.is_file())
        prompts = {p["id"]: p for p in builder.load_prompt_kit_registry()}
        self.assertIn("P07", prompts)
        compiled = prompts["P07"].get("compiledEffectivePrompts")
        self.assertIsInstance(compiled, dict)
        self.assertIn("exhaustive", compiled)
        self.assertIn("efficient", compiled)

        reference = builder._load_json(builder.REFERENCE)
        html = build_prompt_kit.build_html([prompts["P07"]], reference)
        self.assertIn("compiledEffectivePrompts", html)
        self.assertIn(MUST_DISPATCH_PHRASE, html)

    def test_exhaustive_compiled_text_contains_must_dispatch(self) -> None:
        prompts = {p["id"]: p for p in builder.load_prompt_kit_registry()}
        exhaustive = prompts["P07"]["compiledEffectivePrompts"]["exhaustive"]
        self.assertIn(MUST_DISPATCH_PHRASE, exhaustive)
        self.assertIn("typed failure disposition AUTONOMY_GAP", exhaustive)
        self.assertIn("observed_parallel_dispatch_receipt", exhaustive)

    def test_efficient_compiled_text_is_non_weakening_for_must(self) -> None:
        prompts = {p["id"]: p for p in builder.load_prompt_kit_registry()}
        efficient = prompts["P07"]["compiledEffectivePrompts"]["efficient"]
        self.assertIn(MUST_DISPATCH_PHRASE, efficient)
        policy = compiler.load_policy()
        self.assertEqual(compiler.find_weakening(efficient, policy), [])
        for weak in (
            "consider parallel",
            "where useful",
            "if appropriate",
            "could dispatch",
            "may parallelize",
        ):
            self.assertNotIn(weak, efficient.lower())

    def test_python_side_profile_precedence(self) -> None:
        run_beats = engine.resolve_execution_profile(
            explicit_run_override="efficient",
            prompt_override="exhaustive",
            user_default="exhaustive",
            product_default="exhaustive",
        )
        self.assertEqual(run_beats["resolution"]["resolved_from"], "explicit_run_override")
        self.assertEqual(run_beats["profile"]["profile"], "efficient")

        prompt_beats = engine.resolve_execution_profile(
            prompt_override="efficient",
            user_default="exhaustive",
        )
        self.assertEqual(prompt_beats["resolution"]["resolved_from"], "prompt_override")
        self.assertEqual(prompt_beats["profile"]["profile"], "efficient")

        product_default = engine.resolve_execution_profile()
        self.assertEqual(product_default["resolution"]["resolved_from"], "product_default")
        self.assertEqual(product_default["profile"]["profile"], "exhaustive")


if __name__ == "__main__":
    unittest.main()
