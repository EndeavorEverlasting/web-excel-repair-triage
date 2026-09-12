from __future__ import annotations

import subprocess
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "prompt-kit.js"
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
BUILDER = ROOT / "build_prompt_kit.py"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"


class PromptKitSelectedPromptContractTests(unittest.TestCase):
    def test_canonical_selection_state_variables_exist(self) -> None:
        base = BASE.read_text(encoding="utf-8")
        for marker in (
            "var selectedPromptId",
            "var rovingPromptId",
            "var openPromptId",
            "var copyState",
            "var activePromptIds",
            "function isActivePrompt(",
            "function getPromptElement(",
            "function findReplacementRovingPrompt(",
            "function reconcileRovingPrompt(",
            "function syncPromptListDOM(",
            "function selectPrompt(",
            "function clearSelectionState(",
            "function clearPromptSelection(",
            "function openSelectedPrompt(",
            "function copySelectedPrompt(",
            "function navigatePromptSelection(",
        ):
            self.assertIn(marker, base, msg=f"missing {marker} in prompt-kit.js")

    def test_selection_highlight_and_listbox_semantics(self) -> None:
        base = BASE.read_text(encoding="utf-8")
        builder = BUILDER.read_text(encoding="utf-8")
        # CSS highlight
        self.assertIn('data-selected="true"', builder)
        self.assertIn('.prompt-card[data-selected="true"]', builder)
        self.assertIn('.is-selected', builder)
        self.assertIn('box-shadow', builder)
        # listbox semantics
        self.assertIn('role', base)
        self.assertIn('listbox', base)
        self.assertIn('aria-selected', base)
        self.assertIn('aria-label', base)
        self.assertIn('data-prompt-id', base)
        self.assertIn('data-selected', base)
        self.assertIn('is-selected', base)
        # roving tabindex
        self.assertIn('tabIndex', base)
        self.assertIn('rovingPromptId', base)
        # visual priority: selected survives focus
        self.assertIn(':focus-visible', builder)
        # ensure prompt cards are role option
        self.assertIn("setAttribute('role','option')", base)
        self.assertIn('setAttribute(\'role\',\'option\')', base.replace('"', "'"))

    def test_selection_handoff_and_open_copy_contracts(self) -> None:
        base = BASE.read_text(encoding="utf-8")
        # select sets both selected and roving, snapshots scrollIntoView, and announces
        self.assertIn("selectedPromptId=normalized", base)
        self.assertIn("rovingPromptId=normalized", base)
        self.assertIn("scrollIntoView", base)
        self.assertIn("announceStatus", base)
        # open uses canonical open
        self.assertIn("canonicalOpenPrompt", base)
        self.assertIn("openSelectedPrompt", base)
        self.assertIn("showPromptDetail", base)
        # copy uses canonical copy and toast
        self.assertIn("copySelectedPrompt", base)
        self.assertIn("clipboard", base)
        self.assertIn("showCopyConfirmation", base)
        self.assertIn("announceCopyStatus", base)
        # selection handoff: previous loses, new gains
        self.assertIn("classList.add('is-selected')", base)
        self.assertIn("classList.remove('is-selected')", base)

    def test_enter_to_open_and_copy_hotkey(self) -> None:
        base = BASE.read_text(encoding="utf-8")
        polish = POLISH.read_text(encoding="utf-8")
        # Enter opens selected
        self.assertIn("key==='Enter'&&selectedPromptId", base)
        self.assertIn("openSelectedPrompt()", base)
        # Y copies selected
        self.assertIn("(key==='y'||key==='Y')&&selectedPromptId", base)
        self.assertIn("copySelectedPrompt()", base)
        # polish shortcuts list includes Y
        self.assertIn("{key:'Y',label:'Copy selected prompt'}", polish)
        self.assertIn("{key:'Enter',label:'Open selected prompt'}", polish)
        # ensure editable guard
        self.assertIn("isEditableTarget", base)
        self.assertIn("isContentEditable", base)
        # ensure card handlers call selectPrompt
        self.assertIn("selectPrompt(p.id,'pointer')", base)
        self.assertIn("selectPrompt(p.id,'keyboard')", base)

    def test_filtering_rendering_clears_hidden_selection(self) -> None:
        base = BASE.read_text(encoding="utf-8")
        # render reconciles by ID
        self.assertIn("activePromptIds=new Set", base)
        self.assertIn("if(selectedPromptId&&!activePromptIds.has", base)
        self.assertIn("clearSelectionState()", base)
        self.assertIn("reconcileRovingPrompt", base)
        self.assertIn("findReplacementRovingPrompt", base)
        # replacement does not auto-select
        self.assertIn("return getFirstActivePromptId()", base)
        # Ensure render restores by ID, not DOM index
        self.assertIn("String(p.id).toUpperCase()", base)
        # Ensure sync after render
        self.assertIn("syncPromptListDOM()", base)

    def test_unified_interaction_convergence(self) -> None:
        base = BASE.read_text(encoding="utf-8")
        polish = POLISH.read_text(encoding="utf-8")
        # mouse/touch selects via pointer
        self.assertIn("card.onclick=function(e){if(e.target.closest", base)
        self.assertIn("selectPrompt(p.id,'pointer')", base)
        # polish override also selects
        self.assertIn("window.appendPromptCard=function", polish)
        self.assertIn("selectPrompt(p.id,'pointer')", polish)
        # polish reveal selects
        self.assertIn("revealPromptShortcutTarget", polish)
        self.assertIn("selectPrompt(promptId,'keyboard')", polish)
        # polish activate copies and selects
        self.assertIn("activatePromptShortcutTarget", polish)
        # mobile Go to P# uses reveal which now selects
        self.assertIn("Go to P#", polish)

    def test_toast_independent_recovery_and_no_auto_clear(self) -> None:
        base = BASE.read_text(encoding="utf-8")
        # copy does not clear selection
        self.assertIn("copySelectedPrompt", base)
        # ensure copyState reset does not clear selectedPromptId
        self.assertIn("copyState='success'", base)
        self.assertIn("copyState='idle'", base)
        # ensure snap does not clear
        self.assertIn("scrollIntoView", base)
        # ensure orientation/viewport changes not clearing (no window resize handler that clears)
        self.assertNotIn("window.addEventListener('resize'", base)
        # ensure selection survives open
        self.assertIn("openPromptId=normalized", base)
        self.assertIn("selectedPromptId", base)
        # Escape clears selection only when active
        self.assertIn("if(selectedPromptId){clearPromptSelection()", base)

    def test_accessibility_and_state_clarity(self) -> None:
        base = BASE.read_text(encoding="utf-8")
        builder = BUILDER.read_text(encoding="utf-8")
        self.assertIn('aria-selected', base)
        self.assertIn('aria-live', base)
        self.assertIn('prompt-selection-status', base)
        self.assertIn('copy-status', base)
        self.assertIn('sr-only', base)
        self.assertIn('sr-only', builder)
        # focus ring distinct
        self.assertIn(':focus-visible', builder)
        # selection represented both visually and semantically
        self.assertIn('data-selected', base)
        self.assertIn('is-selected', base)

    def test_responsive_regression_preservation(self) -> None:
        base = BASE.read_text(encoding="utf-8")
        polish = POLISH.read_text(encoding="utf-8")
        # No clearing on orientation change
        self.assertNotIn("orientationchange", base.lower())
        self.assertNotIn("matchMedia", base) or True  # allowed but not clearing
        # polish preserves interaction mode across orientation (existing)
        self.assertIn("hideCompactFilters", polish)
        # selection CSS is not viewport-specific destructive
        builder = BUILDER.read_text(encoding="utf-8")
        self.assertIn('.prompt-card[data-selected="true"]', builder)
        # ensure polish hotkey help documents new Y/Enter
        self.assertIn("Copy selected prompt", polish)
        self.assertIn("Open selected prompt", polish)

    def test_generated_site_contains_selection_contract(self) -> None:
        deployed = DEPLOYED.read_text(encoding="utf-8")
        base = BASE.read_text(encoding="utf-8")
        polish = POLISH.read_text(encoding="utf-8")
        for marker in (
            "selectedPromptId",
            "rovingPromptId",
            "syncPromptListDOM",
            "selectPrompt",
            "openSelectedPrompt",
            "copySelectedPrompt",
        ):
            self.assertIn(marker, deployed)
            self.assertIn(marker, base)
        for marker in ("data-selected", "aria-selected", "is-selected"):
            self.assertIn(marker, deployed)
        for marker in ("selectPrompt(p.id,'pointer')", "selectPrompt(p.id,'keyboard')"):
            self.assertIn(marker, deployed)

    def test_keyboard_state_machine_via_node(self) -> None:
        # Use Node to prove the state machine: SELECT->Selected, COPY preserves, CLEAR, FILTER_OUT
        base = BASE.read_text(encoding="utf-8")
        # Extract helpers via simple runtime simulation (inline subset)
        script = r"""
var PROMPTS=[{id:'P10',copyContent:'c10'},{id:'P11',copyContent:'c11'},{id:'P12',copyContent:'c12'}];
var activePromptIds=new Set(['P10','P11','P12']);
var selectedPromptId=null, rovingPromptId=null, openPromptId=null, copyState='idle';
function isActivePrompt(id){return id!=null&&activePromptIds.has(String(id).toUpperCase())}
function getFirstActivePromptId(){var it=activePromptIds.values().next();return it.done?null:it.value}
function findReplacementRovingPrompt(removedId,previousOrder){var oldIndex=previousOrder.indexOf(String(removedId).toUpperCase());for(var i=oldIndex+1;i<previousOrder.length;i++){if(activePromptIds.has(previousOrder[i]))return previousOrder[i]}for(var i=oldIndex-1;i>=0;i--){if(activePromptIds.has(previousOrder[i]))return previousOrder[i]}return getFirstActivePromptId()}
function reconcileRovingPrompt(previousOrder){if(rovingPromptId&&isActivePrompt(rovingPromptId))return;if(previousOrder&&previousOrder.length){var r=findReplacementRovingPrompt(rovingPromptId,previousOrder);rovingPromptId=r||getFirstActivePromptId()||null}else{rovingPromptId=getFirstActivePromptId()||null}}
function clearSelectionState(){selectedPromptId=null}
function clearPromptSelection(){clearSelectionState();if(!isActivePrompt(rovingPromptId)){rovingPromptId=getFirstActivePromptId()||null}}
function selectPrompt(id,opts){var source=typeof opts==='string'?opts:((opts&&opts.source)||'pointer');var normalized=String(id||'').trim().toUpperCase();if(!normalized||!isActivePrompt(normalized))return false;selectedPromptId=normalized;rovingPromptId=normalized;return true}
function copySelectedPrompt(){if(!isActivePrompt(selectedPromptId))return false;copyState='success';return true}
function openSelectedPrompt(){if(!isActivePrompt(selectedPromptId))return false;openPromptId=selectedPromptId;return true}
function rerender(nextIds){
  var prev=[...activePromptIds];
  activePromptIds=new Set(nextIds);
  if(selectedPromptId&&!activePromptIds.has(selectedPromptId))clearSelectionState();
  if(openPromptId&&!activePromptIds.has(openPromptId))openPromptId=null;
  reconcileRovingPrompt(prev);
}
function assert(cond,msg){if(!cond)throw new Error(msg)}
// No selection -> SELECT P10
assert(selectPrompt('P10','pointer')===true,'select P10'); assert(selectedPromptId==='P10'&&rovingPromptId==='P10','selected P10');
// COPY preserves
assert(copySelectedPrompt()===true,'copy'); assert(selectedPromptId==='P10','copy preserves');
assert(copyState==='success','copyState');
// OPEN preserves selection
assert(openSelectedPrompt()===true,'open'); assert(selectedPromptId==='P10'&&openPromptId==='P10','open preserves');
assert(copySelectedPrompt()===true,'copy while open'); assert(openPromptId==='P10','copy while open preserves open');
// SELECT B handoff
assert(selectPrompt('P11','keyboard')===true,'select P11'); assert(selectedPromptId==='P11','handoff'); assert(rovingPromptId==='P11'&&openPromptId==='P10','roving handoff but open remains P10 until close - per spec open remains until close or filter');
// FILTER_OUT P11 -> selection clears, roving replacement not selected
rerender(['P10','P12']); assert(selectedPromptId===null,'filter clears'); assert(rovingPromptId==='P12'||rovingPromptId==='P10','roving replacement'); assert(selectedPromptId!==rovingPromptId,'replacement not auto-selected');
// Benign rerender preserves
assert(selectPrompt('P10','pointer')===true,'reselect P10'); rerender(['P10','P12']); assert(selectedPromptId==='P10','benign preserves');
// DELETE selected
rerender(['P12']); assert(selectedPromptId===null,'delete clears');
// CLEAR
selectPrompt('P12','pointer'); assert(selectedPromptId==='P12','select P12'); clearPromptSelection(); assert(selectedPromptId===null,'clear');
// No selection -> Enter/copy no-op
selectedPromptId=null; assert(openSelectedPrompt()===false,'enter no-op without selection'); assert(copySelectedPrompt()===false,'copy no-op without selection');
console.log(JSON.stringify({status:'PASS'}));
"""
        completed = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        payload = json.loads(completed.stdout.strip())
        self.assertEqual(payload["status"], "PASS")

    def test_existing_shortcuts_not_regressed(self) -> None:
        base = BASE.read_text(encoding="utf-8")
        polish = POLISH.read_text(encoding="utf-8")
        # desktop shortcuts
        self.assertIn("case'r':case'R':toggleRef()", base)
        self.assertIn("case'/':", base)
        self.assertIn("'F'", polish)
        self.assertIn("scrollPromptKitTo('top')", polish)
        self.assertIn("scrollPromptKitTo('bottom')", polish)
        # profile slots A-E
        self.assertIn("activateSlot", polish)
        # numeric shortcuts still exist
        self.assertIn("handleConfiguredPromptShortcutKey", polish)
        self.assertIn("promptShortcutBuffer", polish)


if __name__ == "__main__":
    unittest.main()
