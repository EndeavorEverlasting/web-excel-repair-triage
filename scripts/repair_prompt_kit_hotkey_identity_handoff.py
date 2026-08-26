#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}: {old[:90]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


# Pending exact prompt identity must settle without swallowing an unrelated header/global key.
replace_once(
    "docs/prompt-kit-polish.js",
    """function handleConfiguredPromptShortcutKey(e,key){
  var gestures=Object.keys(promptShortcutBindings);
  if(!gestures.length){resetPromptShortcutBuffer();return false}
  if(key==='.'&&promptShortcutBuffer){e.preventDefault();e.stopImmediatePropagation();schedulePromptShortcutBufferReset();return true}
  if(!/^[a-z0-9]$/.test(key)){resetPromptShortcutBuffer();return false}
  function acceptCandidate(candidate){
    var exact=promptShortcutBindings[candidate];
    var prefix=gestures.some(function(gesture){return gesture.indexOf(candidate)===0});
    if(exact&&!promptShortcutHasLongerPrefix(candidate,gestures)){e.preventDefault();e.stopImmediatePropagation();resetPromptShortcutBuffer();activatePromptShortcutTarget(exact);return true}
    if(prefix){e.preventDefault();e.stopImmediatePropagation();promptShortcutBuffer=candidate;schedulePromptShortcutBufferReset();return true}
    return false
  }
  var candidate=promptShortcutBuffer+key;
  if(acceptCandidate(candidate))return true;
  resetPromptShortcutBuffer();
  return acceptCandidate(key)
}""",
    """function handleConfiguredPromptShortcutKey(e,key){
  var gestures=Object.keys(promptShortcutBindings);
  if(!gestures.length){resetPromptShortcutBuffer();return false}
  if(key==='.'&&promptShortcutBuffer){e.preventDefault();e.stopImmediatePropagation();schedulePromptShortcutBufferReset();return true}
  var pendingExact=promptShortcutBindings[promptShortcutBuffer]||null;
  if(!/^[a-z0-9]$/.test(key)){
    resetPromptShortcutBuffer();
    if(pendingExact)activatePromptShortcutTarget(pendingExact);
    return false
  }
  function acceptCandidate(candidate){
    var exact=promptShortcutBindings[candidate];
    var prefix=gestures.some(function(gesture){return gesture.indexOf(candidate)===0});
    if(exact&&!promptShortcutHasLongerPrefix(candidate,gestures)){e.preventDefault();e.stopImmediatePropagation();resetPromptShortcutBuffer();activatePromptShortcutTarget(exact);return true}
    if(prefix){e.preventDefault();e.stopImmediatePropagation();promptShortcutBuffer=candidate;schedulePromptShortcutBufferReset();return true}
    return false
  }
  var candidate=promptShortcutBuffer+key;
  if(acceptCandidate(candidate))return true;
  resetPromptShortcutBuffer();
  if(pendingExact){activatePromptShortcutTarget(pendingExact);return false}
  return acceptCandidate(key)
}""",
)

# A-E keyboard ownership must be centralized with the prompt-sequence dispatcher.
# The profile runtime still owns slot state/clicks, but cannot pre-empt a pending P11/P111 sequence.
replace_once(
    "docs/prompt-kit-profiles.js",
    """  doc.addEventListener('keydown',function(event){
    var target=event.target;
    var editable=!!(target&&(target.tagName==='INPUT'||target.tagName==='TEXTAREA'||target.tagName==='SELECT'||target.isContentEditable));
    if(editable||event.altKey||event.ctrlKey||event.metaKey)return;
    var key=String(event.key||'').toUpperCase();
    if(SLOT_KEYS.indexOf(key)===-1)return;
    event.preventDefault();event.stopImmediatePropagation();activateSlot(key)
  },true);
""",
    """  // A-E keydown ownership lives in prompt-kit-polish.js so prompt-ID sequences settle before profile navigation.
""",
)
replace_once(
    "docs/prompt-kit-polish.js",
    """    if(key==='escape')resetPromptShortcutBuffer();
    if(promptShortcutBuffer&&handleConfiguredPromptShortcutKey(e,key))return;
    if(key==='f'){e.preventDefault();e.stopImmediatePropagation();toggleCompactFilters();return}
""",
    """    if(key==='escape')resetPromptShortcutBuffer();
    if(promptShortcutBuffer&&handleConfiguredPromptShortcutKey(e,key))return;
    if(/^[a-e]$/.test(key)&&window.PromptKitProfiles&&typeof window.PromptKitProfiles.activateSlot==='function'){
      e.preventDefault();e.stopImmediatePropagation();resetPromptShortcutBuffer();window.PromptKitProfiles.activateSlot(key.toUpperCase());return
    }
    if(key==='f'){e.preventDefault();e.stopImmediatePropagation();toggleCompactFilters();return}
""",
)

# A-E are the complete header namespace. Page navigation uses the native Home/End pair.
replace_once("docs/prompt-kit-polish.js", "{key:'T',label:'Scroll to top'}", "{key:'Home',label:'Scroll to top'}")
replace_once("docs/prompt-kit-polish.js", "if(key==='t'){e.preventDefault();e.stopImmediatePropagation();scrollPromptKitTo('top');return}", "if(key==='home'){e.preventDefault();e.stopImmediatePropagation();scrollPromptKitTo('top');return}")
replace_once("docs/prompt-kit-profiles.js", "['T','Scroll to top']", "['Home','Scroll to top']")
replace_once(
    "docs/prompt-kit-polish.js",
    """function scrollPromptKitTo(edge){
  var anchor=document.getElementById(edge==='top'?'page-top':'page-bottom');
  var behavior=hotkeyScrollBehavior();
  if(anchor&&typeof anchor.scrollIntoView==='function'){
    try{anchor.scrollIntoView({behavior:behavior,block:edge==='top'?'start':'end'});return}catch(e){}
  }
  var height=Math.max(document.documentElement?document.documentElement.scrollHeight:0,document.body?document.body.scrollHeight:0);
  var top=edge==='top'?0:height;
  try{window.scrollTo({top:top,behavior:behavior})}catch(e){window.scrollTo(0,top)}
}""",
    """function scrollPromptKitTo(edge){
  var behavior=hotkeyScrollBehavior();
  var height=Math.max(document.documentElement?document.documentElement.scrollHeight:0,document.body?document.body.scrollHeight:0);
  var top=edge==='top'?0:height;
  try{window.scrollTo({top:top,behavior:behavior})}catch(e){window.scrollTo(0,top)}
}""",
)
replace_once(
    "docs/PROMPT_KIT_FIVE_TAB_PROFILES.md",
    "The former `B` bottom-of-page shortcut moves to `End`; `T` remains the top shortcut.",
    "Page navigation uses the native pair: `Home` scrolls to the true document top and `End` scrolls to the document bottom. No letter in `A`–`E` is reused for page navigation.",
)
replace_once("web/README.md", "| `T` | Scroll to top |", "| `Home` | Scroll to top |")

# Focused static/runtime contract for the agreed namespace.
header_test = ROOT / "tests" / "test_prompt_kit_header_contract.py"
text = header_test.read_text(encoding="utf-8")
text = text.replace(
    "def test_effective_hotkey_help_uses_profile_slots_and_end_for_bottom() -> None:\n",
    "def test_effective_hotkey_help_uses_profile_slots_and_home_end_navigation() -> None:\n",
    1,
)
old = """    assert "['End','Scroll to bottom']" in profiles
    assert "{key:'End',label:'Scroll to bottom'}" in polish
    assert "{key:'B',label:'Scroll to bottom'}" not in polish
"""
new = """    assert "['Home','Scroll to top']" in profiles
    assert "['End','Scroll to bottom']" in profiles
    assert "{key:'Home',label:'Scroll to top'}" in polish
    assert "{key:'End',label:'Scroll to bottom'}" in polish
    assert "{key:'T',label:'Scroll to top'}" not in polish
    assert "{key:'B',label:'Scroll to bottom'}" not in polish
    assert "if(key==='home')" in polish
    assert "if(key==='end')" in polish
    assert "var top=edge==='top'?0:height" in polish
    assert "doc.addEventListener('keydown'" not in profiles
    assert "window.PromptKitProfiles.activateSlot(key.toUpperCase())" in polish
"""
if text.count(old) != 1:
    raise SystemExit("header contract Home/End assertion block drifted")
text = text.replace(old, new, 1)
text = text.replace(
    "assert \"| `End` | Scroll to bottom |\" in text\n",
    "assert \"| `Home` | Scroll to top |\" in text\n    assert \"| `End` | Scroll to bottom |\" in text\n    assert \"| `T` | Scroll to top |\" not in text\n",
    1,
)
text = text.replace(
    "test_effective_hotkey_help_uses_profile_slots_and_end_for_bottom,",
    "test_effective_hotkey_help_uses_profile_slots_and_home_end_navigation,",
    1,
)
header_test.write_text(text, encoding="utf-8")

# Browser proof: wait for the asynchronous clipboard promise to settle between scenarios,
# then prove prompt-prefix handoff and true document-edge Home/End behavior.
browser = ROOT / "tests" / "prompt_kit_hotkey_identity_browser_proof.py"
text = browser.read_text(encoding="utf-8")
if "import time\n" not in text:
    if text.count("import threading\n") != 1:
        raise SystemExit("browser proof import anchor drifted")
    text = text.replace("import threading\n", "import threading\nimport time\n", 1)
marker = """            # Numeric input must never activate A-E header slots.
            active_slot = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")
"""
insert = """            # A pending shorter exact identity settles before the same key continues to A-E header navigation.
            set_clipboard("sentinel-p11-a")
            press("p11")
            page.keyboard.press("a")
            deadline = time.monotonic() + 1.5
            p11_then_a = clipboard()
            while p11_then_a != expected["P11"] and time.monotonic() < deadline:
                page.wait_for_timeout(25)
                p11_then_a = clipboard()
            slot_after_a = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")
            observations.append({
                "id": "pending_p11_hands_off_to_header_a",
                "event": "A settles pending P11 and still activates the All profile",
                "occurred": True,
                "passed": p11_then_a == expected["P11"] and slot_after_a == "A",
                "prompt_matches": p11_then_a == expected["P11"],
                "active_slot": slot_after_a,
            })

            set_clipboard("sentinel-p1-b")
            press("p1")
            page.keyboard.press("b")
            page.wait_for_timeout(250)
            p1_then_b = clipboard()
            slot_after_b = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")
            observations.append({
                "id": "incomplete_prefix_hands_off_to_header_b",
                "event": "B abandons incomplete p1 without firing a prompt and activates Standard",
                "occurred": True,
                "passed": p1_then_b == "sentinel-p1-b" and slot_after_b == "B",
                "clipboard_unchanged": p1_then_b == "sentinel-p1-b",
                "active_slot": slot_after_b,
            })

            # Home/End are page navigation only and do not alter the header/profile namespace.
            page.keyboard.press("End")
            deadline = time.monotonic() + 1.0
            max_scroll = page.evaluate("Math.max(0, document.documentElement.scrollHeight - window.innerHeight)")
            end_y = page.evaluate("window.scrollY")
            while end_y < max_scroll - 2 and time.monotonic() < deadline:
                page.wait_for_timeout(20)
                max_scroll = page.evaluate("Math.max(0, document.documentElement.scrollHeight - window.innerHeight)")
                end_y = page.evaluate("window.scrollY")
            end_slot = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")
            page.keyboard.press("Home")
            deadline = time.monotonic() + 1.0
            home_y = page.evaluate("window.scrollY")
            while home_y > 2 and time.monotonic() < deadline:
                page.wait_for_timeout(20)
                home_y = page.evaluate("window.scrollY")
            home_slot = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")
            observations.append({
                "id": "home_end_page_navigation",
                "event": "End reaches the document bottom and Home returns to the true top without changing the active profile",
                "occurred": True,
                "passed": end_y >= max_scroll - 2 and home_y <= 2 and end_slot == "B" and home_slot == "B",
                "end_y": end_y,
                "max_scroll": max_scroll,
                "home_y": home_y,
                "end_slot": end_slot,
                "home_slot": home_slot,
            })
            page.keyboard.press("a")
            page.wait_for_timeout(50)

            # Numeric input must never activate A-E header slots.
            active_slot = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")
"""
if text.count(marker) != 1:
    raise SystemExit("browser identity handoff marker drifted")
browser.write_text(text.replace(marker, insert, 1), encoding="utf-8")

# Dedicated production-function runtime regression for exact-prefix handoff and namespace ownership.
runtime = ROOT / "tests" / "test_prompt_kit_hotkey_header_handoff.py"
runtime.write_text(r'''from __future__ import annotations

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
            "handleConfiguredPromptShortcutKey",
        ))
        script = f"""
var PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=25;
var promptShortcutBindings={{p11:'P11',p111:'P111'}};
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
''', encoding="utf-8")
