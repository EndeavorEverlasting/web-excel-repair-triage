#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "web/prompt-kit/index.html"


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def observe(port: int, screenshot: Path):
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", port), Quiet)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    observations = []
    expected = ""
    actual = ""
    after_enter = ""
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                permissions=["clipboard-read", "clipboard-write"],
                reduced_motion="reduce",
                viewport={"width": 1440, "height": 900},
            )
            page = context.new_page()
            page.goto(f"http://127.0.0.1:{port}/web/prompt-kit/index.html", wait_until="domcontentloaded")
            expected = page.evaluate("PROMPTS.find(p => p.id === 'P79').copyContent")

            # Configure the Favorite through the actual product UI, not closure internals.
            card = page.locator('[data-prompt-id="P79"]')
            card.locator('.prompt-favorite-btn').click()
            page.locator('#hotkeyHelpToggle').click()
            page.wait_for_timeout(50)
            click_focus = page.evaluate("document.activeElement && document.activeElement.id === 'promptShortcutPromptId'")
            click_visible = page.evaluate("""() => {
              const input=document.getElementById('promptShortcutPromptId');
              const panel=document.getElementById('hotkeyHelpPanel');
              if(!input||!panel||panel.hidden)return false;
              const r=input.getBoundingClientRect();
              const pr=panel.getBoundingClientRect();
              return r.bottom>pr.top && r.top<pr.bottom && r.bottom>0 && r.top<innerHeight;
            }""")
            page.keyboard.press('Escape')
            page.wait_for_timeout(50)
            escape_closed = page.evaluate("document.getElementById('hotkeyHelpPanel').hidden")
            escape_focus_returned = page.evaluate("document.activeElement && document.activeElement.id === 'hotkeyHelpToggle'")
            page.keyboard.press('Backquote')
            page.wait_for_timeout(50)
            backtick_focus = page.evaluate("document.activeElement && document.activeElement.id === 'promptShortcutPromptId'")
            backtick_visible = page.evaluate("""() => {
              const input=document.getElementById('promptShortcutPromptId');
              const panel=document.getElementById('hotkeyHelpPanel');
              if(!input||!panel||panel.hidden)return false;
              const r=input.getBoundingClientRect();
              const pr=panel.getBoundingClientRect();
              return r.bottom>pr.top && r.top<pr.bottom && r.bottom>0 && r.top<innerHeight;
            }""")
            page.locator('#promptShortcutPromptId').fill('P79')
            page.get_by_role('button', name='Save favorite prompt keyboard shortcut').click()
            page.wait_for_timeout(100)
            setup_saved = 'Shortcut p79 saved' in page.locator('#toast').inner_text()
            page.locator('.hotkey-help-close').click()

            # Enter another scope so the shortcut must restore navigation and reveal P79.
            page.locator('.cat-tab[data-cat="doctrine"]').click()
            page.wait_for_timeout(100)
            before_present = page.locator('[data-prompt-id="P79"]').count() > 0
            page.evaluate("document.activeElement && document.activeElement.blur()")

            page.keyboard.press('p')
            page.keyboard.press('7')
            page.keyboard.press('9')
            try:
                page.wait_for_function("""() => {
                  const card=document.querySelector('[data-prompt-id=\"P79\"]');
                  if(!card)return false;
                  const r=card.getBoundingClientRect();
                  return r.bottom>0 && r.top<innerHeight;
                }""", timeout=4000)
            except Exception:
                pass
            toast_text = page.locator('#toast').inner_text()
            shortcut_copied = 'Copied' in toast_text
            try:
                actual = page.evaluate('navigator.clipboard.readText()')
                clipboard_read = True
            except Exception:
                actual = ''
                clipboard_read = False

            target = page.locator('[data-prompt-id="P79"]')
            target_present = target.count() > 0
            visible = False
            if target_present:
                visible = page.evaluate("""() => {
                  const r=document.querySelector('[data-prompt-id="P79"]').getBoundingClientRect();
                  return r.bottom>0 && r.top<innerHeight;
                }""")
            modal_closed = page.evaluate("""() => {
              const o=document.getElementById('promptDetailOverlay');
              return !o || !o.classList.contains('open');
            }""")
            close_focused = page.evaluate("""() => !!(
              document.activeElement &&
              (document.activeElement.classList.contains('pd-close') || document.activeElement.id==='promptDetailClose')
            )""")

            page.keyboard.press('Enter')
            page.wait_for_timeout(100)
            enter_modal_closed = page.evaluate("""() => {
              const o=document.getElementById('promptDetailOverlay');
              return !o || !o.classList.contains('open');
            }""")
            try:
                after_enter = page.evaluate('navigator.clipboard.readText()')
            except Exception:
                after_enter = ''

            screenshot.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot), full_page=False)
            observations = [
                {"id": "hotkey_click_focuses_favorite_input", "event": "Hotkeys button opens the panel with Favorite prompt ID input focused and revealed", "occurred": True, "passed": bool(click_focus and click_visible), "focused": bool(click_focus), "visible": bool(click_visible)},
                {"id": "escape_closes_hotkeys_from_favorite_input", "event": "Escape closes Hotkeys while Favorite prompt ID input owns focus and returns focus to Hotkeys toggle", "occurred": True, "passed": bool(escape_closed and escape_focus_returned), "closed": bool(escape_closed), "toggle_focused": bool(escape_focus_returned)},
                {"id": "hotkey_backtick_focuses_favorite_input", "event": "Backtick opens Hotkeys with Favorite prompt ID input focused and revealed", "occurred": True, "passed": bool(backtick_focus and backtick_visible), "focused": bool(backtick_focus), "visible": bool(backtick_visible)},
                {"id": "favorite_setup_saved", "event": "P79 favorited and p79 shortcut saved through product UI", "occurred": True, "passed": bool(setup_saved)},
                {"id": "alternate_scope_precondition", "event": "P79 absent from Doctrine scope before shortcut", "occurred": True, "passed": not before_present, "present_before": bool(before_present)},
                {"id": "favorite_shortcut_dispatched", "event": "typed favorite shortcut p79", "occurred": True, "passed": bool(shortcut_copied), "toast": toast_text},
                {"id": "prompt_card_scrolled_visible", "event": "P79 card exists and intersects viewport after shortcut", "occurred": True, "passed": bool(target_present and visible), "present": bool(target_present), "visible": bool(visible)},
                {"id": "clipboard_exact_match", "event": "clipboard equals canonical P79 copyContent", "occurred": bool(clipboard_read), "passed": bool(clipboard_read and actual == expected), "actual_length": len(actual), "expected_length": len(expected)},
                {"id": "detail_modal_closed", "event": "favorite shortcut does not open detail modal or focus its close control", "occurred": True, "passed": bool(modal_closed and not close_focused), "modal_closed": bool(modal_closed), "close_focused": bool(close_focused)},
                {"id": "enter_does_not_close_prompt", "event": "Enter after shortcut leaves detail modal closed and clipboard intact", "occurred": True, "passed": bool(enter_modal_closed and after_enter == expected)},
            ]
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    return observations


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--receipt', required=True)
    parser.add_argument('--screenshot', required=True)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args(argv)
    receipt_path = Path(args.receipt)
    screenshot = Path(args.screenshot)
    observations = observe(args.port, screenshot)
    by_id = {item['id']: item for item in observations}
    hotkey_config_recovery = all(by_id[item]['passed'] for item in ('hotkey_click_focuses_favorite_input', 'escape_closes_hotkeys_from_favorite_input', 'hotkey_backtick_focuses_favorite_input'))
    auto_copy = all(by_id[item]['passed'] for item in ('favorite_setup_saved', 'favorite_shortcut_dispatched', 'clipboard_exact_match'))
    reveal = all(by_id[item]['passed'] for item in ('alternate_scope_precondition', 'favorite_shortcut_dispatched', 'prompt_card_scrolled_visible'))
    focus_safe = all(by_id[item]['passed'] for item in ('detail_modal_closed', 'enter_does_not_close_prompt'))
    verdict = 'PASS' if all(item['passed'] for item in observations) else 'FAIL'
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    receipt = {
        "schema_version": "observed-behavior-proof/v1",
        "verdict": verdict,
        "evidence_class": "browser_runtime_observed",
        "subject": {
            "commit_sha": sha,
            "artifact": {
                "path": "web/prompt-kit/index.html",
                "sha256": hashlib.sha256(ARTIFACT.read_bytes()).hexdigest(),
            },
        },
        "environment": {"kind": "github_actions_headless_browser", "engine": "chromium", "scenario": "hotkey-config-focus-escape-and-favorite-shortcut-copy-reveal"},
        "claims": [
            {"id": "hotkey_config_focus_escape", "statement": "Opening Hotkeys by button or backtick focuses and reveals the Favorite prompt ID field, and Escape closes Hotkeys from that field", "status": "PASS" if hotkey_config_recovery else "FAIL", "required_evidence_class": "browser_runtime_observed", "observation_ids": ["hotkey_click_focuses_favorite_input", "escape_closes_hotkeys_from_favorite_input", "hotkey_backtick_focuses_favorite_input"]},
            {"id": "favorite_auto_copy", "statement": "Typing configured Favorite P79 automatically copies canonical prompt content", "status": "PASS" if auto_copy else "FAIL", "required_evidence_class": "browser_runtime_observed", "observation_ids": ["favorite_setup_saved", "favorite_shortcut_dispatched", "clipboard_exact_match"]},
            {"id": "favorite_scroll", "statement": "Typing configured Favorite P79 exits an alternate scope and scrolls the P79 card into view", "status": "PASS" if reveal else "FAIL", "required_evidence_class": "browser_runtime_observed", "observation_ids": ["alternate_scope_precondition", "favorite_shortcut_dispatched", "prompt_card_scrolled_visible"]},
            {"id": "non_destructive_focus", "statement": "Shortcut does not open detail with close focused; Enter cannot immediately close the prompt", "status": "PASS" if focus_safe else "FAIL", "required_evidence_class": "browser_runtime_observed", "observation_ids": ["detail_modal_closed", "enter_does_not_close_prompt"]},
        ],
        "observations": observations,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({"verdict": verdict, "receipt": str(receipt_path), "screenshot": str(screenshot), "observations": observations}))
    return 0 if verdict == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
