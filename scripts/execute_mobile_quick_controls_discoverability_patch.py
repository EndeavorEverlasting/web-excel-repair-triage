from __future__ import annotations

import json
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        label = old.splitlines()[0][:100]
        raise SystemExit(f"{path}: expected one anchor for {label!r}, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_range(path: str, start_marker: str, end_marker: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    start_count = text.count(start_marker)
    end_count = text.count(end_marker)
    if start_count != 1 or end_count != 1:
        raise SystemExit(
            f"{path}: range anchors not unique: start={start_count} end={end_count} "
            f"for {start_marker!r} .. {end_marker!r}"
        )
    start = text.index(start_marker)
    end = text.index(end_marker, start) + len(end_marker)
    target.write_text(text[:start] + new + text[end:], encoding="utf-8")


POLISH = "docs/prompt-kit-polish.js"

old_gesture_fn = '''function installMobileQuickHandleGestures(toggle){
  if(!toggle||toggle.__mobileQuickGesturesInstalled)return;
  toggle.__mobileQuickGesturesInstalled=true;
  var start=null;
  toggle.addEventListener('pointerdown',function(e){
    if(!window.matchMedia||!window.matchMedia('(max-width:760px)').matches)return;
    if(e.pointerType&&e.pointerType!=='touch'&&e.pointerType!=='pen')return;
    start={id:e.pointerId,x:e.clientX,y:e.clientY};
    try{toggle.setPointerCapture(e.pointerId)}catch(ignore){}
  });
  toggle.addEventListener('pointercancel',function(){start=null});
  toggle.addEventListener('pointerup',function(e){
    if(!start||start.id!==e.pointerId){start=null;return}
    var dx=e.clientX-start.x,dy=e.clientY-start.y;
    start=null;
    var ax=Math.abs(dx),ay=Math.abs(dy),action=null;
    if(ay>=MOBILE_QUICK_GESTURE_THRESHOLD&&ay>ax*1.2)action=dy<0?'find':'filters';
    else if(ax>=MOBILE_QUICK_GESTURE_THRESHOLD&&ax>ay*1.2)action=dx<0?'profile-prev':'profile-next';
    if(!action)return;
    e.preventDefault();e.stopPropagation();
    toggle.__mobileQuickGestureConsumed=true;
    var status=document.getElementById('mobileQuickGestureStatus');
    if(status)status.textContent=action==='find'?'Find Prompt opened':action==='filters'?'Filters toggled':action==='profile-prev'?'Previous profile selected':'Next profile selected';
    performMobileQuickAction(action,toggle);
    setTimeout(function(){toggle.__mobileQuickGestureConsumed=false},450)
  })
}'''
new_gesture_fn = '''function installMobileQuickGestureSurface(surface){
  if(!surface||surface.__mobileQuickGesturesInstalled)return;
  surface.__mobileQuickGesturesInstalled=true;
  var start=null;
  surface.addEventListener('pointerdown',function(e){
    if(!window.matchMedia||!window.matchMedia('(max-width:760px)').matches)return;
    if(e.pointerType&&e.pointerType!=='touch'&&e.pointerType!=='pen')return;
    start={id:e.pointerId,x:e.clientX,y:e.clientY};
    try{surface.setPointerCapture(e.pointerId)}catch(ignore){}
  });
  surface.addEventListener('pointercancel',function(){start=null});
  surface.addEventListener('pointerup',function(e){
    if(!start||start.id!==e.pointerId){start=null;return}
    var dx=e.clientX-start.x,dy=e.clientY-start.y;
    start=null;
    var ax=Math.abs(dx),ay=Math.abs(dy),action=null;
    if(ay>=MOBILE_QUICK_GESTURE_THRESHOLD&&ay>ax*1.2)action=dy<0?'find':'filters';
    else if(ax>=MOBILE_QUICK_GESTURE_THRESHOLD&&ax>ay*1.2)action=dx<0?'profile-prev':'profile-next';
    if(!action)return;
    e.preventDefault();e.stopPropagation();
    surface.__mobileQuickGestureConsumed=true;
    var status=document.getElementById('mobileQuickGestureStatus');
    if(status)status.textContent=action==='find'?'Find Prompt opened':action==='filters'?'Filters toggled':action==='profile-prev'?'Previous profile selected':'Next profile selected';
    performMobileQuickAction(action,surface);
    setTimeout(function(){surface.__mobileQuickGestureConsumed=false},450)
  })
}'''
replace_once(POLISH, old_gesture_fn, new_gesture_fn)

replace_once(
    POLISH,
    ".mobile-quick-label{display:none}",
    ".mobile-quick-label{display:none}.mobile-quick-handle-copy{display:none}.mobile-quick-handle-cue{font-size:9px;font-weight:650;letter-spacing:0;color:var(--text-secondary);line-height:1.2}.hotkey-panel-title{display:inline}.mobile-quick-panel-title{display:none}",
)
replace_once(
    POLISH,
    ".mobile-quick-gesture-guide{display:none;padding:9px 10px;border:1px solid rgba(56,189,248,.25);border-radius:9px;background:rgba(14,116,144,.08);color:var(--text-secondary);font-size:10px;line-height:1.45;text-align:center}.mobile-quick-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}",
    ".mobile-quick-gesture-guide{display:none;padding:7px 8px;border:1px solid rgba(56,189,248,.25);border-radius:9px;background:rgba(14,116,144,.08);color:var(--text-secondary);font-size:10px;line-height:1.35;text-align:center}.mobile-quick-gesture-map{display:none;grid-template-columns:repeat(3,minmax(0,1fr));grid-template-areas:'. up .' 'left center right' '. down .';gap:6px;align-items:stretch}.mobile-quick-gesture{min-height:42px;padding:6px;border:1px solid rgba(56,189,248,.34);border-radius:8px;background:rgba(14,116,144,.1);color:var(--text-primary);font:inherit;font-size:10px;font-weight:800;line-height:1.2;text-align:center;cursor:pointer;touch-action:manipulation}.mobile-quick-gesture[data-mobile-quick-action=\"find\"]{grid-area:up}.mobile-quick-gesture[data-mobile-quick-action=\"profile-prev\"]{grid-area:left}.mobile-quick-gesture[data-mobile-quick-action=\"profile-next\"]{grid-area:right}.mobile-quick-gesture[data-mobile-quick-action=\"filters\"]{grid-area:down}.mobile-quick-gesture-center{grid-area:center;display:grid;place-items:center;min-height:42px;padding:6px;border:1px dashed rgba(56,189,248,.48);border-radius:999px;background:rgba(14,116,144,.18);color:var(--accent);font-size:9px;font-weight:850;line-height:1.15;text-align:center;touch-action:none}.mobile-quick-gesture:hover,.mobile-quick-gesture:focus-visible{outline:none;border-color:var(--accent);box-shadow:0 0 0 2px var(--accent-glow)}.mobile-quick-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}",
)
replace_once(
    POLISH,
    "@media(max-width:760px){.ref-toggle{display:none!important}.hotkey-help{right:16px;bottom:16px}.hotkey-help-toggle{min-height:48px;padding:10px 14px;touch-action:none}.hotkey-desktop-label{display:none}.mobile-quick-label{display:inline}.hotkey-help-panel{position:fixed;right:12px;bottom:76px;width:calc(100vw - 24px);max-height:72vh}.mobile-quick-controls{display:grid}.mobile-quick-gesture-guide{display:block}}",
    "@media(max-width:760px){.ref-toggle{display:none!important}.hotkey-help{right:12px;bottom:12px}.hotkey-help-toggle{min-height:52px;padding:8px 12px;touch-action:none}.hotkey-desktop-label{display:none}.mobile-quick-handle-copy{display:grid;gap:2px;text-align:left}.mobile-quick-label{display:inline}.mobile-quick-panel-title{display:inline}.hotkey-panel-title{display:none}.hotkey-help-panel{position:fixed;right:12px;bottom:72px;width:min(340px,calc(100vw - 32px));max-height:min(460px,58vh);padding:10px;overflow:auto}.mobile-quick-controls{display:grid;gap:8px;padding:0;margin:0;border-bottom:0}.mobile-quick-gesture-guide{display:block}.mobile-quick-gesture-map{display:grid}.hotkey-help-list,.hotkey-shortcut-config{display:none}.mobile-quick-grid{gap:6px}.mobile-quick-action{min-height:42px;padding:8px 9px}.hotkey-help-head{margin-bottom:6px}}",
)
replace_once(
    POLISH,
    "toggle.setAttribute('aria-label','Open Hotkeys on desktop or Quick Controls on touch devices');",
    "toggle.setAttribute('aria-label','Open Hotkeys on desktop. On touch, Quick Controls: swipe up Find, left or right Profiles, down Filters, or tap for controls.');",
)
replace_once(
    POLISH,
    "toggle.innerHTML='<span class=\"hotkey-help-icon\" aria-hidden=\"true\">◎</span><span class=\"hotkey-desktop-label\">Hotkeys</span><span class=\"mobile-quick-label\">Quick Controls</span>';",
    "toggle.innerHTML='<span class=\"hotkey-help-icon\" aria-hidden=\"true\">◎</span><span class=\"hotkey-desktop-label\">Hotkeys</span><span class=\"mobile-quick-handle-copy\"><span class=\"mobile-quick-label\">Quick Controls</span><span class=\"mobile-quick-handle-cue\" aria-hidden=\"true\">↑ Find · ↔ Profile · ↓ Filters</span></span>';",
)
replace_once(
    POLISH,
    "title.textContent='Quick controls & hotkeys';",
    "title.innerHTML='<span class=\"hotkey-panel-title\">Hotkeys</span><span class=\"mobile-quick-panel-title\">Quick Controls</span>';",
)

old_mobile_controls = '''  var gestureGuide=document.createElement('div');
  gestureGuide.className='mobile-quick-gesture-guide';
  gestureGuide.textContent='Swipe the Quick Controls handle: ↑ Find · ← previous profile · → next profile · ↓ filters. Tap the handle for these labeled controls.';
  mobileQuick.appendChild(gestureGuide);
  var quickGrid=document.createElement('div');
  quickGrid.className='mobile-quick-grid';
  [
    ['find','✦ Find Prompt'],
    ['search','⌕ Search'],
    ['profile-prev','← Previous profile'],
    ['profile-next','Next profile →'],
    ['favorites','★ Favorites'],
    ['filters','▤ Filters'],
    ['reference','☰ Reference'],
    ['top','↑ Top'],
    ['bottom','↓ Bottom']
  ].forEach(function(item){
    var button=document.createElement('button');
    button.type='button';
    button.className='mobile-quick-action';
    button.setAttribute('data-mobile-quick-action',item[0]);
    button.textContent=item[1];
    button.addEventListener('click',function(){performMobileQuickAction(item[0],toggle)});
    quickGrid.appendChild(button)
  });
  mobileQuick.appendChild(quickGrid);'''
new_mobile_controls = '''  var gestureGuide=document.createElement('div');
  gestureGuide.className='mobile-quick-gesture-guide';
  gestureGuide.textContent='Swipe the Quick Controls pill in the direction shown — or tap an arrow.';
  mobileQuick.appendChild(gestureGuide);
  var gestureMap=document.createElement('div');
  gestureMap.className='mobile-quick-gesture-map';
  gestureMap.id='mobileQuickGestureMap';
  gestureMap.setAttribute('aria-label','Quick Controls swipe directions');
  [
    ['find','↑ Find'],
    ['profile-prev','← Previous profile'],
    ['profile-next','Next profile →'],
    ['filters','↓ Filters']
  ].forEach(function(item){
    var button=document.createElement('button');
    button.type='button';
    button.className='mobile-quick-gesture';
    button.setAttribute('data-mobile-quick-action',item[0]);
    button.textContent=item[1];
    button.addEventListener('click',function(){performMobileQuickAction(item[0],toggle)});
    gestureMap.appendChild(button)
  });
  var gestureCenter=document.createElement('div');
  gestureCenter.className='mobile-quick-gesture-center';
  gestureCenter.id='mobileQuickGestureSurface';
  gestureCenter.setAttribute('aria-label','Swipe here or use the surrounding arrow buttons');
  gestureCenter.textContent='SWIPE HERE';
  gestureMap.appendChild(gestureCenter);
  mobileQuick.appendChild(gestureMap);
  installMobileQuickGestureSurface(gestureCenter);
  var quickGrid=document.createElement('div');
  quickGrid.className='mobile-quick-grid';
  [
    ['search','⌕ Search'],
    ['favorites','★ Favorites'],
    ['reference','☰ Reference'],
    ['top','↑ Top'],
    ['bottom','↓ Bottom']
  ].forEach(function(item){
    var button=document.createElement('button');
    button.type='button';
    button.className='mobile-quick-action';
    button.setAttribute('data-mobile-quick-action',item[0]);
    button.textContent=item[1];
    button.addEventListener('click',function(){performMobileQuickAction(item[0],toggle)});
    quickGrid.appendChild(button)
  });
  mobileQuick.appendChild(quickGrid);'''
replace_once(POLISH, old_mobile_controls, new_mobile_controls)
replace_once(POLISH, "installMobileQuickHandleGestures(toggle);", "installMobileQuickGestureSurface(toggle);")

TEST = "tests/test_prompt_kit_mobile_quick_controls.py"
for old, new in (
    ("def test_handle_gestures_are_bounded_to_touch_handle", "def test_gestures_are_bounded_to_owned_quick_control_surfaces"),
    ('source.index("function installMobileQuickHandleGestures(toggle)")', 'source.index("function installMobileQuickGestureSurface(surface)")'),
    ('"toggle.addEventListener(\'pointerdown\'"', '"surface.addEventListener(\'pointerdown\'"'),
    ('"toggle.addEventListener(\'pointerup\'"', '"surface.addEventListener(\'pointerup\'"'),
    ('"performMobileQuickAction(action,toggle)"', '"performMobileQuickAction(action,surface)"'),
    ("def test_mobile_sheet_is_visible_and_describes_gestures", "def test_mobile_sheet_spatially_teaches_gestures_and_stays_compact"),
    ("Swipe the Quick Controls handle: ↑ Find · ← previous profile · → next profile · ↓ filters.", "Swipe the Quick Controls pill in the direction shown — or tap an arrow."),
    ("['find','✦ Find Prompt']", "['find','↑ Find']"),
    ("['filters','▤ Filters']", "['filters','↓ Filters']"),
    (".hotkey-help-toggle{min-height:48px", ".hotkey-help-toggle{min-height:52px"),
):
    replace_once(TEST, old, new)
replace_once(
    TEST,
    '        self.assertNotIn("document.addEventListener(\'pointerdown\'", gesture)\n',
    '        self.assertIn("installMobileQuickGestureSurface(toggle);", source)\n'
    '        self.assertIn("installMobileQuickGestureSurface(gestureCenter);", source)\n'
    '        self.assertNotIn("document.addEventListener(\'pointerdown\'", gesture)\n',
)
replace_once(
    TEST,
    '            "mobileQuick.id=\'mobileQuickControls\'",\n',
    '            "↑ Find · ↔ Profile · ↓ Filters",\n'
    '            "mobileQuick.id=\'mobileQuickControls\'",\n',
)
replace_once(
    TEST,
    '            "quickHeading.textContent=\'Touch shortcuts\'",\n',
    '            "quickHeading.textContent=\'Touch shortcuts\'",\n'
    '            "gestureMap.id=\'mobileQuickGestureMap\'",\n'
    '            "gestureCenter.id=\'mobileQuickGestureSurface\'",\n',
)
replace_once(
    TEST,
    '            ".mobile-quick-controls{display:grid}",\n',
    '            ".mobile-quick-controls{display:grid}",\n'
    '            ".mobile-quick-gesture-map{display:grid}",\n'
    '            ".hotkey-help-list,.hotkey-shortcut-config{display:none}",\n'
    '            "width:min(340px,calc(100vw - 32px));max-height:min(460px,58vh)",\n',
)
replace_once(
    TEST,
    '        for phrase in ("Quick Controls", "swiping up", "left/right", "down toggles filters", "parallel state"):\n',
    '        for phrase in ("Quick Controls", "compact", "spatial four-way", "desktop Hotkeys list", "parallel state"):\n',
)

contract_path = Path("harness/contracts/prompt-kit-mobile.v1.json")
contract = json.loads(contract_path.read_text(encoding="utf-8"))
requirement = next(item for item in contract["requirements"] if item["id"] == "mobile_quick_controls_gesture_parity")
requirement["expected"] = (
    "Touch users receive one compact visible Quick Controls handle instead of keyboard-only floating controls. "
    "The handle itself labels ↑ Find, ↔ Profile, and ↓ Filters. Tapping opens a compact mobile-only panel with a spatial four-way gesture map: up opens Find Prompt, left selects the previous A-E profile, right selects the next A-E profile, and down toggles filters. "
    "Each directional cell is also tappable, the map center accepts the same swipes for practice, and Search/Favorites/Reference/Top/Bottom remain explicit labeled buttons. "
    "On mobile the desktop Hotkeys list and Favorite-shortcut editor are hidden so the panel does not become screen-filling. The desktop Hotkeys control and shared semantic actions remain authoritative; gestures do not create parallel state."
)
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

guide = Path("OPEN_PROMPT_KIT_ON_PHONE.md")
guide_text = guide.read_text(encoding="utf-8")
start = guide_text.index("## Quick Controls on touch devices")
new_section = '''## Quick Controls on touch devices

On a phone or tablet, the floating **Quick Controls** pill is the touch counterpart to desktop Hotkeys. The pill itself shows the mnemonic **↑ Find · ↔ Profile · ↓ Filters**, so the swipe features are visible before you open anything.

Tap **Quick Controls** to open a compact touch panel. Its four-way map mirrors the gesture directions around a center **SWIPE HERE** target:

- **↑ Find** — swipe up on the pill or center target, or tap the arrow, to open **Find Prompt**.
- **← Previous profile** — swipe left or tap the arrow to move to the previous A-E profile.
- **Next profile →** — swipe right or tap the arrow to move to the next A-E profile.
- **↓ Filters** — swipe down or tap the arrow to show/hide filters.

The same compact panel keeps **Search, Favorites, Reference, Top, and Bottom** as ordinary labeled buttons. Desktop-only Hotkeys rows and Favorite-shortcut configuration stay hidden on narrow touch layouts so Quick Controls does not turn into a screen-filling keyboard reference.

Gestures remain optional accelerators. Recognition is bounded to the Quick Controls pill and the panel's center practice target; normal page scrolling and browser-edge gestures are not captured. Desktop keyboard users keep the existing Hotkeys panel and shortcuts.
'''
guide.write_text(guide_text[:start] + new_section, encoding="utf-8")

PROOF = "tests/prompt_kit_mobile_quick_controls_browser_proof.py"
old_swipe = '''def swipe(page, dx: int, dy: int) -> None:
    page.evaluate(
        """([dx,dy]) => {
          const el=document.getElementById('hotkeyHelpToggle');
          const r=el.getBoundingClientRect();
          const x=r.left+r.width/2,y=r.top+r.height/2,id=71;
          el.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerId:id,pointerType:'touch',clientX:x,clientY:y}));
          el.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,pointerId:id,pointerType:'touch',clientX:x+dx,clientY:y+dy}));
        }""",
        [dx, dy],
    )
    page.wait_for_timeout(120)
'''
new_swipe = '''def swipe(page, dx: int, dy: int, element_id: str = "hotkeyHelpToggle") -> None:
    page.evaluate(
        """([dx,dy,elementId]) => {
          const el=document.getElementById(elementId);
          const r=el.getBoundingClientRect();
          const x=r.left+r.width/2,y=r.top+r.height/2,id=71;
          el.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerId:id,pointerType:'touch',clientX:x,clientY:y}));
          el.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,pointerId:id,pointerType:'touch',clientX:x+dx,clientY:y+dy}));
        }""",
        [dx, dy, element_id],
    )
    page.wait_for_timeout(120)
'''
replace_once(PROOF, old_swipe, new_swipe)

browser_start = '                assert "Quick Controls" in handle.inner_text(), handle.inner_text()\n'
browser_end = '                quick.get_by_role("button", name="✦ Find Prompt").click()\n'
new_browser = '''                handle_text = handle.inner_text()
                assert "Quick Controls" in handle_text, handle_text
                for cue in ("↑ Find", "↔ Profile", "↓ Filters"):
                    assert cue in handle_text, handle_text
                assert not page.locator("#refBtn").is_visible(), "legacy floating Reference button remains visible on mobile"
                box = handle.bounding_box() or {}
                assert box.get("height", 0) >= 44 and box.get("width", 0) >= 44, box

                handle.click()
                panel = page.locator("#hotkeyHelpPanel")
                assert panel.is_visible(), "Quick Controls sheet did not open"
                panel_box = panel.bounding_box() or {}
                assert 0 < panel_box.get("width", 0) <= 350, panel_box
                assert 0 < panel_box.get("height", 0) <= 500, panel_box
                assert not page.locator(".hotkey-help-list").is_visible(), "desktop Hotkeys list leaks into mobile Quick Controls"
                assert not page.locator(".hotkey-shortcut-config").is_visible(), "desktop shortcut editor leaks into mobile Quick Controls"
                quick = page.locator("#mobileQuickControls")
                assert quick.is_visible(), "touch command grid not visible"
                gesture_map = page.locator("#mobileQuickGestureMap")
                center = page.locator("#mobileQuickGestureSurface")
                assert gesture_map.is_visible() and center.is_visible(), "spatial swipe map is not visible"
                active_id = page.evaluate("document.activeElement && document.activeElement.id")
                assert active_id != "promptShortcutPromptId", active_id
                active_action = page.evaluate("document.activeElement && document.activeElement.getAttribute('data-mobile-quick-action')")
                assert active_action == "find", active_action

                center_box = center.bounding_box() or {}
                find_box = quick.locator('[data-mobile-quick-action="find"]').bounding_box() or {}
                prev_box = quick.locator('[data-mobile-quick-action="profile-prev"]').bounding_box() or {}
                next_box = quick.locator('[data-mobile-quick-action="profile-next"]').bounding_box() or {}
                filters_box = quick.locator('[data-mobile-quick-action="filters"]').bounding_box() or {}
                assert find_box.get("y", 9999) < center_box.get("y", 0), (find_box, center_box)
                assert prev_box.get("x", 9999) < center_box.get("x", 0), (prev_box, center_box)
                assert next_box.get("x", 0) > center_box.get("x", 9999), (next_box, center_box)
                assert filters_box.get("y", 0) > center_box.get("y", 9999), (filters_box, center_box)

                gesture_buttons = quick.locator(".mobile-quick-gesture")
                assert gesture_buttons.count() == 4, gesture_buttons.count()
                buttons = quick.locator(".mobile-quick-action")
                assert buttons.count() == 5, buttons.count()
                for group in (gesture_buttons, buttons):
                    for index in range(group.count()):
                        rect = group.nth(index).bounding_box() or {}
                        assert rect.get("height", 0) >= 40, (index, rect)

                page.evaluate("window.PromptKitProfiles.activateSlot('A')")
                swipe(page, 70, 0, "mobileQuickGestureSurface")
                assert page.evaluate("window.PromptKitProfiles.getState().activeKey") == "B"
                handle.click()
                quick.get_by_role("button", name="↑ Find").click()
'''
replace_range(PROOF, browser_start, browser_end, new_browser)

print("mobile Quick Controls discoverability patch applied")
