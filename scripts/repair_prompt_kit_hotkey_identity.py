#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "docs/prompt-kit-polish.js",
    "function normalizePromptShortcutId(raw){\n  var value=String(raw||'').trim().toUpperCase();\n  return /^P\\d+$/.test(value)?value:null\n}",
    "function normalizePromptShortcutId(raw){\n  var value=String(raw||'').trim().toUpperCase().replace(/\\./g,'');\n  return /^P\\d+$/.test(value)?value:null\n}",
)

replace_once(
    "docs/prompt-kit-polish.js",
    "function schedulePromptShortcutBufferReset(){\n  if(promptShortcutBufferTimer)clearTimeout(promptShortcutBufferTimer);\n  promptShortcutBufferTimer=setTimeout(resetPromptShortcutBuffer,PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS)\n}",
    "function schedulePromptShortcutBufferReset(){\n  if(promptShortcutBufferTimer)clearTimeout(promptShortcutBufferTimer);\n  promptShortcutBufferTimer=setTimeout(function(){\n    var exact=promptShortcutBindings[promptShortcutBuffer];\n    resetPromptShortcutBuffer();\n    if(exact)activatePromptShortcutTarget(exact)\n  },PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS)\n}\n\nfunction promptShortcutHasLongerPrefix(candidate,gestures){\n  return gestures.some(function(gesture){return gesture!==candidate&&gesture.indexOf(candidate)===0})\n}",
)

replace_once(
    "docs/prompt-kit-polish.js",
    "function handleConfiguredPromptShortcutKey(e,key){\n  if(!/^[a-z0-9]$/.test(key)){resetPromptShortcutBuffer();return false}\n  var gestures=Object.keys(promptShortcutBindings);\n  if(!gestures.length){resetPromptShortcutBuffer();return false}\n  var candidate=promptShortcutBuffer+key;\n  var exact=promptShortcutBindings[candidate];\n  if(exact){e.preventDefault();e.stopImmediatePropagation();resetPromptShortcutBuffer();activatePromptShortcutTarget(exact);return true}\n  var prefix=gestures.some(function(gesture){return gesture.indexOf(candidate)===0});\n  if(prefix){e.preventDefault();e.stopImmediatePropagation();promptShortcutBuffer=candidate;schedulePromptShortcutBufferReset();return true}\n  resetPromptShortcutBuffer();\n  candidate=key;\n  exact=promptShortcutBindings[candidate];\n  if(exact){e.preventDefault();e.stopImmediatePropagation();activatePromptShortcutTarget(exact);return true}\n  prefix=gestures.some(function(gesture){return gesture.indexOf(candidate)===0});\n  if(prefix){e.preventDefault();e.stopImmediatePropagation();promptShortcutBuffer=candidate;schedulePromptShortcutBufferReset();return true}\n  return false\n}",
    "function handleConfiguredPromptShortcutKey(e,key){\n  var gestures=Object.keys(promptShortcutBindings);\n  if(!gestures.length){resetPromptShortcutBuffer();return false}\n  if(key==='.'&&promptShortcutBuffer){e.preventDefault();e.stopImmediatePropagation();schedulePromptShortcutBufferReset();return true}\n  if(!/^[a-z0-9]$/.test(key)){resetPromptShortcutBuffer();return false}\n  function acceptCandidate(candidate){\n    var exact=promptShortcutBindings[candidate];\n    var prefix=gestures.some(function(gesture){return gesture.indexOf(candidate)===0});\n    if(exact&&!promptShortcutHasLongerPrefix(candidate,gestures)){e.preventDefault();e.stopImmediatePropagation();resetPromptShortcutBuffer();activatePromptShortcutTarget(exact);return true}\n    if(prefix){e.preventDefault();e.stopImmediatePropagation();promptShortcutBuffer=candidate;schedulePromptShortcutBufferReset();return true}\n    return false\n  }\n  var candidate=promptShortcutBuffer+key;\n  if(acceptCandidate(candidate))return true;\n  resetPromptShortcutBuffer();\n  return acceptCandidate(key)\n}",
)

replace_once(
    "docs/PROMPT_KIT_FIVE_TAB_PROFILES.md",
    "`A` through `E` are reserved for the five profile tabs. Header navigation uses no numeric shortcut and\nno header shortcut uses `P`. Digits remain available to configured prompt-ID sequences such as `P111`.\nThe former `B` bottom-of-page shortcut moves to `End`; `T` remains the top shortcut.",
    "`A` through `E` are reserved for the five profile tabs. Header navigation uses no numeric shortcut and\nno header shortcut uses `P`. Digits remain available to configured prompt-ID sequences such as `P111`.\nWhen one configured prompt ID is a prefix of another (for example `P11` and `P111`), the shorter exact\nmatch waits for the existing 1.2-second sequence boundary; continued typing selects the longer match.\nDots are accepted only as separators inside an active prompt sequence, so `p1.1` resolves as `P11` and\n`p1.11` resolves as `P111`. The former `B` bottom-of-page shortcut moves to `End`; `T` remains the top shortcut.",
)

replace_once(
    "docs/PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md",
    "## Success call stack: `p95`\nStarting state: `P95` exists and `p95 → OPEN_PROMPT(P95)` is configured.\n\n`p` → dispatcher buffers `p` → no external side effect\n\n`9` → dispatcher buffers `p9` → no external side effect\n\n`5` → exact binding resolves → `PromptNavigator.openPrompt('P95')` → buffer clears → result/trace returns.\n\nExact prompt identifiers therefore use the normal binding path; they do not require a second global search/router implementation.",
    "## Success call stack: prompt identities\nStarting state: `P11`, `P13`, and `P111` exist and their canonical lower-case sequences are configured.\n\n`p13` → exact non-prefix binding resolves immediately → `PromptNavigator.openPrompt('P13')`.\n\n`p11` → exact binding is also a prefix of `p111` → dispatcher holds the candidate → the existing\n1.2-second boundary expires with no continuation → `PromptNavigator.openPrompt('P11')`.\n\n`p111` → the buffered `p11` candidate receives the final `1` before timeout → the longer exact binding\nresolves → the pending shorter match is cancelled → `PromptNavigator.openPrompt('P111')`.\n\nDots are visual separators, not identity characters, while a prompt sequence is active: `p1.1` follows\nthe `P11` path and `p1.11` follows the `P111` path. Exact prompt identifiers therefore use the normal\nbinding path; they do not require a second global search/router implementation.",
)

replace_once(
    "docs/PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md",
    "- when a prompt-ID buffer is active, that sequence gets first chance to consume later digits such as `1`, `4`, or `5`; built-in digit navigation retains priority only when no configured sequence is in progress.",
    "- header navigation is letter-only (`A`–`E`), so digits never double as header commands; when one configured prompt ID prefixes another, the dispatcher delays the shorter exact match until the sequence boundary or a longer exact match resolves.",
)

readme = ROOT / "web/README.md"
text = readme.read_text(encoding="utf-8")
old = "Favorite-prompt shortcuts are configured from the Hotkeys panel. Favorite a prompt first, enter its canonical ID such as `P95`, and save it; the persisted binding is then the lower-case prompt ID (`p95`). Typed prompt sequences expire after 1.2 seconds and are ignored in editable fields. Completing a configured sequence clears the transient restrictions needed to reveal the target, scrolls the canonical prompt card into view, and copies the canonical prompt through the normal copy path **without opening prompt detail**. The Hotkeys panel labels configured rows as **Copy + reveal P##**."
new = "Favorite-prompt shortcuts are configured from the Hotkeys panel. Favorite a prompt first, enter its canonical ID such as `P95`, and save it; the persisted binding is then the lower-case prompt ID (`p95`). Typed prompt sequences expire after 1.2 seconds and are ignored in editable fields. If one configured ID prefixes another, the shorter exact match waits for that boundary and continued typing selects the longer exact ID. Dots may be typed as separators inside an active sequence (`p1.1` → `P11`, `p1.11` → `P111`). Completing a configured sequence clears the transient restrictions needed to reveal the target, scrolls the canonical prompt card into view, and copies the canonical prompt through the normal copy path **without opening prompt detail**. The Hotkeys panel labels configured rows as **Copy + reveal P##**."
if text.count(old) != 1:
    raise SystemExit("web/README.md: prompt sequence paragraph drifted")
text = text.replace(old, new, 1)
old_header = "### Header navigation contract\n\nThe first three library-view filters are fixed and ordered:\n\n1. All\n2. Standard\n3. GNHF\n\nTheir keyboard shortcuts are `1`, `2`, and `3` respectively. The generated base header still carries Doctrine's legacy `4` label before supplemental runtime enhancement. The supplemental polish runtime assigns `4` to Favorites and remaps Doctrine to `5`; the visible Hotkeys module and effective dispatcher must remain aligned without displacing GNHF."
new_header = "### Header navigation contract\n\nThe five visible profile slots have stable letter identities: `A` All, `B` Standard, `C` Favorites, `D` SAS, and `E` PM by default. Their labels/profile packs may be customized without changing those key identities. Header navigation has no numeric shortcuts and does not reserve `P`, leaving digit-bearing prompt sequences such as `p11`, `p13`, and `p111` exclusively to the prompt shortcut dispatcher."
if text.count(old_header) != 1:
    raise SystemExit("web/README.md: stale numeric header contract not found exactly once")
readme.write_text(text.replace(old_header, new_header, 1), encoding="utf-8")

runtime_test = ROOT / "tests" / "test_prompt_kit_hotkey_identity_runtime.py"
runtime_test.write_text(r'''from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"


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
    raise AssertionError(f"unterminated JavaScript function: {name}")


class PromptKitHotkeyIdentityRuntimeTests(unittest.TestCase):
    def test_production_dispatcher_distinguishes_prefix_and_dotted_prompt_ids(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        blocks = "\n\n".join(
            function_block(source, name)
            for name in (
                "normalizePromptShortcutId",
                "resetPromptShortcutBuffer",
                "schedulePromptShortcutBufferReset",
                "promptShortcutHasLongerPrefix",
                "handleConfiguredPromptShortcutKey",
            )
        )
        script = f"""
var PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=25;
var promptShortcutBindings={{p11:'P11',p13:'P13',p111:'P111'}};
var promptShortcutBuffer='';
var promptShortcutBufferTimer=null;
var activations=[];
function activatePromptShortcutTarget(promptId){{activations.push(promptId);return true}}
{blocks}
function eventStub(){{return{{preventDefault:function(){{}},stopImmediatePropagation:function(){{}}}}}}
function press(key){{return handleConfiguredPromptShortcutKey(eventStub(),key)}}
function resetProbe(){{resetPromptShortcutBuffer();activations=[]}}
function sleep(ms){{return new Promise(function(resolve){{setTimeout(resolve,ms)}})}}
function assert(condition,message){{if(!condition)throw new Error(message)}}
(async function(){{
  assert(normalizePromptShortcutId('p1.1')==='P11','p1.1 normalization');
  assert(normalizePromptShortcutId('p1.11')==='P111','p1.11 normalization');

  ['p','1','1'].forEach(press);
  assert(activations.length===0,'p11 fired before longer-prefix ambiguity closed');
  await sleep(40);
  assert(JSON.stringify(activations)==='["P11"]','p11 timeout resolution');

  resetProbe();
  ['p','1','3'].forEach(press);
  assert(JSON.stringify(activations)==='["P13"]','p13 exact resolution');

  resetProbe();
  ['p','1','1','1'].forEach(press);
  assert(JSON.stringify(activations)==='["P111"]','p111 longer exact resolution');

  resetProbe();
  ['p','1','.','1'].forEach(press);
  assert(activations.length===0,'p1.1 fired before longer-prefix ambiguity closed');
  await sleep(40);
  assert(JSON.stringify(activations)==='["P11"]','p1.1 dotted timeout resolution');

  resetProbe();
  ['p','1','.','1','1'].forEach(press);
  assert(JSON.stringify(activations)==='["P111"]','p1.11 dotted longer resolution');

  console.log(JSON.stringify({{status:'PASS',cases:['p11','p13','p111','p1.1','p1.11']}}));
}})().catch(function(error){{console.error(error.stack||error);process.exit(1)}});
"""
        completed = subprocess.run(
            ["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True
        )
        proof = json.loads(completed.stdout)
        self.assertEqual(proof["status"], "PASS")
        self.assertEqual(proof["cases"], ["p11", "p13", "p111", "p1.1", "p1.11"])

    def test_generated_runtime_contains_exact_identity_dispatcher(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for name in (
            "normalizePromptShortcutId",
            "schedulePromptShortcutBufferReset",
            "promptShortcutHasLongerPrefix",
            "handleConfiguredPromptShortcutKey",
        ):
            self.assertEqual(function_block(source, name), function_block(deployed, name))
        for marker in (
            "replace(/\\./g,'')",
            "if(key==='.'&&promptShortcutBuffer)",
            "if(exact&&!promptShortcutHasLongerPrefix(candidate,gestures))",
        ):
            self.assertIn(marker, deployed)

    def test_header_and_prompt_identity_domains_do_not_overlap(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        base = (ROOT / "docs" / "prompt-kit.js").read_text(encoding="utf-8")
        for digit in "12345":
            self.assertNotIn(f"if(key==='{digit}')", source)
            self.assertNotIn(f"case'{digit}'", base)
        for key in "ABCDE":
            self.assertIn(f"{{key:'{key}'", source)


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")
