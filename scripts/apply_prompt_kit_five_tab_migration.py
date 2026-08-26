#!/usr/bin/env python3
"""Temporary bounded migration driver for the five-tab Prompt Kit sprint.

This file is removed by the validating workflow before the final product commit.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"{relative}: expected one marker, found {count}: {old[:120]!r}"
        )
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_region(relative: str, start_marker: str, end_marker: str, replacement: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")


def replace_test_function(relative: str, function_name: str, next_function: str, replacement: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    start = text.index(f"    def {function_name}")
    end = text.index(f"\n    def {next_function}", start)
    path.write_text(text[:start] + replacement.rstrip() + "\n" + text[end:], encoding="utf-8")


def migrate_builder() -> None:
    buttons = [
        "    html.append('        <button class=\"cat-tab active profile-slot\" data-profile-slot=\"A\" data-cat=\"all\" aria-keyshortcuts=\"A\" aria-pressed=\"true\">All<span class=\"kbd\">A</span></button>')",
        "    html.append('        <button class=\"cat-tab profile-slot\" data-profile-slot=\"B\" data-cat=\"standard\" aria-keyshortcuts=\"B\" aria-pressed=\"false\">Standard<span class=\"kbd\">B</span></button>')",
        "    html.append('        <button class=\"cat-tab profile-slot\" id=\"favoritesShortcut\" data-profile-slot=\"C\" data-view=\"favorites\" aria-keyshortcuts=\"C\" aria-pressed=\"false\">Favorites<span class=\"kbd\">C</span></button>')",
        "    html.append('        <button class=\"cat-tab profile-slot\" data-profile-slot=\"D\" aria-keyshortcuts=\"D\" aria-pressed=\"false\">SAS<span class=\"kbd\">D</span></button>')",
        "    html.append('        <button class=\"cat-tab profile-slot\" data-profile-slot=\"E\" aria-keyshortcuts=\"E\" aria-pressed=\"false\">PM<span class=\"kbd\">E</span></button>')",
    ]
    replace_region(
        "build_prompt_kit.py",
        "    html.append('        <button class=\"cat-tab active\" data-cat=\"all\"",
        "    html.append('      </div>')",
        "\n".join(buttons) + "\n",
    )


def migrate_base_runtime() -> None:
    replace_once(
        "docs/prompt-kit.js",
        "switch(e.key){case'1':activeCat='all';break;case'2':activeCat='standard';break;case'3':activeCat='gnhf';break;case'4':activeCat='doctrine';break;case'r':case'R':toggleRef();return;",
        "switch(e.key){case'r':case'R':toggleRef();return;",
    )


def migrate_profile_runtime() -> None:
    replace_once(
        "docs/prompt-kit-profiles.js",
        "      if(slot.key==='C')button.id='favoritesShortcut';",
        "      if(slot.key==='C'){button.id='favoritesShortcut';button.dataset.view='favorites'}",
    )
    old = """  function setBuiltinView(slot){
    if(typeof root.activeType!=='undefined')root.activeType=null;
    if(typeof root.activeColor!=='undefined')root.activeColor=null;
    if(typeof root.collapsedSections!=='undefined')root.collapsedSections={};
    if(slot.mode==='all'){
      root.activeCat='all';
      root.activeSection=null
    }else if(slot.mode==='standard'){
      root.activeCat='standard';
      root.activeSection=null
    }else if(slot.mode==='favorites'){
      root.activeCat='all';
      root.activeSection='__favorites__'
    }else{
      root.activeCat='all';
      root.activeSection=null
    }
  }
"""
    new = """  function clearTransientBrowserFilters(){
    if(typeof root.activeType!=='undefined')root.activeType=null;
    if(typeof root.activeColor!=='undefined')root.activeColor=null;
    if(typeof root.collapsedSections!=='undefined')root.collapsedSections={};
    var search=doc.getElementById('search');
    if(search)search.value='';
    var clear=doc.getElementById('searchClear');
    if(clear)clear.style.display='none'
  }
  function setBuiltinView(slot){
    clearTransientBrowserFilters();
    if(slot.mode==='all'){
      root.activeCat='all';
      root.activeSection=null
    }else if(slot.mode==='standard'){
      root.activeCat='standard';
      root.activeSection=null
    }else if(slot.mode==='favorites'){
      root.activeCat='all';
      root.activeSection='__favorites__'
    }else{
      root.activeCat='all';
      root.activeSection=null
    }
  }
"""
    replace_once("docs/prompt-kit-profiles.js", old, new)


def migrate_generator() -> None:
    replace_once(
        "scripts/build_prompt_kit_registry.py",
        'PROMPT_JOURNEY_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-journey.js"\nPOLISH_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-polish.js"',
        'PROMPT_JOURNEY_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-journey.js"\nPROFILE_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-profiles.js"\nPOLISH_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-polish.js"',
    )
    replace_once(
        "scripts/build_prompt_kit_registry.py",
        '    journey_script = _read_runtime(PROMPT_JOURNEY_RUNTIME, "Guided next-step journey behavior")\n    polish_script = _read_runtime(POLISH_RUNTIME, "Prompt Kit polish behavior")',
        '    journey_script = _read_runtime(PROMPT_JOURNEY_RUNTIME, "Guided next-step journey behavior")\n    profile_script = _read_runtime(PROFILE_RUNTIME, "Prompt Kit named profile behavior")\n    polish_script = _read_runtime(POLISH_RUNTIME, "Prompt Kit polish behavior")',
    )
    replace_once(
        "scripts/build_prompt_kit_registry.py",
        '        f"<script>\\n{journey_script}\\n</script>\\n"\n        f"<script>\\n{polish_script}\\n</script>\\n"',
        '        f"<script>\\n{journey_script}\\n</script>\\n"\n        f"<script>\\n{profile_script}\\n</script>\\n"\n        f"<script>\\n{polish_script}\\n</script>\\n"',
    )


def migrate_polish_runtime() -> None:
    path = ROOT / "docs/prompt-kit-polish.js"
    text = path.read_text(encoding="utf-8")

    fallback_start = text.index("  var doctrineButton=catTabs.querySelector")
    fallback_end = text.index("  if(!document.getElementById('filterPanelToggle')){", fallback_start)
    fallback = """  if(!document.getElementById('favoritesShortcut')){
    var favoritesButton=document.createElement('button');
    favoritesButton.className='cat-tab profile-slot';
    favoritesButton.id='favoritesShortcut';
    favoritesButton.type='button';
    favoritesButton.dataset.profileSlot='C';
    favoritesButton.setAttribute('data-view','favorites');
    favoritesButton.setAttribute('aria-label','Show saved favorite prompts');
    favoritesButton.setAttribute('aria-keyshortcuts','C');
    favoritesButton.innerHTML='<span class=\"tab-icon\">★</span>Favorites<span class=\"kbd\">C</span>';
    favoritesButton.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();activateFavoritesView()});
    catTabs.appendChild(favoritesButton)
  }

"""
    text = text[:fallback_start] + fallback + text[fallback_end:]

    shortcut_start = text.index("var PROMPT_KIT_SHORTCUTS=[")
    shortcut_end = text.index("];", shortcut_start) + 2
    shortcut_block = """var PROMPT_KIT_SHORTCUTS=[
  {key:'`',label:'Show / hide Hotkeys'},
  {key:'A',label:'All'},
  {key:'B',label:'Standard'},
  {key:'C',label:'Favorites'},
  {key:'D',label:'SAS'},
  {key:'E',label:'PM'},
  {key:'/',label:'Focus search'},
  {key:'R',label:'Reference panel'},
  {key:'F',label:'Show / hide filters'},
  {key:'[',label:'Hide filters'},
  {key:']',label:'Show filters'},
  {key:'T',label:'Scroll to top'},
  {key:'End',label:'Scroll to bottom'},
  {key:'Esc',label:'Close / clear active surface'}
];"""
    text = text[:shortcut_start] + shortcut_block + text[shortcut_end:]

    hotkey_fn = text.index("function installCompactBrowsingHotkeys()")
    numeric_start = text.index("    if(key==='1'){", hotkey_fn)
    next_non_numeric = text.index("    if(key==='f'){", numeric_start)
    text = text[:numeric_start] + text[next_non_numeric:]

    old_bottom = (
        "    if(key==='b'){e.preventDefault();e.stopImmediatePropagation();"
        "scrollPromptKitTo('bottom');return}"
    )
    if text.count(old_bottom) != 1:
        raise SystemExit("docs/prompt-kit-polish.js: bottom hotkey marker missing")
    text = text.replace(
        old_bottom,
        "    if(key==='end'){e.preventDefault();e.stopImmediatePropagation();"
        "scrollPromptKitTo('bottom');return}",
        1,
    )
    path.write_text(text, encoding="utf-8")


def migrate_hotkey_test() -> None:
    replacement = '''    def test_prompt_sequence_owns_digits_and_header_navigation_is_letter_only(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        base = (ROOT / "docs" / "prompt-kit.js").read_text(encoding="utf-8")
        buffered = "if(promptShortcutBuffer&&handleConfiguredPromptShortcutKey(e,key))return;"
        self.assertIn(buffered, source)
        for digit in "12345":
            self.assertNotIn(f"if(key==='{digit}')", source)
            self.assertNotIn(f"case'{digit}'", base)
        self.assertIn("{key:'A',label:'All'}", source)
        self.assertIn("{key:'E',label:'PM'}", source)
        self.assertIn("{key:'End',label:'Scroll to bottom'}", source)
        self.assertIn("var escapeHelpPanel=document.getElementById('hotkeyHelpPanel');", source)
        self.assertIn("if(key==='escape'&&escapeHelpPanel&&!escapeHelpPanel.hidden)", source)
'''
    replace_test_function(
        "tests/test_prompt_kit_hotkey_completion.py",
        "test_buffered_prompt_sequence_precedes_builtin_digit_dispatch(self) -> None:",
        "test_executable_prototype_proves_success_failure_and_digit_collision_paths",
        replacement,
    )


def migrate_filtering_test() -> None:
    replace_once(
        "tests/test_prompt_kit_filtering_access.py",
        'POLISH = ROOT / "docs" / "prompt-kit-polish.js"\n',
        'POLISH = ROOT / "docs" / "prompt-kit-polish.js"\nPROFILES = ROOT / "docs" / "prompt-kit-profiles.js"\n',
    )
    replacement = '''    def test_all_view_is_an_atomic_reset_after_favorites(self) -> None:
        js = JS.read_text(encoding="utf-8")
        polish = POLISH.read_text(encoding="utf-8")
        profiles = PROFILES.read_text(encoding="utf-8")

        start = js.index("function resetPromptKitView()")
        end = js.index("\n\nfunction showAddPrompt", start)
        reset = js[start:end]
        for marker in (
            "activeCat='all'",
            "activeSection=null",
            "activeType=null",
            "activeColor=null",
            "collapsedSections={}",
            "search.value=''",
            "syncLibraryTabs()",
            "renderSections()",
            "renderTypes()",
            "render()",
        ):
            self.assertIn(marker, reset)

        favorites = polish[polish.index("function activateFavoritesView()") : polish.index("function ensureCompactBrowsingControls()")]
        self.assertIn("activeSection='__favorites__'", favorites)
        all_view = polish[polish.index("function activateAllPromptsView()") : polish.index("function activateFavoritesView()")]
        self.assertIn("resetPromptKitView();", all_view)

        self.assertIn("function clearTransientBrowserFilters()", profiles)
        self.assertIn("search.value=''", profiles)
        self.assertIn("if(slot.mode==='all')", profiles)
        self.assertIn("root.activeCat='all'", profiles)
        self.assertIn("if(slot.mode==='favorites')", profiles)
        self.assertIn("root.activeSection='__favorites__'", profiles)
        self.assertIn("SLOT_KEYS.indexOf(key)===-1", profiles)
        self.assertIn("activateSlot(key)", profiles)

        hotkeys = polish[polish.index("function installCompactBrowsingHotkeys()") : polish.index("window.appendPromptCard")]
        for digit in "12345":
            self.assertNotIn(f"if(key==='{digit}')", hotkeys)
        self.assertIn("installCompactBrowsingViewSwitches();", polish)
        self.assertIn("installCompactBrowsingHotkeys();", polish)
'''
    replace_test_function(
        "tests/test_prompt_kit_filtering_access.py",
        "test_all_view_is_an_atomic_reset_after_favorites(self) -> None:",
        "test_render_uses_unique_category_metadata_without_reordering_cards",
        replacement,
    )


def migrate_order_navigation_test() -> None:
    replacement = '''    def test_compact_browsing_uses_favorites_hotkey_and_collapsible_filter_chrome(self) -> None:
        polish = (ROOT / "docs" / "prompt-kit-polish.js").read_text(encoding="utf-8")
        profiles = (ROOT / "docs" / "prompt-kit-profiles.js").read_text(encoding="utf-8")
        for marker in (
            "function activateFavoritesView()",
            "activeSection='__favorites__'",
            "id='favoritesShortcut'",
            "data-view','favorites'",
            "Favorites<span class=\"kbd\">C</span>",
            "aria-keyshortcuts','C'",
            "var key=String(e.key||'').toLowerCase();",
            "e.stopImmediatePropagation()",
            "filterPanelToggle",
            "filters-collapsed",
            "Hide filters ↑",
            "Show filters ↓",
        ):
            self.assertIn(marker, polish)
        self.assertNotIn("doctrineKbd.textContent='5'", polish)
        self.assertNotIn("Favorites<span class=\"kbd\">4</span>", polish)
        for digit in "12345":
            self.assertNotIn(f"if(key==='{digit}')", polish)
        for marker in (
            "SLOT_KEYS=['A','B','C','D','E']",
            "button.dataset.profileSlot=slot.key",
            "button.dataset.view='favorites'",
            "activateSlot(key)",
        ):
            self.assertIn(marker, profiles)
        self.assertIn(
            ".header.filters-collapsed .search-container,.header.filters-collapsed .header-controls,.header.filters-collapsed .sections-nav,.header.filters-collapsed .type-nav{display:none!important}",
            polish,
        )
'''
    replace_test_function(
        "tests/test_prompt_kit_order_navigation_product.py",
        "test_compact_browsing_uses_favorites_hotkey_and_collapsible_filter_chrome(self) -> None:",
        "test_visible_version_is_consistently_v40",
        replacement,
    )


def migrate_readme() -> None:
    path = ROOT / "web/README.md"
    text = path.read_text(encoding="utf-8")
    old = "1. **Library view:** All / Standard / GNHF / Doctrine."
    if old not in text:
        raise SystemExit("web/README.md: library view marker missing")
    text = text.replace(
        old,
        "1. **Profile tab:** five configurable slots A–E, defaulting to All / Standard / Favorites / SAS / PM.",
        1,
    )

    old = (
        "- Use the explicit **Favorites** header view or press **4** to clear the transient "
        "search/category/type restrictions and show the complete saved Favorites collection."
    )
    if old not in text:
        raise SystemExit("web/README.md: Favorites hotkey marker missing")
    text = text.replace(
        old,
        "- Use the explicit **Favorites** profile tab or press **C** to show the complete saved Favorites collection.",
        1,
    )

    hotkey_start = text.index(
        "The glowing **Hotkeys** module beside the floating reference control"
    )
    configured_start = text.index(
        "Favorite-prompt shortcuts are configured from the Hotkeys panel.", hotkey_start
    )
    new_hotkeys = '''The glowing **Hotkeys** module beside the floating reference control is the in-product shortcut reference, five-tab profile editor, profile-pack importer, and favorite-prompt shortcut configurator. Select it or press the unmodified **backtick** key (`` ` ``) to toggle it; select outside it, use its close control, or press **Esc** to dismiss it. The five header identities are always `A`–`E`; their visible names and profile compositions are user configuration. Numeric keys are not header navigation, and no header key uses `P`, so configured prompt sequences such as `P111` retain the digit stream.

| Key | Action |
|---|---|
| `` ` `` | Show / hide Hotkeys |
| `/` | Focus search |
| `A` | All |
| `B` | Standard |
| `C` | Favorites |
| `D` | SAS |
| `E` | PM |
| `R` | Toggle reference panel |
| `F` | Show / hide filters |
| `[` | Hide filters |
| `]` | Show filters |
| `T` | Scroll to top |
| `End` | Scroll to bottom |
| `Esc` | Close the active surface or clear filters |

'''
    text = text[:hotkey_start] + new_hotkeys + text[configured_start:]

    old_tail = (
        "A configured shortcut is rejected when its target is unknown or not currently a Favorite. "
        "Shortcut storage uses the versioned key `promptKit.promptShortcuts.v1` and publishes an "
        "in-memory binding only after the browser storage write succeeds. Once a configured prompt "
        "sequence buffer is active, it receives the next digit before built-in `1`, `4`, or `5` "
        "navigation so valid prompt IDs cannot be interrupted; built-in digit shortcuts keep their "
        "normal meaning when no sequence is active."
    )
    new_tail = (
        "A configured shortcut is rejected when its target is unknown or not currently a Favorite. "
        "Shortcut storage uses the versioned key `promptKit.promptShortcuts.v1` and publishes an "
        "in-memory binding only after the browser storage write succeeds. Once a configured prompt "
        "sequence buffer is active, it owns the following digits. Numeric keys have no header-navigation "
        "meaning, so `P111` and other configured prompt IDs cannot fall through into a tab command."
    )
    if old_tail not in text:
        raise SystemExit("web/README.md: prompt sequence paragraph missing")
    text = text.replace(old_tail, new_tail, 1)

    marker = "### Category and type filtering\n"
    addition = '''### Five-tab named profiles

The top rail exposes five persistent keyboard slots, `A` through `E`. Every slot can be renamed and assigned a built-in view or a custom union of profile packs from the Hotkeys panel. Defaults are **All / Standard / Favorites / SAS / PM**; SAS selects the SAS pack, while PM composes PM + FUN + TRIAGE + H&H. Built-in packs also include CYBERSEC, AGENTIC LOOPING, Gardening, and Future Projects.

Imported profile packs use `prompt-kit-profile-import/v1` JSON and pass a bounded parse → validate → compile evaluator. Imports are data only: JavaScript `eval`, `Function`, and `new Function` are not used. The runtime caps import size, pack count, installed pack count, rule nodes/depth, matcher length, and packs selected per tab, and rejects malformed or unknown operators before persistence. See `docs/PROMPT_KIT_FIVE_TAB_PROFILES.md`.

'''
    if marker not in text:
        raise SystemExit("web/README.md: category marker missing")
    text = text.replace(marker, addition + marker, 1)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    migrate_builder()
    migrate_base_runtime()
    migrate_profile_runtime()
    migrate_generator()
    migrate_polish_runtime()
    migrate_hotkey_test()
    migrate_filtering_test()
    migrate_order_navigation_test()
    migrate_readme()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
