#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
MOBILE_TEST = ROOT / "tests" / "test_prompt_kit_mobile.py"
QUICK_TEST = ROOT / "tests" / "test_prompt_kit_mobile_quick_controls.py"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-mobile.v1.json"
WORKFLOW = ROOT / ".github" / "workflows" / "prompt-kit-mobile-quick-controls.yml"
BROWSER_PROOF = ROOT / "tests" / "prompt_kit_medium_stability_browser_proof.py"

MOBILE_MEDIA = "@media (hover:none) and (pointer:coarse)"
WIDTH_MEDIA = "@media(max-width:760px)"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def patch_polish() -> None:
    source = POLISH.read_text(encoding="utf-8")
    count = source.count(WIDTH_MEDIA)
    if count < 5:
        raise SystemExit(f"expected at least five width-gated mobile interaction blocks, found {count}")
    source = source.replace(WIDTH_MEDIA, MOBILE_MEDIA)
    required = (
        MOBILE_MEDIA + "{.prompt-card .prompt-header",
        MOBILE_MEDIA + "{.favorites-group-jump-nav",
        MOBILE_MEDIA + "{.hotkey-help{display:flex",
        MOBILE_MEDIA + "{.ref-toggle{display:none!important",
        MOBILE_MEDIA + "{.prompt-detail-favorite-btn",
        "@media(max-width:980px){.header-top",
    )
    for marker in required:
        if marker not in source:
            raise SystemExit(f"missing medium-stability marker after patch: {marker}")
    for forbidden in (
        WIDTH_MEDIA + "{.hotkey-help{display:flex",
        WIDTH_MEDIA + "{.ref-toggle{display:none!important",
        WIDTH_MEDIA + "{.prompt-card .prompt-header",
    ):
        if forbidden in source:
            raise SystemExit(f"width still controls interaction identity: {forbidden}")
    POLISH.write_text(source, encoding="utf-8")
    print(f"patched {count} interaction media blocks in {POLISH.relative_to(ROOT)}")


def patch_contract() -> None:
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    requirement_id = "mobile_medium_orientation_invariant"
    if not any(item.get("id") == requirement_id for item in payload["requirements"]):
        requirement = {
            "id": requirement_id,
            "expected": (
                "Mobile interaction identity is derived from the touch/coarse-pointer medium rather than viewport width alone. "
                "The same loaded phone page preserves Go to P#, More, touch action rails, and hidden desktop reference handles across "
                "PORTRAIT -> LANDSCAPE -> PORTRAIT without reload or state reset. Width may still compress layout geometry inside a mode, "
                "but rotating a phone must not switch it to desktop controls. Conversely, a narrow or unusually tall desktop viewport may "
                "reflow content but retains desktop Hotkeys and the bottom-right Reference handle and must not expose mobile-only controls."
            ),
        }
        insert_at = next(
            (i for i, item in enumerate(payload["requirements"]) if item.get("id") == "horizontal_filter_rails"),
            len(payload["requirements"]),
        )
        payload["requirements"].insert(insert_at, requirement)
    proof_command = "python tests/prompt_kit_medium_stability_browser_proof.py"
    if proof_command not in payload["validation"]:
        payload["validation"].append(proof_command)
    payload["proof_ceiling"] = (
        "Static source, deterministic tests, generated-site parity, CI, and exact-head Chromium journeys prove the tracked responsive/browser "
        "behavior they exercise, including Go to P# snap-without-detail, whole-card tap copy, explicit Open inspection, the exact/prefix, "
        "leading-zero, pasted-ID, and missing-ID edge-case matrix, a same-page 390x844 -> 844x390 -> 390x844 phone orientation cycle, and "
        "a narrow/tall desktop control-identity regression. Physical Android thumb reach, real software-keyboard timing, browser-specific clipboard "
        "prompts, hybrid-device primary-input heuristics, and device-specific viewport/browser UI remain field acceptance gates."
    )
    CONTRACT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_mobile_test() -> None:
    source = MOBILE_TEST.read_text(encoding="utf-8")
    if '"mobile_medium_orientation_invariant",' not in source:
        source = replace_once(
            source,
            '                "mobile_prompt_id_jump",\n',
            '                "mobile_prompt_id_jump",\n                "mobile_medium_orientation_invariant",\n',
            "mobile contract requirement set",
        )
    MOBILE_TEST.write_text(source, encoding="utf-8")


def patch_quick_test() -> None:
    source = QUICK_TEST.read_text(encoding="utf-8")
    if "test_interaction_medium_is_not_viewport_width" not in source:
        marker = "    def test_contract_and_phone_guide_define_fast_p111_route(self) -> None:\n"
        test = '''    def test_interaction_medium_is_not_viewport_width(self) -> None:\n        source = POLISH.read_text(encoding="utf-8")\n        medium = "@media (hover:none) and (pointer:coarse)"\n        for marker in (\n            medium + "{.prompt-card .prompt-header",\n            medium + "{.favorites-group-jump-nav",\n            medium + "{.hotkey-help{display:flex",\n            medium + "{.ref-toggle{display:none!important",\n            medium + "{.prompt-detail-favorite-btn",\n        ):\n            self.assertIn(marker, source)\n        for forbidden in (\n            "@media(max-width:760px){.prompt-card .prompt-header",\n            "@media(max-width:760px){.hotkey-help{display:flex",\n            "@media(max-width:760px){.ref-toggle{display:none!important",\n        ):\n            self.assertNotIn(forbidden, source)\n        self.assertIn("@media(max-width:980px){.header-top", source)\n        self.assertIn(".hotkey-help{position:fixed;right:80px;bottom:16px", source)\n\n'''
        if marker not in source:
            raise SystemExit("quick-controls insertion marker moved")
        source = source.replace(marker, test + marker, 1)
    QUICK_TEST.write_text(source, encoding="utf-8")


def patch_workflow() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    path_line = "      - 'tests/prompt_kit_mobile_quick_controls_browser_proof.py'\n"
    new_path_line = "      - 'tests/prompt_kit_medium_stability_browser_proof.py'\n"
    if new_path_line not in source:
        count = source.count(path_line)
        if count != 2:
            raise SystemExit(f"expected browser-proof path twice in workflow, found {count}")
        source = source.replace(path_line, path_line + new_path_line)
    old_run = "      - name: Chromium quick-controls journey\n        run: python tests/prompt_kit_mobile_quick_controls_browser_proof.py\n"
    new_run = (
        "      - name: Chromium quick-controls and medium-stability journeys\n"
        "        run: |\n"
        "          python tests/prompt_kit_mobile_quick_controls_browser_proof.py\n"
        "          python tests/prompt_kit_medium_stability_browser_proof.py\n"
    )
    if old_run in source:
        source = source.replace(old_run, new_run, 1)
    elif "python tests/prompt_kit_medium_stability_browser_proof.py" not in source:
        raise SystemExit("workflow browser run marker moved")
    WORKFLOW.write_text(source, encoding="utf-8")


def write_browser_proof() -> None:
    BROWSER_PROOF.write_text(r'''#!/usr/bin/env python3
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
''', encoding="utf-8")


def main() -> int:
    patch_polish()
    patch_contract()
    patch_mobile_test()
    patch_quick_test()
    patch_workflow()
    write_browser_proof()
    print("Prompt Kit medium-stability patch staged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
