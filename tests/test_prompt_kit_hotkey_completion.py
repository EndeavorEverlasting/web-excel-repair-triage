from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"
README = ROOT / "web" / "README.md"
DESIGN = ROOT / "docs" / "PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md"


class PromptKitHotkeyCompletionTests(unittest.TestCase):
    def test_backtick_and_filter_commands_share_effective_runtime(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        for marker in (
            "{key:'`',label:'Show / hide Hotkeys'}",
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

    def test_favorite_prompt_shortcuts_are_persisted_fail_closed(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        for marker in (
            "promptKit.promptShortcuts.v1",
            "prompt-kit-shortcuts/v1",
            "PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=1200",
            "function configurePromptShortcut(rawPromptId)",
            "if(!isFavoritePrompt(promptId))",
            "if(!persistPromptShortcutBindings(candidate))return false",
            "promptShortcutBindings=candidate",
            "function handleConfiguredPromptShortcutKey(e,key)",
            "showPromptDetail(promptId,null)",
        ):
            self.assertIn(marker, source)
        self.assertLess(
            source.index("if(!persistPromptShortcutBindings(candidate))return false"),
            source.index("promptShortcutBindings=candidate"),
        )

    def test_buffered_prompt_sequence_precedes_builtin_digit_dispatch(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        buffered = "if(promptShortcutBuffer&&handleConfiguredPromptShortcutKey(e,key))return;"
        self.assertIn(buffered, source)
        for built_in in ("if(key==='1')", "if(key==='4')", "if(key==='5')"):
            self.assertLess(source.index(buffered), source.index(built_in))
        self.assertIn("var escapeHelpPanel=document.getElementById('hotkeyHelpPanel');", source)
        self.assertIn("if(key==='escape'&&escapeHelpPanel&&!escapeHelpPanel.hidden)", source)

    def test_shortcut_rows_are_numeric_and_generated_runtime_matches_source(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        self.assertIn("Number(a.slice(1))-Number(b.slice(1))", source)
        start_marker = "function setCompactFiltersVisible(visible)"
        end_marker = "\n\nfunction setHotkeyHelpOpen(open,restoreFocus)"
        source_block = source[source.index(start_marker) : source.index(end_marker)]
        deployed_block = deployed[deployed.index(start_marker) : deployed.index(end_marker)]
        self.assertEqual(source_block, deployed_block)

    def test_configuration_ui_and_generated_parity_are_present(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "Favorite prompt shortcuts",
            "promptShortcutPromptId",
            "promptShortcutBindings",
            "Favorite a prompt, enter its ID",
            "Save favorite prompt keyboard shortcut",
        ):
            self.assertIn(marker, source)
            self.assertIn(marker, deployed)

    def test_human_contract_and_design_close_previous_ux_decisions(self) -> None:
        readme = README.read_text(encoding="utf-8")
        design = DESIGN.read_text(encoding="utf-8")
        for row in (
            "| `` ` `` | Show / hide Hotkeys |",
            "| `[` | Hide filters |",
            "| `]` | Show filters |",
        ):
            self.assertIn(row, readme)
        self.assertIn("Typed prompt sequences expire after 1.2 seconds", readme)
        self.assertIn("only prompts that are currently Favorites", design)
        self.assertIn("opens canonical prompt detail immediately", design)
        self.assertIn("buffer is active", design)
        self.assertNotIn("Still unresolved by design proof:", design)


if __name__ == "__main__":
    unittest.main()
