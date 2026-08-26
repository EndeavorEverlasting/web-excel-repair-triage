from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "docs" / "prompt-kit-profiles.js"
BUILDER = ROOT / "build_prompt_kit.py"
COMBINED = ROOT / "scripts" / "build_prompt_kit_registry.py"
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
BASE = ROOT / "docs" / "prompt-kit.js"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"
DESIGN = ROOT / "docs" / "PROMPT_KIT_FIVE_TAB_PROFILES.md"
ACCESS = ROOT / "PROMPT_KIT_ACCESS.md"


def node_json(script: str) -> dict:
    completed = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


class PromptKitProfileTests(unittest.TestCase):
    def test_runtime_is_parseable_and_defaults_are_five_named_tabs(self) -> None:
        subprocess.run(["node", "--check", str(RUNTIME)], cwd=ROOT, check=True)
        proof = node_json(
            """
const api=require('./docs/prompt-kit-profiles.js');
console.log(JSON.stringify({
  keys:api.SLOT_KEYS,
  names:api.DEFAULT_SLOTS.map(x=>x.name),
  modes:api.DEFAULT_SLOTS.map(x=>x.mode),
  sas:api.DEFAULT_SLOTS[3].packIds,
  pm:api.DEFAULT_SLOTS[4].packIds
}));
"""
        )
        self.assertEqual(proof["keys"], list("ABCDE"))
        self.assertEqual(proof["names"], ["All", "Standard", "Favorites", "SAS", "PM"])
        self.assertEqual(proof["modes"], ["all", "standard", "favorites", "packs", "packs"])
        self.assertEqual(proof["sas"], ["SAS"])
        self.assertEqual(proof["pm"], ["PM", "FUN", "TRIAGE", "H_AND_H"])

    def test_predefined_pack_catalog_contains_requested_building_blocks(self) -> None:
        proof = node_json(
            """
const api=require('./docs/prompt-kit-profiles.js');
console.log(JSON.stringify({ids:Object.keys(api.PREDEFINED_PACKS).sort()}));
"""
        )
        for pack_id in (
            "TRIAGE",
            "FUN",
            "PM",
            "CYBERSEC",
            "AGENTIC_LOOPING",
            "SAS",
            "GARDENING",
            "H_AND_H",
            "FUTURE_PROJECTS",
        ):
            self.assertIn(pack_id, proof["ids"])

    def test_restricted_evaluator_matches_data_without_executing_code(self) -> None:
        proof = node_json(
            """
const api=require('./docs/prompt-kit-profiles.js');
const sample={id:'P77',name:'SysAdminSuite network probe triage',type:'REPAIR',category:'standard',keywords:['powershell']};
const rule={op:'every',rules:[
  {op:'keyword',value:'triage'},
  {op:'any',rules:[{op:'keyword',value:'powershell'},{op:'keyword',value:'linux'}]},
  {op:'not',rule:{op:'keyword',value:'gardening'}}
]};
console.log(JSON.stringify({matched:api.compileRule(rule)(sample)}));
"""
        )
        self.assertTrue(proof["matched"])
        source = RUNTIME.read_text(encoding="utf-8")
        self.assertNotIn("eval(", source)
        self.assertNotIn("new Function", source)
        self.assertNotIn("Function(", source)

    def test_import_guardrails_fail_closed(self) -> None:
        proof = node_json(
            """
const api=require('./docs/prompt-kit-profiles.js');
function code(payload,count=0){
  try{api.validateImport(typeof payload==='string'?payload:JSON.stringify(payload),count);return 'PASS'}
  catch(e){return e.code}
}
const base={schema:api.IMPORT_SCHEMA,packs:[{id:'CUSTOM',label:'Custom',rule:{op:'keyword',value:'example'}}]};
let tooMany={schema:api.IMPORT_SCHEMA,packs:[]};
for(let i=0;i<33;i++)tooMany.packs.push({id:'X'+i,label:'X'+i,rule:{op:'all'}});
let deep={op:'not',rule:{op:'not',rule:{op:'not',rule:{op:'not',rule:{op:'not',rule:{op:'all'}}}}}};
console.log(JSON.stringify({
  valid:code(base),
  badSchema:code({schema:'wrong',packs:base.packs}),
  unknown:code({schema:api.IMPORT_SCHEMA,packs:[{id:'BAD',label:'Bad',rule:{op:'javascript',value:'alert(1)'}}]}),
  reserved:code({schema:api.IMPORT_SCHEMA,packs:[{id:'PM',label:'Shadow',rule:{op:'all'}}]}),
  tooMany:code(tooMany),
  installed:code(base,64),
  deep:code({schema:api.IMPORT_SCHEMA,packs:[{id:'DEEP',label:'Deep',rule:deep}]}),
  tooLarge:code('x'.repeat(api.LIMITS.importBytes+1))
}));
"""
        )
        self.assertEqual(proof["valid"], "PASS")
        self.assertEqual(proof["badSchema"], "IMPORT_SCHEMA")
        self.assertEqual(proof["unknown"], "UNKNOWN_RULE_OP")
        self.assertEqual(proof["reserved"], "RESERVED_PACK_ID")
        self.assertEqual(proof["tooMany"], "IMPORT_PACK_COUNT")
        self.assertEqual(proof["installed"], "INSTALLED_PACK_LIMIT")
        self.assertEqual(proof["deep"], "RULE_DEPTH")
        self.assertEqual(proof["tooLarge"], "IMPORT_TOO_LARGE")

    def test_slot_guardrails_require_exactly_five_and_bound_composition(self) -> None:
        proof = node_json(
            """
const api=require('./docs/prompt-kit-profiles.js');
const available=api.packMap([]);
function code(slots){try{api.normalizeSlots(slots,available);return 'PASS'}catch(e){return e.code}}
const defaults=api.defaultSlots();
const overload=api.defaultSlots();overload[3]={key:'D',name:'Over',mode:'packs',packIds:Array(13).fill('SAS')};
const empty=api.defaultSlots();empty[3]={key:'D',name:'Empty',mode:'packs',packIds:[]};
console.log(JSON.stringify({
  valid:code(defaults),
  four:code(defaults.slice(0,4)),
  overload:code(overload),
  empty:code(empty)
}));
"""
        )
        self.assertEqual(proof["valid"], "PASS")
        self.assertEqual(proof["four"], "SLOT_COUNT")
        self.assertEqual(proof["overload"], "SLOT_PACK_LIMIT")
        self.assertEqual(proof["empty"], "EMPTY_PACK_SLOT")

    def test_generated_header_and_effective_hotkeys_are_letters_a_through_e(self) -> None:
        builder = BUILDER.read_text(encoding="utf-8")
        expected = [
            ('data-profile-slot="A"', "All", "A"),
            ('data-profile-slot="B"', "Standard", "B"),
            ('data-profile-slot="C"', "Favorites", "C"),
            ('data-profile-slot="D"', "SAS", "D"),
            ('data-profile-slot="E"', "PM", "E"),
        ]
        positions = []
        for marker, label, key in expected:
            pos = builder.find(marker)
            self.assertGreaterEqual(pos, 0, marker)
            positions.append(pos)
            self.assertIn(f">{label}<span class=\"kbd\">{key}</span>", builder)
        self.assertEqual(positions, sorted(positions))

        polish = POLISH.read_text(encoding="utf-8")
        base = BASE.read_text(encoding="utf-8")
        for digit in "12345":
            self.assertNotIn(f"if(key==='{digit}')", polish)
            self.assertNotIn(f"case'{digit}'", base)
        self.assertNotIn("if(key==='b'){e.preventDefault();e.stopImmediatePropagation();scrollPromptKitTo('bottom')", polish)
        self.assertIn("if(key==='end'){e.preventDefault();e.stopImmediatePropagation();scrollPromptKitTo('bottom')", polish)

    def test_profile_runtime_is_injected_before_polish_and_generated_artifact_is_current(self) -> None:
        source = COMBINED.read_text(encoding="utf-8")
        self.assertIn('PROFILE_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-profiles.js"', source)
        self.assertLess(source.index("profile_script = _read_runtime"), source.index("polish_script = _read_runtime"))
        deployed = DEPLOYED.read_text(encoding="utf-8")
        self.assertIn("promptKit.profileSlots.v1", deployed)
        self.assertIn("Profile tabs A–E", deployed)
        self.assertIn('data-profile-slot="E"', deployed)

        with tempfile.TemporaryDirectory() as tmp:
            rebuilt = Path(tmp) / "index.html"
            subprocess.run(
                [sys.executable, str(COMBINED), "--output", str(rebuilt)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(rebuilt.read_bytes(), DEPLOYED.read_bytes())

    def test_install_guards_storage_access_and_base_reset_clears_custom_profile(self) -> None:
        proof = node_json(
            r"""
const api=require('./docs/prompt-kit-profiles.js');
function makeDoc(){
  return {
    getElementById(id){return id==='prompt-kit-profile-styles'?{}:null},
    querySelector(){return null},
    addEventListener(){},
    head:{appendChild(){}},
    body:{}
  };
}
function makeRoot(){
  const root={
    document:makeDoc(),
    PROMPTS:[
      {id:'P1',name:'SysAdminSuite SAS PowerShell network probe',type:'REPAIR',category:'standard',keywords:['sas','sysadminsuite','powershell']},
      {id:'P2',name:'General prompt',type:'BUILD',category:'standard',keywords:['general']}
    ],
    activeCat:'all',
    activeSection:null,
    render:function(){root.lastRender=root.PROMPTS.map(item=>item.id)},
    renderTypes:function(){},
    renderSections:function(){},
    setTimeout:function(){},
    showToast:function(){}
  };
  return root;
}
const blocked=makeRoot();
Object.defineProperty(blocked,'localStorage',{get(){throw new Error('blocked storage')}});
const blockedApi=api.install(blocked);
const blockedState=blockedApi.getState();

const stored=makeRoot();
const memory={};
stored.localStorage={
  getItem(key){return Object.prototype.hasOwnProperty.call(memory,key)?memory[key]:null},
  setItem(key,value){memory[key]=String(value)}
};
stored.resetPromptKitView=function(){
  this.activeCat='all';this.activeSection=null;this.render();return 'reset';
};
const installed=api.install(stored);
installed.activateSlot('D',true);
const before=installed.getState().activeKey;
const result=stored.resetPromptKitView();
const after=installed.getState().activeKey;
console.log(JSON.stringify({
  blockedActive:blockedState.activeKey,
  before,
  after,
  persisted:memory[api.STORAGE_KEYS.active],
  result,
  rendered:stored.lastRender
}));
"""
        )
        self.assertEqual(proof["blockedActive"], "A")
        self.assertEqual(proof["before"], "D")
        self.assertEqual(proof["after"], "A")
        self.assertEqual(proof["persisted"], "A")
        self.assertEqual(proof["result"], "reset")
        self.assertEqual(proof["rendered"], ["P1", "P2"])

    def test_configuring_active_slot_reapplies_new_mode(self) -> None:
        proof = node_json(
            r"""
const api=require('./docs/prompt-kit-profiles.js');
const memory={};
const doc={
  getElementById(id){return id==='prompt-kit-profile-styles'?{}:null},
  querySelector(){return null},
  addEventListener(){},
  head:{appendChild(){}},
  body:{}
};
const root={
  document:doc,
  localStorage:{getItem(k){return memory[k]||null},setItem(k,v){memory[k]=String(v)}},
  PROMPTS:[],activeCat:'all',activeSection:null,
  render(){},renderTypes(){},renderSections(){},setTimeout(){},showToast(){}
};
const installed=api.install(root);
installed.activateSlot('B',true);
const candidate=installed.getState().slots;
candidate[1]={key:'B',name:'Saved Favorites',mode:'favorites',packIds:[]};
installed.configureSlots(candidate);
console.log(JSON.stringify({active:installed.getState().activeKey,cat:root.activeCat,section:root.activeSection}));
"""
        )
        self.assertEqual(proof["active"], "B")
        self.assertEqual(proof["cat"], "all")
        self.assertEqual(proof["section"], "__favorites__")

    def test_retired_header_views_remain_profile_packs(self) -> None:
        proof = node_json(
            """
const api=require('./docs/prompt-kit-profiles.js');
console.log(JSON.stringify({ids:Object.keys(api.PREDEFINED_PACKS).sort()}));
"""
        )
        self.assertIn("GNHF", proof["ids"])
        self.assertIn("DOCTRINE", proof["ids"])
        access = ACCESS.read_text(encoding="utf-8")
        self.assertIn("`GNHF` and `DOCTRINE` profile packs", access)
        self.assertIn("Press **Home** for the true document top", access)
        self.assertNotIn("Press **4** or use the header **Favorites**", access)
        self.assertNotIn("Doctrine** remains available in the header", access)

    def test_design_records_import_limits_and_hotkey_collision_rule(self) -> None:
        text = DESIGN.read_text(encoding="utf-8")
        for marker in (
            "32 KiB maximum JSON import",
            "64 installed imported packs",
            "rule nesting depth 4",
            "12 selected packs per tab",
            "never calls JavaScript `eval`, `Function`, or `new Function`",
            "`A` through `E` are reserved",
            "Digits remain available to configured prompt-ID sequences such as `P111`",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
