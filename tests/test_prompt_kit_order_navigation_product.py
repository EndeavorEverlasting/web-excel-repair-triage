from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry


class PromptKitOrderNavigationProductTests(unittest.TestCase):
    def test_registry_defaults_to_numeric_sequence_order(self) -> None:
        prompts = build_prompt_kit_registry.load_prompt_registry()
        sequences = [int(str(prompt["seq"])) for prompt in prompts]
        self.assertEqual(sequences, sorted(sequences))
        self.assertEqual(prompts[0]["id"], "P00")
        self.assertTrue(any(prompt.get("discoveryGroup") == "promoted" for prompt in prompts))

    def test_recommendation_runtime_does_not_replace_library_sort(self) -> None:
        guided = build_prompt_kit_registry.GUIDED_RECOMMENDATIONS.read_text(encoding="utf-8")
        self.assertNotIn("window.promptSequenceValue=rank", guided)
        self.assertIn("function rank(p)", guided)
        self.assertIn("scorePromptFinderAnswers", guided)

    def test_main_renderer_owns_chronology_favorites_and_dense_navigation(self) -> None:
        source = (ROOT / "docs" / "prompt-kit.js").read_text(encoding="utf-8")
        self.assertIn("PROMPT_NAVIGATION_INTERVAL=5", source)
        self.assertIn("function appendDistributedPageNavigation", source)
        self.assertIn("visiblePromptIndex", source)
        self.assertIn("__favorites__", source)
        self.assertIn("orderedPrompts=f.slice().sort", source)
        self.assertIn("renderedSections={}", source)
        self.assertIn(".distributed-page-navigation .page-jump", source)
        self.assertIn("min-height:40px", source)
        self.assertIn("Just before next prompt", source)
        self.assertIn("End of visible prompts", source)
        self.assertNotIn("After prompt '+visiblePromptIndex", source)

    def test_compact_browsing_uses_favorites_hotkey_and_collapsible_filter_chrome(self) -> None:
        polish = (ROOT / "docs" / "prompt-kit-polish.js").read_text(encoding="utf-8")
        profiles = (ROOT / "docs" / "prompt-kit-profiles.js").read_text(encoding="utf-8")
        for marker in (
            "function activateFavoritesView()",
            "activeSection='__favorites__'",
            "id='favoritesShortcut'",
            "data-view','favorites'",
            'Favorites<span class="kbd">C</span>',
            "aria-keyshortcuts','C'",
            "var key=String(e.key||'').toLowerCase();",
            "e.stopImmediatePropagation()",
            "filterPanelToggle",
            "filters-collapsed",
            "Hide filters ↑",
            "Show filters ↓",
        ):
            self.assertIn(marker, polish)
        self.assertNotIn("doctrineKbd.textContent='5'", polish)
        self.assertNotIn('Favorites<span class="kbd">4</span>', polish)
        for digit in "12345":
            self.assertNotIn(f"if(key==='{digit}')", polish)
        for marker in (
            "SLOT_KEYS=['A','B','C','D','E']",
            "button.dataset.profileSlot=slot.key",
            "button.dataset.view='favorites'",
            "activateSlot(key)",
        ):
            self.assertIn(marker, profiles)
        self.assertIn(
            ".header.filters-collapsed .search-container,.header.filters-collapsed .header-controls,.header.filters-collapsed .sections-nav,.header.filters-collapsed .type-nav{display:none!important}",
            polish,
        )

    def test_visible_version_is_consistently_v40(self) -> None:
        html = build_prompt_kit_registry.render()
        self.assertIn('<title>AI Harness Prompt Kit v40</title>', html)
        self.assertIn('AI Harness Prompt Kit <span>v40</span>', html)
        self.assertIn('id=\"versionBadge\">v40</div>', html)
        self.assertNotIn('AI Harness Prompt Kit <span>v39</span>', html)

    def test_dynamic_prompt_id_is_not_embedded_in_inline_copy_javascript(self) -> None:
        source = (ROOT / "docs" / "prompt-kit.js").read_text(encoding="utf-8")
        self.assertIn("id=\"promptDetailCopy\"", source)
        self.assertIn("detailCopy.onclick=function(){copyPrompt(p.id)", source)
        self.assertNotIn("onclick=\"copyPrompt('\\''+safeId", source)
        self.assertIn("/^P\\d+$/.test(rawId)", source)
        self.assertIn("var sequence=Number(rawId.slice(1))", source)
        self.assertIn("promptSequenceValue(existing)===sequence", source)

    def test_strict_harness_gate_accepts_complete_product_surface(self) -> None:
        validator_path = SCRIPTS / "validate_prompt_kit_order_navigation.py"
        spec = importlib.util.spec_from_file_location("prompt_order_validator", validator_path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.evaluate_repository()
        self.assertEqual(report["implementation_status"], "pass")
        self.assertEqual(report["findings"], [])
        self.assertTrue(all(value == "pass" for value in report["requirement_status"].values()))


if __name__ == "__main__":
    unittest.main()
