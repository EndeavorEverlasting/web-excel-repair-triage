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


def canonical(text: str) -> str:
    return str(text or '').replace('\r\n', '\n')


def card_midpoint(page, prompt_id: str) -> tuple[dict, float]:
    box = page.locator(f'[data-prompt-id="{prompt_id}"]').bounding_box() or {}
    return box, box.get('y', 0) + box.get('height', 0) / 2


def assert_detail_closed(page, message: str) -> None:
    assert not page.locator('#promptDetailOverlay').evaluate("el=>el.classList.contains('open')"), message


def main() -> int:
    handler = lambda *args, **kwargs: Quiet(*args, directory=str(ROOT), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        origin = f"http://127.0.0.1:{server.server_port}"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            with closing(browser.new_context(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True, reduced_motion="reduce")) as context:
                context.grant_permissions(["clipboard-read", "clipboard-write"], origin=origin)
                page = context.new_page()
                page.goto(f"{origin}/web/prompt-kit/index.html", wait_until="domcontentloaded")

                jump = page.locator('#mobilePromptJumpToggle')
                more = page.locator('#hotkeyHelpToggle')
                assert jump.is_visible(), 'Go to P# is not visible in the phone thumb zone'
                assert more.is_visible(), 'More control is not visible'
                for control in (jump, more):
                    box = control.bounding_box() or {}
                    assert box.get('height', 0) >= 48, box
                    assert box.get('width', 0) <= 180, box

                form = page.locator('#mobilePromptJumpForm')
                inp = page.locator('#mobilePromptJumpInput')
                go = page.locator('.mobile-prompt-jump-go')

                # Primary known-ID journey: locate/snap, keep detail closed, then card tap copies.
                jump.click()
                assert form.is_visible()
                assert inp.get_attribute('inputmode') == 'numeric'
                assert page.evaluate("document.activeElement && document.activeElement.id") == 'mobilePromptJumpInput'
                inp.press_sequentially('111')
                page.wait_for_timeout(80)
                assert_detail_closed(page, 'Go to P# must not auto-open the space-heavy detail panel')
                assert form.is_hidden(), 'exact P111 should close the jump form after snapping'
                target = page.locator('[data-prompt-id="P111"]')
                assert target.is_visible(), 'P111 card was not revealed'
                target_box, target_mid = card_midpoint(page, 'P111')
                assert abs(target_mid - 844 / 2) <= 150, (target_box, target_mid)
                assert page.evaluate("document.activeElement && document.activeElement.getAttribute('data-prompt-id')") == 'P111'
                toast = page.locator('#toast').inner_text()
                assert 'P111 ready' in toast and 'tap the prompt card to copy' in toast, toast
                assert page.locator('.header').evaluate("el=>el.classList.contains('filters-collapsed')"), 'snap must hide compact filters'
                assert page.locator('#filterPanelToggle').get_attribute('aria-expanded') == 'false'

                expected = page.evaluate("PROMPTS.find(function(item){return item.id==='P111'}).copyContent")
                target.click(position={"x": 24, "y": 44})
                page.wait_for_timeout(380)
                actual = page.evaluate('navigator.clipboard.readText()')
                assert canonical(actual) == canonical(expected), (len(actual), len(expected))
                toast_el = page.locator('#toast')
                toast_text = toast_el.inner_text()
                assert 'Copied to clipboard' in toast_text, toast_text
                assert 'P111' in toast_text, toast_text
                assert toast_el.get_attribute('data-copy-confirmation') == '1'
                assert toast_el.get_attribute('data-prompt-id') == 'P111'
                preview = toast_el.get_attribute('data-copy-preview') or ''
                assert preview, 'copy confirmation must expose a prompt preview'
                normalized_preview = canonical(preview).rstrip('…').rstrip()
                assert normalized_preview and canonical(expected).startswith(normalized_preview), (preview[:80], expected[:80])
                assert toast_el.locator('.toast-copy-preview').count() == 1
                assert_detail_closed(page, 'card tap copy must not open detail')

                # Explicit Open remains available for deliberate inspection only.
                target.locator('.prompt-open-btn').click()
                page.wait_for_timeout(60)
                assert page.locator('#promptDetailOverlay').evaluate("el=>el.classList.contains('open')"), 'explicit Open no longer opens detail'
                assert 'P111' in page.locator('#promptDetail').inner_text()
                page.locator('.prompt-detail-close').click()
                assert_detail_closed(page, 'detail did not close after explicit inspection')

                # Exhaust exact IDs that also prefix longer IDs: explicit confirmation jumps, never opens detail.
                prompt_ids = page.evaluate("PROMPTS.map(function(item){return item.id})")
                collision_ids = [pid for pid in prompt_ids if any(other != pid and other.startswith(pid) for other in prompt_ids)]
                assert collision_ids, 'fixture must contain exact/prefix collisions'
                for prompt_id in collision_ids:
                    jump.click(); inp.fill(prompt_id[1:]); page.wait_for_timeout(40)
                    assert_detail_closed(page, f'{prompt_id} stole a longer route')
                    status = page.locator('#mobilePromptJumpStatus').inner_text()
                    assert f'{prompt_id} is exact' in status and 'Press Enter' in status and 'keep typing' in status.lower(), (prompt_id, status)
                    assert go.is_enabled()
                    assert go.inner_text() == f'Go to {prompt_id}', (prompt_id, go.inner_text())
                    inp.press('Enter'); page.wait_for_timeout(60)
                    assert_detail_closed(page, f'Enter on {prompt_id} opened detail')
                    assert form.is_hidden()
                    card = page.locator(f'[data-prompt-id="{prompt_id}"]')
                    assert card.is_visible()
                    assert page.evaluate("document.activeElement && document.activeElement.getAttribute('data-prompt-id')") == prompt_id

                # Prefix-only remains fail-closed.
                jump.click(); inp.fill('1'); page.wait_for_timeout(40)
                assert go.is_disabled()
                assert 'Keep typing P1' in page.locator('#mobilePromptJumpStatus').inner_text()
                inp.press('Enter'); page.wait_for_timeout(40)
                assert_detail_closed(page, 'prefix-only P1 opened detail')
                assert form.is_visible()

                # Leading-zero canonical ID snaps without detail.
                inp.fill('01'); page.wait_for_timeout(60)
                assert_detail_closed(page, 'P01 auto-opened detail')
                assert form.is_hidden()
                assert page.locator('[data-prompt-id="P01"]').is_visible()

                # Pasted P111 normalizes and snaps without detail.
                jump.click(); inp.fill('P111'); page.wait_for_timeout(60)
                assert_detail_closed(page, 'pasted P111 auto-opened detail')
                assert page.locator('[data-prompt-id="P111"]').is_visible()

                # Missing ID stays fail-closed.
                jump.click(); inp.fill('999999'); page.wait_for_timeout(40)
                assert go.is_disabled()
                assert 'No prompt starts with P999999' in page.locator('#mobilePromptJumpStatus').inner_text()
                inp.press('Enter'); page.wait_for_timeout(40)
                assert_detail_closed(page, 'missing P999999 opened detail')
                assert form.is_visible()

                # Secondary More surface remains compact and explicit.
                page.keyboard.press('Escape')
                more.click()
                panel = page.locator('#hotkeyHelpPanel')
                assert panel.is_visible()
                panel_box = panel.bounding_box() or {}
                assert 0 < panel_box.get('width', 0) <= 350, panel_box
                assert 0 < panel_box.get('height', 0) <= 470, panel_box
                buttons = page.locator('#mobileQuickControls .mobile-quick-action')
                assert buttons.count() == 9

                print(json.dumps({
                    'verdict': 'PASS',
                    'viewport': '390x844',
                    'known_id': 'P111',
                    'direct_path': 'tap Go to P# + type 111 -> snap card -> tap card to copy',
                    'detail_auto_open': False,
                    'card_tap_copy': True,
                    'explicit_open_preserved': True,
                    'underlying_prompt_centered': True,
                    'collision_ids': collision_ids,
                    'edge_cases': ['all-exact-prefix-collisions', 'P1-prefix-enter', 'P01-leading-zero', 'paste-P111', 'P999999-missing-enter'],
                    'more_panel_required': False,
                    'browser_find_required': False,
                }))
            browser.close()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
