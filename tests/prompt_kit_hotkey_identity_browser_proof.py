#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
from prepare_observed_behavior_subject import ExactHeadError, prepare_exact_head_subject

TARGETS = ("P11", "P13", "P111", "P126")


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def environment_kind() -> str:
    return "github_actions_headless_browser" if os.environ.get("GITHUB_ACTIONS", "").lower() == "true" else "local_headless_browser"


def observe(port: int, screenshot: Path) -> list[dict]:
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", port), Quiet)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    observations: list[dict] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                permissions=["clipboard-read", "clipboard-write"],
                viewport={"width": 1440, "height": 900},
                reduced_motion="reduce",
            )
            page = context.new_page()
            page.goto(f"http://127.0.0.1:{port}/web/prompt-kit/index.html", wait_until="domcontentloaded")
            expected = {
                prompt_id: page.evaluate("id => PROMPTS.find(p => p.id === id).copyContent", prompt_id)
                for prompt_id in TARGETS
            }

            # Natural prompt hotkeys are catalog-derived; no Favorite or manual Save setup is required.

            def set_clipboard(value: str) -> None:
                page.evaluate("value => navigator.clipboard.writeText(value)", value)

            def clipboard() -> str:
                return page.evaluate("navigator.clipboard.readText()")

            def press(sequence: str) -> None:
                for char in sequence:
                    page.keyboard.press(char)

            p126_favorite = page.locator('[data-prompt-id="P126"] .prompt-favorite-btn')
            if p126_favorite.count() != 1 or p126_favorite.get_attribute('aria-pressed') != 'false':
                raise AssertionError('P126 proof did not start from a non-favorite state')

            set_clipboard("sentinel-126")
            press("126")
            page.wait_for_timeout(220)
            p126_final = clipboard()
            p126_geometry = page.evaluate("""() => {
              const card=document.querySelector('[data-prompt-id="P126"]');
              if(!card)return null;
              const rect=card.getBoundingClientRect();
              return {center:(rect.top+rect.bottom)/2,viewport:window.innerHeight/2};
            }""")
            p126_snapped = bool(
                p126_geometry
                and abs(p126_geometry["center"] - p126_geometry["viewport"]) <= max(120, 900 * 0.18)
            )
            observations.append({
                "id": "numeric_p126_copies_and_snaps",
                "event": "typing bare 126 copies P126 and centers its canonical card without Favorite/manual setup",
                "occurred": True,
                "passed": p126_final == expected["P126"] and p126_snapped,
                "clipboard_matches": p126_final == expected["P126"],
                "favorite_required": False,
                "geometry": p126_geometry,
                "snapped": p126_snapped,
            })

            set_clipboard("sentinel-p126")
            press("p126")
            page.wait_for_timeout(220)
            p126_compat = clipboard()
            observations.append({
                "id": "p126_compatibility_alias",
                "event": "p126 remains a compatibility alias for canonical P126",
                "occurred": True,
                "passed": p126_compat == expected["P126"],
                "clipboard_matches": p126_compat == expected["P126"],
            })

            # P11 is a prefix of P111: it must remain pending until timeout.
            set_clipboard("sentinel-p11")
            press("p11")
            page.wait_for_timeout(180)
            p11_early = clipboard()
            page.wait_for_timeout(1150)
            p11_final = clipboard()
            observations.append({
                "id": "p11_waits_for_longer_prefix",
                "event": "p11 remains pending before the 1.2s boundary and resolves to P11 after it",
                "occurred": True,
                "passed": p11_early == "sentinel-p11" and p11_final == expected["P11"],
                "early_unchanged": p11_early == "sentinel-p11",
                "final_matches": p11_final == expected["P11"],
            })

            # P13 has no longer configured prefix and resolves immediately.
            set_clipboard("sentinel-p13")
            press("p13")
            page.wait_for_timeout(180)
            p13_final = clipboard()
            observations.append({
                "id": "p13_resolves_exactly",
                "event": "p13 resolves to P13 without being confused with the p11 family",
                "occurred": True,
                "passed": p13_final == expected["P13"],
                "final_matches": p13_final == expected["P13"],
            })

            # Continued typing wins over the pending shorter exact match.
            set_clipboard("sentinel-p111")
            press("p111")
            page.wait_for_timeout(180)
            p111_final = clipboard()
            observations.append({
                "id": "p111_wins_over_p11_prefix",
                "event": "p111 resolves to P111 before the pending P11 timeout fires",
                "occurred": True,
                "passed": p111_final == expected["P111"],
                "final_matches": p111_final == expected["P111"],
            })

            # Dots are accepted as visual separators while the prompt buffer is active.
            set_clipboard("sentinel-p1.1")
            press("p1.1")
            page.wait_for_timeout(180)
            dotted_short_early = clipboard()
            page.wait_for_timeout(1150)
            dotted_short_final = clipboard()
            observations.append({
                "id": "p1_1_aliases_p11",
                "event": "p1.1 follows P11 prefix timing and resolves to canonical P11",
                "occurred": True,
                "passed": dotted_short_early == "sentinel-p1.1" and dotted_short_final == expected["P11"],
                "early_unchanged": dotted_short_early == "sentinel-p1.1",
                "final_matches": dotted_short_final == expected["P11"],
            })

            set_clipboard("sentinel-p1.11")
            press("p1.11")
            page.wait_for_timeout(180)
            dotted_long_final = clipboard()
            observations.append({
                "id": "p1_11_aliases_p111",
                "event": "p1.11 resolves to canonical P111 rather than the shorter P11",
                "occurred": True,
                "passed": dotted_long_final == expected["P111"],
                "final_matches": dotted_long_final == expected["P111"],
            })

            # A pending shorter exact identity settles before the same key continues to A-E header navigation.
            set_clipboard("sentinel-p11-a")
            press("p11")
            page.keyboard.press("a")
            deadline = time.monotonic() + 1.5
            p11_then_a = clipboard()
            while p11_then_a != expected["P11"] and time.monotonic() < deadline:
                page.wait_for_timeout(25)
                p11_then_a = clipboard()
            slot_after_a = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")
            observations.append({
                "id": "pending_p11_hands_off_to_header_a",
                "event": "A settles pending P11 and still activates the All profile",
                "occurred": True,
                "passed": p11_then_a == expected["P11"] and slot_after_a == "A",
                "prompt_matches": p11_then_a == expected["P11"],
                "active_slot": slot_after_a,
            })

            set_clipboard("sentinel-p1-b")
            press("p1")
            page.keyboard.press("b")
            page.wait_for_timeout(250)
            p1_then_b = clipboard()
            slot_after_b = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")
            observations.append({
                "id": "incomplete_prefix_hands_off_to_header_b",
                "event": "B abandons incomplete p1 without firing a prompt and activates Standard",
                "occurred": True,
                "passed": p1_then_b == "sentinel-p1-b" and slot_after_b == "B",
                "clipboard_unchanged": p1_then_b == "sentinel-p1-b",
                "active_slot": slot_after_b,
            })

            # Home/End are page navigation only and do not alter the header/profile namespace.
            page.keyboard.press("End")
            deadline = time.monotonic() + 1.0
            max_scroll = page.evaluate("Math.max(0, document.documentElement.scrollHeight - window.innerHeight)")
            end_y = page.evaluate("window.scrollY")
            while end_y < max_scroll - 2 and time.monotonic() < deadline:
                page.wait_for_timeout(20)
                max_scroll = page.evaluate("Math.max(0, document.documentElement.scrollHeight - window.innerHeight)")
                end_y = page.evaluate("window.scrollY")
            end_slot = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")
            page.keyboard.press("Home")
            deadline = time.monotonic() + 1.0
            home_y = page.evaluate("window.scrollY")
            while home_y > 2 and time.monotonic() < deadline:
                page.wait_for_timeout(20)
                home_y = page.evaluate("window.scrollY")
            home_slot = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")
            observations.append({
                "id": "home_end_page_navigation",
                "event": "End reaches the document bottom and Home returns to the true top without changing the active profile",
                "occurred": True,
                "passed": end_y >= max_scroll - 2 and home_y <= 2 and end_slot == "B" and home_slot == "B",
                "end_y": end_y,
                "max_scroll": max_scroll,
                "home_y": home_y,
                "end_slot": end_slot,
                "home_slot": home_slot,
            })
            page.keyboard.press("a")
            page.wait_for_timeout(50)

            # Numeric input must never activate A-E header slots.
            active_slot = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")
            observations.append({
                "id": "numeric_sequences_do_not_drive_header",
                "event": "digit-bearing prompt sequences leave header navigation in the expected All profile",
                "occurred": True,
                "passed": active_slot == "A",
                "active_slot": active_slot,
            })

            # Falsify the removed-header regression through the real user configuration UI: Doctrine
            # must remain reachable without stealing an A-E slot or masquerading as a PROMPTS pack.
            page.locator('#hotkeyHelpToggle').click()
            page.wait_for_timeout(75)
            doctrine_row = page.locator('.prompt-profile-slot-row[data-key="D"]')
            doctrine_row.locator('[data-slot-name]').fill('Doctrine')
            doctrine_row.locator('[data-slot-mode]').select_option('doctrine')
            page.locator('[data-profile-save]').click()
            page.wait_for_timeout(100)
            saved_doctrine = 'Saved five profile tabs.' in page.locator('.prompt-profile-status').inner_text()
            page.locator('.hotkey-help-close').click()
            page.evaluate("document.activeElement && document.activeElement.blur()")
            page.keyboard.press('d')
            page.wait_for_timeout(120)
            doctrine_active = page.evaluate("""() => {
              const state=window.PromptKitProfiles&&window.PromptKitProfiles.getState();
              const view=document.getElementById('doctrineView');
              const cards=document.querySelectorAll('#doctrineList .doctrine-card');
              return {
                slot:state&&state.activeKey,
                mode:state&&state.slots&&state.slots[3]&&state.slots[3].mode,
                activeCat:window.activeCat,
                viewActive:!!(view&&view.classList.contains('active')),
                doctrineCards:cards.length
              };
            }""")
            observations.append({
                "id": "doctrine_profile_mode_reaches_dedicated_view",
                "event": "D is configured to Doctrine through the Hotkeys UI and opens the dedicated Doctrine renderer",
                "occurred": True,
                "passed": bool(saved_doctrine and doctrine_active.get('slot') == 'D' and doctrine_active.get('mode') == 'doctrine' and doctrine_active.get('activeCat') == 'doctrine' and doctrine_active.get('viewActive') and doctrine_active.get('doctrineCards', 0) > 0),
                "saved": bool(saved_doctrine),
                **doctrine_active,
            })

            page.reload(wait_until='domcontentloaded')
            page.wait_for_timeout(150)
            doctrine_reload = page.evaluate("""() => {
              const state=window.PromptKitProfiles&&window.PromptKitProfiles.getState();
              const view=document.getElementById('doctrineView');
              return {
                slot:state&&state.activeKey,
                mode:state&&state.slots&&state.slots[3]&&state.slots[3].mode,
                activeCat:window.activeCat,
                viewActive:!!(view&&view.classList.contains('active'))
              };
            }""")
            observations.append({
                "id": "doctrine_profile_mode_survives_reload",
                "event": "The configured Doctrine slot and active D state survive a same-origin reload",
                "occurred": True,
                "passed": bool(doctrine_reload.get('slot') == 'D' and doctrine_reload.get('mode') == 'doctrine' and doctrine_reload.get('activeCat') == 'doctrine' and doctrine_reload.get('viewActive')),
                **doctrine_reload,
            })

            screenshot.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot), full_page=False)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    return observations


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--screenshot", required=True)
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args(argv)
    screenshot = Path(args.screenshot)
    try:
        subject = prepare_exact_head_subject()
    except ExactHeadError as exc:
        print(f"exact-head preflight failed; Chromium was not launched\n{exc}", file=sys.stderr)
        return 2
    observations = observe(args.port, screenshot)
    passed = all(item["passed"] for item in observations)
    receipt = {
        "schema_version": "observed-behavior-proof/v1",
        "verdict": "PASS" if passed else "FAIL",
        "evidence_class": "browser_runtime_observed",
        "subject": subject,
        "environment": {
            "kind": environment_kind(),
            "engine": "chromium",
            "scenario": "catalog-derived-numeric-prompt-hotkeys",
        },
        "claims": [{
            "id": "prompt_identity_disambiguation",
            "statement": "bare 126 resolves P126 with canonical copy + snap without Favorite setup while p-prefixed compatibility, prefix disambiguation, and header separation remain intact",
            "status": "PASS" if passed else "FAIL",
            "required_evidence_class": "browser_runtime_observed",
            "observation_ids": [item["id"] for item in observations],
        }],
        "observations": observations,
    }
    receipt_path = Path(args.receipt)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": receipt["verdict"], "receipt": str(receipt_path), "observations": observations}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
