from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"
README = ROOT / "web" / "README.md"
DESIGN = ROOT / "docs" / "PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md"

class PromptKitHotkeyCompletionTests(unittest.TestCase):
    def test_ctrl_slash_and_filter_commands_share_effective_runtime(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        for marker in ("{key:'Ctrl+/',label:'Show / hide Hotkeys'}", "toggle.setAttribute('aria-keyshortcuts','Control+/')", "if(e.ctrlKey&&!e.altKey&&!e.metaKey&&key==='/'&&!editable)", "function setCompactFiltersVisible(visible)", "function hideCompactFilters()", "function showCompactFilters()", "if(key==='[')", "if(key===']')"):
            self.assertIn(marker, source)
        self.assertLess(source.index("if(e.ctrlKey&&!e.altKey&&!e.metaKey&&key==='/'&&!editable)"), source.index("if(e.defaultPrevented||e.altKey||e.metaKey||e.ctrlKey)return"))

    def test_favorite_prompt_shortcuts_are_persisted_fail_closed(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        for marker in ("promptKit.promptShortcuts.v1", "prompt-kit-shortcuts/v1", "PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=1200", "function configurePromptShortcut(rawPromptId)", "if(!isFavoritePrompt(promptId))", "if(!persistPromptShortcutBindings(candidate))return false", "promptShortcutBindings=candidate", "function handleConfiguredPromptShortcutKey(e,key)", "showPromptDetail(promptId,null)"):
            self.assertIn(marker, source)
        self.assertLess(source.index("if(!persistPromptShortcutBindings(candidate))return false"), source.index("promptShortcutBindings=candidate"))

    def test_configuration_ui_and_generated_parity_are_present(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in ("Favorite prompt shortcuts", "promptShortcutPromptId", "promptShortcutBindings", "Favorite a prompt, enter its ID", "Save favorite prompt keyboard shortcut"):
            self.assertIn(marker, source); self.assertIn(marker, deployed)

    def test_human_contract_and_design_close_previous_ux_decisions(self) -> None:
        readme = README.read_text(encoding="utf-8"); design = DESIGN.read_text(encoding="utf-8")
        for row in ("| `Ctrl+/` | Show / hide Hotkeys |", "| `[` | Hide filters |", "| `]` | Show filters |"):
            self.assertIn(row, readme)
        self.assertIn("Typed prompt sequences expire after 1.2 seconds", readme)
        self.assertIn("only prompts that are currently Favorites", design)
        self.assertIn("opens canonical prompt detail immediately", design)
        self.assertNotIn("Still unresolved by design proof:", design)

if __name__ == "__main__": unittest.main()
