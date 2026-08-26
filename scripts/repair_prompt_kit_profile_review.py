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


# Preserve the older design-regression marker while making the identity rule precise.
replace_once(
    "docs/PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md",
    "Dots are visual separators, not identity characters, while a prompt sequence is active: `p1.1` follows",
    "Dots are visual separators, not identity characters, while a prompt-ID buffer is active: `p1.1` follows",
)

# Access to window.localStorage itself can throw in restricted browser contexts.
replace_once(
    "docs/prompt-kit-profiles.js",
    "  var doc=root.document;\n  var storage=root.localStorage;\n  var imported=[];",
    "  var doc=root.document;\n  var storage=null;\n  try{storage=root.localStorage}catch(e){storage=null}\n  var imported=[];",
)

# Retired dedicated header views remain available as profile building blocks instead of
# reclaiming A-E system slots.
replace_once(
    "docs/prompt-kit-profiles.js",
    "  FUTURE_PROJECTS:{id:'FUTURE_PROJECTS',label:'Future Projects',rule:anyKeywords(['future project','roadmap','backlog'])}\n};",
    "  FUTURE_PROJECTS:{id:'FUTURE_PROJECTS',label:'Future Projects',rule:anyKeywords(['future project','roadmap','backlog'])},\n  GNHF:{id:'GNHF',label:'GNHF',rule:{op:'category',value:'gnhf'}},\n  DOCTRINE:{id:'DOCTRINE',label:'Doctrine',rule:{op:'category',value:'doctrine'}}\n};",
)

# Base/logo reset must clear the profile projection before base render runs.
replace_once(
    "docs/prompt-kit-profiles.js",
    "  if(typeof baseRender==='function')root.render=function(){return projectCall(baseRender,arguments)};\n  if(typeof baseRenderTypes==='function')root.renderTypes=function(){return projectCall(baseRenderTypes,arguments)};\n  if(typeof baseRenderSections==='function')root.renderSections=function(){return projectCall(baseRenderSections,arguments)};\n\n  function clearTransientBrowserFilters(){",
    "  if(typeof baseRender==='function')root.render=function(){return projectCall(baseRender,arguments)};\n  if(typeof baseRenderTypes==='function')root.renderTypes=function(){return projectCall(baseRenderTypes,arguments)};\n  if(typeof baseRenderSections==='function')root.renderSections=function(){return projectCall(baseRenderSections,arguments)};\n  var baseResetPromptKitView=root.resetPromptKitView;\n  if(typeof baseResetPromptKitView==='function')root.resetPromptKitView=function(){\n    activeKey='A';\n    try{persistActive('A')}catch(e){}\n    var result=baseResetPromptKitView.apply(root,arguments);\n    refreshHeader();\n    updateEditor();\n    return result\n  };\n\n  function clearTransientBrowserFilters(){",
)

# Saving a definition for the active slot must reapply that slot's newly selected view.
replace_once(
    "docs/prompt-kit-profiles.js",
    "  function configureSlots(candidate){\n    saveSlots(candidate);\n    refreshHeader();\n    renderAll();",
    "  function configureSlots(candidate){\n    saveSlots(candidate);\n    setBuiltinView(currentSlot());\n    refreshHeader();\n    renderAll();",
)

# Escape transitions must synchronize visible navigation with the state they clear.
replace_once(
    "docs/prompt-kit.js",
    "if(activeSection){activeSection=null;render();return}",
    "if(activeSection){activeSection=null;renderSections();renderTypes();render();return}",
)
replace_once(
    "docs/prompt-kit.js",
    "if(activeCat!=='all'){activeCat='all';render();return}",
    "if(activeCat!=='all'){activeCat='all';syncLibraryTabs();renderTypes();render();return}",
)

# Align operator-facing access docs to the five-slot model. Doctrine/GNHF remain available
# through user profile composition rather than dedicated header positions.
replace_once(
    "PROMPT_KIT_ACCESS.md",
    "- Press **4** or use the header **Favorites** shortcut to clear transient search/type/category restrictions and show the complete saved Favorites list. Favorites remain persistent; they are not promoted ahead of normal chronological library order unless this explicit Favorites view is selected.\n- **Doctrine** remains available in the header and moves to keyboard shortcut **5**.",
    "- Press **C** or use the header **Favorites** slot to clear transient search/type/category restrictions and show the complete saved Favorites list. Favorites remain persistent; they are not promoted ahead of normal chronological library order unless this explicit Favorites view is selected.\n- Header slots are `A` All, `B` Standard, `C` Favorites, plus user-configurable `D` and `E`. The retired GNHF and Doctrine header views remain available as predefined `GNHF` and `DOCTRINE` profile packs that can be assigned to D or E without reclaiming a system hotkey.\n- Press **Home** for the true document top and **End** for the document bottom; page navigation never reuses `A`–`E`.",
)

# Executable regressions for storage denial, reset, active-slot reconfiguration, and
# preservation of retired header views as profile packs.
test_path = ROOT / "tests" / "test_prompt_kit_profiles.py"
text = test_path.read_text(encoding="utf-8")
if "ACCESS = ROOT / \"PROMPT_KIT_ACCESS.md\"" not in text:
    anchor = "DESIGN = ROOT / \"docs\" / \"PROMPT_KIT_FIVE_TAB_PROFILES.md\"\n"
    if text.count(anchor) != 1:
        raise SystemExit("tests/test_prompt_kit_profiles.py: ACCESS constant anchor drifted")
    text = text.replace(anchor, anchor + "ACCESS = ROOT / \"PROMPT_KIT_ACCESS.md\"\n", 1)

marker = "    def test_design_records_import_limits_and_hotkey_collision_rule(self) -> None:\n"
if "def test_install_guards_storage_access_and_base_reset_clears_custom_profile" not in text:
    if marker not in text:
        raise SystemExit("tests/test_prompt_kit_profiles.py: insertion marker missing")
    test = r'''    def test_install_guards_storage_access_and_base_reset_clears_custom_profile(self) -> None:
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

'''
    text = text.replace(marker, test + marker, 1)

if "def test_configuring_active_slot_reapplies_new_mode" not in text:
    test = r'''    def test_configuring_active_slot_reapplies_new_mode(self) -> None:
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

'''
    if marker not in text:
        raise SystemExit("tests/test_prompt_kit_profiles.py: second insertion marker missing")
    text = text.replace(marker, test + marker, 1)

test_path.write_text(text, encoding="utf-8")
