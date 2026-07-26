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
        self.assertRegex(
            js,
            re.compile(
                r"card\.onclick=function\(e\)\{cancelPromptCardCopy\(card\);"
                r"card\._copyTimer=setTimeout\(function\(\)\{copyPrompt\(p\.id\);"
                r"card\._copyTimer=null\},300\)\};"
            ),
        )
        self.assertIn(
            "card.ondblclick=function(e){cancelPromptCardCopy(card);e.preventDefault();showPromptDetail(p.id,card)};",
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
        self.assertIn("Double-click or press Enter to expand", js)
        handler = (
            "card.onkeydown=function(e){if(e.target!==card)return;"
            "if(e.key==='Enter'){cancelPromptCardCopy(card);e.preventDefault();e.stopPropagation();"
            "showPromptDetail(p.id,card)}else if(e.key===' '){cancelPromptCardCopy(card);"
            "e.preventDefault();e.stopPropagation();copyPrompt(p.id)}};"
        )
        self.assertIn(handler, js)
        self.assertIn("openBtn.className='prompt-open-btn'", js)
        self.assertIn("btn.className='prompt-copy-btn'", js)
        self.assertIn("return;default:return}", js)

    def test_prompt_fields_are_escaped_before_card_or_detail_html(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("function escapePromptHtml(value)", js)
        self.assertIn("safeName=escapePromptHtml(p.name)", js)
        self.assertIn("safeUseWhen=escapePromptHtml(p.useWhen)", js)
        self.assertIn("safeCopyContent=escapePromptHtml(p.copyContent||'')", js)
        self.assertIn("safeProofGate=escapePromptHtml(p.proofGate)", js)
        self.assertIn("safeName+'</span>", js)
        self.assertIn("safeUseWhen+'</pre>", js)

    def test_checked_in_site_contains_current_interaction_and_navigation_source(self) -> None:
        deployed = DEPLOYED.read_text(encoding="utf-8")
        js = JS.read_text(encoding="utf-8")
        self.assertIn(js, deployed, "checked-in Prompt Kit is stale relative to docs/prompt-kit.js")
        for marker in (
            "card.ondblclick=function(e)",
            'href="#page-top"',
            'href="#page-bottom"',
            "promptDetailOverlay').addEventListener('click'",
        ):
            self.assertIn(marker, deployed)


if __name__ == "__main__":
    unittest.main()
