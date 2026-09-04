from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
PROFILES = ROOT / "docs" / "prompt-kit-profiles.js"


def function_block(text: str, name: str) -> str:
    start = text.index(f"function {name}(")
    brace = text.index("{", start)
    depth = 0
    quote = None
    escaped = False
    for index in range(brace, len(text)):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"', "`"):
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise AssertionError(name)


class PromptKitHotkeyHeaderHandoffTests(unittest.TestCase):
    def test_pending_prompt_identity_hands_back_to_header_key(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        blocks = "\n\n".join(function_block(source, name) for name in (
            "resetPromptShortcutBuffer",
            "schedulePromptShortcutBufferReset",
            "promptShortcutHasLongerPrefix",
            "effectivePromptShortcutBindings",
            "handleConfiguredPromptShortcutKey",
        ))
        script = f"""
var PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=25;
var promptShortcutBindings={{p11:'P11',p111:'P111'}};
var sharedPromptShortcutBindings={{}};
var promptShortcutBuffer='';
var promptShortcutBufferTimer=null;
var activations=[];
function activatePromptShortcutTarget(id){{activations.push(id);return true}}
{blocks}
function eventStub(){{return{{preventDefault:function(){{}},stopImmediatePropagation:function(){{}}}}}}
var header=[];
function dispatch(key){{
  var e=eventStub();
  if(promptShortcutBuffer&&handleConfiguredPromptShortcutKey(e,key))return;
  if('abcde'.indexOf(key)!==-1){{header.push(key.toUpperCase());return}}
  handleConfiguredPromptShortcutKey(e,key);
}}
['p','1','1'].forEach(dispatch);dispatch('a');
if(JSON.stringify(activations)!=='["P11"]'||JSON.stringify(header)!=='["A"]')process.exit(1);
resetPromptShortcutBuffer();activations=[];header=[];
['p','1'].forEach(dispatch);dispatch('b');
if(activations.length!==0||JSON.stringify(header)!=='["B"]')process.exit(2);
"""
        subprocess.run(["node", "-e", script], cwd=ROOT, check=True)

    def test_header_keydown_has_one_runtime_owner(self) -> None:
        polish = POLISH.read_text(encoding="utf-8")
        profiles = PROFILES.read_text(encoding="utf-8")
        self.assertNotIn("doc.addEventListener('keydown'", profiles)
        self.assertIn("window.PromptKitProfiles.activateSlot(key.toUpperCase())", polish)

    def test_home_end_own_page_navigation_and_t_is_free(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        self.assertIn("{key:'Home',label:'Scroll to top'}", source)
        self.assertIn("{key:'End',label:'Scroll to bottom'}", source)
        self.assertIn("if(key==='home')", source)
        self.assertIn("if(key==='end')", source)
        self.assertIn("var top=edge==='top'?0:height", source)
        self.assertNotIn("var anchor=document.getElementById(edge==='top'?'page-top':'page-bottom')", source)
        self.assertNotIn("{key:'T',label:'Scroll to top'}", source)
        self.assertNotIn("if(key==='t')", source)


if __name__ == "__main__":
    unittest.main()
