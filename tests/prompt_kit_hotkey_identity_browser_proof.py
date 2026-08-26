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
TARGETS = ("P11", "P13", "P111")


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

            # Configure all three overlapping identities through the real product UI.
            for prompt_id in TARGETS:
                card = page.locator(f'[data-prompt-id="{prompt_id}"]')
                if card.count() != 1:
                    raise AssertionError(f"missing canonical card {prompt_id}")
                card.locator('.prompt-favorite-btn').click()
            page.locator('#hotkeyHelpToggle').click()
            page.wait_for_timeout(50)
            for prompt_id in TARGETS:
                page.locator('#promptShortcutPromptId').fill(prompt_id)
                page.get_by_role('button', name='Save favorite prompt keyboard shortcut').click()
                page.wait_for_timeout(75)
                if f"Shortcut {prompt_id.lower()} saved" not in page.locator('#toast').inner_text():
                    raise AssertionError(f"shortcut save failed for {prompt_id}")
            page.locator('.hotkey-help-close').click()
            page.evaluate("document.activeElement && document.activeElement.blur()")

            def set_clipboard(value: str) -> None:
                page.evaluate("value => navigator.clipboard.writeText(value)", value)

            def clipboard() -> str:
                return page.evaluate("navigator.clipboard.readText()")

            def press(sequence: str) -> None:
                for char in sequence:
                    page.keyboard.press(char)

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

            # Numeric input must never activate A-E header slots.
            active_slot = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")
            observations.append({
                "id": "numeric_sequences_do_not_drive_header",
                "event": "digit-bearing prompt sequences leave header navigation in the expected All profile",
                "occurred": True,
                "passed": active_slot == "A",
                "active_slot": active_slot,
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
    observations = observe(args.port, screenshot)
    passed = all(item["passed"] for item in observations)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    receipt = {
        "schema_version": "observed-behavior-proof/v1",
        "verdict": "PASS" if passed else "FAIL",
        "evidence_class": "browser_runtime_observed",
        "subject": {
            "commit_sha": sha,
            "artifact": {
                "path": "web/prompt-kit/index.html",
                "sha256": hashlib.sha256(ARTIFACT.read_bytes()).hexdigest(),
            },
        },
        "environment": {
            "kind": environment_kind(),
            "engine": "chromium",
            "scenario": "overlapping-and-dotted-prompt-identity-hotkeys",
        },
        "claims": [{
            "id": "prompt_identity_disambiguation",
            "statement": "p11, p13, p111, p1.1, and p1.11 resolve to distinct canonical prompt identities without numeric header collisions",
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
