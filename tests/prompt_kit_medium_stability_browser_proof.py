#!/usr/bin/env python3
from __future__ import annotations

import json
import threading
from contextlib import closing
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
MOBILE_QUERY = "(hover:none) and (pointer:coarse)"


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        pass


def media_matches(page: Page) -> bool:
    return bool(page.evaluate("query => window.matchMedia(query).matches", MOBILE_QUERY))


def visible(page: Page, selector: str) -> bool:
    return page.locator(selector).is_visible()


def assert_mobile_identity(page: Page, label: str) -> None:
    assert media_matches(page), f"{label}: mobile interaction media query no longer matches"
    assert visible(page, "#mobilePromptJumpToggle"), f"{label}: Go to P# disappeared"
    assert visible(page, "#hotkeyHelpToggle"), f"{label}: More control disappeared"
    assert not visible(page, ".ref-toggle"), f"{label}: desktop Reference handle leaked into mobile mode"
    assert visible(page, ".mobile-quick-label"), f"{label}: mobile More label disappeared"
    assert not visible(page, ".hotkey-desktop-label"), f"{label}: desktop Hotkeys label leaked into mobile mode"


def assert_desktop_identity(page: Page, label: str) -> None:
    assert not media_matches(page), f"{label}: desktop unexpectedly matches mobile interaction media"
    assert not visible(page, "#mobilePromptJumpToggle"), f"{label}: mobile Go to P# leaked into desktop mode"
    assert visible(page, "#hotkeyHelpToggle"), f"{label}: desktop Hotkeys handle disappeared"
    assert visible(page, ".ref-toggle"), f"{label}: bottom-right Reference handle disappeared"
    assert visible(page, ".hotkey-desktop-label"), f"{label}: desktop Hotkeys label disappeared"
    assert not visible(page, ".mobile-quick-label"), f"{label}: mobile More label leaked into desktop mode"
    ref_box = page.locator(".ref-toggle").bounding_box() or {}
    viewport = page.viewport_size or {}
    assert viewport.get("width", 0) - (ref_box.get("x", 0) + ref_box.get("width", 0)) <= 40, (label, ref_box, viewport)
    assert viewport.get("height", 0) - (ref_box.get("y", 0) + ref_box.get("height", 0)) <= 40, (label, ref_box, viewport)


def main() -> int:
    handler = lambda *args, **kwargs: Quiet(*args, directory=str(ROOT), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        origin = f"http://127.0.0.1:{server.server_port}"
        url = f"{origin}/web/prompt-kit/index.html"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            with closing(browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, reduced_motion="reduce")) as context:
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded")
                search = page.locator("#search")
                search.fill("P110 orientation sentinel")
                navigation_count = page.evaluate("performance.getEntriesByType('navigation').length")
                assert_mobile_identity(page, "portrait")

                page.set_viewport_size({"width": 844, "height": 390})
                page.wait_for_timeout(80)
                assert_mobile_identity(page, "landscape")
                assert search.input_value() == "P110 orientation sentinel", "phone rotation reset search state"
                assert page.evaluate("performance.getEntriesByType('navigation').length") == navigation_count, "phone rotation reloaded the page"

                page.set_viewport_size({"width": 390, "height": 844})
                page.wait_for_timeout(80)
                assert_mobile_identity(page, "portrait-return")
                assert search.input_value() == "P110 orientation sentinel", "return rotation reset search state"

            with closing(browser.new_context(viewport={"width": 560, "height": 1100}, is_mobile=False, has_touch=False, reduced_motion="reduce")) as context:
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded")
                assert_desktop_identity(page, "narrow-tall-desktop")
                page.set_viewport_size({"width": 1100, "height": 560})
                page.wait_for_timeout(80)
                assert_desktop_identity(page, "wide-short-desktop")

            browser.close()
            print(json.dumps({
                "verdict": "PASS",
                "mobile_cycle": ["390x844", "844x390", "390x844"],
                "mobile_state_preserved": True,
                "desktop_cycle": ["560x1100", "1100x560"],
                "desktop_handles_preserved": True,
                "interaction_classifier": MOBILE_QUERY,
            }))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
