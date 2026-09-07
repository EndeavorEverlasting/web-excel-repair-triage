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


def swipe(page, dx: int, dy: int) -> None:
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
                handle = page.locator("#hotkeyHelpToggle")
                assert handle.is_visible(), "Quick Controls handle is not visible"
                assert "Quick Controls" in handle.inner_text(), handle.inner_text()
                assert not page.locator("#refBtn").is_visible(), "legacy floating Reference button remains visible on mobile"
                box = handle.bounding_box() or {}
                assert box.get("height", 0) >= 44 and box.get("width", 0) >= 44, box

                handle.click()
                panel = page.locator("#hotkeyHelpPanel")
                assert panel.is_visible(), "Quick Controls sheet did not open"
                quick = page.locator("#mobileQuickControls")
                assert quick.is_visible(), "touch command grid not visible"
                active_id = page.evaluate("document.activeElement && document.activeElement.id")
                assert active_id != "promptShortcutPromptId", active_id
                active_action = page.evaluate("document.activeElement && document.activeElement.getAttribute('data-mobile-quick-action')")
                assert active_action == "find", active_action
                buttons = quick.locator(".mobile-quick-action")
                assert buttons.count() >= 9, buttons.count()
                for index in range(buttons.count()):
                    rect = buttons.nth(index).bounding_box() or {}
                    assert rect.get("height", 0) >= 40, (index, rect)

                quick.get_by_role("button", name="✦ Find Prompt").click()
                assert page.locator("#promptDetailOverlay").evaluate("el=>el.classList.contains('open')")
                assert "Prompt Kit Tutorial" in page.locator("#promptDetail").inner_text()
                page.locator(".prompt-detail-close").click()

                page.evaluate("window.PromptKitProfiles.activateSlot('A')")
                swipe(page, 70, 0)
                assert page.evaluate("window.PromptKitProfiles.getState().activeKey") == "B"
                swipe(page, -70, 0)
                assert page.evaluate("window.PromptKitProfiles.getState().activeKey") == "A"

                before = page.locator(".header").evaluate("el=>el.classList.contains('filters-collapsed')")
                swipe(page, 0, 70)
                after = page.locator(".header").evaluate("el=>el.classList.contains('filters-collapsed')")
                assert before != after, (before, after)

                swipe(page, 0, -70)
                assert page.locator("#promptDetailOverlay").evaluate("el=>el.classList.contains('open')")
                assert "Prompt Kit Tutorial" in page.locator("#promptDetail").inner_text()

                print(json.dumps({"verdict":"PASS","viewport":"390x844","handle":"Quick Controls","gestures":["up=find","left/right=profiles","down=filters"]}))
            browser.close()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
