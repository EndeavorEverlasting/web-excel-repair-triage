#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from contextlib import closing
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
from prepare_observed_behavior_subject import ExactHeadError, prepare_exact_head_subject


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def canonical(text: str) -> str:
    return str(text).replace("\r\n", "\n").replace("\r", "\n")


def execution_environment_kind(env=None) -> str:
    runtime_env = os.environ if env is None else env
    return "github_actions_headless_browser" if str(runtime_env.get("GITHUB_ACTIONS", "")).lower() == "true" else "local_headless_browser"


def near_bottom(page) -> bool:
    return bool(page.evaluate("""() => {
      const el=document.getElementById('promptDetail');
      if(!el)return false;
      return el.scrollTop > 0 && Math.abs((el.scrollHeight-el.clientHeight)-el.scrollTop) <= 3;
    }"""))


def observe(port: int, screenshot: Path):
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", port), Quiet)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    observations = []
    mobile_screenshot = screenshot.with_name(screenshot.stem + "-mobile" + screenshot.suffix)
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
            expected = page.evaluate("PROMPTS.find(p => p.id === 'P08').copyContent")
            card = page.locator('[data-prompt-id="P08"]')
            card.scroll_into_view_if_needed()
            card.locator('.prompt-open-btn').click()
            page.wait_for_timeout(80)

            detail = page.locator('#promptDetail')
            dialog_open = bool(page.locator('#promptDetailOverlay.open').count())
            dialog_semantics = detail.get_attribute('role') == 'dialog' and detail.get_attribute('aria-modal') == 'true'
            controls_visible = all(page.locator(selector).is_visible() for selector in ('#promptDetailTop', '#promptDetailCopyTop', '#promptDetailBottom'))
            hint_visible = page.locator('.pd-panel-hint').is_visible()

            # Non-control detail content copies the canonical prompt.
            page.evaluate("navigator.clipboard.writeText('sentinel-neutral')")
            page.locator('#promptDetail .pd-section h4').nth(1).click()
            page.wait_for_timeout(240)
            neutral_copy = canonical(page.evaluate('navigator.clipboard.readText()')) == canonical(expected)

            # Explicit controls own their own action and must not trigger the broad surface copy.
            page.evaluate("navigator.clipboard.writeText('sentinel-control')")
            page.locator('#promptDetailTop').click()
            page.wait_for_timeout(240)
            control_guard = page.evaluate('navigator.clipboard.readText()') == 'sentinel-control'

            # A double-click text-selection gesture must cancel the delayed single-click copy.
            page.evaluate("navigator.clipboard.writeText('sentinel-double')")
            page.locator('#promptDetail .pd-section pre').nth(1).dblclick()
            page.wait_for_timeout(260)
            double_click_guard = page.evaluate('navigator.clipboard.readText()') == 'sentinel-double'

            # An existing text selection blocks whole-prompt copy even when a click bubbles from content.
            page.evaluate("navigator.clipboard.writeText('sentinel-selection')")
            page.evaluate("""() => {
              const pre=document.querySelectorAll('#promptDetail .pd-section pre')[1];
              const heading=document.querySelectorAll('#promptDetail .pd-section h4')[1];
              const range=document.createRange();
              range.selectNodeContents(pre);
              const selection=window.getSelection();
              selection.removeAllRanges();
              selection.addRange(range);
              heading.dispatchEvent(new MouseEvent('click',{bubbles:true,detail:1}));
            }""")
            page.wait_for_timeout(240)
            selection_guard = page.evaluate('navigator.clipboard.readText()') == 'sentinel-selection'
            page.evaluate("window.getSelection().removeAllRanges()")

            # Panel controls and Home/End move only the modal scroll container.
            page_scroll_before = page.evaluate('window.scrollY')
            page.locator('#promptDetailBottom').click()
            page.wait_for_timeout(80)
            bottom_button = near_bottom(page)
            page.keyboard.press('Home')
            page.wait_for_timeout(50)
            home_local = page.evaluate("document.getElementById('promptDetail').scrollTop") <= 1
            page.keyboard.press('End')
            page.wait_for_timeout(50)
            end_local = near_bottom(page)
            page_scroll_after = page.evaluate('window.scrollY')
            underlying_page_stable = abs(page_scroll_after - page_scroll_before) <= 1

            # Home/End remain native inside editable fields rather than hijacking modal scroll.
            page.evaluate("""() => {
              const detail=document.getElementById('promptDetail');
              const probe=document.createElement('textarea');
              probe.id='detailEditableProbe';
              probe.value='alpha beta gamma';
              probe.setAttribute('data-prompt-detail-no-copy','');
              detail.insertBefore(probe,detail.firstChild);
              window.__detailEdgeCalls=0;
              window.__pageEdgeCalls=0;
              window.__detailEdgeOriginal=window.scrollPromptDetailTo;
              window.__pageEdgeOriginal=window.scrollPromptKitTo;
              window.scrollPromptDetailTo=function(edge){window.__detailEdgeCalls++;return window.__detailEdgeOriginal(edge)};
              window.scrollPromptKitTo=function(edge){window.__pageEdgeCalls++;return window.__pageEdgeOriginal(edge)};
              probe.focus({preventScroll:true});
            }""")
            page.keyboard.press('Home')
            page.keyboard.press('End')
            page.wait_for_timeout(30)
            editable_calls = page.evaluate("({detail:window.__detailEdgeCalls,page:window.__pageEdgeCalls})")
            editable_native = editable_calls['detail'] == 0 and editable_calls['page'] == 0
            page.evaluate("""() => {
              window.scrollPromptDetailTo=window.__detailEdgeOriginal;
              window.scrollPromptKitTo=window.__pageEdgeOriginal;
              document.getElementById('detailEditableProbe').remove();
            }""")

            # Escape remains the close owner after dialog semantics are installed and focus returns to origin.
            page.locator('#promptDetailTop').focus()
            page.keyboard.press('Escape')
            page.wait_for_timeout(50)
            escape_closed = page.locator('#promptDetailOverlay.open').count() == 0
            focus_returned = bool(page.evaluate("""() => {
              const active=document.activeElement;
              return !!(active && active.getAttribute && active.getAttribute('data-prompt-id')==='P08');
            }"""))

            screenshot.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot), full_page=False)

            observations.extend([
                {"id":"detail_dialog_and_controls","event":"P08 detail opens as a dialog with visible sticky Top/Copy/Bottom controls and usage hint","occurred":True,"passed":bool(dialog_open and dialog_semantics and controls_visible and hint_visible)},
                {"id":"detail_neutral_surface_copy","event":"Clicking non-control prompt detail content copies exact canonical P08 copyContent","occurred":True,"passed":bool(neutral_copy)},
                {"id":"detail_control_conflict_guard","event":"Clicking panel-local Top does not also fire whole-prompt surface copy","occurred":True,"passed":bool(control_guard)},
                {"id":"detail_double_click_guard","event":"Double-click text gesture cancels delayed detail-surface copy","occurred":True,"passed":bool(double_click_guard)},
                {"id":"detail_text_selection_guard","event":"Active detail text selection blocks whole-prompt surface copy","occurred":True,"passed":bool(selection_guard)},
                {"id":"detail_local_edges","event":"Bottom control plus Home/End navigate the detail container without moving the underlying page","occurred":True,"passed":bool(bottom_button and home_local and end_local and underlying_page_stable),"bottom_button":bool(bottom_button),"home_local":bool(home_local),"end_local":bool(end_local),"underlying_page_stable":bool(underlying_page_stable)},
                {"id":"detail_editable_home_end_native","event":"Home/End inside a textarea invoke neither Prompt Kit detail-edge nor page-edge handler","occurred":True,"passed":bool(editable_native),"detail_edge_calls":editable_calls["detail"],"page_edge_calls":editable_calls["page"]},
                {"id":"detail_escape_focus_restore","event":"Escape closes detail and restores focus to originating P08 card","occurred":True,"passed":bool(escape_closed and focus_returned)},
            ])
            context.close()

            with closing(browser.new_context(
                permissions=["clipboard-read", "clipboard-write"],
                reduced_motion="reduce",
                viewport={"width": 390, "height": 844},
                is_mobile=True,
                has_touch=True,
            )) as mobile_context:
                mobile = mobile_context.new_page()
                mobile.goto(f"http://127.0.0.1:{port}/web/prompt-kit/index.html", wait_until="domcontentloaded")
                expected_mobile = mobile.evaluate("PROMPTS.find(p => p.id === 'P08').copyContent")
                mobile_card = mobile.locator('[data-prompt-id="P08"]')
                mobile_card.scroll_into_view_if_needed()
                mobile_card.locator('.prompt-open-btn').tap()
                mobile.wait_for_timeout(80)
                boxes = [mobile.locator(selector).bounding_box() for selector in ('#promptDetailTop', '#promptDetailCopyTop', '#promptDetailBottom')]
                tappable = all(box and box['height'] >= 40 and box['width'] > 0 for box in boxes)
                mobile.locator('#promptDetailBottom').tap()
                mobile.wait_for_timeout(80)
                mobile_bottom = near_bottom(mobile)
                mobile.evaluate("navigator.clipboard.writeText('sentinel-mobile')")
                mobile.locator('#promptDetail .pd-section h4').nth(1).tap()
                mobile.wait_for_timeout(240)
                mobile_copy = canonical(mobile.evaluate('navigator.clipboard.readText()')) == canonical(expected_mobile)
                mobile_screenshot.parent.mkdir(parents=True, exist_ok=True)
                mobile.screenshot(path=str(mobile_screenshot), full_page=False)
                observations.append({
                    "id":"detail_mobile_quick_actions",
                    "event":"390x844 touch detail exposes tappable Top/Copy/Bottom controls, reaches bottom, and supports neutral-surface copy",
                    "occurred":True,
                    "passed":bool(tappable and mobile_bottom and mobile_copy),
                    "tappable":bool(tappable),
                    "bottom_reached":bool(mobile_bottom),
                    "neutral_copy":bool(mobile_copy),
                    "viewport":{"width":390,"height":844},
                })

            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    return observations, mobile_screenshot


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--receipt', required=True)
    parser.add_argument('--screenshot', required=True)
    parser.add_argument('--port', type=int, default=8770)
    args = parser.parse_args(argv)
    receipt_path = Path(args.receipt)
    screenshot = Path(args.screenshot)
    try:
        subject = prepare_exact_head_subject()
    except ExactHeadError as exc:
        print(f"exact-head preflight failed; Chromium was not launched\n{exc}", file=sys.stderr)
        return 2
    observations, mobile_screenshot = observe(args.port, screenshot)
    by_id = {item['id']: item for item in observations}
    surface_copy = all(by_id[item]['passed'] for item in ('detail_neutral_surface_copy','detail_control_conflict_guard','detail_double_click_guard','detail_text_selection_guard'))
    edge_nav = all(by_id[item]['passed'] for item in ('detail_local_edges','detail_editable_home_end_native'))
    accessibility = all(by_id[item]['passed'] for item in ('detail_dialog_and_controls','detail_escape_focus_restore'))
    mobile = by_id['detail_mobile_quick_actions']['passed']
    verdict = 'PASS' if all(item['passed'] for item in observations) else 'FAIL'
    receipt = {
        "schema_version":"observed-behavior-proof/v1",
        "verdict":verdict,
        "evidence_class":"browser_runtime_observed",
        "subject":subject,
        "environment":{"kind":execution_environment_kind(),"engine":"chromium","scenario":"prompt-detail-safe-surface-copy-and-local-edge-navigation"},
        "claims":[
            {"id":"detail_safe_surface_copy","statement":"Prompt detail neutral-surface click copies canonical content while controls, double-click, and text selection remain conflict-free","status":"PASS" if surface_copy else "FAIL","required_evidence_class":"browser_runtime_observed","observation_ids":["detail_neutral_surface_copy","detail_control_conflict_guard","detail_double_click_guard","detail_text_selection_guard"]},
            {"id":"detail_local_edge_navigation","statement":"Prompt detail Top/Bottom and Home/End operate on the modal scroll container while editable Home/End remains native","status":"PASS" if edge_nav else "FAIL","required_evidence_class":"browser_runtime_observed","observation_ids":["detail_local_edges","detail_editable_home_end_native"]},
            {"id":"detail_accessibility_close","statement":"Prompt detail exposes dialog semantics, visible actions, and Escape closes with origin focus restoration","status":"PASS" if accessibility else "FAIL","required_evidence_class":"browser_runtime_observed","observation_ids":["detail_dialog_and_controls","detail_escape_focus_restore"]},
            {"id":"detail_mobile_quick_actions","statement":"Mobile touch detail exposes tappable local quick actions and neutral-surface copy","status":"PASS" if mobile else "FAIL","required_evidence_class":"browser_runtime_observed","observation_ids":["detail_mobile_quick_actions"]},
        ],
        "observations":observations,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({"verdict":verdict,"receipt":str(receipt_path),"screenshot":str(screenshot),"mobile_screenshot":str(mobile_screenshot),"observations":observations}))
    return 0 if verdict == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
