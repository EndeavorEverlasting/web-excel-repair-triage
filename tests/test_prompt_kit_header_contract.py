#!/usr/bin/env python3
"""Fail-closed contract for the five-slot Prompt Kit header."""
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
PROFILES = ROOT / "docs" / "prompt-kit-profiles.js"
EXPECTED = [
    ("A", "All"),
    ("B", "Standard"),
    ("C", "Favorites"),
    ("D", "SAS"),
    ("E", "PM"),
]
BUTTON_RE = re.compile(
    r'<button class="cat-tab(?P<classes>[^"]*)"(?P<attrs>[^>]*)>(?P<body>.*?)</button>'
)
KBD_RE = re.compile(r'<span class="kbd">(?P<key>[^<]+)</span>')
TAG_RE = re.compile(r"<[^>]+>")


def read_deployed() -> str:
    assert DEPLOYED.is_file(), f"missing exact deployed artifact: {DEPLOYED}"
    return DEPLOYED.read_text(encoding="utf-8")


def parse_profile_buttons(text: str) -> list[tuple[str, str, str, bool]]:
    assert '<div class="cat-tabs">' in text, "missing fixed tab container"
    region = text.split('<div class="cat-tabs">', 1)[1].split("</div>", 1)[0]
    parsed: list[tuple[str, str, str, bool]] = []
    for match in BUTTON_RE.finditer(region):
        attrs = match.group("attrs")
        slot = re.search(r'data-profile-slot="([A-E])"', attrs)
        if not slot:
            continue
        body = match.group("body")
        key_match = KBD_RE.search(body)
        assert key_match, f"slot {slot.group(1)} is missing its hotkey label"
        label_source = KBD_RE.sub("", body)
        label_source = re.sub(r'<span class="tab-icon">.*?</span>', "", label_source)
        label = html.unescape(TAG_RE.sub("", label_source)).strip()
        parsed.append(
            (
                slot.group(1),
                label,
                key_match.group("key"),
                " active" in match.group(0).split('"', 2)[1],
            )
        )
    return parsed


def test_exact_operator_artifact_header_order() -> None:
    buttons = parse_profile_buttons(read_deployed())
    assert [(slot, label) for slot, label, _, _ in buttons] == EXPECTED
    assert [key for _, _, key, _ in buttons] == list("ABCDE")
    assert buttons[0][3] is True
    assert all(not active for *_, active in buttons[1:])
    assert len(buttons) == 5


def test_header_has_no_numeric_or_p_shortcut() -> None:
    buttons = parse_profile_buttons(read_deployed())
    keys = [key for _, _, key, _ in buttons]
    assert not any(key.isdigit() for key in keys)
    assert "P" not in keys
    base = JS.read_text(encoding="utf-8")
    polish = POLISH.read_text(encoding="utf-8")
    for digit in "12345":
        assert f"case'{digit}'" not in base
        assert f"if(key==='{digit}')" not in polish


def test_builder_owns_five_slot_header() -> None:
    source = BUILDER.read_text(encoding="utf-8")
    positions = []
    for slot, label in EXPECTED:
        marker = f'data-profile-slot="{slot}"'
        position = source.find(marker)
        assert position >= 0, f"builder missing slot {slot}"
        positions.append(position)
        assert f">{label}<span class=\"kbd\">{slot}</span>" in source
    assert positions == sorted(positions)
    assert "GNHF<span class=\"kbd\">3</span>" not in source
    assert "Doctrine<span class=\"kbd\">4</span>" not in source


def test_profile_runtime_is_loaded_before_polish() -> None:
    source = COMBINED_BUILDER.read_text(encoding="utf-8")
    assert 'PROFILE_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-profiles.js"' in source
    assert source.index("profile_script = _read_runtime") < source.index(
        "polish_script = _read_runtime"
    )
    supplemental = source.index('f"<script>\\n{profile_script}\\n</script>\\n"')
    polish = source.index('f"<script>\\n{polish_script}\\n</script>\\n"')
    assert supplemental < polish


def test_profile_runtime_owns_dynamic_names_and_editor() -> None:
    source = PROFILES.read_text(encoding="utf-8")
    deployed = read_deployed()
    for marker in (
        "promptKit.profileSlots.v1",
        "promptKit.activeProfileSlot.v1",
        "promptKit.profilePacks.v1",
        "Profile tabs A–E",
        "data-profile-slot",
        "prompt-profile-pack-select",
        "Import validated pack set",
        "updateHotkeyHelp",
    ):
        assert marker in source
        assert marker in deployed


def test_responsive_header_contract_survives_profile_upgrade() -> None:
    polish = POLISH.read_text(encoding="utf-8")
    deployed = read_deployed()
    for marker in (
        ".header-top{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(280px,400px);",
        ".header-top>.header-controls{grid-column:1/-1;min-width:0;width:100%",
        ".header-top>.header-controls .cat-tabs{max-width:100%;overflow-x:auto;",
        ".header-top>.header-controls .cat-tab{min-height:42px}",
    ):
        assert marker in polish
        assert marker in deployed


def test_effective_hotkey_help_uses_profile_slots_and_home_end_navigation() -> None:
    polish = POLISH.read_text(encoding="utf-8")
    profiles = PROFILES.read_text(encoding="utf-8")
    assert "slots.forEach(function(slot)" in profiles
    assert "label.textContent=slot.name" in profiles
    assert "['Home','Scroll to top']" in profiles
    assert "['End','Scroll to bottom']" in profiles
    assert "{key:'Home',label:'Scroll to top'}" in polish
    assert "{key:'End',label:'Scroll to bottom'}" in polish
    assert "{key:'T',label:'Scroll to top'}" not in polish
    assert "{key:'B',label:'Scroll to bottom'}" not in polish
    assert "if(key==='home')" in polish
    assert "if(key==='end')" in polish
    assert "var top=edge==='top'?0:height" in polish
    assert "doc.addEventListener('keydown'" not in profiles
    assert "window.PromptKitProfiles.activateSlot(key.toUpperCase())" in polish


def test_readme_records_profile_header_and_collision_contract() -> None:
    text = README.read_text(encoding="utf-8")
    assert "All / Standard / Favorites / SAS / PM" in text
    assert "`A`–`E`" in text or "`A` through `E`" in text
    assert "| `A` | All |" in text
    assert "| `E` | PM |" in text
    assert "| `Home` | Scroll to top |" in text
    assert "| `End` | Scroll to bottom |" in text
    assert "| `T` | Scroll to top |" not in text
    assert "numeric keys are not header navigation" in text.lower()
    assert "P111" in text


def test_effective_p07_requires_mainline_convergence() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_prompt_kit_registry

    p07 = next(
        prompt
        for prompt in build_prompt_kit_registry.load_prompt_registry()
        if prompt["id"] == "P07"
    )
    content = p07["copyContent"]
    assert "GREEN BRANCH INTEGRATION CONTRACT" in content
    assert "P07 MAINLINE CONVERGENCE OVERRIDE" in content
    assert "None is sufficient completion" in content
    assert "integration target" in content


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
        assert rebuilt.read_bytes() == DEPLOYED.read_bytes()


def main() -> None:
    tests = [
        test_exact_operator_artifact_header_order,
        test_header_has_no_numeric_or_p_shortcut,
        test_builder_owns_five_slot_header,
        test_profile_runtime_is_loaded_before_polish,
        test_profile_runtime_owns_dynamic_names_and_editor,
        test_responsive_header_contract_survives_profile_upgrade,
        test_effective_hotkey_help_uses_profile_slots_and_home_end_navigation,
        test_readme_records_profile_header_and_collision_contract,
        test_effective_p07_requires_mainline_convergence,
        test_deployed_artifact_is_current_combined_registry_output,
    ]
    for test in tests:
        test()
    print(f"PASS: {len(tests)} five-tab Prompt Kit header contracts")


if __name__ == "__main__":
    main()
