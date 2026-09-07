from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
TEST = ROOT / "tests" / "test_prompt_kit_mobile_quick_controls.py"
BROWSER = ROOT / "tests" / "prompt_kit_mobile_quick_controls_browser_proof.py"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-mobile.v1.json"
GUIDE = ROOT / "OPEN_PROMPT_KIT_ON_PHONE.md"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    start_i = text.find(start)
    if start_i < 0:
        raise SystemExit(f"{label}: start anchor missing")
    end_i = text.find(end, start_i)
    if end_i < 0:
        raise SystemExit(f"{label}: end anchor missing")
    if text.find(start, start_i + 1) >= 0:
        raise SystemExit(f"{label}: start anchor is not unique")
    return text[:start_i] + replacement + text[end_i:]


source = POLISH.read_text(encoding="utf-8")

# Replace gesture-first mobile navigation with a direct known-ID route plus explicit More actions.
new_mobile_block = r'''var MOBILE_QUICK_PROFILE_KEYS=['A','B','C','D','E'];

function mobileQuickCurrentProfileKey(){
  try{
    if(window.PromptKitProfiles&&typeof window.PromptKitProfiles.getState==='function'){
      var state=window.PromptKitProfiles.getState();
      if(state&&MOBILE_QUICK_PROFILE_KEYS.indexOf(state.activeKey)>=0)return state.activeKey
    }
  }catch(e){}
  var active=document.querySelector('.cat-tab.profile-slot.active[data-profile-slot]');
  var key=active&&active.getAttribute('data-profile-slot');
  return MOBILE_QUICK_PROFILE_KEYS.indexOf(key)>=0?key:'A'
}

function mobileQuickCycleProfile(delta){
  if(!window.PromptKitProfiles||typeof window.PromptKitProfiles.activateSlot!=='function')return false;
  var current=mobileQuickCurrentProfileKey();
  var index=MOBILE_QUICK_PROFILE_KEYS.indexOf(current);
  var next=(index+delta+MOBILE_QUICK_PROFILE_KEYS.length)%MOBILE_QUICK_PROFILE_KEYS.length;
  window.PromptKitProfiles.activateSlot(MOBILE_QUICK_PROFILE_KEYS[next]);
  return true
}

function mobileQuickFocusSearch(){
  showCompactFilters();
  var search=document.getElementById('search');
  if(!search)return false;
  try{search.focus()}catch(e){return false}
  try{search.scrollIntoView({block:'center',inline:'nearest'})}catch(e){}
  return true
}

function performMobileQuickAction(action,origin){
  if(action!=='panel')setHotkeyHelpOpen(false,false);
  if(action==='find'){
    if(typeof window.openPromptFinder==='function'){
      window.openPromptFinder(origin||document.getElementById('hotkeyHelpToggle'));
      return true
    }
    return mobileQuickFocusSearch()
  }
  if(action==='search')return mobileQuickFocusSearch();
  if(action==='profile-prev')return mobileQuickCycleProfile(-1);
  if(action==='profile-next')return mobileQuickCycleProfile(1);
  if(action==='favorites'){activateFavoritesView();return true}
  if(action==='filters'){toggleCompactFilters();return true}
  if(action==='reference'){
    var ref=document.getElementById('refBtn');
    if(ref){ref.click();return true}
    return false
  }
  if(action==='top'){scrollPromptKitTo('top');return true}
  if(action==='bottom'){scrollPromptKitTo('bottom');return true}
  return false
}

function mobilePromptJumpDigits(raw){
  return String(raw||'').replace(/\D+/g,'').slice(0,6)
}

function mobilePromptJumpPrompt(promptId){
  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];
  return catalog.find(function(item){return item&&item.id===promptId})||null
}

function mobilePromptJumpHasPrefix(promptId){
  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];
  return catalog.some(function(item){return item&&typeof item.id==='string'&&item.id!==promptId&&item.id.indexOf(promptId)===0})
}

function setMobilePromptJumpOpen(open,restoreFocus){
  var form=document.getElementById('mobilePromptJumpForm');
  var toggle=document.getElementById('mobilePromptJumpToggle');
  var input=document.getElementById('mobilePromptJumpInput');
  if(!form||!toggle)return false;
  form.hidden=!open;
  toggle.setAttribute('aria-expanded',open?'true':'false');
  if(open&&input){
    input.value='';
    var status=document.getElementById('mobilePromptJumpStatus');
    if(status)status.textContent='Type the digits after P. Example: 111.';
    try{input.focus({preventScroll:true})}catch(e){input.focus()}
  }else if(restoreFocus){
    try{toggle.focus({preventScroll:true})}catch(e){toggle.focus()}
  }
  return true
}

function resolveMobilePromptJump(force){
  var input=document.getElementById('mobilePromptJumpInput');
  var status=document.getElementById('mobilePromptJumpStatus');
  var toggle=document.getElementById('mobilePromptJumpToggle');
  if(!input)return false;
  var digits=mobilePromptJumpDigits(input.value);
  if(input.value!==digits)input.value=digits;
  if(!digits){if(status)status.textContent='Type the digits after P. Example: 111.';return false}
  var promptId='P'+digits;
  var prompt=mobilePromptJumpPrompt(promptId);
  var longer=mobilePromptJumpHasPrefix(promptId);
  if(prompt&&(!longer||force)){
    setMobilePromptJumpOpen(false,false);
    setHotkeyHelpOpen(false,false);
    if(typeof window.showPromptDetail==='function'){
      window.showPromptDetail(promptId,toggle||null);
      return true
    }
    if(status)status.textContent='Prompt detail is unavailable.';
    return false
  }
  if(prompt&&longer){if(status)status.textContent=promptId+' exists. Keep typing, or tap Go for '+promptId+'.';return false}
  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];
  var hasCandidate=catalog.some(function(item){return item&&typeof item.id==='string'&&item.id.indexOf(promptId)===0});
  if(status)status.textContent=hasCandidate?'Keep typing '+promptId+'…':'No prompt begins with '+promptId+'.';
  return false
}

function installMobilePromptJump(shell){
  if(!shell||document.getElementById('mobilePromptJump'))return;
  if(!document.getElementById('mobile-prompt-jump-styles')){
    var style=document.createElement('style');
    style.id='mobile-prompt-jump-styles';
    style.textContent='.mobile-prompt-jump{display:none}.mobile-prompt-jump-form[hidden]{display:none}@media(max-width:760px){.hotkey-help{display:flex;align-items:flex-end;gap:8px;right:12px;bottom:12px}.mobile-prompt-jump{display:block;position:relative}.mobile-prompt-jump-toggle,.hotkey-help-toggle{min-height:52px;border-radius:999px;touch-action:manipulation!important}.mobile-prompt-jump-toggle{display:inline-flex;align-items:center;justify-content:center;padding:8px 14px;border:1px solid rgba(56,189,248,.75);background:linear-gradient(135deg,rgba(2,132,199,.96),rgba(15,23,42,.98));color:var(--text-primary);font:800 12px/1 inherit;box-shadow:0 0 0 1px rgba(56,189,248,.14),0 0 18px rgba(56,189,248,.28),0 8px 24px rgba(0,0,0,.28)}.mobile-prompt-jump-toggle:focus-visible{outline:none;box-shadow:0 0 0 3px var(--accent-glow),0 0 24px rgba(56,189,248,.4)}.mobile-prompt-jump-form{position:fixed;right:12px;bottom:74px;width:min(300px,calc(100vw - 24px));display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:center;gap:8px;padding:10px;border:1px solid rgba(56,189,248,.55);border-radius:12px;background:rgba(15,23,42,.99);box-shadow:0 14px 40px rgba(0,0,0,.48);z-index:47}.mobile-prompt-jump-prefix{font:900 18px/1 ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--accent)}.mobile-prompt-jump-input{min-width:0;height:48px;box-sizing:border-box;padding:8px 10px;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);color:var(--text-primary);font:800 18px/1 ui-monospace,SFMono-Regular,Consolas,monospace}.mobile-prompt-jump-go{min-width:52px;height:48px;border:1px solid var(--accent);border-radius:8px;background:var(--accent-glow);color:var(--text-primary);font:800 12px/1 inherit}.mobile-prompt-jump-status{grid-column:1/-1;min-height:16px;color:var(--text-secondary);font-size:10px;line-height:1.35}.mobile-quick-label{display:inline}.mobile-quick-handle-cue{display:none!important}}';
    document.head.appendChild(style)
  }
  var jump=document.createElement('div');
  jump.className='mobile-prompt-jump';
  jump.id='mobilePromptJump';
  var toggle=document.createElement('button');
  toggle.className='mobile-prompt-jump-toggle';
  toggle.id='mobilePromptJumpToggle';
  toggle.type='button';
  toggle.textContent='Go to P#';
  toggle.setAttribute('aria-expanded','false');
  toggle.setAttribute('aria-controls','mobilePromptJumpForm');
  toggle.setAttribute('aria-label','Go directly to a prompt by number');
  var form=document.createElement('form');
  form.className='mobile-prompt-jump-form';
  form.id='mobilePromptJumpForm';
  form.hidden=true;
  form.setAttribute('aria-label','Go directly to prompt ID');
  var prefix=document.createElement('span');
  prefix.className='mobile-prompt-jump-prefix';
  prefix.textContent='P';
  prefix.setAttribute('aria-hidden','true');
  var input=document.createElement('input');
  input.className='mobile-prompt-jump-input';
  input.id='mobilePromptJumpInput';
  input.type='text';
  input.inputMode='numeric';
  input.pattern='[0-9]*';
  input.enterKeyHint='go';
  input.autocomplete='off';
  input.placeholder='111';
  input.setAttribute('aria-label','Prompt number after P');
  var go=document.createElement('button');
  go.className='mobile-prompt-jump-go';
  go.type='submit';
  go.textContent='Go';
  go.setAttribute('aria-label','Open exact prompt ID');
  var status=document.createElement('div');
  status.className='mobile-prompt-jump-status';
  status.id='mobilePromptJumpStatus';
  status.setAttribute('role','status');
  status.setAttribute('aria-live','polite');
  form.appendChild(prefix);form.appendChild(input);form.appendChild(go);form.appendChild(status);
  jump.appendChild(toggle);jump.appendChild(form);shell.appendChild(jump);
  toggle.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();setHotkeyHelpOpen(false,false);setMobilePromptJumpOpen(form.hidden,false)});
  input.addEventListener('input',function(){resolveMobilePromptJump(false)});
  input.addEventListener('keydown',function(e){if(e.key==='Escape'){e.preventDefault();setMobilePromptJumpOpen(false,true)}});
  form.addEventListener('submit',function(e){e.preventDefault();resolveMobilePromptJump(true)});
}

'''
source = replace_between(
    source,
    "var MOBILE_QUICK_GESTURE_THRESHOLD=38;",
    "function normalizePromptShortcutId(raw){",
    new_mobile_block,
    "mobile navigation block",
)

# Remove obsolete gesture-only CSS when present. Keep this tolerant of the older main variant after merge.
gesture_css_start = source.find(".mobile-quick-gesture-guide{")
gesture_css_end = source.find(".mobile-quick-grid{", gesture_css_start)
if gesture_css_start >= 0 and gesture_css_end > gesture_css_start:
    source = source[:gesture_css_start] + source[gesture_css_end:]
source = source.replace(".mobile-quick-gesture-guide{display:block}.mobile-quick-gesture-map{display:grid}", "")

# Ensure the direct jump is installed before the More control is created.
source = replace_once(
    source,
    "  shell.className='hotkey-help';\n  shell.id='hotkeyHelp';\n\n  var toggle=document.createElement('button');",
    "  shell.className='hotkey-help';\n  shell.id='hotkeyHelp';\n  installMobilePromptJump(shell);\n\n  var toggle=document.createElement('button');",
    "jump installation",
)

# Normalize mobile handle semantics after reconciling whichever prior Quick Controls wording was present.
source = re.sub(
    r"  toggle\.setAttribute\('aria-label','[^']*(?:Hotkeys|Quick Controls)[^']*'\);",
    "  toggle.setAttribute('aria-label','Open Hotkeys on desktop. On touch, open More controls. Use Go to P# for the fastest known prompt ID path.');",
    source,
    count=1,
)
source = re.sub(
    r"  toggle\.innerHTML='<span class=\\\"hotkey-help-icon\\\" aria-hidden=\\\"true\\\">◎</span><span class=\\\"hotkey-desktop-label\\\">Hotkeys</span>[^;]+;",
    "  toggle.innerHTML='<span class=\\\"hotkey-help-icon\\\" aria-hidden=\\\"true\\\">◎</span><span class=\\\"hotkey-desktop-label\\\">Hotkeys</span><span class=\\\"mobile-quick-label\\\">More</span>';",
    source,
    count=1,
)
source = source.replace(
    "title.innerHTML='<span class=\"hotkey-panel-title\">Hotkeys</span><span class=\"mobile-quick-panel-title\">Quick Controls</span>';",
    "title.innerHTML='<span class=\"hotkey-panel-title\">Hotkeys</span><span class=\"mobile-quick-panel-title\">More controls</span>';",
)

# Remove the spatial swipe teaching block and replace it with a concise secondary-control heading.
start = source.find("  var quickHeading=document.createElement('strong');")
end = source.find("  var quickGrid=document.createElement('div');", start)
if start < 0 or end < 0:
    raise SystemExit("mobile panel heading/grid anchors missing")
source = source[:start] + "  var quickHeading=document.createElement('strong');\n  quickHeading.className='mobile-quick-heading';\n  quickHeading.textContent='More controls';\n  mobileQuick.appendChild(quickHeading);\n" + source[end:]

array_start = source.find("  [\n", source.find("  var quickGrid=document.createElement('div');"))
array_end = source.find("  ].forEach(function(item){", array_start)
if array_start < 0 or array_end < 0:
    raise SystemExit("mobile quick-grid action array anchors missing")
new_actions = "  [\n    ['find','✦ Find Prompt'],\n    ['profile-prev','← Previous profile'],\n    ['profile-next','Next profile →'],\n    ['search','⌕ Search'],\n    ['favorites','★ Favorites'],\n    ['filters','▤ Filters'],\n    ['reference','☰ Reference'],\n    ['top','↑ Top'],\n    ['bottom','↓ Bottom']\n"
source = source[:array_start] + new_actions + source[array_end:]

# Remove obsolete gesture status DOM if it survived the prior implementation.
status_start = source.find("  var gestureStatus=document.createElement('div');")
if status_start >= 0:
    status_end = source.find("  panel.appendChild(mobileQuick);", status_start)
    if status_end < 0:
        raise SystemExit("gesture status end anchor missing")
    source = source[:status_start] + source[status_end:]

# Replace gesture-aware toggle click and any gesture installer with ordinary More behavior.
source = re.sub(
    r"  toggle\.addEventListener\('click',function\(e\)\{[^\n]*setHotkeyHelpOpen\(panel\.hidden\)[^\n]*\}\);",
    "  toggle.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();setMobilePromptJumpOpen(false,false);setHotkeyHelpOpen(panel.hidden)});",
    source,
    count=1,
)
source = re.sub(r"\n  installMobileQuick(?:GestureSurface|HandleGestures)\(toggle\);", "", source)
source = re.sub(r"\n  installMobileQuickGestureSurface\(gestureCenter\);", "", source)

# Fail closed if user-facing gesture artifacts still remain in executable/mobile markup.
for forbidden in (
    "MOBILE_QUICK_GESTURE_THRESHOLD",
    "installMobileQuickGestureSurface",
    "installMobileQuickHandleGestures",
    "mobileQuickGestureMap",
    "mobileQuickGestureSurface",
    "SWIPE HERE",
    "↑ Find · ↔ Profile · ↓ Filters",
):
    if forbidden in source:
        raise SystemExit(f"obsolete gesture artifact still present: {forbidden}")

POLISH.write_text(source, encoding="utf-8")

# Rewrite focused contract tests around the actual phone goal: fastest known-ID navigation.
TEST.write_text(r'''from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-mobile.v1.json"
PHONE_GUIDE = ROOT / "OPEN_PROMPT_KIT_ON_PHONE.md"
GENERATED = ROOT / "web" / "prompt-kit" / "index.html"


class PromptKitMobileQuickControlsTests(unittest.TestCase):
    def test_known_id_jump_is_first_class_and_not_favorite_gated(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        for marker in (
            "function mobilePromptJumpDigits(raw)",
            "function mobilePromptJumpPrompt(promptId)",
            "function mobilePromptJumpHasPrefix(promptId)",
            "function resolveMobilePromptJump(force)",
            "function installMobilePromptJump(shell)",
            "mobilePromptJumpToggle",
            "mobilePromptJumpInput",
            "input.inputMode='numeric'",
            "input.pattern='[0-9]*'",
            "input.enterKeyHint='go'",
            "window.showPromptDetail(promptId,toggle||null)",
            "input.addEventListener('input',function(){resolveMobilePromptJump(false)})",
            "form.addEventListener('submit',function(e){e.preventDefault();resolveMobilePromptJump(true)})",
        ):
            self.assertIn(marker, source)
        jump_start = source.index("function mobilePromptJumpDigits")
        jump_end = source.index("function normalizePromptShortcutId", jump_start)
        jump = source[jump_start:jump_end]
        self.assertNotIn("isFavoritePrompt", jump)
        self.assertNotIn("promptShortcutBindings", jump)

    def test_prefix_collision_waits_but_unambiguous_exact_id_auto_opens(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        self.assertIn("if(prompt&&(!longer||force))", source)
        self.assertIn("if(prompt&&longer){if(status)status.textContent=promptId+' exists. Keep typing, or tap Go for '+promptId+'.'", source)
        self.assertIn("hasCandidate?'Keep typing '+promptId+'…':'No prompt begins with '+promptId+'.'", source)

    def test_mobile_more_panel_uses_explicit_controls_without_swipe_guessing(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        for marker in (
            "mobile-quick-label\\\">More",
            "mobile-quick-panel-title\\\">More controls",
            "quickHeading.textContent='More controls'",
            "['find','✦ Find Prompt']",
            "['profile-prev','← Previous profile']",
            "['profile-next','Next profile →']",
            "['search','⌕ Search']",
            "['favorites','★ Favorites']",
            "['filters','▤ Filters']",
            "['reference','☰ Reference']",
            "['top','↑ Top']",
            "['bottom','↓ Bottom']",
            ".hotkey-help-list,.hotkey-shortcut-config,.prompt-profile-editor{display:none!important}",
        ):
            self.assertIn(marker, source)
        for obsolete in (
            "MOBILE_QUICK_GESTURE_THRESHOLD",
            "installMobileQuickGestureSurface",
            "installMobileQuickHandleGestures",
            "mobileQuickGestureMap",
            "mobileQuickGestureSurface",
            "SWIPE HERE",
            "↑ Find · ↔ Profile · ↓ Filters",
        ):
            self.assertNotIn(obsolete, source)

    def test_desktop_hotkeys_and_shared_semantic_actions_remain_authoritative(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        for marker in (
            "function handleConfiguredPromptShortcutKey(e,key)",
            "function activatePromptShortcutTarget(promptId)",
            "window.PromptKitProfiles.activateSlot",
            "activateFavoritesView()",
            "toggleCompactFilters()",
            "scrollPromptKitTo('top')",
            "scrollPromptKitTo('bottom')",
            "toggle.setAttribute('aria-keyshortcuts','`')",
        ):
            self.assertIn(marker, source)

    def test_contract_and_phone_guide_define_fast_p111_route(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        requirement = next(item for item in contract["requirements"] if item["id"] == "mobile_prompt_id_jump")
        expected = requirement["expected"]
        for phrase in ("Go to P#", "digits only", "P111", "without opening More", "browser Find", "not required"):
            self.assertIn(phrase, expected)
        guide = PHONE_GUIDE.read_text(encoding="utf-8")
        for phrase in (
            "## Fastest path to a known prompt ID",
            "Tap **Go to P#**",
            "type **111**",
            "opens automatically",
            "You do not open **More** first",
            "Swiping is not required",
            "Chrome Find in page",
        ):
            self.assertIn(phrase, guide)

    def test_generated_site_contains_direct_jump_runtime(self) -> None:
        generated = GENERATED.read_text(encoding="utf-8")
        for marker in (
            "mobilePromptJumpToggle",
            "mobilePromptJumpInput",
            "Go to P#",
            "resolveMobilePromptJump(force)",
            "window.showPromptDetail(promptId,toggle||null)",
        ):
            self.assertIn(marker, generated)
        self.assertNotIn("mobileQuickGestureMap", generated)
        self.assertNotIn("SWIPE HERE", generated)


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")

BROWSER.write_text(r'''#!/usr/bin/env python3
from __future__ import annotations

import json
import threading
from contextlib import closing
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        pass


def main() -> int:
    handler = lambda *args, **kwargs: Quiet(*args, directory=str(ROOT), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            with closing(browser.new_context(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True, reduced_motion="reduce")) as context:
                page = context.new_page()
                page.goto(f"http://127.0.0.1:{server.server_port}/web/prompt-kit/index.html", wait_until="domcontentloaded")

                jump = page.locator("#mobilePromptJumpToggle")
                more = page.locator("#hotkeyHelpToggle")
                assert jump.is_visible(), "Go to P# is not visible in the phone thumb zone"
                assert more.is_visible(), "More control is not visible"
                assert "Go to P#" in jump.inner_text()
                assert "More" in more.inner_text()
                assert "Find" not in more.inner_text(), more.inner_text()
                for control in (jump, more):
                    box = control.bounding_box() or {}
                    assert box.get("height", 0) >= 48, box
                    assert box.get("width", 0) <= 180, box

                # Known-ID acceptance: one app tap + the digits. No More panel, swipe, result tap, or P key.
                jump.click()
                form = page.locator("#mobilePromptJumpForm")
                inp = page.locator("#mobilePromptJumpInput")
                assert form.is_visible(), "known-ID jump form did not open"
                assert inp.get_attribute("inputmode") == "numeric"
                assert page.evaluate("document.activeElement && document.activeElement.id") == "mobilePromptJumpInput"
                assert page.locator("#hotkeyHelpPanel").is_hidden(), "More panel should not be part of the P111 path"
                inp.press_sequentially("111")
                overlay = page.locator("#promptDetailOverlay")
                assert overlay.evaluate("el=>el.classList.contains('open')"), "P111 did not auto-open after exact digits"
                detail_text = page.locator("#promptDetail").inner_text()
                assert "P111" in detail_text, detail_text[:300]
                page.locator(".prompt-detail-close").click()

                # Prefix collision: P11 must not steal P111; explicit Go still opens exact P11 when requested.
                jump.click()
                inp.fill("11")
                inp.dispatch_event("input")
                page.wait_for_timeout(80)
                assert not overlay.evaluate("el=>el.classList.contains('open')"), "P11 opened before the user resolved its P111 prefix collision"
                status = page.locator("#mobilePromptJumpStatus").inner_text()
                assert "P11 exists" in status and "Keep typing" in status, status
                page.locator(".mobile-prompt-jump-go").click()
                assert overlay.evaluate("el=>el.classList.contains('open')"), "explicit Go did not open exact P11"
                assert "P11" in page.locator("#promptDetail").inner_text()
                page.locator(".prompt-detail-close").click()

                # Secondary actions are explicit and compact; gesture discovery is not required.
                more.click()
                panel = page.locator("#hotkeyHelpPanel")
                assert panel.is_visible(), "More controls panel did not open"
                panel_box = panel.bounding_box() or {}
                assert 0 < panel_box.get("width", 0) <= 350, panel_box
                assert 0 < panel_box.get("height", 0) <= 470, panel_box
                assert not page.locator(".hotkey-help-list").is_visible()
                assert not page.locator(".hotkey-shortcut-config").is_visible()
                assert not page.locator(".prompt-profile-editor").is_visible()
                assert page.locator("#mobileQuickGestureMap").count() == 0
                assert page.locator("#mobileQuickGestureSurface").count() == 0
                buttons = page.locator("#mobileQuickControls .mobile-quick-action")
                assert buttons.count() == 9, buttons.count()
                labels = [buttons.nth(i).inner_text() for i in range(buttons.count())]
                for expected in ("Find Prompt", "Previous profile", "Next profile", "Search", "Favorites", "Filters", "Reference", "Top", "Bottom"):
                    assert any(expected in label for label in labels), (expected, labels)

                print(json.dumps({
                    "verdict": "PASS",
                    "viewport": "390x844",
                    "known_id": "P111",
                    "direct_path": "tap Go to P# + type 111",
                    "direct_interactions": 4,
                    "more_panel_required": False,
                    "swipe_required": False,
                    "result_tap_required": False,
                    "browser_find_required": False,
                }))
            browser.close()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''', encoding="utf-8")

contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
requirements = contract.get("requirements", [])
old = next((item for item in requirements if item.get("id") == "mobile_quick_controls_gesture_parity"), None)
if old is None:
    old = next((item for item in requirements if item.get("id") == "mobile_prompt_id_jump"), None)
if old is None:
    raise SystemExit("mobile navigation contract requirement missing")
old["id"] = "mobile_prompt_id_jump"
old["expected"] = (
    "On narrow touch layouts, a persistent Go to P# control is the fastest route when the user already knows a prompt ID. "
    "The user taps Go to P#, enters digits only (for P111, type 111), and an exact unambiguous ID opens its canonical prompt detail automatically without opening More, swiping, browser Find, typing the P prefix, or tapping a search result. "
    "When an exact ID is also a prefix of a longer prompt ID, automatic opening waits for disambiguation and the explicit Go button may select the shorter exact ID. "
    "A separate compact More control exposes Find Prompt, previous/next profile, Search, Favorites, Filters, Reference, Top, and Bottom as labeled buttons. Swiping is not required and no hidden gesture vocabulary is part of the primary phone interaction contract. "
    "Desktop Hotkeys and shared semantic actions remain authoritative; phone controls do not create parallel prompt state."
)
contract["proof_ceiling"] = (
    "Static source, deterministic tests, generated-site parity, CI, and an exact-head 390x844 Chromium journey prove the tracked responsive/browser behavior they exercise, including the P111 one-tap-plus-digits direct path. "
    "Browser chrome itself is outside page automation, so this proof does not claim a measured Chrome Find-in-page benchmark. Physical Android thumb reach, real software-keyboard timing, browser-specific clipboard prompts, and device-specific viewport/browser UI remain field acceptance gates."
)
CONTRACT.write_text(json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

guide = GUIDE.read_text(encoding="utf-8")
heading = "## Quick Controls on touch devices"
idx = guide.find(heading)
if idx < 0:
    raise SystemExit("phone guide mobile section missing")
new_guide = '''## Fastest path to a known prompt ID

If you already know the prompt ID, do **not** open More and do **not** use a swipe gesture. Use the dedicated thumb-zone jump:

1. Tap **Go to P#**.
2. For `P111`, type **111**. The `P` is already supplied by the control.
3. When the ID is exact and unambiguous, **P111 opens automatically**. There is no search-results tap.

You do not open **More** first. **Swiping is not required.** This path also avoids opening Chrome's **Find in page**, typing the `P`, and stepping through text matches that do not understand Prompt Kit IDs.

If a shorter ID is also the start of a longer ID (for example `P11` and `P111`), the shorter one waits instead of stealing the route. Keep typing for the longer ID, or tap **Go** to deliberately open the shorter exact ID.

## More controls on touch devices

The second floating control is **More**. Open it only when you need a secondary action: **Find Prompt, Previous profile, Next profile, Search, Favorites, Filters, Reference, Top, or Bottom**. These are ordinary labeled buttons; there is no hidden swipe vocabulary to memorize.

Desktop keyboard users keep the existing Hotkeys panel and prompt-ID sequences. The phone controls call the same underlying Prompt Kit actions and do not create a second prompt database or parallel state.
'''
GUIDE.write_text(guide[:idx].rstrip() + "\n\n" + new_guide, encoding="utf-8")

print("direct mobile prompt jump patch applied")
