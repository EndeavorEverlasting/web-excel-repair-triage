from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_prompt_kit_interactions as interactions


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


class PromptKitInteractionHarnessTests(unittest.TestCase):
    def test_contract_is_complete_and_versioned(self) -> None:
        contract = interactions.validate_contract()
        self.assertEqual(contract["schema_version"], "prompt-kit-interaction-contract/v1")
        self.assertEqual(contract["contract_id"], "prompt-kit-card-interactions")
        self.assertEqual(
            {item["id"] for item in contract["requirements"]},
            interactions.REQUIRED_REQUIREMENT_IDS,
        )
        self.assertIn("--require-implementation", contract["validation"]["implementation_gate"])

    def test_current_source_audit_is_structured_without_inflating_proof(self) -> None:
        report = interactions.audit_implementation()
        self.assertEqual(report["schema_version"], "prompt-kit-interaction-audit-result/v1")
        self.assertEqual(
            {item["id"] for item in report["requirements"]},
            interactions.REQUIRED_REQUIREMENT_IDS,
        )
        self.assertIn("implementation_ready", report)
        self.assertIn("missing_static_markers", report)
        self.assertIn("does not prove", report["proof_ceiling"].lower())

    def test_synthetic_compliant_source_satisfies_static_gate(self) -> None:
        js = """
        card.onclick=function(e){copyPrompt(p.id)};
        card.ondblclick=function(e){e.preventDefault();showPromptDetail(p.id)};
        document.getElementById('promptDetailOverlay').addEventListener('click',function(e){
          if(e.target===this){closePromptDetail();document.getElementById('grid').focus()}
        });
        btn.onclick=function(e){e.stopPropagation();copyPrompt(p.id)};
        document.addEventListener('keydown',function(e){
          switch(e.key){case'Escape':if(document.getElementById('promptDetailOverlay').classList.contains('open')){closePromptDetail();return}}
        });
        """
        checks = interactions.evaluate_source(js)
        self.assertEqual(set(checks), interactions.REQUIRED_REQUIREMENT_IDS)
        self.assertTrue(all(checks.values()), checks)

    def test_legacy_single_click_expand_is_detected_as_gap(self) -> None:
        js = """
        card.onclick=function(){showPromptDetail(p.id)};
        btn.onclick=function(e){e.stopPropagation();copyPrompt(p.id)};
        document.addEventListener('keydown',function(e){
          switch(e.key){case'Escape':if(document.getElementById('promptDetailOverlay').classList.contains('open')){closePromptDetail();return}}
        });
        """
        checks = interactions.evaluate_source(js)
        self.assertFalse(checks["single_click_copy"])
        self.assertFalse(checks["double_click_expand"])
        self.assertFalse(checks["outside_click_collapse_restore"])
        self.assertTrue(checks["escape_close_preserved"])
        self.assertTrue(checks["copy_button_compatibility"])

    def test_catalog_derived_prompt_hotkeys_resolve_numeric_identity_and_prefixes(self) -> None:
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
  console.log('PASS');
}})().catch(function(error){{console.error(error.stack||error);process.exit(1)}});
"""
        completed = subprocess.run(
            ["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True
        )
        self.assertEqual(completed.stdout.strip(), "PASS")
        self.assertIn("bindings[digits]=promptId", source)
        self.assertIn("bindings['p'+digits]=promptId", source)
        self.assertNotIn("PROMPT_KIT_SHORTCUT_STORAGE_KEY", source)
        self.assertNotIn("function configurePromptShortcut(", source)
        self.assertNotIn("promptShortcutPromptId", source)

    def test_harness_mode_writes_report_without_requiring_product_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "interaction-audit.json"
            rc = interactions.main(["--output", str(output)])
            self.assertEqual(rc, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["contract_id"], "prompt-kit-card-interactions")


if __name__ == "__main__":
    unittest.main()
