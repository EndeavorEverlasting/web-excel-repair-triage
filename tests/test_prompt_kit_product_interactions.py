from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_prompt_kit_interactions as interactions

JS = ROOT / "docs" / "prompt-kit.js"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-interactions.v1.json"


class PromptKitProductInteractionTests(unittest.TestCase):
    def test_interaction_contract_is_marked_implemented(self) -> None:
        payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "implemented")
        self.assertEqual(
            {item["id"] for item in payload["requirements"]},
            interactions.REQUIRED_REQUIREMENT_IDS,
        )

    def test_strict_static_interaction_gate_is_green(self) -> None:
        report = interactions.audit_implementation()
        self.assertTrue(report["implementation_ready"], report["missing_static_markers"])
        self.assertEqual(report["missing_static_markers"], [])

    def test_single_click_copy_is_disambiguated_from_double_click_expand(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("if(e.target.closest&&e.target.closest('button'))return", js)
        self.assertIn("selectPrompt(p.id,'pointer');cancelPromptCardCopy(card)", js)
        self.assertIn("card._copyTimer=setTimeout(function(){copyPrompt(p.id);card._copyTimer=null},160)", js)
        self.assertIn(
            "card.ondblclick=function(e){cancelPromptCardCopy(card);e.preventDefault();selectPrompt(p.id,'pointer');showPromptDetail(p.id,card)};",
            js,
        )
        self.assertIn("function cancelPromptCardCopy(card)", js)

    def test_outside_click_collapses_detail_and_restores_origin_focus(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("function focusPromptOrigin()", js)
        self.assertIn(
            "document.getElementById('promptDetailOverlay').addEventListener('click',function(e){if(e.target!==this)return;closePromptDetail(false);focusPromptOrigin()});",
            js,
        )
        self.assertIn(
            "case'Escape':if(document.getElementById('promptDetailOverlay').classList.contains('open')){closePromptDetail();return}",
            js,
        )

    def test_repeated_section_headers_have_top_left_and_bottom_right_links(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn('href="#page-top"', js)
        self.assertIn('href="#page-bottom"', js)
        self.assertIn("page-jump page-jump-top", js)
        self.assertIn("page-jump page-jump-bottom", js)
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
        self.assertIn("activeCat='all';activeSection=null;activeType=null;activeColor=null;collapsedSections={};", js)
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
        self.assertIn("card.tabIndex=isRoving?0:-1", js)
        self.assertIn("card.setAttribute('role','option')", js)
        self.assertIn("card.setAttribute('aria-selected',String(isSelected))", js)
        self.assertNotIn("card.setAttribute('role','button')", js)
        self.assertIn("Double-click or press Enter to inspect", js)
        self.assertIn("if(e.key==='Enter')", js)
        self.assertIn("showPromptDetail(p.id,card)", js)
        self.assertIn("else if(e.key===' ')", js)
        self.assertIn("copyPrompt(p.id)", js)
        self.assertIn("openBtn.className='prompt-open-btn'", js)
        self.assertIn("btn.className='prompt-copy-btn'", js)

    def test_prompt_fields_are_escaped_before_card_or_detail_html(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("function escapePromptHtml(value)", js)
        self.assertIn("safeName=escapePromptHtml(p.name)", js)
        self.assertIn("safeUseWhen=escapePromptHtml(p.useWhen)", js)
        self.assertIn("safeCopyContent=escapePromptHtml(p.copyContent||'')", js)
        self.assertIn("safeProofGate=escapePromptHtml(p.proofGate)", js)
        self.assertIn("safeName+'</span>", js)
        self.assertIn("safeUseWhen+'</pre>", js)

    def test_detail_panel_click_copy_is_safe_and_conflict_aware(self) -> None:
        js = JS.read_text(encoding="utf-8")
        for marker in (
            "function handlePromptDetailSurfaceCopy(e)",
            "function isPromptDetailCopyConflict(target)",
            "function promptDetailHasTextSelection()",
            "function cancelPromptDetailSurfaceCopy()",
            "copyPrompt(openPromptId)",
            "[data-prompt-detail-no-copy]",
            "if(e.detail&&e.detail>1)return",
            "el.onclick=handlePromptDetailSurfaceCopy",
            "el.ondblclick=cancelPromptDetailSurfaceCopy",
            "el.setAttribute('role','dialog')",
            "el.setAttribute('aria-modal','true')",
        ):
            self.assertIn(marker, js)

    def test_detail_panel_has_local_edge_controls_and_home_end_hotkeys(self) -> None:
        js = JS.read_text(encoding="utf-8")
        for marker in (
            "function scrollPromptDetailTo(edge)",
            "id=\"promptDetailTop\"",
            "id=\"promptDetailBottom\"",
            "Home/End jump",
            "aria-keyshortcuts=\"Home\"",
            "aria-keyshortcuts=\"End\"",
            "function handlePromptDetailKeydown(e)",
            "e.key==='Home'||e.key==='End'",
            "scrollPromptDetailTo(e.key==='Home'?'top':'bottom')",
            "el.onkeydown=handlePromptDetailKeydown",
        ):
            self.assertIn(marker, js)
        self.assertIn("tag==='INPUT'||tag==='TEXTAREA'||tag==='SELECT'", js)
        self.assertIn("if(e.key==='Escape')", js)

    def test_checked_in_site_contains_current_interaction_and_navigation_source(self) -> None:
        deployed = DEPLOYED.read_text(encoding="utf-8")
        js = JS.read_text(encoding="utf-8")
        self.assertIn(js, deployed, "checked-in Prompt Kit is stale relative to docs/prompt-kit.js")
        for marker in (
            "card.ondblclick=function(e)",
            'href="#page-top"',
            'href="#page-bottom"',
            "promptDetailOverlay').addEventListener('click'",
            "section-toggle",
            "collapsedSections",
        ):
            self.assertIn(marker, deployed)


if __name__ == "__main__":
    unittest.main()
