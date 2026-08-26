from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"{label} anchor drifted")
    return text.replace(old, new, 1)


polish_path = ROOT / "docs/prompt-kit-polish.js"
source = polish_path.read_text(encoding="utf-8")

if "function focusFavoritePromptShortcutInput(panel)" not in source:
    old_open = """function setHotkeyHelpOpen(open,restoreFocus){
  var panel=document.getElementById('hotkeyHelpPanel');
  var toggle=document.getElementById('hotkeyHelpToggle');
  if(!panel||!toggle)return;
  panel.hidden=!open;
  toggle.setAttribute('aria-expanded',open?'true':'false');
  if(open){
    var close=panel.querySelector('.hotkey-help-close');
    if(close){try{close.focus({preventScroll:true})}catch(e){close.focus()}}
    return;
  }
  if(restoreFocus){try{toggle.focus({preventScroll:true})}catch(e){toggle.focus()}}
}
"""
    new_open = """function focusFavoritePromptShortcutInput(panel){
  var promptInput=document.getElementById('promptShortcutPromptId');
  if(!panel||!promptInput||!panel.contains(promptInput))return false;
  try{promptInput.focus()}catch(e){return false}
  try{promptInput.scrollIntoView({block:'nearest',inline:'nearest'})}catch(e){try{promptInput.scrollIntoView()}catch(ignore){}}
  return document.activeElement===promptInput
}

function setHotkeyHelpOpen(open,restoreFocus){
  var panel=document.getElementById('hotkeyHelpPanel');
  var toggle=document.getElementById('hotkeyHelpToggle');
  if(!panel||!toggle)return;
  panel.hidden=!open;
  toggle.setAttribute('aria-expanded',open?'true':'false');
  if(open){
    if(focusFavoritePromptShortcutInput(panel))return;
    var close=panel.querySelector('.hotkey-help-close');
    if(close){try{close.focus({preventScroll:true})}catch(e){close.focus()}}
    return;
  }
  if(restoreFocus){try{toggle.focus({preventScroll:true})}catch(e){toggle.focus()}}
}
"""
    source = replace_once(source, old_open, new_open, "setHotkeyHelpOpen")

escape_guard = "if(key==='escape'&&escapeHelpPanel&&!escapeHelpPanel.hidden)"
editable_guard = "if(editable)return;"
if source.index(escape_guard) > source.index(editable_guard):
    old_dispatch = """    if(e.defaultPrevented||e.altKey||e.metaKey||e.ctrlKey)return;
    if(editable)return;
    if(key==='`'){
      e.preventDefault();e.stopImmediatePropagation();
      var helpPanel=document.getElementById('hotkeyHelpPanel');
      setHotkeyHelpOpen(helpPanel?helpPanel.hidden:true,false);
      resetPromptShortcutBuffer();
      return
    }
    if(key==='escape')resetPromptShortcutBuffer();
    var escapeHelpPanel=document.getElementById('hotkeyHelpPanel');
    if(key==='escape'&&escapeHelpPanel&&!escapeHelpPanel.hidden){
      e.preventDefault();e.stopImmediatePropagation();setHotkeyHelpOpen(false,true);return
    }
"""
    new_dispatch = """    if(e.defaultPrevented||e.altKey||e.metaKey||e.ctrlKey)return;
    var escapeHelpPanel=document.getElementById('hotkeyHelpPanel');
    if(key==='escape'&&escapeHelpPanel&&!escapeHelpPanel.hidden){
      e.preventDefault();e.stopImmediatePropagation();resetPromptShortcutBuffer();setHotkeyHelpOpen(false,true);return
    }
    if(editable)return;
    if(key==='`'){
      e.preventDefault();e.stopImmediatePropagation();
      var helpPanel=document.getElementById('hotkeyHelpPanel');
      setHotkeyHelpOpen(helpPanel?helpPanel.hidden:true,false);
      resetPromptShortcutBuffer();
      return
    }
    if(key==='escape')resetPromptShortcutBuffer();
"""
    source = replace_once(source, old_dispatch, new_dispatch, "hotkey dispatcher")

polish_path.write_text(source, encoding="utf-8")


test_path = ROOT / "tests/test_prompt_kit_hotkey_completion.py"
tests = test_path.read_text(encoding="utf-8")
if "def test_hotkey_open_focuses_favorite_input_and_escape_recovers_from_editable" not in tests:
    anchor = "    def test_favorite_prompt_shortcuts_are_persisted_fail_closed(self) -> None:\n"
    method = '''    def test_hotkey_open_focuses_favorite_input_and_escape_recovers_from_editable(self) -> None:\n        source = POLISH.read_text(encoding="utf-8")\n        for marker in (\n            "function focusFavoritePromptShortcutInput(panel)",\n            "document.getElementById('promptShortcutPromptId')",\n            "promptInput.focus()",\n            "promptInput.scrollIntoView({block:'nearest',inline:'nearest'})",\n            "if(focusFavoritePromptShortcutInput(panel))return",\n        ):\n            self.assertIn(marker, source)\n        escape_guard = "if(key==='escape'&&escapeHelpPanel&&!escapeHelpPanel.hidden)"\n        editable_guard = "if(editable)return;"\n        backtick = "if(key==='`')"\n        self.assertLess(source.index(escape_guard), source.index(editable_guard))\n        self.assertLess(source.index(editable_guard), source.index(backtick))\n        self.assertIn("resetPromptShortcutBuffer();setHotkeyHelpOpen(false,true);return", source)\n\n'''
    tests = replace_once(tests, anchor, method + anchor, "hotkey static test insertion")

parity_start = tests.index("    def test_configuration_ui_and_generated_parity_are_present")
if '"function focusFavoritePromptShortcutInput(panel)",' not in tests[parity_start:]:
    anchor = '            "Save favorite prompt keyboard shortcut",\n'
    addition = (
        '            "function focusFavoritePromptShortcutInput(panel)",\n'
        '            "promptInput.scrollIntoView({block:\'nearest\',inline:\'nearest\'})",\n'
        '            "resetPromptShortcutBuffer();setHotkeyHelpOpen(false,true);return",\n'
    )
    tests = replace_once(tests, anchor, anchor + addition, "generated parity marker")
test_path.write_text(tests, encoding="utf-8")


browser_path = ROOT / "tests/prompt_kit_favorite_browser_proof.py"
browser = browser_path.read_text(encoding="utf-8")
if "hotkey_click_focuses_favorite_input" not in browser:
    anchor = "            page.locator('#hotkeyHelpToggle').click()\n            page.locator('#promptShortcutPromptId').fill('P79')\n"
    replacement = '''            page.locator('#hotkeyHelpToggle').click()\n            page.wait_for_timeout(50)\n            click_focus = page.evaluate("document.activeElement && document.activeElement.id === 'promptShortcutPromptId'")\n            click_visible = page.evaluate("""() => {\n              const input=document.getElementById('promptShortcutPromptId');\n              const panel=document.getElementById('hotkeyHelpPanel');\n              if(!input||!panel||panel.hidden)return false;\n              const r=input.getBoundingClientRect();\n              const pr=panel.getBoundingClientRect();\n              return r.bottom>pr.top && r.top<pr.bottom && r.bottom>0 && r.top<innerHeight;\n            }""")\n            page.keyboard.press('Escape')\n            page.wait_for_timeout(50)\n            escape_closed = page.evaluate("document.getElementById('hotkeyHelpPanel').hidden")\n            escape_focus_returned = page.evaluate("document.activeElement && document.activeElement.id === 'hotkeyHelpToggle'")\n            page.keyboard.press('Backquote')\n            page.wait_for_timeout(50)\n            backtick_focus = page.evaluate("document.activeElement && document.activeElement.id === 'promptShortcutPromptId'")\n            backtick_visible = page.evaluate("""() => {\n              const input=document.getElementById('promptShortcutPromptId');\n              const panel=document.getElementById('hotkeyHelpPanel');\n              if(!input||!panel||panel.hidden)return false;\n              const r=input.getBoundingClientRect();\n              const pr=panel.getBoundingClientRect();\n              return r.bottom>pr.top && r.top<pr.bottom && r.bottom>0 && r.top<innerHeight;\n            }""")\n            page.locator('#promptShortcutPromptId').fill('P79')\n'''
    browser = replace_once(browser, anchor, replacement, "browser focus setup")

    anchor = '''            observations = [\n                {"id": "favorite_setup_saved", "event": "P79 favorited and p79 shortcut saved through product UI", "occurred": True, "passed": bool(setup_saved)},\n'''
    replacement = '''            observations = [\n                {"id": "hotkey_click_focuses_favorite_input", "event": "Hotkeys button opens the panel with Favorite prompt ID input focused and revealed", "occurred": True, "passed": bool(click_focus and click_visible), "focused": bool(click_focus), "visible": bool(click_visible)},\n                {"id": "escape_closes_hotkeys_from_favorite_input", "event": "Escape closes Hotkeys while Favorite prompt ID input owns focus and returns focus to Hotkeys toggle", "occurred": True, "passed": bool(escape_closed and escape_focus_returned), "closed": bool(escape_closed), "toggle_focused": bool(escape_focus_returned)},\n                {"id": "hotkey_backtick_focuses_favorite_input", "event": "Backtick opens Hotkeys with Favorite prompt ID input focused and revealed", "occurred": True, "passed": bool(backtick_focus and backtick_visible), "focused": bool(backtick_focus), "visible": bool(backtick_visible)},\n                {"id": "favorite_setup_saved", "event": "P79 favorited and p79 shortcut saved through product UI", "occurred": True, "passed": bool(setup_saved)},\n'''
    browser = replace_once(browser, anchor, replacement, "browser observations")

    anchor = "    auto_copy = all(by_id[item]['passed'] for item in ('favorite_setup_saved', 'favorite_shortcut_dispatched', 'clipboard_exact_match'))\n"
    replacement = "    hotkey_config_recovery = all(by_id[item]['passed'] for item in ('hotkey_click_focuses_favorite_input', 'escape_closes_hotkeys_from_favorite_input', 'hotkey_backtick_focuses_favorite_input'))\n" + anchor
    browser = replace_once(browser, anchor, replacement, "browser claim calculation")

    browser = replace_once(
        browser,
        '"scenario": "favorite-shortcut-copy-reveal-focus"',
        '"scenario": "hotkey-config-focus-escape-and-favorite-shortcut-copy-reveal"',
        "browser scenario",
    )

    anchor = '''        "claims": [\n            {"id": "favorite_auto_copy", "statement": "Typing configured Favorite P79 automatically copies canonical prompt content", "status": "PASS" if auto_copy else "FAIL", "required_evidence_class": "browser_runtime_observed", "observation_ids": ["favorite_setup_saved", "favorite_shortcut_dispatched", "clipboard_exact_match"]},\n'''
    replacement = '''        "claims": [\n            {"id": "hotkey_config_focus_escape", "statement": "Opening Hotkeys by button or backtick focuses and reveals the Favorite prompt ID field, and Escape closes Hotkeys from that field", "status": "PASS" if hotkey_config_recovery else "FAIL", "required_evidence_class": "browser_runtime_observed", "observation_ids": ["hotkey_click_focuses_favorite_input", "escape_closes_hotkeys_from_favorite_input", "hotkey_backtick_focuses_favorite_input"]},\n            {"id": "favorite_auto_copy", "statement": "Typing configured Favorite P79 automatically copies canonical prompt content", "status": "PASS" if auto_copy else "FAIL", "required_evidence_class": "browser_runtime_observed", "observation_ids": ["favorite_setup_saved", "favorite_shortcut_dispatched", "clipboard_exact_match"]},\n'''
    browser = replace_once(browser, anchor, replacement, "browser claims")

browser_path.write_text(browser, encoding="utf-8")


design_path = ROOT / "docs/PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md"
design = design_path.read_text(encoding="utf-8")
design_line = "- opening Hotkeys by either the visible button or unmodified backtick reveals and focuses the Favorite prompt ID input; `Escape` closes Hotkeys even while that editable input owns focus and restores focus to the Hotkeys toggle.\n"
if design_line not in design:
    anchor = "- shortcut persistence uses versioned `promptKit.promptShortcuts.v1` storage and publishes only after a successful durable write.\n"
    design = replace_once(design, anchor, anchor + design_line, "hotkey design")
design_path.write_text(design, encoding="utf-8")

print("hotkey favorite focus + escape patch applied")
