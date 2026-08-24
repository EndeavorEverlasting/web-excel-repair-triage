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

    def test_extension_is_executable_and_covers_all_requested_archetypes(self) -> None:
        syntax = subprocess.run(
            ["node", "--check", str(PROTOTYPE)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
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
        self.assertEqual(report["archetypeSupport"]["mousePointerOnly"], "PASS")
        self.assertEqual(report["archetypeSupport"]["keyboardOnly"], "PASS")
        self.assertEqual(report["archetypeSupport"]["singleProfile"], "PASS")
        self.assertEqual(report["archetypeSupport"]["multiProfile"], "PASS")

    def test_pointer_and_keyboard_share_terminal_commands_without_global_input_mode(self) -> None:
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

    def test_profile_state_is_scoped_without_cloning_catalog_or_session(self) -> None:
        report = self.run_prototype()
        self.assertEqual(report["journeys"]["defaultProfileLegacyCompatibility"], "PASS")
        self.assertEqual(report["journeys"]["profileFavoriteIsolation"], "PASS")
        self.assertEqual(report["journeys"]["profilePersistenceFailureIsolation"], "PASS")
        self.assertEqual(report["journeys"]["inFlightProfileSnapshot"], "PASS")
        self.assertEqual(report["statePolicy"]["promptCatalog"], "shared across profiles")
        self.assertIn("does not reset", report["statePolicy"]["sessionState"])
        self.assertIn("legacy preference storage", report["statePolicy"]["defaultProfile"])

        text = PROTOTYPE.read_text(encoding="utf-8")
        self.assertIn("class ProfileCatalog", text)
        self.assertIn("class ActiveProfile", text)
        self.assertIn("class MemoryProfilePreferenceStore", text)
        self.assertIn("class ProfiledFavoritePreferences", text)
        self.assertIn("legacy-default-slot", text)
        self.assertIn("PROFILE_PREFERENCE_PERSISTENCE_FAILED", text)
        self.assertIn("defaultProfileId: profileCatalog.defaultProfile().id", text)
        self.assertNotIn("return profileId === 'default' ?", text)
        self.assertNotIn("const favorites = profileId === 'default'", text)
        self.assertNotIn("if (profileId === 'default') {", text)

    def test_failure_boundaries_are_observable_and_do_not_leak_prompt_bodies(self) -> None:
        report = self.run_prototype()
        self.assertEqual(report["journeys"]["unknownProfileFailure"], "PASS")
        self.assertEqual(report["journeys"]["invalidModalityBoundary"], "PASS")
        self.assertEqual(report["journeys"]["profilePersistenceFailureIsolation"], "PASS")

        encoded = json.dumps(report, sort_keys=True)
        self.assertNotIn("EXECUTE THE REPO SPRINT.", encoded)
        self.assertNotIn("EXAMPLE PROMPT CONTENT.", encoded)
        self.assertIn("interaction_context", encoded)
        self.assertIn("profileId", encoded)
        self.assertIn("modality", encoded)

    def test_design_extends_canonical_program_owner_and_defers_broad_build(self) -> None:
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
            "## Executable prototype",
            "## Failure call stacks",
            "## State model",
            "## Productivity feature admission",
            "## Feature shortlist after this design session",
            "## Second-pass architecture critique",
            "## Exact implementation seam ready for the next build sprint",
            "## Unresolved decisions",
            "## Proof ceiling",
        ]
        for marker in required:
            self.assertIn(marker, text)

        self.assertIn("No global input mode", text)
        self.assertIn("Visible controls are canonical capability surfaces", text)
        self.assertIn("Default profile is a compatibility boundary", text)
        self.assertIn("Transient browsing state is not profile-owned by default", text)
        self.assertIn("profile-specific Favorite + shortcut worksets", text)
        self.assertIn("microsoft/vscode", text)
        self.assertIn("w3c/aria-practices", text)
        self.assertIn("broad production migration", text)


if __name__ == "__main__":
    unittest.main()
