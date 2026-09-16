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
BRANCH = "fix/prompt-snap-header-first-current-20260916"
WORKFLOW = ".github/workflows/prompt-snap-header-first-current.yml"
CARRIER = ".github/carriers/prompt_snap_header_first_current.py"


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


def snap_geometry(page, prompt_id: str) -> dict[str, object]:
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
            headerBottom:hr.bottom,
            chromeBottom:chromeBottom,
            cardTop:cr.top,
            cardBottom:cr.bottom,
            titleTop:tr.top,
            titleBottom:tr.bottom,
            viewportHeight:innerHeight,
            filtersCollapsed:header.classList.contains('filters-collapsed'),
            selected:card.getAttribute('data-selected')==='true'
          };
        }""",
        prompt_id,
    )
    if result is None:
        raise AssertionError(f"missing snap geometry for {prompt_id}")
    result = dict(result)
    result["header_first"] = bool(
        result["filtersCollapsed"]
        and result["selected"]
        and result["cardTop"] >= result["chromeBottom"] + 6
        and result["cardTop"] <= result["chromeBottom"] + 24
        and result["titleTop"] >= result["chromeBottom"] + 6
        and result["titleBottom"] <= result["viewportHeight"]
    )
    return result


def desktop_numeric_probe(expect_header_first: bool) -> dict[str, object]:
    with serve_repo() as origin, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 360}, reduced_motion="reduce")
        context.grant_permissions(["clipboard-read", "clipboard-write"], origin=origin)
        page = context.new_page()
        page.goto(f"{origin}/web/prompt-kit/index.html", wait_until="domcontentloaded")
        card_height = page.locator('[data-prompt-id="P126"]').bounding_box()["height"]
        if card_height <= 360:
            raise AssertionError(f"P126 must exceed short regression viewport, got {card_height}")
        page.evaluate("() => { if(document.activeElement && document.activeElement.blur)document.activeElement.blur(); window.scrollTo(0,0); }")
        page.keyboard.type("126")
        page.wait_for_timeout(900)
        result = snap_geometry(page, "P126")
        result["source_height"] = card_height
        print(json.dumps({"desktop_numeric_snap_probe": result}, sort_keys=True), flush=True)
        if bool(result["header_first"]) != expect_header_first:
            raise AssertionError(
                f"desktop header-first expectation={expect_header_first} observed={result}"
            )
        context.close()
        browser.close()
        return result


def patch_product() -> None:
    old_select = "function selectPrompt(id,opts){var source=typeof opts==='string'?opts:((opts&&opts.source)||'pointer');var normalized=String(id||'').trim().toUpperCase();if(!normalized||!isActivePrompt(normalized))return false;selectedPromptId=normalized;rovingPromptId=normalized;syncPromptListDOM();var el=getPromptElement(normalized);if(el){try{el.scrollIntoView({behavior:'smooth',block:'nearest'})}catch(e){try{el.scrollIntoView()}catch(ignore){}}if(source==='keyboard'){try{el.focus({preventScroll:true})}catch(err){try{el.focus()}catch(ignore2){}}}}announceStatus(normalized+' selected');return true}"
    new_select = "function selectPrompt(id,opts){var source=typeof opts==='string'?opts:((opts&&opts.source)||'pointer');var shouldScroll=!(opts&&typeof opts==='object'&&opts.scroll===false);var normalized=String(id||'').trim().toUpperCase();if(!normalized||!isActivePrompt(normalized))return false;selectedPromptId=normalized;rovingPromptId=normalized;syncPromptListDOM();var el=getPromptElement(normalized);if(el){if(shouldScroll){try{el.scrollIntoView({behavior:'smooth',block:'nearest'})}catch(e){try{el.scrollIntoView()}catch(ignore){}}}if(source==='keyboard'){try{el.focus({preventScroll:true})}catch(err){try{el.focus()}catch(ignore2){}}}}announceStatus(normalized+' selected');return true}"
    replace_once("docs/prompt-kit.js", old_select, new_select)

    old_center = """function centerRenderedPromptCard(promptId,behavior){
  hideCompactFilters();
  var selector='[data-prompt-id=\"'+String(promptId||'').replace(/\"/g,'')+'\"]';
  var card=document.querySelector(selector);
  if(!card)return false;
  var scrollBehavior=behavior||hotkeyScrollBehavior();
  try{card.scrollIntoView({behavior:scrollBehavior,block:'center',inline:'nearest'})}catch(e){try{card.scrollIntoView()}catch(ignore){}}
  return true
}
"""
    new_center = """function promptSnapViewportOffset(){
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

function snapRenderedPromptCardHeader(card,behavior){
  if(!card)return false;
  var scrollBehavior=behavior||hotkeyScrollBehavior();
  try{
    var rect=card.getBoundingClientRect();
    var pageTop=window.scrollY||window.pageYOffset||0;
    var top=Math.max(0,pageTop+rect.top-promptSnapViewportOffset());
    if(scrollBehavior==='instant'){
      var root=document.documentElement;
      var previousScrollBehavior=root&&root.style?root.style.scrollBehavior:'';
      if(root&&root.style)root.style.scrollBehavior='auto';
      try{window.scrollTo(0,top)}
      finally{if(root&&root.style)root.style.scrollBehavior=previousScrollBehavior}
    }else{
      window.scrollTo({top:top,behavior:scrollBehavior})
    }
  }catch(e){
    try{card.scrollIntoView({behavior:scrollBehavior,block:'start',inline:'nearest'});window.scrollBy(0,-promptSnapViewportOffset())}
    catch(ignore){try{card.scrollIntoView()}catch(ignore2){}}
  }
  return true
}

function centerRenderedPromptCard(promptId,behavior){
  hideCompactFilters();
  var selector='[data-prompt-id=\"'+String(promptId||'').replace(/\"/g,'')+'\"]';
  var card=document.querySelector(selector);
  if(!card)return false;
  return snapRenderedPromptCardHeader(card,behavior||hotkeyScrollBehavior())
}
"""
    replace_once("docs/prompt-kit-polish.js", old_center, new_center)

    old_activation = """function activatePromptShortcutTarget(promptId){
  var prompt=PROMPTS.find(function(item){return item.id===promptId});
  if(!prompt)return false;
  if(!revealPromptShortcutTarget(promptId,'instant')){showToast(promptId+' could not be revealed');return false}
  try{if(typeof selectPrompt==='function')selectPrompt(promptId,'keyboard')}catch(e){}
  copyPrompt(promptId);
  return true
}
"""
    new_activation = """function activatePromptShortcutTarget(promptId){
  var prompt=PROMPTS.find(function(item){return item.id===promptId});
  if(!prompt)return false;
  if(!revealPromptShortcutTarget(promptId,'instant')){showToast(promptId+' could not be revealed');return false}
  copyPrompt(promptId);
  return true
}
"""
    replace_once("docs/prompt-kit-polish.js", old_activation, new_activation)
    replace_once(
        "docs/prompt-kit-polish.js",
        "  try{if(typeof selectPrompt==='function')selectPrompt(promptId,'keyboard')}catch(e){}\n  return centerRenderedPromptCard(promptId,behavior||hotkeyScrollBehavior())",
        "  try{if(typeof selectPrompt==='function')selectPrompt(promptId,{source:'keyboard',scroll:false})}catch(e){}\n  return centerRenderedPromptCard(promptId,behavior||hotkeyScrollBehavior())",
    )

    old_contract = """    {
      \"id\": \"snap_hides_filters\",
      \"expected\": \"Any snap-to-prompt path that centers a rendered prompt card (centerRenderedPromptCard, including reveal/activate shortcut targets and detail open) automatically collapses the compact filter chrome via hideCompactFilters so the filter menu cannot obscure the snapped prompt.\"
    },
"""
    new_contract = """    {
      \"id\": \"snap_hides_filters\",
      \"expected\": \"Any snap-to-prompt path that reveals a rendered prompt card (centerRenderedPromptCard, including reveal/activate shortcut targets and detail open) automatically collapses the compact filter chrome via hideCompactFilters so the filter menu cannot obscure the snapped prompt.\"
    },
    {
      \"id\": \"snap_prioritizes_prompt_header\",
      \"expected\": \"Every snap-to-prompt path gives snap navigation sole scroll ownership, makes requested instant snaps independent of page-level smooth-scroll CSS, suppresses selection's ordinary smooth-scroll side effect for that composed journey, and places the target prompt header immediately below visible fixed/sticky page chrome or near the viewport top when that chrome is not occupying the viewport; tall prompt cards must not clip prompt identity above the viewport.\"
    },
"""
    replace_once("harness/contracts/prompt-kit-discovery.v1.json", old_contract, new_contract)

    replace_once(
        "scripts/validate_prompt_kit_discovery.py",
        '    "snap_hides_filters",\n    "stable_identity_resequence",',
        '    "snap_hides_filters",\n    "snap_prioritizes_prompt_header",\n    "stable_identity_resequence",',
    )
    old_markers = """        \"snap_hides_filters\": (
            \"function centerRenderedPromptCard(promptId,behavior)\",
            \"hideCompactFilters();\",
            \"function revealPromptShortcutTarget(promptId,behavior)\",
            \"return centerRenderedPromptCard(promptId,behavior||hotkeyScrollBehavior())\",
        ),
"""
    new_markers = """        \"snap_hides_filters\": (
            \"function centerRenderedPromptCard(promptId,behavior)\",
            \"hideCompactFilters();\",
            \"function revealPromptShortcutTarget(promptId,behavior)\",
            \"return centerRenderedPromptCard(promptId,behavior||hotkeyScrollBehavior())\",
        ),
        \"snap_prioritizes_prompt_header\": (
            \"function promptSnapViewportOffset()\",
            \"function snapRenderedPromptCardHeader(card,behavior)\",
            \"window.getComputedStyle(header).position\",
            \"window.scrollTo({top:top,behavior:scrollBehavior})\",
            \"root.style.scrollBehavior='auto'\",
            \"selectPrompt(promptId,{source:'keyboard',scroll:false})\",
            \"return snapRenderedPromptCardHeader(card,behavior||hotkeyScrollBehavior())\",
        ),
"""
    replace_once("scripts/validate_prompt_kit_discovery.py", old_markers, new_markers)

    replace_once(
        "tests/test_prompt_kit_discovery.py",
        '                "snap_hides_filters",\n                "stable_identity_resequence",',
        '                "snap_hides_filters",\n                "snap_prioritizes_prompt_header",\n                "stable_identity_resequence",',
    )
    replace_once(
        "tests/test_prompt_kit_discovery.py",
        '        self.assertIn("hideCompactFilters", expected["snap_hides_filters"])\n',
        '        self.assertIn("hideCompactFilters", expected["snap_hides_filters"])\n        self.assertIn("sole scroll ownership", expected["snap_prioritizes_prompt_header"])\n',
    )
    old_test = """    def test_snap_to_prompt_hides_compact_filters(self) -> None:
        polish = POLISH_JS.read_text(encoding=\"utf-8\")
        center = polish[
            polish.index(\"function centerRenderedPromptCard\") : polish.index(\"function revealPromptShortcutTarget\")
        ]
        self.assertIn(\"hideCompactFilters();\", center)
        reveal = polish[
            polish.index(\"function revealPromptShortcutTarget\") : polish.index(\"function activatePromptShortcutTarget\")
        ]
        self.assertIn(\"return centerRenderedPromptCard(promptId,behavior||hotkeyScrollBehavior())\", reveal)
"""
    new_test = """    def test_snap_to_prompt_hides_filters_and_prioritizes_prompt_header(self) -> None:
        base = JS.read_text(encoding=\"utf-8\")
        polish = POLISH_JS.read_text(encoding=\"utf-8\")
        center = polish[
            polish.index(\"function promptSnapViewportOffset\") : polish.index(\"function revealPromptShortcutTarget\")
        ]
        for marker in (
            \"hideCompactFilters();\",
            \"function promptSnapViewportOffset()\",
            \"function snapRenderedPromptCardHeader(card,behavior)\",
            \"window.getComputedStyle(header).position\",
            \"window.scrollTo({top:top,behavior:scrollBehavior})\",
            \"root.style.scrollBehavior='auto'\",
            \"return snapRenderedPromptCardHeader(card,behavior||hotkeyScrollBehavior())\",
        ):
            self.assertIn(marker, center)
        self.assertNotIn(\"block:'center'\", center)
        self.assertIn(\"var shouldScroll=!(opts&&typeof opts==='object'&&opts.scroll===false)\", base)
        reveal = polish[
            polish.index(\"function revealPromptShortcutTarget\") : polish.index(\"function activatePromptShortcutTarget\")
        ]
        self.assertIn(\"selectPrompt(promptId,{source:'keyboard',scroll:false})\", reveal)
        self.assertIn(\"return centerRenderedPromptCard(promptId,behavior||hotkeyScrollBehavior())\", reveal)
        activation = polish[
            polish.index(\"function activatePromptShortcutTarget\") : polish.index(\"function handleConfiguredPromptShortcutKey\")
        ]
        self.assertNotIn(\"selectPrompt(promptId\", activation)
"""
    replace_once("tests/test_prompt_kit_discovery.py", old_test, new_test)

    replace_once(
        "tests/test_prompt_kit_selected_prompt.py",
        '        self.assertIn("scrollIntoView", base)\n        self.assertIn("announceStatus", base)\n',
        '        self.assertIn("scrollIntoView", base)\n        self.assertIn("var shouldScroll=!(opts&&typeof opts===\'object\'&&opts.scroll===false)", base)\n        self.assertIn("announceStatus", base)\n',
    )
    replace_once(
        "tests/test_prompt_kit_selected_prompt.py",
        '        self.assertIn("selectPrompt(promptId,\'keyboard\')", polish)\n',
        '        self.assertIn("selectPrompt(promptId,{source:\'keyboard\',scroll:false})", polish)\n',
    )

    old_mobile = """                target_box, target_mid = card_midpoint(page, 'P111')
                assert abs(target_mid - 844 / 2) <= 150, (target_box, target_mid)
"""
    new_mobile = """                target_box = target.bounding_box() or {}
                snap_geometry = page.evaluate(\"\"\"() => {
                  const header=document.querySelector('.header');
                  const card=document.querySelector('[data-prompt-id=\\\"P111\\\"]');
                  const title=card && card.querySelector('.prompt-header');
                  const hr=header.getBoundingClientRect(),cr=card.getBoundingClientRect(),tr=title.getBoundingClientRect();
                  const position=getComputedStyle(header).position;
                  const chromeBottom=(position==='sticky'||position==='fixed')?Math.max(0,Math.min(innerHeight,hr.bottom)):0;
                  return {headerPosition:position,chromeBottom:chromeBottom,cardTop:cr.top,titleTop:tr.top,titleBottom:tr.bottom,viewportHeight:innerHeight};
                }\"\"\")
                assert snap_geometry['cardTop'] >= snap_geometry['chromeBottom'] + 6, snap_geometry
                assert snap_geometry['cardTop'] <= snap_geometry['chromeBottom'] + 24, snap_geometry
                assert snap_geometry['titleTop'] >= snap_geometry['chromeBottom'] + 6, snap_geometry
                assert snap_geometry['titleBottom'] <= snap_geometry['viewportHeight'], snap_geometry
"""
    replace_once("tests/prompt_kit_mobile_quick_controls_browser_proof.py", old_mobile, new_mobile)
    replace_once(
        "tests/prompt_kit_mobile_quick_controls_browser_proof.py",
        "                    'underlying_prompt_centered': True,",
        "                    'underlying_prompt_header_first': True,",
    )

    old_favorite_geometry = """            target = page.locator('[data-prompt-id=\"P126\"]')
            target_present = target.count() > 0
            visible = False
            if target_present:
                visible = page.evaluate(\"\"\"() => {
                  const r=document.querySelector('[data-prompt-id=\"P126\"]').getBoundingClientRect();
                  return r.bottom>0 && r.top<innerHeight;
                }\"\"\")
"""
    new_favorite_geometry = """            target = page.locator('[data-prompt-id=\"P126\"]')
            target_present = target.count() > 0
            visible = False
            header_first = False
            snap_geometry = {}
            if target_present:
                snap_geometry = page.evaluate(\"\"\"() => {
                  const header=document.querySelector('.header');
                  const card=document.querySelector('[data-prompt-id=\"P126\"]');
                  const title=card && card.querySelector('.prompt-header');
                  const hr=header.getBoundingClientRect(),cr=card.getBoundingClientRect(),tr=title.getBoundingClientRect();
                  const position=getComputedStyle(header).position;
                  const chromeBottom=(position==='sticky'||position==='fixed')?Math.max(0,Math.min(innerHeight,hr.bottom)):0;
                  return {headerPosition:position,chromeBottom:chromeBottom,cardTop:cr.top,titleTop:tr.top,titleBottom:tr.bottom,viewportHeight:innerHeight};
                }\"\"\")
                visible = snap_geometry['titleBottom'] > 0 and snap_geometry['titleTop'] < snap_geometry['viewportHeight']
                header_first = bool(
                    snap_geometry['cardTop'] >= snap_geometry['chromeBottom'] + 6
                    and snap_geometry['cardTop'] <= snap_geometry['chromeBottom'] + 24
                    and snap_geometry['titleTop'] >= snap_geometry['chromeBottom'] + 6
                    and snap_geometry['titleBottom'] <= snap_geometry['viewportHeight']
                )
"""
    replace_once("tests/prompt_kit_favorite_browser_proof.py", old_favorite_geometry, new_favorite_geometry)
    old_observation = """                {\"id\": \"prompt_card_scrolled_visible\", \"event\": \"P126 card exists and intersects viewport after shortcut with filters collapsed\", \"occurred\": True, \"passed\": bool(target_present and visible and filters_collapsed), \"present\": bool(target_present), \"visible\": bool(visible), \"filters_collapsed\": bool(filters_collapsed)},
"""
    new_observation = """                {\"id\": \"prompt_card_scrolled_visible\", \"event\": \"P126 prompt header exists and intersects viewport after shortcut with filters collapsed\", \"occurred\": True, \"passed\": bool(target_present and visible and filters_collapsed), \"present\": bool(target_present), \"visible\": bool(visible), \"filters_collapsed\": bool(filters_collapsed)},
                {\"id\": \"prompt_header_first_after_shortcut\", \"event\": \"P126 prompt header is positioned below visible sticky chrome rather than centering the full card\", \"occurred\": True, \"passed\": bool(header_first), \"geometry\": snap_geometry},
"""
    replace_once("tests/prompt_kit_favorite_browser_proof.py", old_observation, new_observation)


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
        "tests.test_prompt_kit_hotkey_completion",
        "tests.test_prompt_kit_mobile_quick_controls",
        "tests.test_prompt_kit_selected_prompt",
        "tests.test_prompt_kit_cross_input_modality",
        "tests.test_prompt_kit_ui_format_alignment",
        "tests.test_prompt_kit_storage_lifecycle_runtime",
        "-v",
    )
    run("git", "diff", "--check")


def browser_candidate_validation() -> None:
    desktop_numeric_probe(expect_header_first=True)
    run("python", "tests/prompt_kit_mobile_quick_controls_browser_proof.py")
    run("python", "tests/prompt_kit_medium_stability_browser_proof.py")
    run(
        "python",
        "tests/prompt_kit_favorite_browser_proof.py",
        "--receipt",
        "Outputs/observed-proof/snap-header-favorite-receipt.json",
        "--screenshot",
        "Outputs/observed-proof/snap-header-favorite.png",
    )


def main() -> int:
    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")

    # Current-source baseline projection. Commit only when accepted main had a stale generated site.
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
    subprocess.run(["git", "add", "web/prompt-kit/index.html"], cwd=ROOT, check=True)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode != 0
    if staged:
        run("git", "commit", "-m", "chore(carrier): materialize current-source snap baseline")

    run("node", "--check", "docs/prompt-kit.js")
    run("node", "--check", "docs/prompt-kit-polish.js")
    run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
    run(
        "python",
        "-m",
        "unittest",
        "tests.test_prompt_kit_discovery",
        "tests.test_prompt_kit_hotkey_completion",
        "tests.test_prompt_kit_mobile_quick_controls",
        "tests.test_prompt_kit_selected_prompt",
        "tests.test_prompt_kit_cross_input_modality",
        "-v",
    )
    run("python", "tests/prompt_kit_mobile_quick_controls_browser_proof.py")
    run(
        "python",
        "tests/prompt_kit_favorite_browser_proof.py",
        "--receipt",
        "Outputs/observed-proof/baseline-snap-favorite-receipt.json",
        "--screenshot",
        "Outputs/observed-proof/baseline-snap-favorite.png",
    )
    desktop_numeric_probe(expect_header_first=False)

    patch_product()
    deterministic_candidate_validation()

    owned = [
        "docs/prompt-kit.js",
        "docs/prompt-kit-polish.js",
        "harness/contracts/prompt-kit-discovery.v1.json",
        "scripts/validate_prompt_kit_discovery.py",
        "tests/test_prompt_kit_discovery.py",
        "tests/test_prompt_kit_selected_prompt.py",
        "tests/prompt_kit_mobile_quick_controls_browser_proof.py",
        "tests/prompt_kit_favorite_browser_proof.py",
        "web/prompt-kit/index.html",
    ]
    run("git", "add", *owned)
    run("git", "diff", "--cached", "--check")
    run("git", "commit", "-m", "fix(prompt-kit): keep prompt headers visible when snapping")
    candidate_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    print(f"CANDIDATE_SHA={candidate_sha}", flush=True)

    browser_candidate_validation()

    # Second pass after browser green: deterministic contract still matches exact committed candidate.
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
    run("git", "diff", "--check")

    # Carrier cleanup is bookkeeping-only; behavior/proof inputs stay unchanged.
    run("git", "rm", WORKFLOW, CARRIER)
    run("git", "commit", "-m", "chore(carrier): retire snap header repair executor")
    final_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    print(f"FINAL_SHA={final_sha}", flush=True)
    run("git", "push", "origin", f"HEAD:{BRANCH}")
    run("git", "status", "--short", "--untracked-files=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
