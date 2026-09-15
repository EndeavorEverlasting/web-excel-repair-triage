#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected exactly one replacement target, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


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


def snap_probe(expect_header_first: bool) -> dict[str, object]:
    with serve_repo() as origin, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 620}, reduced_motion="reduce")
        page = context.new_page()
        page.goto(f"{origin}/web/prompt-kit/index.html", wait_until="domcontentloaded")
        candidate = page.evaluate(
            """() => {
              const cards=Array.from(document.querySelectorAll('[data-prompt-id]'));
              const pageHeight=document.documentElement.scrollHeight;
              const ranked=cards.map(card => {
                const r=card.getBoundingClientRect();
                return {id:card.getAttribute('data-prompt-id'),height:r.height,top:r.top+scrollY};
              }).filter(item => item.top>700 && item.top<pageHeight-700)
                .sort((a,b)=>b.height-a.height);
              return ranked[0] || null;
            }"""
        )
        if not candidate:
            raise AssertionError("No real mid-page prompt card available for snap probe")
        prompt_id = str(candidate["id"])
        page.evaluate("id => centerRenderedPromptCard(id,'instant')", prompt_id)
        page.wait_for_timeout(120)
        geometry = page.evaluate(
            """id => {
              const header=document.querySelector('.header');
              const card=document.querySelector('[data-prompt-id="'+id+'"]');
              const title=card && card.querySelector('.prompt-header');
              if(!header||!card||!title)return null;
              const hr=header.getBoundingClientRect();
              const cr=card.getBoundingClientRect();
              const tr=title.getBoundingClientRect();
              return {
                headerBottom:hr.bottom,
                cardTop:cr.top,
                cardBottom:cr.bottom,
                titleTop:tr.top,
                titleBottom:tr.bottom,
                viewportHeight:innerHeight,
                filtersCollapsed:header.classList.contains('filters-collapsed')
              };
            }""",
            prompt_id,
        )
        if geometry is None:
            raise AssertionError(f"Missing geometry for {prompt_id}")
        header_first = bool(
            geometry["filtersCollapsed"]
            and geometry["cardTop"] >= geometry["headerBottom"] + 6
            and geometry["cardTop"] <= geometry["headerBottom"] + 24
            and geometry["titleTop"] >= geometry["headerBottom"] + 6
            and geometry["titleBottom"] <= geometry["viewportHeight"]
        )
        result = {"prompt_id": prompt_id, "source_height": candidate["height"], **geometry, "header_first": header_first}
        print(json.dumps({"snap_probe": result}, sort_keys=True), flush=True)
        if expect_header_first:
            if not header_first:
                raise AssertionError(f"candidate did not produce header-first snap: {result}")
        else:
            if header_first:
                raise AssertionError(f"baseline unexpectedly already satisfies header-first contract: {result}")
        context.close()
        browser.close()
        return result


def patch() -> None:
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
    new_center = """function promptSnapHeaderOffset(){
  var gap=12;
  var header=document.querySelector('.header');
  if(!header)return gap;
  try{
    var rect=header.getBoundingClientRect();
    var bottom=Number(rect&&rect.bottom)||0;
    return Math.max(gap,Math.ceil(bottom+gap))
  }catch(e){return gap}
}

function snapRenderedPromptCardHeader(card,behavior){
  if(!card)return false;
  var scrollBehavior=behavior||hotkeyScrollBehavior();
  if(scrollBehavior==='instant')scrollBehavior='auto';
  try{
    var rect=card.getBoundingClientRect();
    var pageTop=window.scrollY||window.pageYOffset||0;
    var top=Math.max(0,pageTop+rect.top-promptSnapHeaderOffset());
    window.scrollTo({top:top,behavior:scrollBehavior})
  }catch(e){
    try{card.scrollIntoView({behavior:scrollBehavior,block:'start',inline:'nearest'});window.scrollBy(0,-promptSnapHeaderOffset())}
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
      \"expected\": \"Every snap-to-prompt path places the target card's prompt header immediately below the current sticky page header with a small readable gap, even when the prompt card is taller than the viewport; it must not center the whole card and clip the prompt identity above the viewport.\"
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
            \"function promptSnapHeaderOffset()\",
            \"function snapRenderedPromptCardHeader(card,behavior)\",
            \"header.getBoundingClientRect()\",
            \"card.getBoundingClientRect()\",
            \"window.scrollTo({top:top,behavior:scrollBehavior})\",
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
        '        self.assertIn("hideCompactFilters", expected["snap_hides_filters"])\n        self.assertIn("immediately below the current sticky page header", expected["snap_prioritizes_prompt_header"])\n',
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
        polish = POLISH_JS.read_text(encoding=\"utf-8\")
        center = polish[
            polish.index(\"function promptSnapHeaderOffset\") : polish.index(\"function revealPromptShortcutTarget\")
        ]
        for marker in (
            \"hideCompactFilters();\",
            \"function promptSnapHeaderOffset()\",
            \"function snapRenderedPromptCardHeader(card,behavior)\",
            \"header.getBoundingClientRect()\",
            \"card.getBoundingClientRect()\",
            \"window.scrollTo({top:top,behavior:scrollBehavior})\",
            \"return snapRenderedPromptCardHeader(card,behavior||hotkeyScrollBehavior())\",
        ):
            self.assertIn(marker, center)
        self.assertNotIn(\"block:'center'\", center)
        reveal = polish[
            polish.index(\"function revealPromptShortcutTarget\") : polish.index(\"function activatePromptShortcutTarget\")
        ]
        self.assertIn(\"return centerRenderedPromptCard(promptId,behavior||hotkeyScrollBehavior())\", reveal)
"""
    replace_once("tests/test_prompt_kit_discovery.py", old_test, new_test)

    old_mobile = """                target_box, target_mid = card_midpoint(page, 'P111')
                assert abs(target_mid - 844 / 2) <= 150, (target_box, target_mid)
"""
    new_mobile = """                target_box = target.bounding_box() or {}
                snap_geometry = page.evaluate(\"\"\"() => {
                  const header=document.querySelector('.header');
                  const card=document.querySelector('[data-prompt-id=\\\"P111\\\"]');
                  const title=card && card.querySelector('.prompt-header');
                  const hr=header.getBoundingClientRect(),cr=card.getBoundingClientRect(),tr=title.getBoundingClientRect();
                  return {headerBottom:hr.bottom,cardTop:cr.top,titleTop:tr.top,titleBottom:tr.bottom,viewportHeight:innerHeight};
                }\"\"\")
                assert snap_geometry['cardTop'] >= snap_geometry['headerBottom'] + 6, snap_geometry
                assert snap_geometry['cardTop'] <= snap_geometry['headerBottom'] + 24, snap_geometry
                assert snap_geometry['titleTop'] >= snap_geometry['headerBottom'] + 6, snap_geometry
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
            snap_geometry = {}
            header_first = False
            if target_present:
                snap_geometry = page.evaluate(\"\"\"() => {
                  const header=document.querySelector('.header');
                  const card=document.querySelector('[data-prompt-id=\"P126\"]');
                  const title=card && card.querySelector('.prompt-header');
                  const hr=header.getBoundingClientRect(),cr=card.getBoundingClientRect(),tr=title.getBoundingClientRect();
                  return {headerBottom:hr.bottom,cardTop:cr.top,titleTop:tr.top,titleBottom:tr.bottom,viewportHeight:innerHeight};
                }\"\"\")
                visible = snap_geometry['titleBottom'] > 0 and snap_geometry['titleTop'] < snap_geometry['viewportHeight']
                header_first = bool(
                    snap_geometry['cardTop'] >= snap_geometry['headerBottom'] + 6
                    and snap_geometry['cardTop'] <= snap_geometry['headerBottom'] + 24
                    and snap_geometry['titleTop'] >= snap_geometry['headerBottom'] + 6
                    and snap_geometry['titleBottom'] <= snap_geometry['viewportHeight']
                )
"""
    replace_once("tests/prompt_kit_favorite_browser_proof.py", old_favorite_geometry, new_favorite_geometry)
    old_observation = """                {\"id\": \"prompt_card_scrolled_visible\", \"event\": \"P126 card exists and intersects viewport after shortcut with filters collapsed\", \"occurred\": True, \"passed\": bool(target_present and visible and filters_collapsed), \"present\": bool(target_present), \"visible\": bool(visible), \"filters_collapsed\": bool(filters_collapsed)},
"""
    new_observation = """                {\"id\": \"prompt_card_scrolled_visible\", \"event\": \"P126 prompt header exists and intersects viewport after shortcut with filters collapsed\", \"occurred\": True, \"passed\": bool(target_present and visible and filters_collapsed), \"present\": bool(target_present), \"visible\": bool(visible), \"filters_collapsed\": bool(filters_collapsed)},
                {\"id\": \"prompt_card_header_first_snap\", \"event\": \"P126 snap places the prompt header immediately below the sticky page header instead of centering a tall card\", \"occurred\": True, \"passed\": bool(header_first), \"geometry\": snap_geometry},
"""
    replace_once("tests/prompt_kit_favorite_browser_proof.py", old_observation, new_observation)

    replacements = {
        "- Snap-to-prompt centering always collapses compact filter chrome (`hideCompactFilters` via `centerRenderedPromptCard`) so filters cannot obscure the target card.": "- Snap-to-prompt navigation always collapses compact filter chrome (`hideCompactFilters` via `centerRenderedPromptCard`) and aligns the target prompt header immediately below the sticky page header so the prompt identity remains readable even for cards taller than the viewport.",
        "- `126` resolves `P126` immediately, copies canonical `copyContent`, and snaps its card to center.": "- `126` resolves `P126` immediately, copies canonical `copyContent`, and snaps its prompt header immediately below the sticky page header.",
        "- observed Chromium literally types bare `126` through the page keyboard path from a non-Favorite state, then verifies canonical P126 clipboard content and centered-card geometry;": "- observed Chromium literally types bare `126` through the page keyboard path from a non-Favorite state, then verifies canonical P126 clipboard content and header-first snap geometry;",
        "- **PromptNavigator**: translation from a PromptTarget to the existing reveal/center/copy behavior.": "- **PromptNavigator**: translation from a PromptTarget to the existing reveal/header-first-snap/copy behavior.",
    }
    design_path = ROOT / "docs/PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md"
    design = design_path.read_text(encoding="utf-8")
    for old, new in replacements.items():
        if design.count(old) != 1:
            raise RuntimeError(f"hotkey design replacement count for {old!r}: {design.count(old)}")
        design = design.replace(old, new, 1)
    design_path.write_text(design, encoding="utf-8")


def prove_candidate() -> None:
    run("node", "--check", "docs/prompt-kit-polish.js")
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
    run(
        "python", "-m", "unittest",
        "tests.test_prompt_kit_discovery",
        "tests.test_prompt_kit_hotkey_completion",
        "tests.test_prompt_kit_mobile_quick_controls",
        "tests.test_prompt_kit_selected_prompt",
        "tests.test_prompt_kit_cross_input_modality",
        "-v",
    )
    snap_probe(expect_header_first=True)
    run("python", "tests/prompt_kit_mobile_quick_controls_browser_proof.py")
    run(
        "python", "tests/prompt_kit_favorite_browser_proof.py",
        "--receipt", "Outputs/observed-proof/prompt-snap-header-first-favorite-receipt.json",
        "--screenshot", "Outputs/observed-proof/prompt-snap-header-first-favorite.png",
    )
    run("git", "diff", "--check")


def cleanup_and_commit() -> None:
    carrier = ROOT / ".github/carriers/prompt_snap_header_first_carrier.py"
    workflow = ROOT / ".github/workflows/prompt-snap-header-first-carrier.yml"
    if carrier.exists():
        carrier.unlink()
    if workflow.exists():
        workflow.unlink()
    run("git", "add", "-A")
    status = subprocess.run(["git", "status", "--short"], cwd=ROOT, check=True, capture_output=True, text=True).stdout
    print(status, flush=True)
    if not status.strip():
        raise RuntimeError("No durable changes to commit")
    run("git", "commit", "-m", "fix(prompt-kit): keep snapped prompt headers visible")
    run("git", "push", "origin", "HEAD:fix/prompt-snap-header-first-20260915")


def main() -> int:
    os.chdir(ROOT)
    print("BASELINE_HEADER_FIRST_EXPECTED_FAIL", flush=True)
    snap_probe(expect_header_first=False)
    patch()
    prove_candidate()
    cleanup_and_commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
