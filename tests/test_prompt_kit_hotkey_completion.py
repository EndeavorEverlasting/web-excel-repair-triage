from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
BASE_RUNTIME = ROOT / "docs" / "prompt-kit.js"
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
            "function activatePromptShortcutTarget(promptId)",
            "revealPromptShortcutTarget(promptId)",
            "renderTypes();",
            "copyPrompt(promptId)",
        ):
            self.assertIn(marker, source)
        self.assertLess(
            source.index("if(!persistPromptShortcutBindings(candidate))return false"),
            source.index("promptShortcutBindings=candidate"),
        )

    def test_p111_digits_cannot_fall_through_to_header_navigation(self) -> None:
            source = POLISH.read_text(encoding="utf-8")
            base = BASE_RUNTIME.read_text(encoding="utf-8")
            buffered = "if(promptShortcutBuffer&&handleConfiguredPromptShortcutKey(e,key))return;"
            self.assertIn(buffered, source)
            for digit in "12345":
                self.assertNotIn(f"if(key==='{digit}')", source)
                self.assertNotIn(f"case'{digit}'", base)
            for header in ("if(key==='a')", "if(key==='s')", "if(key==='g')", "if(key==='v')", "if(key==='d')"):
                self.assertIn(header, source)
                self.assertLess(source.index(buffered), source.index(header))
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
            "User profiles",
            "User Profile 1",
            "User Profile 2",
            "hotkey-profile-choice",
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
        self.assertIn("copies the canonical prompt and scrolls its card into view without opening prompt detail", design)
        self.assertIn("buffer is active", design)
        self.assertIn("one hand", design)
        self.assertNotIn("Still unresolved by design proof:", design)


if __name__ == "__main__":
    unittest.main()
