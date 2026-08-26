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

# Base/logo reset must clear the profile projection before base render runs.
replace_once(
    "docs/prompt-kit-profiles.js",
    "  if(typeof baseRender==='function')root.render=function(){return projectCall(baseRender,arguments)};\n  if(typeof baseRenderTypes==='function')root.renderTypes=function(){return projectCall(baseRenderTypes,arguments)};\n  if(typeof baseRenderSections==='function')root.renderSections=function(){return projectCall(baseRenderSections,arguments)};\n\n  function clearTransientBrowserFilters(){",
    "  if(typeof baseRender==='function')root.render=function(){return projectCall(baseRender,arguments)};\n  if(typeof baseRenderTypes==='function')root.renderTypes=function(){return projectCall(baseRenderTypes,arguments)};\n  if(typeof baseRenderSections==='function')root.renderSections=function(){return projectCall(baseRenderSections,arguments)};\n  var baseResetPromptKitView=root.resetPromptKitView;\n  if(typeof baseResetPromptKitView==='function')root.resetPromptKitView=function(){\n    activeKey='A';\n    try{persistActive('A')}catch(e){}\n    var result=baseResetPromptKitView.apply(root,arguments);\n    refreshHeader();\n    updateEditor();\n    return result\n  };\n\n  function clearTransientBrowserFilters(){",
)

# Executable regression for storage denial + custom-profile reset.
test_path = ROOT / "tests" / "test_prompt_kit_profiles.py"
text = test_path.read_text(encoding="utf-8")
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
    test_path.write_text(text.replace(marker, test + marker, 1), encoding="utf-8")
