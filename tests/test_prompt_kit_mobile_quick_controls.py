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
    def test_touch_handle_reuses_existing_semantic_commands(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        for marker in (
            "MOBILE_QUICK_GESTURE_THRESHOLD=38",
            "MOBILE_QUICK_PROFILE_KEYS=['A','B','C','D','E']",
            "function performMobileQuickAction(action,origin)",
            "window.openPromptFinder",
            "mobileQuickFocusSearch()",
            "window.PromptKitProfiles.activateSlot",
            "activateFavoritesView()",
            "toggleCompactFilters()",
            "document.getElementById('refBtn')",
            "scrollPromptKitTo('top')",
            "scrollPromptKitTo('bottom')",
        ):
            self.assertIn(marker, source)
        self.assertNotIn("mobileQuickProfileState=", source)
        self.assertNotIn("mobileQuickFavoritesState=", source)

    def test_handle_gestures_are_bounded_to_touch_handle(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        start = source.index("function installMobileQuickHandleGestures(toggle)")
        end = source.index("function normalizePromptShortcutId", start)
        gesture = source[start:end]
        for marker in (
            "toggle.addEventListener('pointerdown'",
            "toggle.addEventListener('pointerup'",
            "window.matchMedia('(max-width:760px)').matches",
            "e.pointerType!=='touch'&&e.pointerType!=='pen'",
            "ay>ax*1.2",
            "ax>ay*1.2",
            "dy<0?'find':'filters'",
            "dx<0?'profile-prev':'profile-next'",
            "performMobileQuickAction(action,toggle)",
        ):
            self.assertIn(marker, gesture)
        self.assertNotIn("document.addEventListener('pointerdown'", gesture)
        self.assertNotIn("document.addEventListener('touchstart'", gesture)

    def test_mobile_open_focuses_touch_command_without_opening_keyboard_input(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        self.assertIn("function mobileQuickControlsActive()", source)
        self.assertIn("if(!mobileQuickControlsActive()&&focusFavoritePromptShortcutInput(panel))return;", source)
        self.assertIn("panel.querySelector('[data-mobile-quick-action=\"find\"]')", source)

    def test_mobile_sheet_is_visible_and_describes_gestures(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        for marker in (
            "class=\"mobile-quick-label\">Quick Controls",
            "mobileQuick.id='mobileQuickControls'",
            "quickHeading.textContent='Touch shortcuts'",
            "Swipe the Quick Controls handle: ↑ Find · ← previous profile · → next profile · ↓ filters.",
            "['find','✦ Find Prompt']",
            "['search','⌕ Search']",
            "['profile-prev','← Previous profile']",
            "['profile-next','Next profile →']",
            "['favorites','★ Favorites']",
            "['filters','▤ Filters']",
            "['reference','☰ Reference']",
            "['top','↑ Top']",
            "['bottom','↓ Bottom']",
            ".ref-toggle{display:none!important}",
            ".mobile-quick-controls{display:grid}",
            ".hotkey-help-toggle{min-height:48px",
        ):
            self.assertIn(marker, source)

    def test_contract_and_phone_guide_make_touch_parity_explicit(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        requirement = next(item for item in contract["requirements"] if item["id"] == "mobile_quick_controls_gesture_parity")
        for phrase in ("Quick Controls", "swiping up", "left/right", "down toggles filters", "parallel state"):
            self.assertIn(phrase, requirement["expected"])
        guide = PHONE_GUIDE.read_text(encoding="utf-8")
        for phrase in (
            "## Quick Controls on touch devices",
            "Tap Quick Controls",
            "Swipe up from Quick Controls",
            "Swipe left from Quick Controls",
            "Swipe right from Quick Controls",
            "Swipe down from Quick Controls",
            "optional accelerators",
        ):
            self.assertIn(phrase, guide)

    def test_generated_site_contains_quick_controls_runtime(self) -> None:
        generated = GENERATED.read_text(encoding="utf-8")
        for marker in (
            "mobileQuickControls",
            "Quick Controls",
            "MOBILE_QUICK_GESTURE_THRESHOLD=38",
            "performMobileQuickAction(action,origin)",
        ):
            self.assertIn(marker, generated)


if __name__ == "__main__":
    unittest.main()
