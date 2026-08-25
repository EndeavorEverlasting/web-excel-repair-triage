#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPLOYED = ROOT / 'web' / 'prompt-kit' / 'index.html'
README = ROOT / 'web' / 'README.md'
BUILDER = ROOT / 'build_prompt_kit.py'
COMBINED_BUILDER = ROOT / 'scripts' / 'build_prompt_kit_registry.py'
JS = ROOT / 'docs' / 'prompt-kit.js'
POLISH = ROOT / 'docs' / 'prompt-kit-polish.js'
HEADER_KEYS = {'A':'All prompts','S':'Standard prompts','G':'User Profile 1','V':'Favorites','D':'User Profile 2'}


def read_deployed() -> str:
    assert DEPLOYED.is_file(), f'missing exact deployed artifact: {DEPLOYED}'
    return DEPLOYED.read_text(encoding='utf-8')


def test_builder_header_replaces_obsolete_slots() -> None:
        source = BUILDER.read_text(encoding='utf-8')
        start = source.index('<div class="cat-tabs">')
        end = source.index("html.append('      </div>')", start)
        region = source[start:end]
        expected = [
            ('data-cat="all"', 'All', 'A'),
            ('data-cat="standard"', 'Standard', 'S'),
            ('data-profile="profile1"', 'User Profile 1', 'G'),
            ('data-profile="profile2"', 'User Profile 2', 'D'),
        ]
        positions = []
        for marker, label, key in expected:
            position = region.find(marker)
            assert position >= 0, f'missing {label}'
            positions.append(position)
            assert f'>{label}<span class="kbd">{key}</span>' in region
        assert positions == sorted(positions)
        assert 'GNHF<span class="kbd">' not in region
        assert 'Doctrine<span class="kbd">' not in region
        assert not re.search(r'<span class="kbd">[1-5]</span>', region)


def test_runtime_header_keys_are_single_letters_and_not_prompt_prefix() -> None:
    source = POLISH.read_text(encoding='utf-8')
    deployed = read_deployed()
    for key,label in HEADER_KEYS.items():
        marker=f"{{key:'{key}',label:'{label}'}}"
        assert marker in source and marker in deployed
        assert len(key)==1 and key.upper()!='P'
    for obsolete in ("{key:'1',label:'All prompts'}","{key:'2',label:'Standard prompts'}","{key:'3',label:'GNHF prompts'}","{key:'4',label:'Favorites'}","{key:'5',label:'Doctrine'}"):
        assert obsolete not in source
    assert "aria-keyshortcuts','V'" in source
    assert "User profiles" in source
    assert "hotkey-profile-choice" in source


def test_digits_are_never_header_navigation() -> None:
    base = JS.read_text(encoding='utf-8')
    polish = POLISH.read_text(encoding='utf-8')
    for digit in '12345':
        assert f"case'{digit}'" not in base
        assert f"key==='{digit}'" not in polish
    assert "case'a':case'A':activeCat='all';break;case's':case'S':activeCat='standard';break;" in base
    buffered="if(promptShortcutBuffer&&handleConfiguredPromptShortcutKey(e,key))return;"
    assert buffered in polish
    for marker in ("if(key==='a')","if(key==='s')","if(key==='g')","if(key==='v')","if(key==='d')"):
        assert marker in polish
        assert polish.index(buffered) < polish.index(marker)


def test_profiles_isolate_favorites_and_shortcuts_while_profile1_preserves_legacy_keys() -> None:
    source = POLISH.read_text(encoding='utf-8')
    for marker in (
        "profile1:{label:'User Profile 1',favorites:'promptKit.favoritePromptIds.v1',shortcuts:'promptKit.promptShortcuts.v1'}",
        "profile2:{label:'User Profile 2',favorites:'promptKit.profile.profile2.favoritePromptIds.v1',shortcuts:'promptKit.profile.profile2.promptShortcuts.v1'}",
        "FAVORITES_STORAGE_KEY=target.favorites",
        "PROMPT_KIT_SHORTCUT_STORAGE_KEY=target.shortcuts",
        "favoritePromptIds=loadFavoritePromptIds()",
        "promptShortcutBindings=loadPromptShortcutBindings()",
        "saveFavoritePromptIds()",
        "persistPromptShortcutBindings(promptShortcutBindings)",
    ):
        assert marker in source


def test_gnhf_and_doctrine_content_owners_remain_available() -> None:
    base = JS.read_text(encoding='utf-8')
    builder = BUILDER.read_text(encoding='utf-8')
    assert "p.category==='gnhf'" in base
    assert 'build_doctrine' in builder


def test_readme_matches_header_and_profile_contract() -> None:
    text=README.read_text(encoding='utf-8')
    assert 'A / S / G / V / D' in text
    assert '| `G` | User Profile 1 |' in text
    assert '| `D` | User Profile 2 |' in text
    assert '| `V` | Favorites |' in text
    assert 'Digits are intentionally not header shortcuts' in text
    assert 'Profile 1 preserves the legacy Favorites and prompt-shortcut keys' in text


def test_deployed_artifact_is_current_combined_registry_output() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        rebuilt=Path(tmp)/'index.html'
        subprocess.run([sys.executable,str(COMBINED_BUILDER),'--output',str(rebuilt)],cwd=ROOT,check=True,capture_output=True,text=True)
        assert rebuilt.read_bytes()==DEPLOYED.read_bytes()


def main() -> None:
    tests=[test_builder_header_replaces_obsolete_slots,test_runtime_header_keys_are_single_letters_and_not_prompt_prefix,test_digits_are_never_header_navigation,test_profiles_isolate_favorites_and_shortcuts_while_profile1_preserves_legacy_keys,test_gnhf_and_doctrine_content_owners_remain_available,test_readme_matches_header_and_profile_contract,test_deployed_artifact_is_current_combined_registry_output]
    for test in tests:test()
    print(f'PASS: {len(tests)} prompt-kit header/profile contracts')

if __name__ == '__main__':main()
