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
    def test_catalog_derived_dispatcher_accepts_numeric_and_p_prefixed_prompt_ids(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        blocks = "\n\n".join(
            function_block(source, name)
            for name in (
                "normalizePromptShortcutId",
                "catalogPromptShortcutBindings",
                "resetPromptShortcutBuffer",
                "schedulePromptShortcutBufferReset",
                "promptShortcutHasLongerPrefix",
                "effectivePromptShortcutBindings",
                "handleConfiguredPromptShortcutKey",
            )
        )
        script = f"""
var PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=25;
var PROMPTS=[{{id:'P01'}},{{id:'P11'}},{{id:'P13'}},{{id:'P111'}},{{id:'P125'}}];
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
  var bindings=catalogPromptShortcutBindings();
  assert(bindings['125']==='P125','numeric P125 binding missing');
  assert(bindings['p125']==='P125','p-prefixed P125 compatibility binding missing');
  assert(bindings['01']==='P01','zero-padded P01 binding missing');

  ['1','2','5'].forEach(press);
  assert(JSON.stringify(activations)==='["P125"]','125 did not activate P125');

  resetProbe();
  ['p','1','2','5'].forEach(press);
  assert(JSON.stringify(activations)==='["P125"]','p125 did not activate P125');

  resetProbe();
  ['0','1'].forEach(press);
  assert(JSON.stringify(activations)==='["P01"]','01 did not preserve zero-padded P01 identity');

  resetProbe();
  ['1','1'].forEach(press);
  assert(activations.length===0,'11 fired before longer-prefix ambiguity closed');
  await sleep(40);
  assert(JSON.stringify(activations)==='["P11"]','11 timeout resolution');

  resetProbe();
  ['1','1','1'].forEach(press);
  assert(JSON.stringify(activations)==='["P111"]','111 longer exact resolution');

  resetProbe();
  ['1','3'].forEach(press);
  assert(JSON.stringify(activations)==='["P13"]','13 exact resolution');

  console.log(JSON.stringify({{status:'PASS',cases:['125','p125','01','11','111','13']}}));
}})().catch(function(error){{console.error(error.stack||error);process.exit(1)}});
"""
        completed = subprocess.run(
            ["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True
        )
        proof = json.loads(completed.stdout)
        self.assertEqual(proof["status"], "PASS")
        self.assertEqual(proof["cases"], ["125", "p125", "01", "11", "111", "13"])

    def test_generated_runtime_contains_exact_catalog_identity_dispatcher(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for name in (
            "normalizePromptShortcutId",
            "catalogPromptShortcutBindings",
            "schedulePromptShortcutBufferReset",
            "promptShortcutHasLongerPrefix",
            "effectivePromptShortcutBindings",
            "handleConfiguredPromptShortcutKey",
        ):
            self.assertEqual(function_block(source, name), function_block(deployed, name))
        for marker in (
            "bindings[digits]=promptId",
            "bindings['p'+digits]=promptId",
            "if(exact&&!promptShortcutHasLongerPrefix(candidate,gestures))",
        ):
            self.assertIn(marker, deployed)

    def test_prompt_identity_is_catalog_owned_not_manual_or_header_owned(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        base = (ROOT / "docs" / "prompt-kit.js").read_text(encoding="utf-8")
        self.assertIn("function catalogPromptShortcutBindings()", source)
        self.assertNotIn("PROMPT_KIT_SHORTCUT_STORAGE_KEY", source)
        self.assertNotIn("function configurePromptShortcut(", source)
        self.assertNotIn("promptShortcutPromptId", source)
        for digit in "12345":
            self.assertNotIn(f"if(key==='{digit}')", source)
            self.assertNotIn(f"case'{digit}'", base)
        for key in "ABCDE":
            self.assertIn(f"{{key:'{key}'", source)


if __name__ == "__main__":
    unittest.main()
