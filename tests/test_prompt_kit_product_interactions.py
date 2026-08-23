from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "docs" / "prompt-kit.js"
SITE = ROOT / "web" / "prompt-kit" / "index.html"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-interactions.v1.json"
VALIDATOR = ROOT / "scripts" / "validate_prompt_kit_interactions.py"


class PromptKitProductInteractionTests(unittest.TestCase):
    def test_checked_in_site_contains_current_interaction_and_navigation_source(self) -> None:
        site = SITE.read_text(encoding="utf-8")
        js = JS.read_text(encoding="utf-8")
        self.assertIn(js, site)
        self.assertIn("function appendDistributedPageNavigation", site)
        self.assertIn("function resetPromptKitView", site)

    def test_single_click_copy_is_disambiguated_from_double_click_expand(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("card._copyTimer=setTimeout(function(){copyPrompt(p.id);card._copyTimer=null},300)", js)
        self.assertIn("card.ondblclick=function(e){cancelPromptCardCopy(card)", js)
        self.assertIn("card.onkeydown=function(e){if(e.target!==card)return;if(e.key==='Enter')", js)
        self.assertIn("else if(e.key===' ')", js)

    def test_outside_click_collapses_detail_and_restores_origin_focus(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("promptDetailOrigin=origin||null", js)
        self.assertIn("if(e.target!==this)return;closePromptDetail(false);focusPromptOrigin()", js)
        self.assertIn("function focusPromptOrigin()", js)

    def test_prompt_fields_are_escaped_before_card_or_detail_html(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("function escapePromptHtml(value)", js)
        self.assertIn("safeUseWhen=escapePromptHtml(p.useWhen)", js)
        self.assertIn("safeCopyContent=escapePromptHtml(p.copyContent||'')", js)
        self.assertIn("safeName=escapePromptHtml(p.name)", js)

    def test_repeated_section_headers_have_top_left_and_bottom_right_links(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn('class="page-jump page-jump-top" href="#page-top"', js)
        self.assertIn('class="page-jump page-jump-bottom" href="#page-bottom"', js)
        self.assertIn('aria-label="Go to top of page"', js)
        self.assertIn('aria-label="Go to bottom of page"', js)
        self.assertLess(js.index("page-jump page-jump-top"), js.index("sd-label"))
        divider_region = js[js.index("divider.innerHTML="):js.index("grid.appendChild(divider)")]
        self.assertLess(divider_region.index("page-jump-top"), divider_region.index("sd-label"))
        self.assertGreater(divider_region.index("page-jump-bottom"), divider_region.index("sd-label"))

    def test_category_dividers_are_accessible_expand_collapse_controls(self) -> None:
        js = JS.read_text(encoding="utf-8")
        for marker in (
            "var collapsedSections={};",
            "function isSectionCollapsed(name)",
            "function togglePromptSection(name)",
            'class="sd-label section-toggle"',
            'data-collapse-section="',
            'aria-expanded="',
            "section-chevron",
            "togglePromptSection(collapse.getAttribute('data-collapse-section'))",
        ):
            self.assertIn(marker, js)
        self.assertIn("if(isSectionCollapsed(sectionName))return;", js)
        self.assertIn("orderedPrompts.forEach(function(p)", js)
        self.assertIn("renderedSections={}", js)

    def test_collapse_state_survives_rerenders_and_home_reset_expands_all(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("if(isSectionCollapsed(name)){delete collapsedSections[name]}else{collapsedSections[name]=true}render()", js)
        self.assertIn("activeCat='all';activeSection=null;activeType=null;activeColor=null;activeProfile=null;collapsedSections={};", js)
        self.assertNotIn("collapsedSections={};var groups=groupPromptsBySection", js)

    def test_page_targets_are_stable_unique_runtime_anchors(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("if(!document.getElementById('page-top'))", js)
        self.assertIn("top.id='page-top'", js)
        self.assertIn("if(!document.getElementById('page-bottom'))", js)
        self.assertIn("bottom.id='page-bottom'", js)
        self.assertIn("ensurePageNavigation();", js)

    def test_prompt_cards_remain_keyboard_accessible_without_nested_button_semantics(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("card.tabIndex=0", js)
        self.assertIn("card.setAttribute('role','group')", js)
        self.assertNotIn("card.setAttribute('role','button')", js)

    def test_interaction_contract_is_marked_implemented(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")
        self.assertIn('"implementation_status": "implemented"', text)

    def test_strict_static_interaction_gate_is_green(self) -> None:
        spec = importlib.util.spec_from_file_location("prompt_interactions", VALIDATOR)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.evaluate_repository()
        self.assertEqual(report["implementation_status"], "implemented")
        self.assertEqual(report["missing_markers"], [])


if __name__ == "__main__":
    unittest.main()
