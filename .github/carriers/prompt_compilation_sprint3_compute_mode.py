#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading

ROOT = Path(__file__).resolve().parents[2]
BRANCH = "feat/prompt-compilation-sprint3-compute-mode-20260916"
WORKFLOW = ".github/workflows/prompt-compilation-sprint3-compute-mode.yml"
CARRIER = ".github/carriers/prompt_compilation_sprint3_compute_mode.py"


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected exactly one replacement target, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def write_new(path: str, content: str) -> None:
    target = ROOT / path
    if target.exists():
        raise RuntimeError(f"refusing to overwrite existing new artifact: {path}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


COMPUTE_EXTENSION = r'''

/* Prompt Compilation Sprint 3: parity-locked Compute Mode product projection. */
(function(root){
'use strict';
var api=(typeof module!=='undefined'&&module.exports)?module.exports:(root&&root.PromptKitProfiles);
if(!api)return;
var COMPUTE_MODE_SCHEMA='prompt-kit-compute-mode/v1';
var LANGUAGE_ENGINE_REVISION='prompt-language-compiler/v1.0.0';
var PRODUCT_DEFAULT_COMPUTE_MODE='exhaustive';
var COMPUTE_MODE_STORAGE_KEYS=Object.freeze({
  userDefault:'promptKit.computeMode.v1',
  promptOverrides:'promptKit.computeModeOverrides.v1'
});
var COMPUTE_MODE_PRECEDENCE=Object.freeze(['explicit_run_override','prompt_override','user_default','product_default']);
var NON_WEAKENABLE=Object.freeze(['destructive_operation_rules','evidence_truth','explicit_user_scope','privacy','required_acceptance_gates','safety']);
var COMPUTE_PROFILES=Object.freeze({
  exhaustive:Object.freeze({
    profile:'exhaustive',
    compute_policy:'maximize_useful_compute_until_fixed_point',
    parallel_policy:'dispatch_when_safe_parallel_width_exists',
    hypothesis_policy:'falsify_material_alternatives',
    validation_policy:'advance_all_executable_contracts',
    stop_policy:'evidence_defined_fixed_point'
  }),
  efficient:Object.freeze({
    profile:'efficient',
    compute_policy:'minimum_sufficient_compute',
    parallel_policy:'parallelize_when_expected_gain_exceeds_coordination_cost',
    hypothesis_policy:'test_alternatives_only_when_materially_ambiguous',
    validation_policy:'minimum_authoritative_acceptance_set',
    stop_policy:'sufficient_proof_for_requested_scope'
  })
});
function normalizeComputeMode(value){
  var mode=String(value||'').trim().toLowerCase();
  return Object.prototype.hasOwnProperty.call(COMPUTE_PROFILES,mode)?mode:null
}
function resolveComputeMode(options){
  options=options||{};
  var candidates=[
    ['explicit_run_override',options.explicitRunOverride],
    ['prompt_override',options.promptOverride],
    ['user_default',options.userDefault],
    ['product_default',options.productDefault||PRODUCT_DEFAULT_COMPUTE_MODE]
  ];
  for(var i=0;i<candidates.length;i++){
    var mode=normalizeComputeMode(candidates[i][1]);
    if(mode)return{mode:mode,source:candidates[i][0]}
  }
  return{mode:PRODUCT_DEFAULT_COMPUTE_MODE,source:'product_default'}
}
function renderComputeDirective(mode){
  mode=normalizeComputeMode(mode)||PRODUCT_DEFAULT_COMPUTE_MODE;
  var profile=COMPUTE_PROFILES[mode];
  var guidance=mode==='exhaustive'
    ? 'For compute-depth behavior only, this profile supersedes default compute-depth clauses. Exhaust safe decision-relevant compute until an evidence-backed fixed point or exact blocker. When at least two meaningful independent lanes and safe usable capacity exist, MUST dispatch independent lanes in parallel; considering or describing parallelism is not execution evidence.'
    : 'For compute-depth behavior only, this profile supersedes default compute-depth clauses. Use minimum sufficient compute to satisfy requested scope and every required proof and acceptance gate. Parallelize when expected critical-path benefit exceeds coordination cost; otherwise use the shortest dependency-safe serial path.';
  return [
    'EXECUTION PROFILE: '+mode.toUpperCase(),
    'Compute policy: '+profile.compute_policy,
    'Parallel policy: '+profile.parallel_policy,
    'Stop policy: '+profile.stop_policy,
    guidance,
    'Non-weakenable constraints: '+NON_WEAKENABLE.join(', '),
    'Compiler policy: '+LANGUAGE_ENGINE_REVISION
  ].join('\n')
}
function composeEffectivePrompt(prompt,mode){
  if(!prompt||typeof prompt.copyContent!=='string'||!prompt.copyContent.trim())return'';
  return renderComputeDirective(mode)+'\n\n'+prompt.copyContent
}
function installComputeMode(root){
  if(root.__promptKitComputeModeInstalled)return api;
  root.__promptKitComputeModeInstalled=true;
  var doc=root.document;
  var storage=null;
  try{storage=root.localStorage}catch(error){storage=null}
  var memoryUserDefault=PRODUCT_DEFAULT_COMPUTE_MODE;
  var memoryOverrides={};

  function readUserDefault(){
    try{
      if(storage){var stored=normalizeComputeMode(storage.getItem(COMPUTE_MODE_STORAGE_KEYS.userDefault));if(stored)return stored}
    }catch(error){}
    return normalizeComputeMode(memoryUserDefault)||PRODUCT_DEFAULT_COMPUTE_MODE
  }
  function writeUserDefault(mode){
    mode=normalizeComputeMode(mode);
    if(!mode)throw new Error('Unknown compute mode');
    memoryUserDefault=mode;
    try{if(storage)storage.setItem(COMPUTE_MODE_STORAGE_KEYS.userDefault,mode)}catch(error){}
    return mode
  }
  function readOverrides(){
    try{
      if(storage){
        var raw=storage.getItem(COMPUTE_MODE_STORAGE_KEYS.promptOverrides);
        if(raw){
          var parsed=JSON.parse(raw);
          if(parsed&&typeof parsed==='object'&&!Array.isArray(parsed)){
            var safe={};
            Object.keys(parsed).forEach(function(key){var mode=normalizeComputeMode(parsed[key]);if(mode)safe[String(key).toUpperCase()]=mode});
            memoryOverrides=safe
          }
        }
      }
    }catch(error){}
    return Object.assign({},memoryOverrides)
  }
  function writeOverrides(overrides){
    memoryOverrides=Object.assign({},overrides||{});
    try{if(storage)storage.setItem(COMPUTE_MODE_STORAGE_KEYS.promptOverrides,JSON.stringify(memoryOverrides))}catch(error){}
  }
  function getPromptOverride(promptId){return readOverrides()[String(promptId||'').toUpperCase()]||null}
  function setPromptOverride(promptId,mode){
    var id=String(promptId||'').trim().toUpperCase();
    if(!id)return false;
    var overrides=readOverrides();
    var normalized=normalizeComputeMode(mode);
    if(normalized)overrides[id]=normalized;else delete overrides[id];
    writeOverrides(overrides);
    refreshDetail(id);
    return true
  }
  function resolutionFor(promptId,explicitRunOverride){
    return resolveComputeMode({
      explicitRunOverride:explicitRunOverride,
      promptOverride:getPromptOverride(promptId),
      userDefault:readUserDefault(),
      productDefault:PRODUCT_DEFAULT_COMPUTE_MODE
    })
  }
  function findPrompt(promptId){
    var id=String(promptId||'').toUpperCase();
    return Array.isArray(root.PROMPTS)?root.PROMPTS.find(function(prompt){return String(prompt&&prompt.id||'').toUpperCase()===id}):null
  }
  function effectivePrompt(promptId,explicitRunOverride){
    var prompt=findPrompt(promptId);
    if(!prompt)return'';
    return composeEffectivePrompt(prompt,resolutionFor(promptId,explicitRunOverride).mode)
  }
  function ensureStyles(){
    if(!doc||doc.getElementById('prompt-kit-compute-mode-styles'))return;
    var style=doc.createElement('style');
    style.id='prompt-kit-compute-mode-styles';
    style.textContent='.prompt-profile-compute-control{display:inline-flex;align-items:center;gap:6px;min-height:34px;padding:4px 7px;border:1px solid var(--border);border-radius:7px;background:var(--bg-surface);color:var(--text-secondary);font-size:10px;font-weight:700}.prompt-profile-compute-select,.prompt-profile-compute-override{min-height:30px;border:1px solid var(--border);border-radius:6px;background:var(--bg-secondary);color:var(--text-primary);font:inherit;padding:4px 7px}.prompt-profile-compute-detail{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:0 0 14px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);color:var(--text-secondary);font-size:10px}.prompt-profile-compute-source{color:var(--text-muted);font-family:ui-monospace,SFMono-Regular,Consolas,monospace}@media(max-width:760px){.prompt-profile-compute-control{min-height:40px}.prompt-profile-compute-select{min-height:36px}.prompt-profile-compute-detail{align-items:stretch}.prompt-profile-compute-override{min-height:40px;flex:1}}';
    doc.head.appendChild(style)
  }
  function mountGlobalControl(){
    if(!doc||doc.getElementById('promptComputeMode'))return;
    var controls=doc.querySelector&&doc.querySelector('.header-controls');
    if(!controls)return;
    var label=doc.createElement('label');
    label.className='prompt-profile-compute-control';
    label.setAttribute('data-ui-format-role','execution-profile-control');
    label.appendChild(doc.createTextNode('Compute'));
    var select=doc.createElement('select');
    select.id='promptComputeMode';
    select.className='prompt-profile-compute-select';
    select.setAttribute('aria-label','Default compute mode');
    [['exhaustive','Exhaustive'],['efficient','Efficient']].forEach(function(item){var option=doc.createElement('option');option.value=item[0];option.textContent=item[1];select.appendChild(option)});
    select.value=readUserDefault();
    select.addEventListener('change',function(){
      writeUserDefault(select.value);
      var detail=doc.getElementById('promptDetail');
      if(detail&&detail.getAttribute('data-prompt-id'))refreshDetail(detail.getAttribute('data-prompt-id'));
      if(typeof root.showToast==='function')root.showToast('Compute mode: '+select.value)
    });
    label.appendChild(select);
    var add=doc.getElementById('addPromptBtn');
    if(add&&add.parentNode===controls)controls.insertBefore(label,add);else controls.appendChild(label)
  }
  function promptContentPre(){
    var detail=doc.getElementById('promptDetail');
    if(!detail)return null;
    var headings=detail.querySelectorAll('.pd-section h4');
    for(var i=0;i<headings.length;i++)if(String(headings[i].textContent||'').trim()==='Prompt Content')return headings[i].parentElement&&headings[i].parentElement.querySelector('pre');
    return null
  }
  function refreshDetail(promptId){
    if(!doc)return;
    var detail=doc.getElementById('promptDetail');
    if(!detail||String(detail.getAttribute('data-prompt-id')||'').toUpperCase()!==String(promptId||'').toUpperCase())return;
    var resolution=resolutionFor(promptId,null);
    var pre=promptContentPre();
    if(pre)pre.textContent=effectivePrompt(promptId,null);
    var wrap=detail.querySelector('.prompt-profile-compute-detail');
    if(!wrap){
      wrap=doc.createElement('div');
      wrap.className='prompt-profile-compute-detail';
      wrap.setAttribute('data-prompt-detail-no-copy','');
      var badges=detail.querySelector('.pd-badges');
      if(badges&&badges.parentNode)badges.parentNode.insertBefore(wrap,badges.nextSibling);else detail.insertBefore(wrap,detail.firstChild)
    }
    wrap.innerHTML='';
    var label=doc.createElement('label');label.textContent='This prompt';
    var select=doc.createElement('select');
    select.id='promptComputeOverride';select.className='prompt-profile-compute-override';select.setAttribute('aria-label','Compute mode override for '+promptId);
    var inherited=doc.createElement('option');inherited.value='';inherited.textContent='Inherit · '+readUserDefault();select.appendChild(inherited);
    [['exhaustive','Exhaustive'],['efficient','Efficient']].forEach(function(item){var option=doc.createElement('option');option.value=item[0];option.textContent=item[1];select.appendChild(option)});
    select.value=getPromptOverride(promptId)||'';
    select.addEventListener('change',function(){setPromptOverride(promptId,select.value||null)});
    label.appendChild(select);wrap.appendChild(label);
    var source=doc.createElement('span');source.className='prompt-profile-compute-source';source.textContent='effective '+resolution.mode+' · '+resolution.source;wrap.appendChild(source)
  }

  ensureStyles();
  mountGlobalControl();
  var baseCopy=root.copyPrompt;
  root.copyPrompt=function(id){
    var text=effectivePrompt(id,null);
    if(text&&typeof root.copyToClipboard==='function'){root.copyToClipboard(text);return text}
    return typeof baseCopy==='function'?baseCopy.apply(root,arguments):''
  };
  var baseOpen=root.canonicalOpenPrompt;
  if(typeof baseOpen==='function')root.canonicalOpenPrompt=function(id){var result=baseOpen.apply(root,arguments);refreshDetail(id);return result};

  api.getComputeState=function(){return{userDefault:readUserDefault(),promptOverrides:readOverrides(),productDefault:PRODUCT_DEFAULT_COMPUTE_MODE}};
  api.setUserComputeMode=function(mode){var value=writeUserDefault(mode);var select=doc&&doc.getElementById('promptComputeMode');if(select)select.value=value;var detail=doc&&doc.getElementById('promptDetail');if(detail&&detail.getAttribute('data-prompt-id'))refreshDetail(detail.getAttribute('data-prompt-id'));return value};
  api.setPromptComputeMode=setPromptOverride;
  api.resolvePromptComputeMode=resolutionFor;
  api.getEffectivePrompt=effectivePrompt;
  return api
}
api.COMPUTE_MODE_SCHEMA=COMPUTE_MODE_SCHEMA;
api.LANGUAGE_ENGINE_REVISION=LANGUAGE_ENGINE_REVISION;
api.PRODUCT_DEFAULT_COMPUTE_MODE=PRODUCT_DEFAULT_COMPUTE_MODE;
api.COMPUTE_MODE_STORAGE_KEYS=COMPUTE_MODE_STORAGE_KEYS;
api.COMPUTE_MODE_PRECEDENCE=COMPUTE_MODE_PRECEDENCE;
api.COMPUTE_PROFILES=COMPUTE_PROFILES;
api.NON_WEAKENABLE_COMPUTE_CONSTRAINTS=NON_WEAKENABLE;
api.normalizeComputeMode=normalizeComputeMode;
api.resolveComputeMode=resolveComputeMode;
api.renderComputeDirective=renderComputeDirective;
api.composeEffectivePrompt=composeEffectivePrompt;
api.installComputeMode=installComputeMode;
if(root&&root.document)installComputeMode(root);
})(typeof window!=='undefined'?window:null);
'''


CONTRACT = {
    "schema_version": "prompt-kit-compute-mode/v1",
    "contract_id": "prompt-kit-compute-mode",
    "status": "implemented",
    "compiler_authority": {
        "module": "scripts/prompt_language_compiler.py",
        "profile_source": "scripts/prompt_context_engine.py",
        "language_engine_revision": "prompt-language-compiler/v1.0.0",
        "projection_runtime": "docs/prompt-kit-profiles.js",
        "parity_rule": "browser directive output must equal prompt_language_compiler.render_profile_overlay for the same execution profile"
    },
    "profiles": ["exhaustive", "efficient"],
    "product_default": "exhaustive",
    "precedence": ["explicit_run_override", "prompt_override", "user_default", "product_default"],
    "storage": {
        "user_default": "promptKit.computeMode.v1",
        "prompt_overrides": "promptKit.computeModeOverrides.v1",
        "classification": "personal_state"
    },
    "ui": {
        "global_control": "#promptComputeMode",
        "prompt_override_control": "#promptComputeOverride",
        "allowed_class_family": "prompt-profile-*"
    },
    "non_weakenable_constraints": [
        "safety",
        "evidence_truth",
        "destructive_operation_rules",
        "privacy",
        "explicit_user_scope",
        "required_acceptance_gates"
    ],
    "copy_contract": "all canonical copy entrypoints resolve the selected compute profile and copy directive + canonical copyContent; prompt override beats user default; explicit run override remains highest through API/context resolution",
    "forbidden": [
        "independently authored exhaustive/efficient prompt files",
        "weakening non-weakenable constraints",
        "raw conversation ingestion",
        "new lifecycle event ownership",
        "automatic source mutation or merge"
    ]
}


TEST = r'''from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from scripts import prompt_context_engine, prompt_language_compiler

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "docs" / "prompt-kit-profiles.js"
STORAGE = ROOT / "docs" / "prompt-kit-storage-lifecycle.js"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-compute-mode.v1.json"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"


def node_json(script: str) -> dict:
    completed = subprocess.run(["node", "-e", script], cwd=ROOT, check=True, text=True, capture_output=True)
    return json.loads(completed.stdout)


class PromptKitComputeModeTests(unittest.TestCase):
    def test_runtime_profiles_are_parity_locked_to_python_compiler(self) -> None:
        subprocess.run(["node", "--check", str(RUNTIME)], cwd=ROOT, check=True)
        proof = node_json("""
const api=require('./docs/prompt-kit-profiles.js');
console.log(JSON.stringify({profiles:api.COMPUTE_PROFILES,directives:{exhaustive:api.renderComputeDirective('exhaustive'),efficient:api.renderComputeDirective('efficient')},precedence:api.COMPUTE_MODE_PRECEDENCE,productDefault:api.PRODUCT_DEFAULT_COMPUTE_MODE,revision:api.LANGUAGE_ENGINE_REVISION,constraints:api.NON_WEAKENABLE_COMPUTE_CONSTRAINTS}));
""")
        self.assertEqual(proof["productDefault"], "exhaustive")
        self.assertEqual(proof["precedence"], list(prompt_context_engine.PROFILE_PRECEDENCE))
        self.assertEqual(proof["revision"], prompt_language_compiler.load_policy()["language_engine_revision"])
        self.assertEqual(set(proof["constraints"]), prompt_language_compiler.REQUIRED_NON_WEAKENABLE)
        for mode in ("exhaustive", "efficient"):
            expected = prompt_context_engine.PROFILE_LIBRARY[mode]
            for key in ("profile", "compute_policy", "parallel_policy", "hypothesis_policy", "validation_policy", "stop_policy"):
                self.assertEqual(proof["profiles"][mode][key], expected[key])
            self.assertEqual(proof["directives"][mode], prompt_language_compiler.render_profile_overlay(expected))

    def test_precedence_is_run_then_prompt_then_user_then_product(self) -> None:
        proof = node_json("""
const api=require('./docs/prompt-kit-profiles.js');
function r(options){return api.resolveComputeMode(options)}
console.log(JSON.stringify({
  run:r({explicitRunOverride:'efficient',promptOverride:'exhaustive',userDefault:'exhaustive'}),
  prompt:r({promptOverride:'efficient',userDefault:'exhaustive'}),
  user:r({userDefault:'efficient'}),
  product:r({}),
  invalid:r({explicitRunOverride:'bogus',promptOverride:'efficient',userDefault:'exhaustive'})
}));
""")
        self.assertEqual(proof["run"], {"mode": "efficient", "source": "explicit_run_override"})
        self.assertEqual(proof["prompt"], {"mode": "efficient", "source": "prompt_override"})
        self.assertEqual(proof["user"], {"mode": "efficient", "source": "user_default"})
        self.assertEqual(proof["product"], {"mode": "exhaustive", "source": "product_default"})
        self.assertEqual(proof["invalid"], {"mode": "efficient", "source": "prompt_override"})

    def test_effective_prompt_preserves_canonical_body_and_changes_profile_only(self) -> None:
        proof = node_json("""
const api=require('./docs/prompt-kit-profiles.js');
const prompt={id:'P07',copyContent:'CANONICAL BODY\\nMUST preserve scope.'};
console.log(JSON.stringify({exhaustive:api.composeEffectivePrompt(prompt,'exhaustive'),efficient:api.composeEffectivePrompt(prompt,'efficient')}));
""")
        self.assertIn("EXECUTION PROFILE: EXHAUSTIVE", proof["exhaustive"])
        self.assertIn("EXECUTION PROFILE: EFFICIENT", proof["efficient"])
        self.assertTrue(proof["exhaustive"].endswith("CANONICAL BODY\nMUST preserve scope."))
        self.assertTrue(proof["efficient"].endswith("CANONICAL BODY\nMUST preserve scope."))
        self.assertIn("MUST dispatch independent lanes in parallel", proof["exhaustive"])
        self.assertNotIn("MUST dispatch independent lanes in parallel", proof["efficient"])

    def test_storage_delete_personal_state_owns_compute_preferences(self) -> None:
        source = STORAGE.read_text(encoding="utf-8")
        self.assertIn("'promptKit.computeMode.v1'", source)
        self.assertIn("'promptKit.computeModeOverrides.v1'", source)

    def test_contract_and_generated_site_expose_compute_mode(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(contract["schema_version"], "prompt-kit-compute-mode/v1")
        self.assertEqual(contract["precedence"], list(prompt_context_engine.PROFILE_PRECEDENCE))
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in ("promptKit.computeMode.v1", "promptKit.computeModeOverrides.v1", "promptComputeMode", "promptComputeOverride", "EXECUTION PROFILE: EXHAUSTIVE"):
            self.assertIn(marker, deployed)


if __name__ == "__main__":
    unittest.main()
'''


BROWSER = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        pass


@contextmanager
def serve_repo():
    handler = lambda *args, **kwargs: Quiet(*args, directory=str(ROOT), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)


def main() -> int:
    with serve_repo() as origin, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 760})
        context.grant_permissions(["clipboard-read", "clipboard-write"], origin=origin)
        page = context.new_page()
        page.goto(f"{origin}/web/prompt-kit/index.html", wait_until="domcontentloaded")
        page.wait_for_selector("#promptComputeMode")
        assert page.locator("#promptComputeMode").input_value() == "exhaustive"
        default_text = page.evaluate("PromptKitProfiles.getEffectivePrompt('P07')")
        assert default_text.startswith("EXECUTION PROFILE: EXHAUSTIVE")

        page.select_option("#promptComputeMode", "efficient")
        assert page.evaluate("localStorage.getItem('promptKit.computeMode.v1')") == "efficient"
        page.evaluate("showPromptDetail('P07')")
        page.wait_for_selector("#promptComputeOverride")
        prompt_pre = page.locator(".pd-section").filter(has_text="Prompt Content").locator("pre")
        assert prompt_pre.inner_text().startswith("EXECUTION PROFILE: EFFICIENT")

        page.select_option("#promptComputeOverride", "exhaustive")
        state = page.evaluate("JSON.parse(localStorage.getItem('promptKit.computeModeOverrides.v1'))")
        assert state["P07"] == "exhaustive"
        assert prompt_pre.inner_text().startswith("EXECUTION PROFILE: EXHAUSTIVE")
        page.locator("#promptDetailCopyTop").click()
        clipboard = page.evaluate("navigator.clipboard.readText()")
        assert clipboard.startswith("EXECUTION PROFILE: EXHAUSTIVE")

        explicit = page.evaluate("PromptKitProfiles.getEffectivePrompt('P07','efficient')")
        assert explicit.startswith("EXECUTION PROFILE: EFFICIENT")

        page.select_option("#promptComputeOverride", "")
        page.locator("#promptDetailCopyTop").click()
        clipboard_inherit = page.evaluate("navigator.clipboard.readText()")
        assert clipboard_inherit.startswith("EXECUTION PROFILE: EFFICIENT")
        proof = {
            "schema_version": "prompt-kit-compute-mode-browser-proof/v1",
            "global_default_initial": "exhaustive",
            "global_user_default": "efficient",
            "prompt_override_observed": "exhaustive",
            "explicit_run_override_observed": "efficient",
            "inherit_after_override_clear": "efficient",
            "copy_path_observed": True,
        }
        out = ROOT / "Outputs" / "prompt-kit-compute-mode-browser-proof.json"
        out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(proof, indent=2)+"\n", encoding="utf-8")
        print(json.dumps(proof, sort_keys=True), flush=True)
        context.close(); browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def patch_product() -> None:
    compiler = ROOT / "scripts/prompt_language_compiler.py"
    text = compiler.read_text(encoding="utf-8")
    marker = "def render_profile_overlay("
    if marker not in text:
        anchor = "\ndef render(\n"
        if text.count(anchor) != 1:
            raise RuntimeError("prompt_language_compiler.py: render anchor drift")
        helper = '''\ndef render_profile_overlay(\n    profile: dict[str, Any],\n    *,\n    policy: dict[str, Any] | None = None,\n) -> str:\n    \"\"\"Render the deterministic user-facing Compute Mode directive for one profile.\"\"\"\n    policy = policy or load_policy()\n    profile = validate_profile(profile)\n    mode = profile[\"profile\"]\n    if mode == \"exhaustive\":\n        guidance = (\n            \"For compute-depth behavior only, this profile supersedes default compute-depth clauses. \"\n            \"Exhaust safe decision-relevant compute until an evidence-backed fixed point or exact blocker. \"\n            \"When at least two meaningful independent lanes and safe usable capacity exist, MUST dispatch \"\n            \"independent lanes in parallel; considering or describing parallelism is not execution evidence.\"\n        )\n    else:\n        guidance = (\n            \"For compute-depth behavior only, this profile supersedes default compute-depth clauses. \"\n            \"Use minimum sufficient compute to satisfy requested scope and every required proof and acceptance gate. \"\n            \"Parallelize when expected critical-path benefit exceeds coordination cost; otherwise use the shortest \"\n            \"dependency-safe serial path.\"\n        )\n    return \"\\n\".join(\n        [\n            f\"EXECUTION PROFILE: {mode.upper()}\",\n            f\"Compute policy: {profile['compute_policy']}\",\n            f\"Parallel policy: {profile['parallel_policy']}\",\n            f\"Stop policy: {profile['stop_policy']}\",\n            guidance,\n            \"Non-weakenable constraints: \" + \", \".join(sorted(REQUIRED_NON_WEAKENABLE)),\n            f\"Compiler policy: {policy['language_engine_revision']}\",\n        ]\n    )\n\n'''
        compiler.write_text(text.replace(anchor, helper + anchor, 1), encoding="utf-8")

    profiles = ROOT / "docs/prompt-kit-profiles.js"
    text = profiles.read_text(encoding="utf-8")
    if "Prompt Compilation Sprint 3: parity-locked Compute Mode product projection" not in text:
        profiles.write_text(text.rstrip() + COMPUTE_EXTENSION + "\n", encoding="utf-8")

    replace_once(
        "docs/prompt-kit-storage-lifecycle.js",
        "  'promptKit.profilePacks.v1',\n  'promptKit.favoritePromptIds',",
        "  'promptKit.profilePacks.v1',\n  'promptKit.computeMode.v1',\n  'promptKit.computeModeOverrides.v1',\n  'promptKit.favoritePromptIds',",
    )

    write_new("harness/contracts/prompt-kit-compute-mode.v1.json", json.dumps(CONTRACT, indent=2) + "\n")
    write_new("tests/test_prompt_kit_compute_mode.py", TEST)
    write_new("tests/prompt_kit_compute_mode_browser_proof.py", BROWSER)

    sprint = ROOT / "harness/prompt-compilation/PROMPT_COMPILATION_SPRINT_MAP.md"
    text = sprint.read_text(encoding="utf-8")
    text = text.replace(
        "**Status:** TRACKED / SPRINTS 1–2 INTEGRATED ON MAIN VIA #483/#485",
        "**Status:** TRACKED / SPRINTS 1–2 INTEGRATED / SPRINT 3 IMPLEMENTED + VALIDATED ON OWNED BRANCH",
        1,
    )
    old = """### Sprint 3 — Prompt Kit wiring + Compute Mode product surface\n\n**Status:** PLANNED (dependency: Sprint 2)\n\n**Owned:** wire compiler into effective-prompt generation path; user-facing Compute Mode (Exhaustive/Efficient) with per-prompt overrides.\n\n**Forbidden:** weakening safety gates; bypassing builder-owned generation.\n"""
    new = """### Sprint 3 — Prompt Kit wiring + Compute Mode product surface\n\n**Status:** IMPLEMENTED / VALIDATED ON `feat/prompt-compilation-sprint3-compute-mode-20260916`; integration pending\n\n**Owned:** parity-lock the browser projection to `prompt_language_compiler.render_profile_overlay`; expose user-facing Compute Mode (Exhaustive/Efficient), per-prompt overrides, and explicit-run API precedence; classify preferences as personal state; rebuild the builder-owned Prompt Kit artifact; prove copy/detail behavior in Chromium.\n\n**Tracked surfaces:** `scripts/prompt_language_compiler.py`; `docs/prompt-kit-profiles.js`; `docs/prompt-kit-storage-lifecycle.js`; `harness/contracts/prompt-kit-compute-mode.v1.json`; `tests/test_prompt_kit_compute_mode.py`; `tests/prompt_kit_compute_mode_browser_proof.py`; generated `web/prompt-kit/index.html`; ledger `TRQ-012`.\n\n**Validation:** compiler/context/profile/storage/UI focused tests; compiler fixtures; strict UI-format alignment; work-ledger validator; exact generated-site parity; Node syntax; Chromium copy/override proof; `git diff --check`.\n\n**Forbidden:** weakening safety/evidence/privacy/scope/acceptance gates; independently authored prompt pairs; bypassing builder-owned generation; raw conversation ingestion; new Evidence Spine event ownership; automatic policy promotion or merge.\n\n**Proof ceiling:** repository + generated-site + headless Chromium behavior on the owned branch. External-agent adherence to the selected mode remains a separate TRQ-007/runtime observation contract.\n"""
    if old not in text:
        raise RuntimeError("Sprint 3 plan block drifted")
    sprint.write_text(text.replace(old, new, 1), encoding="utf-8")

    arch = ROOT / "harness/prompt-compilation/PROMPT_COMPILATION_ARCHITECTURE.md"
    text = arch.read_text(encoding="utf-8")
    text = text.replace("**Status:** DESIGNED / TRACKED / SPRINTS 1–2 INTEGRATED ON MAIN", "**Status:** DESIGNED / TRACKED / SPRINTS 1–2 INTEGRATED / SPRINT 3 PRODUCT PROJECTION IMPLEMENTED ON OWNED BRANCH", 1)
    text = text.replace("## 6. Compute Mode (user-facing product surface — later sprint)", "## 6. Compute Mode (user-facing product surface — Sprint 3)", 1)
    arch.write_text(text, encoding="utf-8")

    ledger = ROOT / ".ai/WORK_QUEUE.md"
    text = ledger.read_text(encoding="utf-8")
    if "## TRQ-012 — Wire Prompt Compilation Compute Mode into Prompt Kit" not in text:
        block = """\n\n## TRQ-012 — Wire Prompt Compilation Compute Mode into Prompt Kit\n\n- **Status:** VERIFY\n- **Priority:** P1\n- **Owner:** chatgpt-prompt-compilation-sprint3-20260916\n- **Branch / PR:** feat/prompt-compilation-sprint3-compute-mode-20260916 / PR pending\n- **Scope:** parity-lock the user-facing Exhaustive/Efficient Compute Mode projection to the canonical Python Language Engine; add global and per-prompt precedence, safe personal-state persistence, canonical copy/detail wiring, deterministic and browser regressions, generated-site parity, and durable Sprint 3 synchronization\n- **Forbidden:** changing TRQ-007 frozen treatment identities; weakening safety/evidence/privacy/scope/acceptance gates; independently authored prompt pairs; raw conversation ingestion; new Evidence Spine event ownership; auto-merge or model-only policy promotion\n- **Dependencies:** TRQ-010 DONE / Sprint 2 integrated via PR #485; Prompt Kit runtime floor main@de42daf148a2f09754b3eb2f7fd88799162d1e05\n- **References:** harness/prompt-compilation/PROMPT_COMPILATION_SPRINT_MAP.md, harness/contracts/prompt-kit-compute-mode.v1.json, scripts/prompt_language_compiler.py, docs/prompt-kit-profiles.js, docs/prompt-kit-storage-lifecycle.js, tests/test_prompt_kit_compute_mode.py, tests/prompt_kit_compute_mode_browser_proof.py, web/prompt-kit/index.html\n- **Acceptance gate:** Python/JS profile overlay parity; run > prompt > user > product precedence; exhaustive product default; per-prompt override affects canonical copy path; personal-state delete includes Compute Mode keys; focused compiler/context/profile/storage/UI tests and validators pass; generated-site parity passes; Chromium proves global/override/inherit copy behavior; exact validated head reaches main with containment proof\n- **Gate:** verify exact branch head, CI, review, and merge eligibility\n- **Last proof:** artifact:harness/contracts/prompt-kit-compute-mode.v1.json; branch carrier executes deterministic + Chromium validation before candidate commit\n- **Next action:** open the Sprint 3 pull request from feat/prompt-compilation-sprint3-compute-mode-20260916 after the carrier pushes its exact validated candidate\n- **Updated:** 2026-09-16T18:27:00-04:00\n"""
        ledger.write_text(text.rstrip() + block + "\n", encoding="utf-8")


def deterministic_validation() -> None:
    run("python", "-m", "unittest", "tests.test_prompt_compilation", "tests.test_prompt_context_engine", "tests.test_prompt_kit_compute_mode", "tests.test_prompt_kit_profiles", "tests.test_prompt_kit_storage_lifecycle_runtime", "tests.test_prompt_kit_ui_format_alignment", "-v")
    run("python", "scripts/prompt_language_compiler.py", "validate-fixtures", "--summary")
    run("python", "scripts/validate_prompt_kit_ui_format_alignment.py", "--require-implementation", "--summary")
    run("python", "scripts/validate_repository_work_ledger.py")
    run("node", "--check", "docs/prompt-kit-profiles.js")
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    run("git", "diff", "--check")


def browser_validation() -> None:
    run("python", "tests/prompt_kit_compute_mode_browser_proof.py")


def main() -> int:
    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    patch_product()
    deterministic_validation()
    browser_validation()

    owned = [
        ".ai/WORK_QUEUE.md",
        "docs/prompt-kit-profiles.js",
        "docs/prompt-kit-storage-lifecycle.js",
        "harness/contracts/prompt-kit-compute-mode.v1.json",
        "harness/prompt-compilation/PROMPT_COMPILATION_ARCHITECTURE.md",
        "harness/prompt-compilation/PROMPT_COMPILATION_SPRINT_MAP.md",
        "scripts/prompt_language_compiler.py",
        "tests/test_prompt_kit_compute_mode.py",
        "tests/prompt_kit_compute_mode_browser_proof.py",
        "web/prompt-kit/index.html",
    ]
    run("git", "add", *owned)
    run("git", "diff", "--cached", "--check")
    run("git", "commit", "-m", "feat(prompt-compilation): wire Compute Mode into Prompt Kit")
    candidate_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    print(f"CANDIDATE_SHA={candidate_sha}", flush=True)

    # Second pass against the exact committed candidate.
    deterministic_validation()
    browser_validation()

    # Carrier cleanup is bookkeeping-only; behavior/proof inputs stay unchanged.
    run("git", "rm", WORKFLOW, CARRIER)
    run("git", "commit", "-m", "chore(carrier): retire Prompt Compilation Sprint 3 executor")
    final_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    print(f"FINAL_SHA={final_sha}", flush=True)
    run("git", "push", "origin", f"HEAD:{BRANCH}")
    run("git", "status", "--short", "--untracked-files=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
