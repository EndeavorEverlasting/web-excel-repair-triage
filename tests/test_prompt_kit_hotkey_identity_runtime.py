from __future__ import annotations

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
                "effectivePromptShortcutBindings",
                "handleConfiguredPromptShortcutKey",
            )
        )
        script = f"""
var PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=25;
var promptShortcutBindings={{p11:'P11',p13:'P13',p111:'P111'}};
var sharedPromptShortcutBindings={{}};
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
            "computeSharedPromptShortcutBindings",
            "effectivePromptShortcutBindings",
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
