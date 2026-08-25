from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "docs" / "prompt-kit-profile-modality-prototype.js"
DESIGN = ROOT / "docs" / "PROMPT_KIT_PROFILE_MODALITY_PROGRAM_DESIGN.md"
PARENT_PROTOTYPE = ROOT / "docs" / "prompt-kit-program-prototype.js"
PARENT_DESIGN = ROOT / "docs" / "PROMPT_KIT_PROGRAM_ARCHITECTURE.md"
HOTKEY_PROTOTYPE = ROOT / "docs" / "prompt-kit-hotkey-prototype.js"


class PromptKitProfileModalityPrototypeTests(unittest.TestCase):
    def run_prototype(self) -> dict:
        result = subprocess.run(
            ["node", str(PROTOTYPE)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_extension_is_executable_and_covers_requested_archetypes(self) -> None:
        for script in (PROTOTYPE, HOTKEY_PROTOTYPE):
            syntax = subprocess.run(
                ["node", "--check", str(script)], cwd=ROOT, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(syntax.returncode, 0, syntax.stderr or syntax.stdout)

        report = self.run_prototype()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(
            report["selectedExtension"],
            "INTERACTION_CONTEXT_WITH_PROFILE_SCOPED_PREFERENCES",
        )
        self.assertTrue(all(value == "PASS" for value in report["archetypeSupport"].values()))
        self.assertTrue(all(value == "PASS" for value in report["journeys"].values()))
        for archetype in ("mousePointerOnly", "keyboardOnly", "singleProfile", "multiProfile"):
            self.assertEqual(report["archetypeSupport"][archetype], "PASS")

    def test_pointer_and_keyboard_converge_without_global_input_mode(self) -> None:
        text = PROTOTYPE.read_text(encoding="utf-8")
        self.assertIn("class InteractionContextFactory", text)
        self.assertIn("class InteractionCommandGateway", text)
        self.assertIn("'COPY_REVEAL_PROMPT'", text)
        self.assertIn("'prompt-control'", text)
        self.assertIn("'favorite-shortcut'", text)
        self.assertIn("VALID_MODALITIES = new Set(['pointer', 'keyboard'])", text)
        self.assertNotIn("mouseMode", text)
        self.assertNotIn("keyboardMode", text)
        self.assertNotIn("currentModality", text)

        report = self.run_prototype()
        self.assertEqual(report["journeys"]["pointerVisibleControlCopy"], "PASS")
        self.assertEqual(report["journeys"]["keyboardVisibleControlCopy"], "PASS")
        self.assertEqual(report["journeys"]["keyboardShortcutRevealFocus"], "PASS")
        self.assertIn("never global mutable mode", report["statePolicy"]["interactionModality"])

    def test_profiles_scope_preferences_through_canonical_owners(self) -> None:
        report = self.run_prototype()
        expected = (
            "defaultProfileLegacyCompatibility",
            "canonicalFavoriteOwnerReuse",
            "profileFavoriteIsolation",
            "profileFavoriteProjectionRefresh",
            "profileShortcutIsolation",
            "profileShortcutRehydration",
            "profileShortcutPersistenceFailure",
            "profilePersistenceFailureIsolation",
            "inFlightProfileSnapshot",
        )
        for journey in expected:
            self.assertEqual(report["journeys"][journey], "PASS")

        self.assertEqual(report["statePolicy"]["promptCatalog"], "shared across profiles")
        self.assertIn("does not reset", report["statePolicy"]["sessionState"])
        self.assertIn("FavoritePreferences", report["statePolicy"]["favorites"])
        self.assertIn("ShortcutRegistry", report["statePolicy"]["shortcuts"])
        self.assertIn("legacy preference storage", report["statePolicy"]["defaultProfile"])

        text = PROTOTYPE.read_text(encoding="utf-8")
        hotkey = HOTKEY_PROTOTYPE.read_text(encoding="utf-8")
        self.assertIn("FavoritePreferences,", text)
        self.assertIn("class FavoritePreferenceContexts", text)
        self.assertIn("new FavoritePreferences", text)
        self.assertNotIn("class ProfiledFavoritePreferences", text)
        self.assertIn("class ShortcutRegistryContexts", text)
        self.assertIn("new ShortcutRegistry", text)
        self.assertIn("initialBindings: boundStore.load()", text)
        self.assertIn("initialBindings = []", hotkey)
        self.assertIn("bindings_hydrated", hotkey)
        self.assertIn("projectFavoriteSet(target.id, favorites.snapshot(target.id))", text)

    def test_default_role_is_catalog_owned_not_a_magic_id(self) -> None:
        text = PROTOTYPE.read_text(encoding="utf-8")
        self.assertIn("defaultProfileId: profileCatalog.defaultProfile().id", text)
        self.assertIn("profiles: [{id: 'solo', name: 'Default', isDefault: true}]", text)
        self.assertIn("legacy-default-slot", text)
        self.assertNotIn("return profileId === 'default' ?", text)
        self.assertNotIn("const favorites = profileId === 'default'", text)
        self.assertNotIn("if (profileId === 'default') {", text)

    def test_failure_and_trace_boundaries_are_explicit_and_private(self) -> None:
        report = self.run_prototype()
        for journey in (
            "unknownProfileFailure",
            "invalidModalityBoundary",
            "profilePersistenceFailureIsolation",
            "profileShortcutPersistenceFailure",
            "privacyBoundedTrace",
        ):
            self.assertEqual(report["journeys"][journey], "PASS")

        encoded = json.dumps(report, sort_keys=True)
        self.assertNotIn("EXECUTE THE REPO SPRINT.", encoded)
        self.assertNotIn("EXAMPLE PROMPT CONTENT.", encoded)
        self.assertNotIn("Repo Sprint Executor", encoded)
        self.assertIn("interaction_context", encoded)
        self.assertIn("profileId", encoded)
        self.assertIn("modality", encoded)

    def test_design_extends_parent_architecture_and_stays_prototype_bounded(self) -> None:
        text = DESIGN.read_text(encoding="utf-8")
        parent = PARENT_DESIGN.read_text(encoding="utf-8")
        parent_prototype = PARENT_PROTOTYPE.read_text(encoding="utf-8")

        self.assertIn("Prompt Kit program architecture — prototype-earned seams", parent)
        self.assertIn("class CommandKernel", parent_prototype)
        self.assertIn("bounded program-design extension", text)
        self.assertIn("parent architecture remains the canonical owner", text)

        required = [
            "## Observable done checklist",
            "## Primary user outcomes",
            "## Core invariants",
            "## Domain vocabulary",
            "## External prior-art inspection",
            "## Candidate designs",
            "Candidate C — explicit InteractionContext + profile-scoped preference ports",
            "## Selected module/interface map",
            "## State and data ownership",
            "## Dependency direction",
            "## Executable prototypes and call stacks",
            "## Failure call stacks",
            "## State model",
            "## Productivity feature admission",
            "## Feature shortlist after this design session",
            "## Second-pass architecture critique and reconciliation",
            "## Exact implementation seam ready for the next build sprint",
            "## Unresolved decisions",
            "## Proof ceiling",
        ]
        for marker in required:
            self.assertIn(marker, text)

        for phrase in (
            "No global input mode",
            "Visible controls are canonical capability surfaces",
            "Default profile is a compatibility boundary",
            "Transient browsing state is not profile-owned by default",
            "profile-specific Favorite + shortcut worksets",
            "canonical `FavoritePreferences`",
            "canonical `ShortcutRegistry`",
            "microsoft/vscode",
            "w3c/aria-practices",
            "broad production migration",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
