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

    def test_gestures_are_bounded_to_owned_quick_control_surfaces(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        start = source.index("function installMobileQuickGestureSurface(surface)")
        end = source.index("function normalizePromptShortcutId", start)
        gesture = source[start:end]
        for marker in (
            "surface.addEventListener('pointerdown'",
            "surface.addEventListener('pointerup'",
            "window.matchMedia('(max-width:760px)').matches",
            "e.pointerType!=='touch'&&e.pointerType!=='pen'",
            "ay>ax*1.2",
            "ax>ay*1.2",
            "dy<0?'find':'filters'",
            "dx<0?'profile-prev':'profile-next'",
            "performMobileQuickAction(action,surface)",
        ):
            self.assertIn(marker, gesture)
        self.assertIn("installMobileQuickGestureSurface(toggle);", source)
        self.assertIn("installMobileQuickGestureSurface(gestureCenter);", source)
        self.assertNotIn("document.addEventListener('pointerdown'", gesture)
        self.assertNotIn("document.addEventListener('touchstart'", gesture)

    def test_mobile_open_focuses_touch_command_without_opening_keyboard_input(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        self.assertIn("function mobileQuickControlsActive()", source)
        self.assertIn("if(!mobileQuickControlsActive()&&focusFavoritePromptShortcutInput(panel))return;", source)
        self.assertIn("panel.querySelector('[data-mobile-quick-action=\"find\"]')", source)

    def test_mobile_sheet_spatially_teaches_gestures_and_stays_compact(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        for marker in (
            "class=\"mobile-quick-label\">Quick Controls",
            "↑ Find · ↔ Profile · ↓ Filters",
            "mobileQuick.id='mobileQuickControls'",
            "quickHeading.textContent='Touch shortcuts'",
            "gestureMap.id='mobileQuickGestureMap'",
            "gestureCenter.id='mobileQuickGestureSurface'",
            "Swipe the Quick Controls pill in the direction shown — or tap an arrow.",
            "['find','↑ Find']",
            "['search','⌕ Search']",
            "['profile-prev','← Previous profile']",
            "['profile-next','Next profile →']",
            "['favorites','★ Favorites']",
            "['filters','↓ Filters']",
            "['reference','☰ Reference']",
            "['top','↑ Top']",
            "['bottom','↓ Bottom']",
            ".ref-toggle{display:none!important}",
            ".mobile-quick-controls{display:grid;gap:8px",
            ".mobile-quick-gesture-map{display:grid}",
            ".hotkey-help-list,.hotkey-shortcut-config,.prompt-profile-editor{display:none!important}",
            "width:min(340px,calc(100vw - 32px));max-height:min(460px,58vh)",
            ".hotkey-help-toggle{min-height:52px",
        ):
            self.assertIn(marker, source)

    def test_contract_and_phone_guide_make_touch_parity_explicit(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        requirement = next(item for item in contract["requirements"] if item["id"] == "mobile_quick_controls_gesture_parity")
        for phrase in ("Quick Controls", "compact", "spatial four-way", "desktop Hotkeys list", "parallel state"):
            self.assertIn(phrase, requirement["expected"])
        guide = PHONE_GUIDE.read_text(encoding="utf-8")
        for phrase in (
            "## Quick Controls on touch devices",
            "Tap **Quick Controls**",
            "swipe up on the pill",
            "swipe left or tap the arrow",
            "swipe right or tap the arrow",
            "swipe down or tap the arrow",
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
