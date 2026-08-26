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
