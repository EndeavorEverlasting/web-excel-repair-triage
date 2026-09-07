#!/usr/bin/env python3
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
