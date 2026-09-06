#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
from prepare_observed_behavior_subject import ExactHeadError, prepare_exact_head_subject


def canonical_clipboard_text(text: str) -> str:
    return str(text).replace("\r\n", "\n").replace("\r", "\n")


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
    profile_hotkeys = {}
    search_escape = {}
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

            # Exercise search mode exactly as a keyboard user does: slash, type, Escape.
            page.keyboard.press("/")
            page.wait_for_timeout(50)
            search_focused = page.evaluate("document.activeElement && document.activeElement.id === 'search'")
            page.keyboard.type("P79")
            page.wait_for_timeout(100)
            search_value_before = page.locator('#search').input_value()
            search_clear_visible_before = page.evaluate("""() => {
              const clear=document.getElementById('searchClear');
              return !!(clear && getComputedStyle(clear).display!=='none');
            }""")
            page.keyboard.press("Escape")
            page.wait_for_timeout(100)
            search_value_after = page.locator('#search').input_value()
            search_focus_released = page.evaluate("!(document.activeElement && document.activeElement.id === 'search')")
            search_clear_hidden_after = page.evaluate("""() => {
              const clear=document.getElementById('searchClear');
              return !clear || getComputedStyle(clear).display==='none';
            }""")

            # Escape must also release an already-empty focused search field.
            page.keyboard.press("/")
            page.wait_for_timeout(50)
            empty_search_refocused = page.evaluate("document.activeElement && document.activeElement.id === 'search'")
            page.keyboard.press("Escape")
            page.wait_for_timeout(50)
            empty_search_focus_released = page.evaluate("!(document.activeElement && document.activeElement.id === 'search')")

            # Prove document-level hotkeys are usable immediately after leaving search mode.
            page.keyboard.press("a")
            page.wait_for_timeout(50)
            global_hotkey_after_escape = page.evaluate(
                """() => {
                  const button=document.querySelector('.cat-tab[data-profile-slot="A"]');
                  return !!(button && button.classList.contains('active') && button.getAttribute('aria-pressed')==='true');
                }"""
            )
            search_escape = {
                "slash_focused": bool(search_focused),
                "typed_value": search_value_before,
                "clear_visible_before": bool(search_clear_visible_before),
                "cleared": search_value_after == "",
                "focus_released": bool(search_focus_released),
                "clear_hidden_after": bool(search_clear_hidden_after),
                "empty_refocused": bool(empty_search_refocused),
                "empty_focus_released": bool(empty_search_focus_released),
                "global_hotkey_restored": bool(global_hotkey_after_escape),
            }

            # Exercise the actual five-slot header hotkeys before configuring the Favorite.
            for slot_key in "ABCDE":
                page.keyboard.press(slot_key.lower())
                page.wait_for_timeout(50)
                profile_hotkeys[slot_key] = page.evaluate(
                    """slot => {
                      const button=document.querySelector('.cat-tab[data-profile-slot="'+slot+'"]');
                      return !!(button && button.classList.contains('active') && button.getAttribute('aria-pressed')==='true');
                    }""",
                    slot_key,
                )
            page.keyboard.press("a")
            page.wait_for_timeout(50)

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

            # Enter custom profile D through its real hotkey so the Favorite shortcut must restore All and reveal P79.
            page.keyboard.press("d")
            page.wait_for_timeout(100)
            d_active = page.evaluate(
                """() => {
                  const button=document.querySelector('.cat-tab[data-profile-slot="D"]');
                  return !!(button && button.classList.contains('active') && button.getAttribute('aria-pressed')==='true');
                }"""
            )
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
                {"id": "search_escape_recovery", "event": "Slash focuses search; Escape clears and releases populated or empty search and restores global hotkeys", "occurred": True, "passed": bool(all((search_escape["slash_focused"], search_escape["typed_value"] == "P79", search_escape["clear_visible_before"], search_escape["cleared"], search_escape["focus_released"], search_escape["clear_hidden_after"], search_escape["empty_refocused"], search_escape["empty_focus_released"], search_escape["global_hotkey_restored"]))), **search_escape},
                {"id": "profile_header_hotkeys_a_to_e", "event": "A-E header hotkeys activate their matching profile slots", "occurred": True, "passed": bool(set(profile_hotkeys) == set("ABCDE") and all(profile_hotkeys.values())), "slots": profile_hotkeys},
                {"id": "hotkey_click_focuses_favorite_input", "event": "Hotkeys button opens the panel with Favorite prompt ID input focused and revealed", "occurred": True, "passed": bool(click_focus and click_visible), "focused": bool(click_focus), "visible": bool(click_visible)},
                {"id": "escape_closes_hotkeys_from_favorite_input", "event": "Escape closes Hotkeys while Favorite prompt ID input owns focus and returns focus to Hotkeys toggle", "occurred": True, "passed": bool(escape_closed and escape_focus_returned), "closed": bool(escape_closed), "toggle_focused": bool(escape_focus_returned)},
                {"id": "hotkey_backtick_focuses_favorite_input", "event": "Backtick opens Hotkeys with Favorite prompt ID input focused and revealed", "occurred": True, "passed": bool(backtick_focus and backtick_visible), "focused": bool(backtick_focus), "visible": bool(backtick_visible)},
                {"id": "favorite_setup_saved", "event": "P79 favorited and p79 shortcut saved through product UI", "occurred": True, "passed": bool(setup_saved)},
                {"id": "alternate_scope_precondition", "event": "D custom profile hotkey activates and excludes P79 before shortcut", "occurred": True, "passed": bool(d_active and not before_present), "profile_d_active": bool(d_active), "present_before": bool(before_present)},
                {"id": "favorite_shortcut_dispatched", "event": "typed favorite shortcut p79", "occurred": True, "passed": bool(shortcut_copied), "toast": toast_text},
                {"id": "prompt_card_scrolled_visible", "event": "P79 card exists and intersects viewport after shortcut", "occurred": True, "passed": bool(target_present and visible), "present": bool(target_present), "visible": bool(visible)},
                {"id": "clipboard_exact_match", "event": "clipboard equals canonical P79 copyContent", "occurred": bool(clipboard_read), "passed": bool(clipboard_read and canonical_clipboard_text(actual) == canonical_clipboard_text(expected)), "actual_length": len(actual), "expected_length": len(expected)},
                {"id": "detail_modal_closed", "event": "favorite shortcut does not open detail modal or focus its close control", "occurred": True, "passed": bool(modal_closed and not close_focused), "modal_closed": bool(modal_closed), "close_focused": bool(close_focused)},
                {"id": "enter_does_not_close_prompt", "event": "Enter after shortcut leaves detail modal closed and clipboard intact", "occurred": True, "passed": bool(enter_modal_closed and canonical_clipboard_text(after_enter) == canonical_clipboard_text(expected))},
            ]
            mobile_context = browser.new_context(
                viewport={"width": 390, "height": 844},
                is_mobile=True,
                has_touch=True,
                reduced_motion="reduce",
            )
            mobile_page = mobile_context.new_page()
            mobile_page.goto(f"http://127.0.0.1:{port}/web/prompt-kit/index.html", wait_until="domcontentloaded")
            favorites_key = "promptKit.favoritePromptIds.v1"

            def control_tappable(locator) -> bool:
                if locator is None or not locator.is_visible():
                    return False
                box = locator.bounding_box() or {}
                width = float(box.get("width") or 0)
                height = float(box.get("height") or 0)
                x = float(box.get("x") or -1)
                y = float(box.get("y") or -1)
                return bool(
                    width >= 40
                    and height >= 40
                    and x >= 0
                    and y >= 0
                    and x + width <= 390
                    and y + height <= 844
                )

            quick = mobile_page.locator("#mobileFavoritesQuick")
            quick_visible = quick.is_visible()
            quick_rect = quick.bounding_box() or {}
            quick_in_viewport = bool(
                quick_rect
                and quick_rect.get("x", -1) >= 0
                and quick_rect.get("y", -1) >= 0
                and quick_rect.get("x", 0) + quick_rect.get("width", 0) <= 390
                and quick_rect.get("y", 0) + quick_rect.get("height", 0) <= 844
            )
            mobile_page.locator("#filterPanelToggle").click()
            mobile_page.wait_for_timeout(80)
            quick_visible_when_filters_collapsed = quick.is_visible()

            group_pair = mobile_page.evaluate(
                """() => {
                  const firstBySection={};
                  for(const prompt of PROMPTS){
                    const section=sectionForPrompt(prompt);
                    const name=section?section.name:'Other';
                    if(!firstBySection[name])firstBySection[name]=prompt.id;
                  }
                  return Object.keys(firstBySection).slice(0,2).map(name => ({name,id:firstBySection[name]}));
                }"""
            )
            structured_pair_available = len(group_pair) == 2

            # save → canonical key
            saved_in_canonical_key = False
            if structured_pair_available:
                for item in group_pair:
                    mobile_page.locator(f'[data-prompt-id="{item["id"]}"] .prompt-favorite-btn').click()
                    mobile_page.wait_for_timeout(60)
                stored_after_save = mobile_page.evaluate(
                    f"JSON.parse(localStorage.getItem('{favorites_key}')||'[]')"
                )
                saved_in_canonical_key = all(item["id"] in stored_after_save for item in group_pair)

            # reload → persisted Favorites appear → structured groups
            persisted_after_reload = False
            favorites_appear_after_reload = False
            group_nav_visible = False
            group_link_count = 0
            group_labels = []
            counts_present = False
            target_visible = False
            target_focused = False
            favorites_state_preserved = False
            if structured_pair_available and saved_in_canonical_key:
                mobile_page.reload(wait_until="domcontentloaded")
                mobile_page.wait_for_timeout(120)
                quick = mobile_page.locator("#mobileFavoritesQuick")
                quick.click()
                mobile_page.wait_for_timeout(120)
                persisted_after_reload = all(
                    mobile_page.locator(f'[data-prompt-id="{item["id"]}"]').count() == 1
                    for item in group_pair
                )
                favorites_appear_after_reload = persisted_after_reload and mobile_page.evaluate(
                    "activeSection === '__favorites__'"
                )
                group_nav = mobile_page.locator("#favoritesGroupJumpNav")
                group_nav_visible = group_nav.is_visible()
                group_links = group_nav.locator(".favorite-group-jump")
                group_link_count = group_links.count()
                group_labels = [
                    group_links.nth(i).get_attribute("data-favorite-group")
                    for i in range(group_link_count)
                ]
                counts_present = all(
                    "prompt" in group_links.nth(i).inner_text().lower()
                    for i in range(group_link_count)
                )
                if group_link_count >= 2:
                    second_link = group_links.nth(1)
                    target_id = (second_link.get_attribute("href") or "").lstrip("#")
                    second_link.click()
                    mobile_page.wait_for_timeout(120)
                    target_visible = mobile_page.evaluate(
                        """targetId => {
                          const target=document.getElementById(targetId);
                          if(!target)return false;
                          const r=target.getBoundingClientRect();
                          return r.bottom>0 && r.top<innerHeight;
                        }""",
                        target_id,
                    )
                    target_focused = mobile_page.evaluate(
                        """targetId => {
                          const target=document.getElementById(targetId);
                          return !!(target && target.contains(document.activeElement));
                        }""",
                        target_id,
                    )
                    favorites_state_preserved = mobile_page.evaluate(
                        "activeSection === '__favorites__'"
                    )

            # remove all → zero-saved recovery → Browse all prompts
            empty_state_visible = False
            empty_state_kind = None
            empty_title = ""
            browse_all_tappable = False
            browse_all_returned = False
            browse_all_useful_content = False
            if structured_pair_available and favorites_appear_after_reload:
                for item in group_pair:
                    card = mobile_page.locator(f'[data-prompt-id="{item["id"]}"]')
                    if card.count():
                        card.locator(".prompt-favorite-btn").click()
                        mobile_page.wait_for_timeout(80)
                empty = mobile_page.locator("#favoritesEmptyState")
                empty_state_visible = empty.is_visible()
                empty_state_kind = empty.get_attribute("data-empty-kind")
                empty_title = empty.locator(".favorites-empty-title").inner_text() if empty_state_visible else ""
                browse_all = empty.get_by_role("button", name="Browse all prompts") if empty_state_visible else None
                browse_all_tappable = control_tappable(browse_all)
                if browse_all is not None and browse_all_tappable:
                    browse_all.click()
                    mobile_page.wait_for_timeout(100)
                    browse_all_returned = mobile_page.evaluate(
                        "activeSection === null && activeCat === 'all'"
                    )
                    browse_all_useful_content = browse_all_returned and (
                        mobile_page.locator('[data-prompt-id="P79"]').count() == 1
                    )

            # save again → filter away → Clear filters (membership unchanged)
            filtered_empty_visible = False
            filtered_empty_kind = None
            filtered_title = ""
            clear_filters_tappable = False
            clear_filters_restored = False
            membership_unchanged_after_clear = False
            if browse_all_useful_content:
                mobile_page.locator('[data-prompt-id="P79"] .prompt-favorite-btn').click()
                mobile_page.wait_for_timeout(80)
                membership_before_filter = mobile_page.evaluate(
                    f"JSON.parse(localStorage.getItem('{favorites_key}')||'[]')"
                )
                quick = mobile_page.locator("#mobileFavoritesQuick")
                quick.click()
                mobile_page.wait_for_timeout(100)
                mobile_page.locator("#search").fill("definitely-no-favorite-match-xyz")
                mobile_page.wait_for_timeout(100)
                filtered_empty = mobile_page.locator("#favoritesEmptyState")
                filtered_empty_visible = filtered_empty.is_visible()
                filtered_empty_kind = filtered_empty.get_attribute("data-empty-kind")
                filtered_title = (
                    filtered_empty.locator(".favorites-empty-title").inner_text()
                    if filtered_empty_visible
                    else ""
                )
                clear_filters = (
                    filtered_empty.get_by_role("button", name="Clear Favorites filters")
                    if filtered_empty_visible
                    else None
                )
                clear_filters_tappable = control_tappable(clear_filters)
                if clear_filters is not None and clear_filters_tappable:
                    clear_filters.click()
                    mobile_page.wait_for_timeout(100)
                    membership_after_clear = mobile_page.evaluate(
                        f"JSON.parse(localStorage.getItem('{favorites_key}')||'[]')"
                    )
                    membership_unchanged_after_clear = (
                        sorted(membership_before_filter) == sorted(membership_after_clear)
                        and "P79" in membership_after_clear
                    )
                    clear_filters_restored = (
                        mobile_page.locator('[data-prompt-id="P79"]').count() == 1
                        and mobile_page.locator("#search").input_value() == ""
                        and mobile_page.evaluate("activeSection === '__favorites__'")
                        and membership_unchanged_after_clear
                    )

            # mixed known/unknown → mutate known → unknown preserved → unavailable → Browse current
            known_favorite_rendered = False
            unknown_id_preserved_before_mutation = False
            unknown_id_preserved_after_mutation = False
            known_id_removed = False
            unavailable_visible = False
            unavailable_kind = None
            unavailable_title = ""
            browse_current_tappable = False
            browse_current_prompts_returned = False
            current_prompt_visible = False
            if clear_filters_restored:
                mobile_page.evaluate(
                    f"localStorage.setItem('{favorites_key}', JSON.stringify(['P79','P999999']))"
                )
                mobile_page.reload(wait_until="domcontentloaded")
                mobile_page.wait_for_timeout(120)
                mobile_page.locator("#mobileFavoritesQuick").click()
                mobile_page.wait_for_timeout(100)
                known_favorite_rendered = mobile_page.locator('[data-prompt-id="P79"]').count() == 1
                unknown_id_preserved_before_mutation = mobile_page.evaluate(
                    f"JSON.parse(localStorage.getItem('{favorites_key}')||'[]').includes('P999999')"
                )
                if known_favorite_rendered:
                    mobile_page.locator('[data-prompt-id="P79"] .prompt-favorite-btn').click()
                    mobile_page.wait_for_timeout(100)
                stored_after_mutation = mobile_page.evaluate(
                    f"JSON.parse(localStorage.getItem('{favorites_key}')||'[]')"
                )
                unknown_id_preserved_after_mutation = "P999999" in stored_after_mutation
                known_id_removed = "P79" not in stored_after_mutation
                unavailable_empty = mobile_page.locator("#favoritesEmptyState")
                unavailable_visible = unavailable_empty.is_visible()
                unavailable_kind = unavailable_empty.get_attribute("data-empty-kind")
                unavailable_title = (
                    unavailable_empty.locator(".favorites-empty-title").inner_text()
                    if unavailable_visible
                    else ""
                )
                browse_current = (
                    unavailable_empty.get_by_role("button", name="Browse current prompts")
                    if unavailable_visible
                    else None
                )
                browse_current_tappable = control_tappable(browse_current)
                if browse_current is not None and browse_current_tappable:
                    browse_current.click()
                    mobile_page.wait_for_timeout(100)
                    browse_current_prompts_returned = mobile_page.evaluate(
                        "activeSection === null && activeCat === 'all'"
                    )
                    current_prompt_visible = mobile_page.locator('[data-prompt-id="P79"]').count() == 1

            recovery_controls_tappable = bool(
                browse_all_tappable and clear_filters_tappable and browse_current_tappable
            )
            observations.append({
                "id": "mobile_favorites_definitive_journey",
                "event": (
                    "One 390x844 Favorites journey: save, reload, persist, structured groups, "
                    "zero-saved recovery, filter recovery, unknown-ID preservation, and Browse current prompts"
                ),
                "occurred": True,
                "passed": bool(all((
                    quick_visible,
                    quick_in_viewport,
                    quick_visible_when_filters_collapsed,
                    structured_pair_available,
                    saved_in_canonical_key,
                    persisted_after_reload,
                    favorites_appear_after_reload,
                    group_nav_visible,
                    group_link_count >= 2,
                    set(group_labels) == {item["name"] for item in group_pair},
                    counts_present,
                    target_visible,
                    target_focused,
                    favorites_state_preserved,
                    empty_state_visible,
                    empty_state_kind == "none-saved",
                    empty_title == "No Favorites yet",
                    browse_all_tappable,
                    browse_all_returned,
                    browse_all_useful_content,
                    filtered_empty_visible,
                    filtered_empty_kind == "filtered",
                    filtered_title == "No Favorites match these filters",
                    clear_filters_tappable,
                    clear_filters_restored,
                    membership_unchanged_after_clear,
                    known_favorite_rendered,
                    unknown_id_preserved_before_mutation,
                    unknown_id_preserved_after_mutation,
                    known_id_removed,
                    unavailable_visible,
                    unavailable_kind == "unavailable",
                    unavailable_title == "Saved Favorites unavailable in this version",
                    browse_current_tappable,
                    browse_current_prompts_returned,
                    current_prompt_visible,
                    recovery_controls_tappable,
                ))),
                "favorites_storage_key": favorites_key,
                "saved_in_canonical_key": bool(saved_in_canonical_key),
                "persisted_after_reload": bool(persisted_after_reload),
                "favorites_appear_after_reload": bool(favorites_appear_after_reload),
                "pair": group_pair,
                "group_nav_visible": bool(group_nav_visible),
                "group_link_count": group_link_count,
                "group_labels": group_labels,
                "counts_present": bool(counts_present),
                "target_visible": bool(target_visible),
                "target_focused": bool(target_focused),
                "favorites_state_preserved": bool(favorites_state_preserved),
                "empty_state_visible": bool(empty_state_visible),
                "empty_state_kind": empty_state_kind,
                "empty_title": empty_title,
                "browse_all_tappable": bool(browse_all_tappable),
                "browse_all_returned": bool(browse_all_returned),
                "browse_all_useful_content": bool(browse_all_useful_content),
                "filtered_empty_visible": bool(filtered_empty_visible),
                "filtered_empty_kind": filtered_empty_kind,
                "filtered_title": filtered_title,
                "clear_filters_tappable": bool(clear_filters_tappable),
                "clear_filters_restored": bool(clear_filters_restored),
                "membership_unchanged_after_clear": bool(membership_unchanged_after_clear),
                "known_favorite_rendered": bool(known_favorite_rendered),
                "unknown_id_preserved_before_mutation": bool(unknown_id_preserved_before_mutation),
                "unknown_id_preserved_after_mutation": bool(unknown_id_preserved_after_mutation),
                "known_id_removed": bool(known_id_removed),
                "unavailable_visible": bool(unavailable_visible),
                "unavailable_kind": unavailable_kind,
                "unavailable_title": unavailable_title,
                "browse_current_tappable": bool(browse_current_tappable),
                "browse_current_prompts_returned": bool(browse_current_prompts_returned),
                "current_prompt_visible": bool(current_prompt_visible),
                "recovery_controls_tappable": bool(recovery_controls_tappable),
                "quick_visible": bool(quick_visible),
                "quick_in_viewport": bool(quick_in_viewport),
                "quick_visible_when_filters_collapsed": bool(quick_visible_when_filters_collapsed),
                "viewport": {"width": 390, "height": 844},
            })
            mobile_context.close()

            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    return observations


def execution_environment_kind(env=None) -> str:
    runtime_env = os.environ if env is None else env
    return "github_actions_headless_browser" if str(runtime_env.get("GITHUB_ACTIONS", "")).lower() == "true" else "local_headless_browser"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--receipt', required=True)
    parser.add_argument('--screenshot', required=True)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args(argv)
    receipt_path = Path(args.receipt)
    screenshot = Path(args.screenshot)
    try:
        subject = prepare_exact_head_subject()
    except ExactHeadError as exc:
        print(f"exact-head preflight failed; Chromium was not launched\n{exc}", file=sys.stderr)
        return 2
    observations = observe(args.port, screenshot)
    by_id = {item['id']: item for item in observations}
    search_escape_recovery = by_id['search_escape_recovery']['passed']
    profile_header_navigation = by_id['profile_header_hotkeys_a_to_e']['passed']
    hotkey_config_recovery = all(by_id[item]['passed'] for item in ('hotkey_click_focuses_favorite_input', 'escape_closes_hotkeys_from_favorite_input', 'hotkey_backtick_focuses_favorite_input'))
    auto_copy = all(by_id[item]['passed'] for item in ('favorite_setup_saved', 'favorite_shortcut_dispatched', 'clipboard_exact_match'))
    reveal = all(by_id[item]['passed'] for item in ('alternate_scope_precondition', 'favorite_shortcut_dispatched', 'prompt_card_scrolled_visible'))
    focus_safe = all(by_id[item]['passed'] for item in ('detail_modal_closed', 'enter_does_not_close_prompt'))
    verdict = 'PASS' if all(item['passed'] for item in observations) else 'FAIL'
    receipt = {
        "schema_version": "observed-behavior-proof/v1",
        "verdict": verdict,
        "evidence_class": "browser_runtime_observed",
        "subject": subject,
        "environment": {"kind": execution_environment_kind(), "engine": "chromium", "scenario": "search-escape-profile-tabs-a-e-favorite-shortcut-and-mobile-favorites-definitive-journey"},
        "claims": [
            {"id": "mobile_favorites_definitive_journey", "statement": "One 390x844 Favorites journey proves canonical save/reload persistence, structured group jumps, zero-saved and filter recovery, unknown-ID preservation through known-Favorite mutation, Browse current prompts, and tappable recovery controls", "status": "PASS" if by_id["mobile_favorites_definitive_journey"]["passed"] else "FAIL", "required_evidence_class": "browser_runtime_observed", "observation_ids": ["mobile_favorites_definitive_journey"]},
            {"id": "search_escape_recovery", "statement": "Slash focuses search; one Escape clears a populated query, hides the clear affordance, releases focus, also releases an empty focused search, and restores global hotkeys", "status": "PASS" if search_escape_recovery else "FAIL", "required_evidence_class": "browser_runtime_observed", "observation_ids": ["search_escape_recovery"]},
            {"id": "profile_header_navigation", "statement": "A-E header hotkeys activate their matching profile slots in the browser", "status": "PASS" if profile_header_navigation else "FAIL", "required_evidence_class": "browser_runtime_observed", "observation_ids": ["profile_header_hotkeys_a_to_e"]},
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
