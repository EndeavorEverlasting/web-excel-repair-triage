#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    polish_path = ROOT / "docs" / "prompt-kit-polish.js"
    source = polish_path.read_text(encoding="utf-8")

    old_fn = """function setHotkeyHelpOpen(open,restoreFocus){
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
    new_fn = """function mobileQuickControlsActive(){
  return !!(window.matchMedia&&window.matchMedia('(max-width:760px)').matches)
}

function setHotkeyHelpOpen(open,restoreFocus){
  var panel=document.getElementById('hotkeyHelpPanel');
  var toggle=document.getElementById('hotkeyHelpToggle');
  if(!panel||!toggle)return;
  panel.hidden=!open;
  toggle.setAttribute('aria-expanded',open?'true':'false');
  if(open){
    if(!mobileQuickControlsActive()&&focusFavoritePromptShortcutInput(panel))return;
    var target=mobileQuickControlsActive()?panel.querySelector('[data-mobile-quick-action="find"]'):panel.querySelector('.hotkey-help-close');
    if(target){try{target.focus({preventScroll:true})}catch(e){target.focus()}}
    return;
  }
  if(restoreFocus){try{toggle.focus({preventScroll:true})}catch(e){toggle.focus()}}
}
"""
    source = replace_once(source, old_fn, new_fn, "hotkey panel focus function")
    polish_path.write_text(source, encoding="utf-8")

    static_path = ROOT / "tests" / "test_prompt_kit_mobile_quick_controls.py"
    static = static_path.read_text(encoding="utf-8")
    anchor = """    def test_mobile_sheet_is_visible_and_describes_gestures(self) -> None:
"""
    test = """    def test_mobile_open_focuses_touch_command_without_opening_keyboard_input(self) -> None:
        source = POLISH.read_text(encoding=\"utf-8\")
        self.assertIn(\"function mobileQuickControlsActive()\", source)
        self.assertIn(\"if(!mobileQuickControlsActive()&&focusFavoritePromptShortcutInput(panel))return;\", source)
        self.assertIn(\"panel.querySelector('[data-mobile-quick-action=\\\"find\\\"]')\", source)

"""
    if "test_mobile_open_focuses_touch_command_without_opening_keyboard_input" not in static:
        static = replace_once(static, anchor, test + anchor, "static focus regression")
    static_path.write_text(static, encoding="utf-8")

    browser_path = ROOT / "tests" / "prompt_kit_mobile_quick_controls_browser_proof.py"
    browser = browser_path.read_text(encoding="utf-8")
    anchor = """                assert quick.is_visible(), \"touch command grid not visible\"
                buttons = quick.locator(\".mobile-quick-action\")
"""
    replacement = """                assert quick.is_visible(), \"touch command grid not visible\"
                active_id = page.evaluate(\"document.activeElement && document.activeElement.id\")
                assert active_id != \"promptShortcutPromptId\", active_id
                active_action = page.evaluate(\"document.activeElement && document.activeElement.getAttribute('data-mobile-quick-action')\")
                assert active_action == \"find\", active_action
                buttons = quick.locator(\".mobile-quick-action\")
"""
    if "active_action == \"find\"" not in browser:
        browser = replace_once(browser, anchor, replacement, "browser focus regression")
    browser_path.write_text(browser, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
