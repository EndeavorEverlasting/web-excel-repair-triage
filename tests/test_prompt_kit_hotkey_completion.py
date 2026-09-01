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

    def test_hotkey_open_focuses_favorite_input_and_escape_recovers_from_editable(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        for marker in (
            "function focusFavoritePromptShortcutInput(panel)",
            "document.getElementById('promptShortcutPromptId')",
            "promptInput.focus()",
            "promptInput.scrollIntoView({block:'nearest',inline:'nearest'})",
            "if(focusFavoritePromptShortcutInput(panel))return",
        ):
            self.assertIn(marker, source)
        escape_guard = "if(key==='escape'&&escapeHelpPanel&&!escapeHelpPanel.hidden)"
        editable_guard = "if(editable)return;"
        backtick = "if(key==='`')"
        self.assertLess(source.index(escape_guard), source.index(editable_guard))
        self.assertLess(source.index(editable_guard), source.index(backtick))
        self.assertIn("resetPromptShortcutBuffer();setHotkeyHelpOpen(false,true);return", source)

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
        self.assertIn("Number(a.slice(1))-Number(b.slice(1))", source)
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

        for function_name in ("focusFavoritePromptShortcutInput", "setHotkeyHelpOpen"):
            self.assertEqual(function_block(source, function_name), function_block(deployed, function_name))

        escape_start = "var escapeHelpPanel=document.getElementById('hotkeyHelpPanel');"
        escape_end = "if(editable)return;"
        source_escape = source[source.index(escape_start) : source.index(escape_end) + len(escape_end)]
        deployed_escape = deployed[deployed.index(escape_start) : deployed.index(escape_end) + len(escape_end)]
        self.assertEqual(source_escape, deployed_escape)

    def test_browser_proof_reports_actual_execution_topology(self) -> None:
        proof = (ROOT / "tests" / "prompt_kit_favorite_browser_proof.py").read_text(encoding="utf-8")
        for marker in (
            "def execution_environment_kind(env=None)",
            "GITHUB_ACTIONS",
            "github_actions_headless_browser",
            "local_headless_browser",
            '"kind": execution_environment_kind()',
            'for slot_key in "ABCDE":',
            'profile_header_hotkeys_a_to_e',
            'page.keyboard.press("d")',
            'D custom profile hotkey activates and excludes P79 before shortcut',
        ):
            self.assertIn(marker, proof)
        self.assertNotIn('.cat-tab[data-cat="doctrine"]', proof)
        source = POLISH.read_text(encoding="utf-8")
        self.assertIn("window.PromptKitProfiles.activateSlot('A',true)", source)

    def test_configuration_ui_and_generated_parity_are_present(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "Favorite prompt shortcuts",
            "promptShortcutPromptId",
            "promptShortcutBindings",
            "Favorite a prompt, enter its ID",
            "Save favorite prompt keyboard shortcut",
            "function focusFavoritePromptShortcutInput(panel)",
            "promptInput.scrollIntoView({block:'nearest',inline:'nearest'})",
            "resetPromptShortcutBuffer();setHotkeyHelpOpen(false,true);return",
        ):
            self.assertIn(marker, source)
            self.assertIn(marker, deployed)

    def test_shared_registry_shortcuts_publish_without_favorite_gate(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "function computeSharedPromptShortcutBindings()",
            "item.sharedShortcut!==true",
            "function effectivePromptShortcutBindings()",
            "var bindings=effectivePromptShortcutBindings();",
            "if(!sharedPromptShortcutBindings[String(promptId).toLowerCase()]&&!isFavoritePrompt(promptId))",
            "function sharedPromptShortcutIds()",
            "shared.textContent='Recommended'",
        ):
            self.assertIn(marker, source)
            self.assertIn(marker, deployed)
        registry = json.loads(
            (ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json").read_text(encoding="utf-8")
        )
        shared_ids = [
            prompt["id"]
            for prompt in registry["prompts"]
            if prompt.get("sharedShortcut") is True
        ]
        self.assertEqual(shared_ids, ["P95"])
        self.assertIn('"sharedShortcut": true', deployed)

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
