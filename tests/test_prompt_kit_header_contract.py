#!/usr/bin/env python3
"""Fail-closed contract for the operator-opened prompt-kit header."""
from __future__ import annotations

import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"
README = ROOT / "web" / "README.md"
BUILDER = ROOT / "build_prompt_kit.py"
COMBINED_BUILDER = ROOT / "scripts" / "build_prompt_kit_registry.py"
JS = ROOT / "docs" / "prompt-kit.js"
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
EXPECTED = [
    ("data-cat", "all", "All", "1"),
    ("data-cat", "standard", "Standard", "2"),
    ("data-view", "favorites", "Favorites", "3"),
    ("data-view", "triage", "Triage", "4"),
    ("data-view", "fun", "Fun", "5"),
    ("data-cat", "gnhf", "GNHF", None),
    ("data-cat", "doctrine", "Doctrine", None),
]
BUTTON_RE = re.compile(
    r'<button class="cat-tab(?P<active> active)?"[^>]*?(?P<attr>data-(?:cat|view))="(?P<value>[^"]+)"[^>]*>(?P<body>.*?)</button>'
)
KBD_RE = re.compile(r'<span class="kbd">(?P<key>[^<]+)</span>')
TAG_RE = re.compile(r"<[^>]+>")


def read_deployed() -> str:
    assert DEPLOYED.is_file(), f"missing exact deployed artifact: {DEPLOYED}"
    return DEPLOYED.read_text(encoding="utf-8")


def polish_runtime(text: str) -> str:
    marker = "style.id='prompt-kit-polish-styles';"
    start = text.find(marker)
    assert start >= 0, "missing Prompt Kit polish runtime"
    return text[start:]


def media_block(css: str, width: int) -> str:
    marker = f"@media(max-width:{width}px){{"
    start = css.find(marker)
    assert start >= 0, f"missing {marker}"
    depth = 0
    for index in range(start + len(marker) - 1, len(css)):
        char = css[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return css[start : index + 1]
    raise AssertionError(f"unterminated {marker}")


def parse_header_buttons(text: str) -> list[tuple[str, str, str, bool]]:
    assert '<div class="cat-tabs">' in text, "missing fixed category-tab container"
    region = text.split('<div class="cat-tabs">', 1)[1].split("</div>", 1)[0]
    parsed = []
    for match in BUTTON_RE.finditer(region):
        body = match.group("body")
        key_match = KBD_RE.search(body)
        label_source = re.sub(r'<span class="tab-icon">.*?</span>', "", body)
        label_source = KBD_RE.sub("", label_source)
        label = html.unescape(TAG_RE.sub("", label_source)).strip()
        parsed.append((match.group("attr"), match.group("value"), label, key_match.group("key") if key_match else None, bool(match.group("active"))))
    return parsed


def test_exact_operator_artifact_header_order() -> None:
    buttons = parse_header_buttons(read_deployed())
    assert [(attr, value, label, key) for attr, value, label, key, _ in buttons[:7]] == EXPECTED
    assert buttons[0][4] is True, "All must remain the default active filter"
    assert all(not active for *_, active in buttons[1:7])


def test_gnhf_is_a_filter_not_a_stats_substitute() -> None:
    text = read_deployed()
    buttons = parse_header_buttons(text)
    assert any(attr == "data-cat" and value == "gnhf" and label == "GNHF" and key is None for attr, value, label, key, _ in buttons)
    assert any(attr == "data-cat" and value == "doctrine" and label == "Doctrine" and key is None for attr, value, label, key, _ in buttons)
    stats = text.split('<div class="stats">', 1)[1].split("</div>\n    </div>", 1)[0]
    assert "> GNHF<" not in stats


def test_keyboard_routes_match_visible_contract() -> None:
    js = JS.read_text(encoding="utf-8")
    polish = POLISH.read_text(encoding="utf-8")
    assert "case'1':activeProfile=null;activeCat='all';break;" in js
    assert "case'2':activeProfile=null;activeCat='standard';break;" in js
    assert "case'3':activeCat='gnhf';break;" not in js
    assert "case'4':activeCat='doctrine';break;" not in js
    for marker in (
        "if(key==='1')",
        "if(key==='2')",
        "if(key==='3'){e.preventDefault();e.stopImmediatePropagation();activateFavoritesView();return}",
        "if(key==='4'){e.preventDefault();e.stopImmediatePropagation();activateProfilePromptsView('triage-management','triage');return}",
        "if(key==='5'){e.preventDefault();e.stopImmediatePropagation();activateProfilePromptsView('fun-management','fun');return}",
    ):
        assert marker in polish


def test_builder_owns_the_same_fixed_header() -> None:
    source = BUILDER.read_text(encoding="utf-8")
    header_source = source.split("html.append('      <div class=\"cat-tabs\">')", 1)[1].split("html.append('      </div>')", 1)[0]
    positions = []
    for attr, value, label, key in EXPECTED:
        marker = f'{attr}="{value}"'
        position = header_source.find(marker)
        assert position >= 0, f"builder missing {label} view"
        positions.append(position)
        if key is None:
            segment = header_source[position:header_source.find("</button>", position)]
            assert '<span class="kbd">' not in segment, f"{label} must not claim a numeric hotkey"
        else:
            assert f'>{label}<span class="kbd">{key}</span>' in header_source
    assert positions == sorted(positions), "builder may not reorder the numeric view cluster"


def test_triage_fun_views_use_stable_prompt_profiles() -> None:
    js = JS.read_text(encoding="utf-8")
    polish = POLISH.read_text(encoding="utf-8")
    assert "if(activeProfile)f=f.filter(function(p){return String(p.profile||'').toLowerCase()===activeProfile});" in js
    assert "activateProfilePromptsView('triage-management','triage')" in polish
    assert "activateProfilePromptsView('fun-management','fun')" in polish


def test_responsive_header_reflows_before_collision() -> None:
    polish = polish_runtime(POLISH.read_text(encoding="utf-8"))
    deployed = polish_runtime(read_deployed())
    wide_required = (
        ".header-top{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(280px,400px);",
        ".header-top>.logo{grid-column:1;min-width:0}",
        ".header-top>.search-container{grid-column:3;min-width:0;width:100%;max-width:none}",
        ".header-top>.header-controls{grid-column:1/-1;min-width:0;width:100%;justify-self:stretch;justify-content:flex-end;flex-wrap:wrap}",
    )
    for marker in wide_required:
        assert marker in polish, f"responsive header source is missing: {marker}"
        assert marker in deployed, f"generated Prompt Kit is missing responsive header marker: {marker}"

    for text, label in ((polish, "source"), (deployed, "generated Prompt Kit")):
        medium = media_block(text, 980)
        mobile = media_block(text, 760)
        assert ".header-top{grid-template-columns:minmax(0,1fr) auto}" in medium, f"{label} medium breakpoint lost header grid"
        assert ".header-top>.search-container{grid-column:1/-1;max-width:none}" in medium, f"{label} medium breakpoint must move search to its own row"
        assert ".header-top>.header-controls{grid-column:1/-1}" in medium, f"{label} medium breakpoint must keep controls below search"
        assert ".header-top>.header-controls{grid-column:1/-1;display:grid;grid-template-columns:minmax(0,1fr);" in mobile, f"{label} mobile controls must stack"
        assert ".header-top>.header-controls .cat-tabs{max-width:100%;overflow-x:auto;" in mobile, f"{label} mobile category tabs must scroll inside their own rail"
        assert ".header-top>.header-controls .cat-tab{min-height:42px}" in mobile, f"{label} mobile category targets must remain touch-sized"

    assert ".header.filters-collapsed .header-top{padding-bottom:0;flex-wrap:nowrap}" not in polish
    assert ".header.filters-collapsed .header-top{padding-bottom:0;flex-wrap:nowrap}" not in deployed


def test_polish_hotkeys_and_glowing_help_are_source_and_deployed_contract() -> None:
    source = POLISH.read_text(encoding="utf-8")
    deployed = read_deployed()
    required = (
        "var PROMPT_KIT_SHORTCUTS=[",
        "{key:'`',label:'Show / hide Hotkeys'}",
        "{key:'3',label:'Favorites'}",
        "{key:'4',label:'Triage prompts'}",
        "{key:'5',label:'Fun prompts'}",
        "{key:'F',label:'Show / hide filters'}",
        "{key:'T',label:'Scroll to top'}",
        "{key:'B',label:'Scroll to bottom'}",
        "function scrollPromptKitTo(edge)",
        "function toggleCompactFilters()",
        "function ensureHotkeyHelp()",
        "id='prompt-kit-hotkey-help-styles'",
        "animation:hotkey-help-glow",
        "toggle.setAttribute('aria-label','Open keyboard shortcut help')",
        "toggle.setAttribute('aria-keyshortcuts','`')",
        "panel.setAttribute('role','dialog')",
        "var close=panel.querySelector('.hotkey-help-close');",
        "if(close){try{close.focus({preventScroll:true})}catch(e){close.focus()}}",
        "@media(prefers-reduced-motion:reduce){.hotkey-help-toggle{animation:none}}",
        "if(key==='`')",
        "if(key==='f')",
        "scrollPromptKitTo('top')",
        "scrollPromptKitTo('bottom')",
    )
    for text, label in ((source, "polish source"), (deployed, "generated Prompt Kit")):
        for marker in required:
            assert marker in text, f"{label} missing hotkey/help contract: {marker}"

    assert "toggle.setAttribute('aria-keyshortcuts','F')" in source
    assert "target.tagName==='SELECT'||target.isContentEditable" in source
    assert "var escapeHelpPanel=document.getElementById('hotkeyHelpPanel');" in source
    assert "if(key==='escape'&&escapeHelpPanel&&!escapeHelpPanel.hidden)" in source
    assert "if(promptShortcutBuffer&&handleConfiguredPromptShortcutKey(e,key))return;" in source
    assert ".hotkey-help{position:fixed;right:80px;bottom:16px" in source
    assert "@media(max-width:760px){.hotkey-help{right:78px;bottom:16px}" in source


def test_readme_records_exact_deployed_surface() -> None:
    text = README.read_text(encoding="utf-8")
    assert "### Header navigation contract" in text
    assert "1. All (`1`)\n2. Standard (`2`)\n3. Favorites (`3`)\n4. Triage (`4`)\n5. Fun (`5`)" in text
    assert "GNHF and Doctrine remain available as non-numeric library views" in text
    assert "`web/prompt-kit/index.html`" in text
    assert "| `` ` `` | Show / hide Hotkeys |" in text
    for key, label in (
        ("1", "All prompts"),
        ("2", "Standard prompts"),
        ("3", "Favorites"),
        ("4", "Triage prompts"),
        ("5", "Fun prompts"),
        ("F", "Show / hide filters"),
        ("T", "Scroll to top"),
        ("B", "Scroll to bottom"),
    ):
        assert f"| `{key}` | {label} |" in text


def test_effective_p07_requires_mainline_convergence() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_prompt_kit_registry

    p07 = next(prompt for prompt in build_prompt_kit_registry.load_prompt_registry() if prompt["id"] == "P07")
    content = p07["copyContent"]
    assert "GREEN BRANCH INTEGRATION CONTRACT" in content
    assert "P07 MAINLINE CONVERGENCE OVERRIDE" in content
    assert "Any earlier legacy sentence" in content
    assert "is superseded by this section" in content
    assert "must not create a feature branch merely because repository mutation is requested" in content
    assert "None is sufficient completion" in content
    assert "integration target" in content
    assert "pre/post default-branch SHA" in content
    assert "exact blocking gate" in content


def test_deployed_artifact_is_current_combined_registry_output() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        rebuilt = Path(tmp) / "index.html"
        subprocess.run(
            [sys.executable, str(COMBINED_BUILDER), "--output", str(rebuilt)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert rebuilt.read_bytes() == DEPLOYED.read_bytes(), (
            "web/prompt-kit/index.html is stale; regenerate it from the combined prompt registry"
        )


def main() -> None:
    tests = [
        test_exact_operator_artifact_header_order,
        test_gnhf_is_a_filter_not_a_stats_substitute,
        test_keyboard_routes_match_visible_contract,
        test_builder_owns_the_same_fixed_header,
        test_triage_fun_views_use_stable_prompt_profiles,
        test_responsive_header_reflows_before_collision,
        test_polish_hotkeys_and_glowing_help_are_source_and_deployed_contract,
        test_readme_records_exact_deployed_surface,
        test_effective_p07_requires_mainline_convergence,
        test_deployed_artifact_is_current_combined_registry_output,
    ]
    for test in tests:
        test()
    print(f"PASS: {len(tests)} prompt-kit header contracts")


if __name__ == "__main__":
    main()
