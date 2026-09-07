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
            "Find in page",
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
