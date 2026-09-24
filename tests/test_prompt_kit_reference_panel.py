from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "docs" / "prompt-kit.js"
REFERENCE = ROOT / "docs" / "reference.json"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"
WEB_README = ROOT / "web" / "README.md"
PHONE_GUIDE = ROOT / "OPEN_PROMPT_KIT_ON_PHONE.md"


class PromptKitReferencePanelTests(unittest.TestCase):
    def test_variables_section_renders_variable_and_meaning_fields(self) -> None:
        js = JS.read_text(encoding="utf-8")
        ref = json.loads(REFERENCE.read_text(encoding="utf-8"))
        sample = ref["variables"][0]
        self.assertIn("variable", sample)
        self.assertIn("meaning", sample)
        self.assertNotIn("name", sample)
        self.assertNotIn("description", sample)

        variables_render = js[js.index("if(REF.variables)") : js.index("if(REF.promptSequence)")]
        self.assertIn("v.variable", variables_render)
        self.assertIn("v.meaning", variables_render)
        self.assertNotIn("v.name", variables_render)
        self.assertNotIn("v.description", variables_render)
        self.assertIn(
            "REF.variables.forEach(function(v){html+='<div class=\"ref-item\"><span class=\"label\">'"
            "+(v.variable||'')+'</span> '+(v.meaning||'')+'</div>'});",
            variables_render,
        )

    def test_reference_prompt_navigation_uses_tap_not_long_press(self) -> None:
        js = JS.read_text(encoding="utf-8")
        build_ref = js[js.index("(function buildRef()") : js.index("})();", js.index("(function buildRef()")) + 5]
        self.assertIn('data-prompt="\'+s.promptId+\'"', build_ref)
        self.assertIn(
            "el.querySelectorAll('.ref-item[data-prompt]').forEach(function(item){"
            "item.addEventListener('click',function(){",
            build_ref,
        )
        self.assertIn("showPromptDetail(pid)", build_ref)
        for gesture in (
            "longpress",
            "long-press",
            "long_press",
            "contextmenu",
            "touchstart",
            "touchend",
            "pointerdown",
            "pointerup",
        ):
            self.assertNotIn(gesture, build_ref.lower())

        for doc in (WEB_README, PHONE_GUIDE):
            text = doc.read_text(encoding="utf-8").lower()
            self.assertIn("long-press", text)
            self.assertIn("not a product gesture", text)

    def test_checked_in_site_contains_reference_variables_fix(self) -> None:
        deployed = DEPLOYED.read_text(encoding="utf-8")
        js = JS.read_text(encoding="utf-8")
        self.assertIn(js, deployed, "checked-in Prompt Kit is stale relative to docs/prompt-kit.js")
        self.assertIn("v.variable", deployed)
        self.assertIn("v.meaning", deployed)
        self.assertNotIn(
            "REF.variables.forEach(function(v){html+='<div class=\"ref-item\"><span class=\"label\">'+v.name+'</span> '+v.description+'</div>'});",
            deployed,
        )


if __name__ == "__main__":
    unittest.main()
