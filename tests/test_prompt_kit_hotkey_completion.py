from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"
README = ROOT / "web" / "README.md"
DESIGN = ROOT / "docs" / "PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md"
PROTOTYPE = ROOT / "docs" / "prompt-kit-hotkey-prototype.js"


class PromptKitHotkeyCompletionTests(unittest.TestCase):
    def test_backtick_and_filter_commands_share_effective_runtime(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        for marker in (
            "{key:'`',label:'Show / hide Hotkeys'}",
            "{key:'/',label:'Focus search'}",
            "toggle.setAttribute('aria-keyshortcuts','`')",
            "if(key==='`')",
            "if(e.defaultPrevented||e.altKey||e.metaKey||e.ctrlKey)return",
            "if(editable)return",
            "function setCompactFiltersVisible(visible)",
            "function hideCompactFilters()",
            "function showCompactFilters()",
            "if(key==='[')",
            "if(key===']')",
        ):
            self.assertIn(marker, source)
        self.assertNotIn("{key:'Ctrl+/'", source)
        self.assertNotIn("aria-keyshortcuts','Control+/", source)
        self.assertLess(source.index("if(editable)return"), source.index("if(key==='`')"))

    def test_backtick_does_not_steal_search_or_modified_typing(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        modifier_guard = "if(e.defaultPrevented||e.altKey||e.metaKey||e.ctrlKey)return;"
        editable_guard = "if(editable)return;"
        backtick = "if(key==='`')"
        self.assertLess(source.index(modifier_guard), source.index(backtick))
        self.assertLess(source.index(editable_guard), source.index(backtick))
        self.assertIn("{key:'/',label:'Focus search'}", source)
        self.assertNotIn("key==='/'&&e.ctrlKey", source)
        self.assertNotIn("key==='/'&&e.metaKey", source)

    def test_escape_clears_and_releases_focused_search_before_editable_guard(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        markers = (
            "function exitFocusedSearch(search)",
            "var changed=search.value!=='';",
            "search.value='';",
            "var clear=document.getElementById('searchClear');",
            "if(clear)clear.style.display='none';",
            "if(changed)render();",
            "search.blur()",
            "var search=document.getElementById('search');",
            "if(key==='escape'&&search&&target===search)",
            "resetPromptShortcutBuffer();exitFocusedSearch(search);return",
        )
        for marker in markers:
            self.assertIn(marker, source)
            self.assertIn(marker, deployed)
        escape_guard = "if(key==='escape'&&search&&target===search)"
        editable_guard = "if(editable)return;"
        self.assertLess(source.index(escape_guard), source.index(editable_guard))
        self.assertLess(deployed.index(escape_guard), deployed.index(editable_guard))

    def test_hotkey_open_focuses_close_and_escape_recovers_without_manual_shortcut_input(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        self.assertNotIn("focusFavoritePromptShortcutInput", source)
        self.assertNotIn("promptShortcutPromptId", source)
        self.assertIn("var close=panel.querySelector('.hotkey-help-close');", source)
        escape_guard = "if(key==='escape'&&escapeHelpPanel&&!escapeHelpPanel.hidden)"
        editable_guard = "if(editable)return;"
        backtick = "if(key==='`')"
        self.assertLess(source.index(escape_guard), source.index(editable_guard))
        self.assertLess(source.index(editable_guard), source.index(backtick))
        self.assertIn("resetPromptShortcutBuffer();setHotkeyHelpOpen(false,true);return", source)

    def test_catalog_prompt_shortcuts_are_derived_without_manual_persistence(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=1200",
            "function catalogPromptShortcutBindings()",
            "bindings[digits]=promptId",
            "bindings['p'+digits]=promptId",
            "function handleConfiguredPromptShortcutKey(e,key)",
            "function activatePromptShortcutTarget(promptId)",
            "revealPromptShortcutTarget(promptId,'instant')",
            "copyPrompt(promptId)",
        ):
            self.assertIn(marker, source)
            self.assertIn(marker, deployed)
        for removed in (
            "PROMPT_KIT_SHORTCUT_STORAGE_KEY",
            "PROMPT_KIT_SHORTCUT_SCHEMA",
            "function configurePromptShortcut(",
            "function removePromptShortcut(",
            "promptShortcutPromptId",
        ):
            self.assertNotIn(removed, source)
            self.assertNotIn(removed, deployed)
        activation = source[source.index("function activatePromptShortcutTarget"):source.index("function handleConfiguredPromptShortcutKey")]
        self.assertNotIn("isFavoritePrompt", activation)
        self.assertNotIn("sharedPromptShortcutBindings", activation)

    def test_favorites_are_organizational_and_detail_control_keeps_numeric_shortcut_visible(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "function favoritePromptShortcutBindings()",
            "bindings[digits]=promptId",
            "function centerRenderedPromptCard(promptId,behavior)",
            "hideCompactFilters();",
            "function toggleFavoritePromptAndRefreshShortcut(rawPromptId)",
            "function decoratePromptDetailFavorite(promptId)",
            "prompt-detail-favorite-btn",
            "type '+promptId.slice(1)+' anytime",
            "shortcut '+promptId.slice(1)+' still available",
            "centerRenderedPromptCard(id,'instant');",
            "toggleFavoritePromptAndRefreshShortcut(p.id)",
        ):
            self.assertIn(marker, source)
            self.assertIn(marker, deployed)
        center = source[
            source.index("function centerRenderedPromptCard") : source.index("function revealPromptShortcutTarget")
        ]
        self.assertIn("hideCompactFilters();", center)
        self.assertIn("return catalogPromptShortcutBindings()", source)

    def test_keyboard_digit_grammar_does_not_require_leading_p(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        readme = README.read_text(encoding="utf-8")
        self.assertIn("`126` → `P126`", readme)
        self.assertIn("leading `p`/`P` remains a compatibility alias", readme)
        self.assertIn("function catalogPromptShortcutBindings()", source)
        self.assertIn("bindings[digits]=promptId", source)
        self.assertIn("bindings['p'+digits]=promptId", source)

    def test_prompt_sequence_owns_digits_and_header_navigation_is_letter_only(self) -> None:
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

    def test_executable_prototype_proves_success_failure_and_digit_collision_paths(self) -> None:
        completed = subprocess.run(
            ["node", str(PROTOTYPE)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        proof = json.loads(completed.stdout)
        self.assertEqual(proof["status"], "PASS")
        for path in (
            "HOTKEY_HELP_TOGGLE",
            "FILTER_HIDE",
            "FILTER_SHOW",
            "FILTER_TOGGLE",
            "COPY_REVEAL_PROMPT(P95)",
            "COPY_REVEAL_PROMPT(P14)",
            "VIEW_DOCTRINE",
        ):
            self.assertIn(path, proof["success_paths"])
        for path in (
            "EDITABLE_TARGET",
            "MODIFIED_OR_PREVENTED",
            "RESERVED_COLLISION",
            "UNKNOWN_PROMPT",
            "PERSISTENCE_FAILED",
        ):
            self.assertIn(path, proof["failure_paths"])
        self.assertTrue(any(item.get("promptId") == "P95" for item in proof["trace"]))
        self.assertTrue(any(item.get("promptId") == "P14" for item in proof["trace"]))
        self.assertTrue(any(item.get("event") == "prompt_copied_and_revealed" for item in proof["trace"]))

    def test_shortcut_rows_are_numeric_and_generated_runtime_matches_source(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        self.assertIn("Number(a)-Number(b)", source)
        start_marker = "function setCompactFiltersVisible(visible)"
        end_marker = "\n\nfunction setHotkeyHelpOpen(open,restoreFocus)"
        source_block = source[source.index(start_marker) : source.index(end_marker)]
        deployed_block = deployed[deployed.index(start_marker) : deployed.index(end_marker)]
        self.assertEqual(source_block, deployed_block)

        def function_block(text: str, name: str) -> str:
            start = text.index(f"function {name}(")
            brace = text.index("{", start)
            depth = 0
            for index in range(brace, len(text)):
                if text[index] == "{":
                    depth += 1
                elif text[index] == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start : index + 1]
            self.fail(f"unterminated JavaScript function: {name}")

        for function_name in ("setHotkeyHelpOpen",):
            self.assertEqual(function_block(source, function_name), function_block(deployed, function_name))

        escape_start = "var escapeHelpPanel=document.getElementById('hotkeyHelpPanel');"
        escape_end = "if(editable)return;"
        source_escape = source[source.index(escape_start) : source.index(escape_end) + len(escape_end)]
        deployed_escape = deployed[deployed.index(escape_start) : deployed.index(escape_end) + len(escape_end)]
        self.assertEqual(source_escape, deployed_escape)

    def test_browser_proof_reports_actual_execution_topology(self) -> None:
        proof = (ROOT / "tests" / "prompt_kit_favorite_browser_proof.py").read_text(encoding="utf-8")
        identity = (ROOT / "tests" / "prompt_kit_hotkey_identity_browser_proof.py").read_text(encoding="utf-8")
        for marker in (
            "def execution_environment_kind(env=None)",
            "GITHUB_ACTIONS",
            "github_actions_headless_browser",
            "local_headless_browser",
            '"kind": execution_environment_kind()',
            'page.keyboard.press("/")',
            'search_escape_recovery',
            'empty_search_focus_released',
            'global_hotkey_restored',
            'for slot_key in "ABCDE":',
            'profile_header_hotkeys_a_to_e',
            'page.keyboard.type("126")',
            'catalog_numeric_shortcut_dispatched',
            'clipboard equals canonical P126 copyContent',
            "def canonical_clipboard_text(text: str) -> str:",
            'canonical_clipboard_text(actual) == canonical_clipboard_text(expected)',
        ):
            self.assertIn(marker, proof)
        for marker in (
            'TARGETS = ("P11", "P13", "P111", "P126")',
            'Natural prompt hotkeys are catalog-derived',
            'P126',
        ):
            self.assertIn(marker, identity)
        self.assertNotIn('promptShortcutPromptId', proof)
        self.assertNotIn('Save favorite prompt keyboard shortcut', proof)
        source = POLISH.read_text(encoding="utf-8")
        self.assertIn("window.PromptKitProfiles.activateSlot('A',true)", source)

    def test_hotkey_help_exposes_natural_numeric_route_without_manual_setup(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "Prompt shortcuts",
            "Every prompt has a natural numeric shortcut",
            "Example: type 126 to copy + snap to P126",
            "Type the digits after P anywhere outside editable fields",
            "p126 remains accepted for compatibility",
            "{key:'126',label:'Prompt number → copy + snap to P126'}",
        ):
            self.assertIn(marker, source)
            self.assertIn(marker, deployed)
        self.assertNotIn("promptShortcutPromptId", source)
        self.assertNotIn("Save favorite prompt keyboard shortcut", source)

    def test_shared_registry_shortcuts_remain_recommendation_metadata_not_activation_authority(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "function computeSharedPromptShortcutBindings()",
            "item.sharedShortcut!==true",
            "function effectivePromptShortcutBindings()",
            "return catalogPromptShortcutBindings()",
            "function sharedPromptShortcutIds()",
            "shared.textContent='Recommended'",
        ):
            self.assertIn(marker, source)
            self.assertIn(marker, deployed)
        registry = json.loads(
            (ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json").read_text(encoding="utf-8")
        )
        shared_ids = [
            prompt["id"] for prompt in registry["prompts"] if prompt.get("sharedShortcut") is True
        ]
        self.assertEqual(shared_ids, ["P95"])
        activation = source[source.index("function activatePromptShortcutTarget"):source.index("function handleConfiguredPromptShortcutKey")]
        self.assertNotIn("sharedPromptShortcutBindings", activation)

    def test_human_contract_and_design_close_natural_numeric_hotkey_decision(self) -> None:
        readme = README.read_text(encoding="utf-8")
        design = DESIGN.read_text(encoding="utf-8")
        for row in (
            "| `` ` `` | Show / hide Hotkeys |",
            "| `[` | Hide filters |",
            "| `]` | Show filters |",
        ):
            self.assertIn(row, readme)
        self.assertIn("Type the digits after `P`", readme)
        self.assertIn("`126` → `P126`", readme)
        self.assertIn("canonical `PROMPTS` catalog owns prompt-number hotkeys", design)
        self.assertIn("bare numeric identity is the primary gesture", design)
        self.assertIn("manual prompt-shortcut persistence is retired", design.lower())
        self.assertIn("copy + instant snap", design)
        self.assertIn("hideCompactFilters", design)
        self.assertIn("formatCopyConfirmationPreview", design)
        self.assertIn("buffer is active", design)
        self.assertIn("one hand", design)
        for stale in (
            "Every current Favorite automatically publishes",
            "Manual shortcut configuration remains a compatibility/repair path",
            "**ShortcutStore**: persistence port",
            "Favoriting from either surface immediately makes the canonical lower-case prompt ID an effective hotkey",
        ):
            self.assertNotIn(stale, design)

if __name__ == "__main__":
    unittest.main()
