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
EXPECTED = [
    ("all", "All", "1"),
    ("standard", "Standard", "2"),
    ("gnhf", "GNHF", "3"),
    ("doctrine", "Doctrine", "4"),
]
BUTTON_RE = re.compile(
    r'<button class="cat-tab(?P<active> active)?" data-cat="(?P<cat>[^"]+)">(?P<body>.*?)</button>'
)
KBD_RE = re.compile(r'<span class="kbd">(?P<key>[^<]+)</span>')
TAG_RE = re.compile(r"<[^>]+>")


def read_deployed() -> str:
    assert DEPLOYED.is_file(), f"missing exact deployed artifact: {DEPLOYED}"
    return DEPLOYED.read_text(encoding="utf-8")


def parse_header_buttons(text: str) -> list[tuple[str, str, str, bool]]:
    assert '<div class="cat-tabs">' in text, "missing fixed category-tab container"
    region = text.split('<div class="cat-tabs">', 1)[1].split("</div>", 1)[0]
    parsed = []
    for match in BUTTON_RE.finditer(region):
        body = match.group("body")
        key_match = KBD_RE.search(body)
        assert key_match, f"{match.group('cat')} button is missing a hotkey label"
        label_source = re.sub(r'<span class="tab-icon">.*?</span>', "", body)
        label_source = KBD_RE.sub("", label_source)
        label = html.unescape(TAG_RE.sub("", label_source)).strip()
        parsed.append((match.group("cat"), label, key_match.group("key"), bool(match.group("active"))))
    return parsed


def test_exact_operator_artifact_header_order() -> None:
    buttons = parse_header_buttons(read_deployed())
    assert [(cat, label, key) for cat, label, key, _ in buttons[:4]] == EXPECTED
    assert buttons[0][3] is True, "All must remain the default active filter"
    assert all(not active for *_, active in buttons[1:4])


def test_gnhf_is_a_filter_not_a_stats_substitute() -> None:
    text = read_deployed()
    buttons = parse_header_buttons(text)
    assert any(cat == "gnhf" and label == "GNHF" for cat, label, _, _ in buttons)
    stats = text.split('<div class="stats">', 1)[1].split("</div>\n    </div>", 1)[0]
    assert "> GNHF<" not in stats, "remove the stale GNHF legend once GNHF is restored as a filter"


def test_keyboard_routes_match_visible_contract() -> None:
    js = JS.read_text(encoding="utf-8")
    for key, category in (("1", "all"), ("2", "standard"), ("3", "gnhf"), ("4", "doctrine")):
        marker = f"case'{key}':activeCat='{category}';break;"
        assert marker in js, f"missing keyboard route: {marker}"
    assert "case'3':activeCat='doctrine';break;" not in js


def test_builder_owns_the_same_fixed_header() -> None:
    source = BUILDER.read_text(encoding="utf-8")
    header_source = source.split("html.append('      <div class=\"cat-tabs\">')", 1)[1].split("html.append('      </div>')", 1)[0]
    positions = []
    for category, label, key in EXPECTED:
        marker = f'data-cat="{category}"'
        position = header_source.find(marker)
        assert position >= 0, f"builder missing {label} filter"
        positions.append(position)
        assert f'>{label}<span class="kbd">{key}</span>' in header_source
    assert positions == sorted(positions), "builder may not reorder the fixed header contract"


def test_readme_records_exact_deployed_surface() -> None:
    text = README.read_text(encoding="utf-8")
    assert "### Header navigation contract" in text
    assert "1. All\n2. Standard\n3. GNHF" in text
    assert "Doctrine may use shortcut `4`, but it must never displace GNHF." in text
    assert "`web/prompt-kit/index.html`" in text
    for key, label in (("1", "All prompts"), ("2", "Standard prompts"), ("3", "GNHF prompts"), ("4", "Doctrine")):
        assert f"| `{key}` | {label} |" in text


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
        test_readme_records_exact_deployed_surface,
        test_deployed_artifact_is_current_combined_registry_output,
    ]
    for test in tests:
        test()
    print(f"PASS: {len(tests)} prompt-kit header contracts")


if __name__ == "__main__":
    main()
