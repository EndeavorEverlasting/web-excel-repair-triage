from __future__ import annotations

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
            "function setMobilePromptJumpSubmitState(promptId,exact,longer)",
            "function resolveMobilePromptJump(force)",
            "function installMobilePromptJump(shell)",
            "mobilePromptJumpToggle",
            "mobilePromptJumpInput",
            "input.inputMode='numeric'",
            "input.pattern='[0-9]*'",
            "input.enterKeyHint='go'",
            "revealPromptShortcutTarget(promptId,'instant')",
            "hideCompactFilters();",
            "tap the prompt card to copy",
            "input.addEventListener('input',function(){resolveMobilePromptJump(false)})",
            "form.addEventListener('submit',function(e){e.preventDefault();resolveMobilePromptJump(true)})",
        ):
            self.assertIn(marker, source)
        jump_start = source.index("function mobilePromptJumpDigits")
        jump_end = source.index("function normalizePromptShortcutId", jump_start)
        jump = source[jump_start:jump_end]
        self.assertNotIn("isFavoritePrompt", jump)
        self.assertNotIn("promptShortcutBindings", jump)
        self.assertNotIn("window.showPromptDetail(promptId,toggle||null)", jump)
        self.assertIn("document.querySelector('[data-prompt-id=\"'+promptId+'\"]')", jump)
        self.assertIn("card.focus({preventScroll:true})", jump)
        center = source[
            source.index("function centerRenderedPromptCard") : source.index("function revealPromptShortcutTarget")
        ]
        self.assertIn("hideCompactFilters();", center)

    def test_prefix_collision_requires_explicit_exact_confirmation_without_timing_race(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        self.assertIn("if(prompt&&(!longer||force))", source)
        self.assertIn("go.textContent=longer?'Go to '+promptId:'Go'", source)
        self.assertIn("promptId+' is exact. Press Enter or tap Go to '+promptId+', or keep typing for a longer ID.'", source)
        self.assertIn("setMobilePromptJumpSubmitState(promptId,false,false)", source)
        self.assertIn("hasCandidate?'Keep typing '+promptId+'…':'No prompt starts with '+promptId+'.'", source)
        self.assertNotIn("setTimeout(function(){resolveMobilePromptJump", source)

    def test_mobile_more_panel_uses_explicit_controls_without_swipe_guessing(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        for marker in (
            'mobile-quick-label">More',
            'mobile-quick-panel-title">More controls',
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
            ".hotkey-help-panel{width:min(340px,calc(100vw - 24px));max-height:min(460px,58vh)}",
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
            "if(typeof toggleRef==='function'){toggleRef();return true}",
            "toggle.setAttribute('aria-keyshortcuts','`')",
        ):
            self.assertIn(marker, source)
        action_start = source.index("function performMobileQuickAction")
        action_end = source.index("function mobilePromptJumpDigits", action_start)
        action = source[action_start:action_end]
        self.assertNotIn("ref.click()", action)
        self.assertNotIn("getElementById('refBtn')", action)

    def test_contract_and_phone_guide_define_fast_p111_route(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        requirement = next(item for item in contract["requirements"] if item["id"] == "mobile_prompt_id_jump")
        expected = requirement["expected"]
        for phrase in ("Go to P#", "digits only", "P111", "P11", "Enter", "leading zero", "without opening More", "browser Find", "detail", "tap", "copy"):
            self.assertIn(phrase, expected)
        guide = PHONE_GUIDE.read_text(encoding="utf-8")
        for phrase in (
            "## Fastest path to a known prompt ID",
            "Tap **Go to P#**",
            "type **111**",
            "snaps into view automatically with prompt detail closed",
            "You do not open **More** first",
            "Swiping is not required",
            "Find in page",
            "P11",
            "Press **Enter**",
            "leading zero",
            "Tap anywhere on the prompt card outside its explicit controls to copy",
            "Use **Open** only when you deliberately want prompt detail",
        ):
            self.assertIn(phrase, guide)

    def test_generated_site_contains_direct_jump_runtime(self) -> None:
        generated = GENERATED.read_text(encoding="utf-8")
        for marker in (
            "mobilePromptJumpToggle",
            "mobilePromptJumpInput",
            "Go to P#",
            "resolveMobilePromptJump(force)",
            "revealPromptShortcutTarget(promptId,'instant')",
            "tap the prompt card to copy",
        ):
            self.assertIn(marker, generated)
        self.assertNotIn("mobileQuickGestureMap", generated)
        self.assertNotIn("SWIPE HERE", generated)


if __name__ == "__main__":
    unittest.main()
