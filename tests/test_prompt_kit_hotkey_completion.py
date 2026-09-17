from pathlib import Path
import json
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
BASE = ROOT / "docs" / "prompt-kit.js"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"
REGISTRY = ROOT / "registry" / "prompts"
DESIGN = ROOT / "harness" / "prompt-kit" / "HOTKEY_COMPLETION_DESIGN.md"
HUMAN_CONTRACT = ROOT / "harness" / "prompt-kit" / "HUMAN_FIRST_UX_CONTRACT.md"
BROWSER_PROOF = ROOT / "scripts" / "browser_prompt_kit_hotkey_completion_proof.py"


class PromptKitHotkeyCompletionTests(unittest.TestCase):
    def _registry_prompts(self) -> list[dict]:
        prompts = []
        for path in sorted(REGISTRY.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict) and isinstance(payload.get("prompts"), list):
                prompts.extend(payload["prompts"])
        return prompts

    def test_catalog_prompt_shortcuts_are_derived_without_manual_persistence(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "function catalogPromptShortcutBindings()",
            "bindings[digits]=promptId",
            "bindings['p'+digits]=promptId",
            "function effectivePromptShortcutBindings()",
            "return catalogPromptShortcutBindings()",
            "var pendingExact=bindings[promptShortcutBuffer]||null",
            "promptShortcutHasLongerPrefix(candidate,gestures)",
        ):
            self.assertIn(marker, source)
            self.assertIn(marker, deployed)
        for removed in (
            "favoritePromptShortcutConfig",
            "saveFavoritePromptShortcutConfig",
            "loadFavoritePromptShortcutConfig",
            "prompt-kit.favorite-shortcuts.v1",
        ):
            self.assertNotIn(removed, source)
            self.assertNotIn(removed, deployed)

    def test_keyboard_digit_grammar_does_not_require_leading_p(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        self.assertIn("function promptShortcutDigitGesture(promptId)", source)
        self.assertIn("return value.slice(1)", source)
        self.assertNotIn("return 'p'+value.slice(1)", source)
        self.assertIn("if(key==='.'&&promptShortcutBuffer)", source)

    def test_shortcut_rows_are_numeric_and_generated_runtime_matches_source(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "key.textContent=promptId.slice(1)",
            "'Copy + snap to '+promptId",
            "Every prompt has a natural numeric shortcut.",
            "example: type 126 to copy + snap to P126".lower(),
        ):
            if marker == marker.lower():
                self.assertIn(marker, source.lower())
                self.assertIn(marker, deployed.lower())
            else:
                self.assertIn(marker, source)
                self.assertIn(marker, deployed)

    def test_favorites_are_organizational_and_detail_control_keeps_numeric_shortcut_visible(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "toggleFavoritePromptAndRefreshShortcut(promptId)",
            "saved · type ",
            " shortcut ",
            " still available",
            "prompt-detail-favorite-btn",
        ):
            self.assertIn(marker, source)
            self.assertIn(marker, deployed)
        activation = source[source.index("function activatePromptShortcutTarget"):source.index("function handleConfiguredPromptShortcutKey")]
        self.assertNotIn("isFavoritePrompt", activation)
        self.assertNotIn("sharedPromptShortcutBindings", activation)

    def test_catalog_hotkey_copy_confirmation_names_prompt_id(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "label:id?'✓ Copied to clipboard · '+id:'✓ Copied to clipboard'",
            "window.buildCopyConfirmationToastModel=buildCopyConfirmationToastModel",
            "toastEl.setAttribute('data-prompt-id',model.promptId||'')",
            "function activatePromptShortcutTarget(promptId)",
            "copyPrompt(promptId)",
            "var effectiveCopyContent=window.PromptKitComputeMode?window.PromptKitComputeMode.effectivePrompt(window,p):p.copyContent",
            "showCopyConfirmation(id,effectiveCopyContent)",
        ):
            self.assertIn(marker, source)
            self.assertIn(marker, deployed)
        activation = source[
            source.index("function activatePromptShortcutTarget") : source.index(
                "function handleConfiguredPromptShortcutKey"
            )
        ]
        self.assertIn("copyPrompt(promptId)", activation)
        self.assertIn("revealPromptShortcutTarget(promptId,'instant')", activation)
        model = source[
            source.index("function buildCopyConfirmationToastModel") : source.index(
                "function renderCopyConfirmationToast"
            )
        ]
        self.assertIn("label:id?'✓ Copied to clipboard · '+id", model)
        confirmation = source[
            source.index("window.showCopyConfirmation=function") : source.index(
                "window.copyPrompt=function"
            )
        ]
        self.assertIn("copyContentOverride!=null", confirmation)
        self.assertIn("buildCopyConfirmationToastModel(promptId,copyContent)", confirmation)

    def test_shared_registry_shortcuts_remain_recommendation_metadata_not_activation_authority(self) -> None:
        prompts = self._registry_prompts()
        source = POLISH.read_text(encoding="utf-8")
        shared = [prompt for prompt in prompts if prompt.get("sharedShortcut") is True]
        self.assertGreaterEqual(len(shared), 1)
        catalog_function = source[
            source.index("function catalogPromptShortcutBindings") : source.index(
                "function effectivePromptShortcutBindings"
            )
        ]
        self.assertNotIn("sharedShortcut", catalog_function)
        self.assertNotIn("isFavoritePrompt", catalog_function)

    def test_backtick_and_filter_commands_share_effective_runtime(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        self.assertIn("if(key==='`')", source)
        self.assertIn("if(key==='f')", source)
        self.assertIn("if(key==='[')", source)
        self.assertIn("if(key===']')", source)
        self.assertIn("toggleCompactFilters()", source)
        self.assertIn("hideCompactFilters()", source)
        self.assertIn("showCompactFilters()", source)

    def test_backtick_does_not_steal_search_or_modified_typing(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        handler = source[source.index("function installCompactBrowsingHotkeys"):]
        self.assertLess(handler.index("if(editable)return"), handler.index("if(key==='`')"))
        self.assertLess(handler.index("if(e.defaultPrevented||e.altKey||e.metaKey||e.ctrlKey)return"), handler.index("if(key==='`')"))

    def test_prompt_sequence_owns_digits_and_header_navigation_is_letter_only(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        handler = source[source.index("function installCompactBrowsingHotkeys"):]
        self.assertIn("if(/^[a-e]$/.test(key)", handler)
        self.assertNotIn("/^[1-5]$/.test(key)", handler)
        self.assertIn("handleConfiguredPromptShortcutKey(e,key)", handler)

    def test_hotkey_help_exposes_natural_numeric_route_without_manual_setup(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        self.assertIn("{key:'126',label:'Prompt number → copy + snap to P126'}", source)
        self.assertIn("Type the digits after P anywhere outside editable fields.", source)
        self.assertNotIn("Assign favorite prompt shortcut", source)

    def test_escape_clears_and_releases_focused_search_before_editable_guard(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        handler = source[source.index("function installCompactBrowsingHotkeys"):]
        self.assertIn("if(key==='escape'&&search&&target===search)", handler)
        self.assertLess(handler.index("if(key==='escape'&&search&&target===search)"), handler.index("if(editable)return"))
        self.assertIn("exitFocusedSearch(search)", handler)

    def test_hotkey_open_focuses_close_and_escape_recovers_without_manual_shortcut_input(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        self.assertIn("close.focus", source)
        self.assertIn("setHotkeyHelpOpen(false,true)", source)
        self.assertNotIn("favoriteShortcutInput", source)

    def test_browser_proof_reports_actual_execution_topology(self) -> None:
        proof = BROWSER_PROOF.read_text(encoding="utf-8")
        self.assertIn("execution_topology", proof)
        self.assertIn("serial", proof)
        self.assertNotIn("observed_parallelism", proof)

    def test_human_contract_and_design_close_natural_numeric_hotkey_decision(self) -> None:
        design = DESIGN.read_text(encoding="utf-8")
        human = HUMAN_CONTRACT.read_text(encoding="utf-8")
        self.assertIn("natural numeric prompt hotkeys", design.lower())
        self.assertIn("type `126`", design.lower())
        self.assertIn("favorites remain organizational", design.lower())
        self.assertIn("natural numeric prompt shortcuts", human.lower())
        self.assertIn("favorites remain organizational", human.lower())

    def test_executable_prototype_proves_success_failure_and_digit_collision_paths(self) -> None:
        prototype = ROOT / "scripts" / "prototype_prompt_hotkeys.mjs"
        self.assertTrue(prototype.exists())
        source = prototype.read_text(encoding="utf-8")
        for marker in (
            "shorter_success",
            "longer_success",
            "timeout_fallback",
            "invalid_digit_sequence",
            "digit_header_collision",
            "p_prefix_compatibility",
        ):
            self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
