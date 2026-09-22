#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import threading
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BRANCH = "fix/prompt-desktop-selection-header-offset-20260921"
WORKFLOW = ".github/workflows/prompt-desktop-selection-header-offset.yml"
CARRIER = ".github/carriers/prompt_desktop_selection_header_offset.py"


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected exactly one replacement target, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        pass


@contextmanager
def serve_repo():
    handler = lambda *args, **kwargs: Quiet(*args, directory=str(ROOT), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def pointer_geometry(page, prompt_id: str) -> dict[str, object]:
    result = page.evaluate(
        """id => {
          const header=document.querySelector('.header');
          const card=document.querySelector('[data-prompt-id="'+id+'"]');
          const title=card && card.querySelector('.prompt-header');
          if(!header||!card||!title)return null;
          const hr=header.getBoundingClientRect();
          const cr=card.getBoundingClientRect();
          const tr=title.getBoundingClientRect();
          const position=getComputedStyle(header).position;
          const chromeBottom=(position==='sticky'||position==='fixed')
            ? Math.max(0,Math.min(innerHeight,hr.bottom))
            : 0;
          return {
            headerPosition:position,
            chromeBottom:chromeBottom,
            cardTop:cr.top,
            cardBottom:cr.bottom,
            titleTop:tr.top,
            titleBottom:tr.bottom,
            viewportHeight:innerHeight,
            selected:card.getAttribute('data-selected')==='true'
          };
        }""",
        prompt_id,
    )
    if result is None:
        raise AssertionError(f"missing pointer geometry for {prompt_id}")
    return dict(result)


def desktop_pointer_probe(expect_header_first: bool) -> dict[str, object]:
    with serve_repo() as origin, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            reduced_motion="reduce",
        )
        page = context.new_page()
        page.goto(f"{origin}/web/prompt-kit/index.html", wait_until="domcontentloaded")
        page.evaluate("() => { if(typeof hideCompactFilters==='function')hideCompactFilters(); }")
        page.wait_for_timeout(100)
        positioned = page.evaluate(
            """() => {
              const header=document.querySelector('.header');
              const card=document.querySelector('[data-prompt-id="P07"]');
              if(!header||!card)return false;
              const position=getComputedStyle(header).position;
              if(position!=='sticky'&&position!=='fixed')return false;
              const hr=header.getBoundingClientRect();
              const chromeBottom=Math.max(0,Math.min(innerHeight,hr.bottom));
              const cr=card.getBoundingClientRect();
              const absoluteTop=(window.scrollY||window.pageYOffset||0)+cr.top;
              const root=document.documentElement;
              const previous=root&&root.style?root.style.scrollBehavior:'';
              if(root&&root.style)root.style.scrollBehavior='auto';
              try{window.scrollTo(0,Math.max(0,absoluteTop-Math.max(8,chromeBottom-24)))}
              finally{if(root&&root.style)root.style.scrollBehavior=previous}
              return true;
            }"""
        )
        if not positioned:
            raise AssertionError("desktop sticky-header precondition unavailable")
        page.wait_for_timeout(100)
        before = pointer_geometry(page, "P07")
        if not (before["titleTop"] < before["chromeBottom"] and before["cardBottom"] < before["viewportHeight"]):
            raise AssertionError(f"failed to reproduce layout-visible sticky-header overlap precondition: {before}")

        target = page.locator('[data-prompt-id="P07"] .prompt-desc')
        box = target.bounding_box()
        if not box:
            raise AssertionError("P07 prompt description is not pointer-addressable")
        page.mouse.click(box["x"] + min(16, box["width"] / 2), box["y"] + min(12, box["height"] / 2))
        page.wait_for_function(
            """() => {
              const card=document.querySelector('[data-prompt-id="P07"]');
              return !!card && card.getAttribute('data-selected')==='true';
            }""",
            timeout=2000,
        )
        page.wait_for_timeout(900)
        after = pointer_geometry(page, "P07")
        header_first = bool(
            after["selected"]
            and after["cardTop"] >= after["chromeBottom"] + 6
            and after["cardTop"] <= after["chromeBottom"] + 24
            and after["titleTop"] >= after["chromeBottom"] + 6
            and after["titleBottom"] <= after["viewportHeight"]
        )
        payload = {
            "before": before,
            "after": after,
            "header_first": header_first,
            "expected_header_first": expect_header_first,
        }
        print(json.dumps({"desktop_pointer_selection_probe": payload}, sort_keys=True), flush=True)
        if header_first != expect_header_first:
            raise AssertionError(
                f"desktop pointer header-first expectation={expect_header_first} observed={payload}"
            )
        context.close()
        browser.close()
        return payload


def patch_product() -> None:
    old_select = "function selectPrompt(id,opts){var source=typeof opts==='string'?opts:((opts&&opts.source)||'pointer');var shouldScroll=!(opts&&typeof opts==='object'&&opts.scroll===false);var normalized=String(id||'').trim().toUpperCase();if(!normalized||!isActivePrompt(normalized))return false;selectedPromptId=normalized;rovingPromptId=normalized;syncPromptListDOM();var el=getPromptElement(normalized);if(el){if(shouldScroll){try{el.scrollIntoView({behavior:'smooth',block:'nearest'})}catch(e){try{el.scrollIntoView()}catch(ignore){}}}if(source==='keyboard'){try{el.focus({preventScroll:true})}catch(err){try{el.focus()}catch(ignore2){}}}}announceStatus(normalized+' selected');return true}"
    new_select = "function selectPrompt(id,opts){var source=typeof opts==='string'?opts:((opts&&opts.source)||'pointer');var shouldScroll=!(opts&&typeof opts==='object'&&opts.scroll===false);var normalized=String(id||'').trim().toUpperCase();if(!normalized||!isActivePrompt(normalized))return false;selectedPromptId=normalized;rovingPromptId=normalized;syncPromptListDOM();var el=getPromptElement(normalized);if(el){if(shouldScroll){try{if(typeof promptHasViewportOccludingHeader==='function'&&promptHasViewportOccludingHeader()&&typeof snapRenderedPromptCardHeader==='function'){snapRenderedPromptCardHeader(el,'smooth')}else{el.scrollIntoView({behavior:'smooth',block:'nearest'})}}catch(e){try{el.scrollIntoView({behavior:'smooth',block:'nearest'})}catch(ignore){try{el.scrollIntoView()}catch(ignore2){}}}}if(source==='keyboard'){try{el.focus({preventScroll:true})}catch(err){try{el.focus()}catch(ignore3){}}}}announceStatus(normalized+' selected');return true}"
    replace_once("docs/prompt-kit.js", old_select, new_select)

    old_offset = """function promptSnapViewportOffset(){
  var gap=12;
  var header=document.querySelector('.header');
  if(!header)return gap;
  try{
    var position=window.getComputedStyle(header).position;
    if(position!=='sticky'&&position!=='fixed')return gap;
    var rect=header.getBoundingClientRect();
    var viewportHeight=window.innerHeight||document.documentElement.clientHeight||0;
    var bottom=Number(rect&&rect.bottom)||0;
    var visibleBottom=Math.max(0,Math.min(viewportHeight,bottom));
    return Math.max(gap,Math.ceil(visibleBottom+gap))
  }catch(e){return gap}
}
"""
    new_offset = """function promptHasViewportOccludingHeader(){
  var header=document.querySelector('.header');
  if(!header)return false;
  try{
    var position=window.getComputedStyle(header).position;
    return position==='sticky'||position==='fixed'
  }catch(e){return false}
}

function promptSnapViewportOffset(){
  var gap=12;
  var header=document.querySelector('.header');
  if(!header||!promptHasViewportOccludingHeader())return gap;
  try{
    var rect=header.getBoundingClientRect();
    var viewportHeight=window.innerHeight||document.documentElement.clientHeight||0;
    var bottom=Number(rect&&rect.bottom)||0;
    var visibleBottom=Math.max(0,Math.min(viewportHeight,bottom));
    return Math.max(gap,Math.ceil(visibleBottom+gap))
  }catch(e){return gap}
}
"""
    replace_once("docs/prompt-kit-polish.js", old_offset, new_offset)

    old_contract = '"expected": "Every snap-to-prompt path gives snap navigation sole scroll ownership, makes requested instant snaps independent of page-level smooth-scroll CSS, suppresses selection\'s ordinary smooth-scroll side effect for that composed journey, and places the target prompt header immediately below visible fixed/sticky page chrome or near the viewport top when that chrome is not occupying the viewport; tall prompt cards must not clip prompt identity above the viewport."'
    new_contract = '"expected": "Every snap-to-prompt path gives snap navigation sole scroll ownership, makes requested instant snaps independent of page-level smooth-scroll CSS, suppresses selection\'s ordinary smooth-scroll side effect for that composed journey, and places the target prompt header immediately below visible fixed/sticky page chrome or near the viewport top when that chrome is not occupying the viewport. Ordinary sticky-header selection, including desktop mouse selection, must reuse the same header-aware positioning instead of relying only on layout visibility from scrollIntoView; static-header mobile selection retains nearest-scroll behavior. Tall prompt cards must not clip prompt identity above the viewport."'
    replace_once("harness/contracts/prompt-kit-discovery.v1.json", old_contract, new_contract)

    replace_once(
        "scripts/validate_prompt_kit_discovery.py",
        '        "snap_prioritizes_prompt_header": (\n            "function promptSnapViewportOffset()",',
        '        "snap_prioritizes_prompt_header": (\n            "function promptHasViewportOccludingHeader()",\n            "function promptSnapViewportOffset()",',
    )
    validator_anchor = """    for requirement_id, markers in polish_markers.items():
        if any(marker not in polish_js for marker in markers):
            missing.append(requirement_id)
    if "card.querySelector('.prompt-header').appendChild(favBtn)" in polish_js:
"""
    validator_replacement = """    for requirement_id, markers in polish_markers.items():
        if any(marker not in polish_js for marker in markers):
            missing.append(requirement_id)
    selection_start = js.find("function selectPrompt(id,opts)")
    selection_end = js.find("function clearSelectionState()", selection_start)
    selection_source = js[selection_start:selection_end] if selection_start >= 0 and selection_end > selection_start else ""
    if any(
        marker not in selection_source
        for marker in (
            "promptHasViewportOccludingHeader()",
            "snapRenderedPromptCardHeader(el,'smooth')",
            "scrollIntoView({behavior:'smooth',block:'nearest'})",
        )
    ) and "snap_prioritizes_prompt_header" not in missing:
        missing.append("snap_prioritizes_prompt_header")
    if "card.querySelector('.prompt-header').appendChild(favBtn)" in polish_js:
"""
    replace_once("scripts/validate_prompt_kit_discovery.py", validator_anchor, validator_replacement)

    replace_once(
        "tests/test_prompt_kit_discovery.py",
        '        self.assertIn("sole scroll ownership", expected["snap_prioritizes_prompt_header"])\n',
        '        self.assertIn("sole scroll ownership", expected["snap_prioritizes_prompt_header"])\n        self.assertIn("Ordinary sticky-header selection", expected["snap_prioritizes_prompt_header"])\n',
    )
    replace_once(
        "tests/test_prompt_kit_discovery.py",
        '        center = polish[\n            polish.index("function promptSnapViewportOffset") : polish.index("function revealPromptShortcutTarget")\n        ]\n',
        '        center = polish[\n            polish.index("function promptHasViewportOccludingHeader") : polish.index("function revealPromptShortcutTarget")\n        ]\n',
    )
    replace_once(
        "tests/test_prompt_kit_discovery.py",
        '            "hideCompactFilters();",\n            "function promptSnapViewportOffset()",',
        '            "hideCompactFilters();",\n            "function promptHasViewportOccludingHeader()",\n            "function promptSnapViewportOffset()",',
    )
    discovery_anchor = """        self.assertNotIn("block:'center'", center)
        self.assertIn("var shouldScroll=!(opts&&typeof opts==='object'&&opts.scroll===false)", base)
        reveal = polish[
"""
    discovery_replacement = """        self.assertNotIn("block:'center'", center)
        self.assertIn("var shouldScroll=!(opts&&typeof opts==='object'&&opts.scroll===false)", base)
        selection = base[base.index("function selectPrompt(id,opts)") : base.index("function clearSelectionState()")]
        self.assertIn("promptHasViewportOccludingHeader()", selection)
        self.assertIn("snapRenderedPromptCardHeader(el,'smooth')", selection)
        self.assertIn("scrollIntoView({behavior:'smooth',block:'nearest'})", selection)
        self.assertLess(selection.index("snapRenderedPromptCardHeader"), selection.index("scrollIntoView"))
        reveal = polish[
"""
    replace_once("tests/test_prompt_kit_discovery.py", discovery_anchor, discovery_replacement)

    selected_anchor = """        self.assertIn("classList.add('is-selected')", base)
        self.assertIn("classList.remove('is-selected')", base)

    def test_enter_to_open_and_copy_hotkey(self) -> None:
"""
    selected_replacement = """        self.assertIn("classList.add('is-selected')", base)
        self.assertIn("classList.remove('is-selected')", base)

    def test_pointer_selection_avoids_sticky_header_occlusion(self) -> None:
        base = BASE.read_text(encoding="utf-8")
        polish = POLISH.read_text(encoding="utf-8")
        selection = base[base.index("function selectPrompt(id,opts)") : base.index("function clearSelectionState()")]
        self.assertIn("promptHasViewportOccludingHeader()", selection)
        self.assertIn("snapRenderedPromptCardHeader(el,'smooth')", selection)
        self.assertIn("scrollIntoView({behavior:'smooth',block:'nearest'})", selection)
        self.assertLess(selection.index("snapRenderedPromptCardHeader"), selection.index("scrollIntoView"))
        helper = polish[
            polish.index("function promptHasViewportOccludingHeader()") :
            polish.index("function snapRenderedPromptCardHeader(card,behavior)")
        ]
        self.assertIn("return position==='sticky'||position==='fixed'", helper)
        self.assertIn("if(!header||!promptHasViewportOccludingHeader())return gap", helper)

    def test_enter_to_open_and_copy_hotkey(self) -> None:
"""
    replace_once("tests/test_prompt_kit_selected_prompt.py", selected_anchor, selected_replacement)

    browser_anchor = """            expected = page.evaluate("PROMPTS.find(p => p.id === 'P126').copyContent")

            # Exercise search mode exactly as a keyboard user does: slash, type, Escape.
"""
    browser_replacement = """            expected = page.evaluate("PROMPTS.find(p => p.id === 'P126').copyContent")

            # Regression: a desktop mouse click on a layout-visible card whose title is
            # underneath sticky chrome must reposition the title below that chrome.
            page.evaluate("() => { if(typeof hideCompactFilters==='function')hideCompactFilters(); }")
            page.wait_for_timeout(100)
            pointer_positioned = page.evaluate(
                \"\"\"() => {
                  const header=document.querySelector('.header');
                  const card=document.querySelector('[data-prompt-id="P07"]');
                  if(!header||!card)return false;
                  const position=getComputedStyle(header).position;
                  if(position!=='sticky'&&position!=='fixed')return false;
                  const hr=header.getBoundingClientRect();
                  const chromeBottom=Math.max(0,Math.min(innerHeight,hr.bottom));
                  const cr=card.getBoundingClientRect();
                  const absoluteTop=(scrollY||pageYOffset||0)+cr.top;
                  const root=document.documentElement;
                  const previous=root&&root.style?root.style.scrollBehavior:'';
                  if(root&&root.style)root.style.scrollBehavior='auto';
                  try{scrollTo(0,Math.max(0,absoluteTop-Math.max(8,chromeBottom-24)))}
                  finally{if(root&&root.style)root.style.scrollBehavior=previous}
                  return true;
                }\"\"\"
            )
            page.wait_for_timeout(100)
            pointer_before = page.evaluate(
                \"\"\"() => {
                  const header=document.querySelector('.header');
                  const card=document.querySelector('[data-prompt-id="P07"]');
                  const title=card && card.querySelector('.prompt-header');
                  const hr=header.getBoundingClientRect(),cr=card.getBoundingClientRect(),tr=title.getBoundingClientRect();
                  const position=getComputedStyle(header).position;
                  const chromeBottom=(position==='sticky'||position==='fixed')?Math.max(0,Math.min(innerHeight,hr.bottom)):0;
                  return {headerPosition:position,chromeBottom:chromeBottom,cardTop:cr.top,cardBottom:cr.bottom,titleTop:tr.top,titleBottom:tr.bottom,viewportHeight:innerHeight};
                }\"\"\"
            ) if pointer_positioned else {}
            pointer_target = page.locator('[data-prompt-id="P07"] .prompt-desc')
            pointer_box = pointer_target.bounding_box() or {}
            if pointer_box:
                page.mouse.click(
                    pointer_box['x'] + min(16, pointer_box['width'] / 2),
                    pointer_box['y'] + min(12, pointer_box['height'] / 2),
                )
                page.wait_for_timeout(900)
            pointer_after = page.evaluate(
                \"\"\"() => {
                  const header=document.querySelector('.header');
                  const card=document.querySelector('[data-prompt-id="P07"]');
                  const title=card && card.querySelector('.prompt-header');
                  const hr=header.getBoundingClientRect(),cr=card.getBoundingClientRect(),tr=title.getBoundingClientRect();
                  const position=getComputedStyle(header).position;
                  const chromeBottom=(position==='sticky'||position==='fixed')?Math.max(0,Math.min(innerHeight,hr.bottom)):0;
                  return {headerPosition:position,chromeBottom:chromeBottom,cardTop:cr.top,titleTop:tr.top,titleBottom:tr.bottom,viewportHeight:innerHeight,selected:card.getAttribute('data-selected')==='true'};
                }\"\"\"
            ) if pointer_box else {}
            pointer_header_first = bool(
                pointer_before
                and pointer_after
                and pointer_before['titleTop'] < pointer_before['chromeBottom']
                and pointer_before['cardBottom'] < pointer_before['viewportHeight']
                and pointer_after['selected']
                and pointer_after['cardTop'] >= pointer_after['chromeBottom'] + 6
                and pointer_after['cardTop'] <= pointer_after['chromeBottom'] + 24
                and pointer_after['titleTop'] >= pointer_after['chromeBottom'] + 6
                and pointer_after['titleBottom'] <= pointer_after['viewportHeight']
            )
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(100)

            # Exercise search mode exactly as a keyboard user does: slash, type, Escape.
"""
    replace_once("tests/prompt_kit_favorite_browser_proof.py", browser_anchor, browser_replacement)

    observations_anchor = """            observations = [
"""
    observations_replacement = """            observations = [
                {"id": "desktop_pointer_selected_header_first", "event": "Desktop mouse selection repositions a selected prompt title below visible sticky chrome instead of accepting layout-visible overlap", "occurred": True, "passed": bool(pointer_header_first), "before": pointer_before, "after": pointer_after},
"""
    replace_once("tests/prompt_kit_favorite_browser_proof.py", observations_anchor, observations_replacement)


def deterministic_candidate_validation() -> None:
    run("node", "--check", "docs/prompt-kit.js")
    run("node", "--check", "docs/prompt-kit-polish.js")
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
    run("python", "scripts/validate_prompt_kit_ui_format_alignment.py", "--require-implementation", "--summary")
    run(
        "python",
        "-m",
        "unittest",
        "tests.test_prompt_kit_discovery",
        "tests.test_prompt_kit_selected_prompt",
        "tests.test_prompt_kit_hotkey_completion",
        "tests.test_prompt_kit_mobile_quick_controls",
        "tests.test_prompt_kit_cross_input_modality",
        "-v",
    )
    run("git", "diff", "--check")


def browser_candidate_validation() -> None:
    desktop_pointer_probe(expect_header_first=True)
    run(
        "python",
        "tests/prompt_kit_favorite_browser_proof.py",
        "--receipt",
        "Outputs/observed-proof/desktop-selection-header-receipt.json",
        "--screenshot",
        "Outputs/observed-proof/desktop-selection-header.png",
    )
    run("python", "tests/prompt_kit_mobile_quick_controls_browser_proof.py")
    run("python", "tests/prompt_kit_medium_stability_browser_proof.py")


def main() -> int:
    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")

    # Current-floor baseline: canonical generated parity must already hold while
    # the direct desktop mouse geometry probe reproduces the reported overlap.
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    run("node", "--check", "docs/prompt-kit.js")
    run("node", "--check", "docs/prompt-kit-polish.js")
    run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
    run(
        "python",
        "-m",
        "unittest",
        "tests.test_prompt_kit_discovery",
        "tests.test_prompt_kit_selected_prompt",
        "-v",
    )
    desktop_pointer_probe(expect_header_first=False)

    patch_product()
    deterministic_candidate_validation()

    owned = [
        "docs/prompt-kit.js",
        "docs/prompt-kit-polish.js",
        "harness/contracts/prompt-kit-discovery.v1.json",
        "scripts/validate_prompt_kit_discovery.py",
        "tests/test_prompt_kit_discovery.py",
        "tests/test_prompt_kit_selected_prompt.py",
        "tests/prompt_kit_favorite_browser_proof.py",
        "web/prompt-kit/index.html",
    ]
    run("git", "add", *owned)
    run("git", "diff", "--cached", "--check")
    run("git", "commit", "-m", "fix(prompt-kit): keep desktop selections below sticky header")
    candidate_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    print(f"CANDIDATE_SHA={candidate_sha}", flush=True)

    browser_candidate_validation()

    # Deliberate second pass: re-run the owner contract, focused tests, parity,
    # and patch hygiene against the committed behavior candidate.
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
    run(
        "python",
        "-m",
        "unittest",
        "tests.test_prompt_kit_discovery",
        "tests.test_prompt_kit_selected_prompt",
        "-v",
    )
    run("git", "diff", "--check")

    # Carrier cleanup is transport-only; PR CI will validate the final branch head.
    run("git", "rm", WORKFLOW, CARRIER)
    run("git", "commit", "-m", "chore(carrier): retire desktop selection repair executor")
    final_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    print(f"FINAL_SHA={final_sha}", flush=True)
    run("git", "push", "origin", f"HEAD:{BRANCH}")
    run("git", "status", "--short", "--untracked-files=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
