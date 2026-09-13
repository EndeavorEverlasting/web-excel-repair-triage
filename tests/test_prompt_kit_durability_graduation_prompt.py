from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry


class PromptDurabilityGraduationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = {
            prompt["id"]: prompt
            for prompt in json.loads((REPO_ROOT / "docs" / "prompts.json").read_text(encoding="utf-8"))
        }
        cls.effective = {
            prompt["id"]: prompt for prompt in build_prompt_kit_registry.load_prompt_registry()
        }

    def test_p07_owns_cross_repo_durability_graduation_without_cmd_lock_in(self) -> None:
        prompt = self.raw["P07"]
        self.assertEqual(prompt["name"], "Repo Sprint Executor")
        self.assertEqual(prompt["type"], "BUILD")
        content = prompt["copyContent"]
        for phrase in (
            "DURABILITY / GRADUATION GATE — NO SNIPPET HELL",
            "REQUEST / EXPERIMENT -> SNIPPET -> REUSABLE EXECUTABLE -> REPOSITORY-NATIVE TOOL -> VALIDATED INTERFACE / ARTIFACT",
            "CMD is one valid implementation form, not the definition of maturity",
            "substantially the same commands are being recreated across conversations",
            "The interface MUST call or consume the validated canonical implementation",
            "Do not force a later stage before evidence justifies it",
            "previous stage; resulting stage; canonical implementation owner",
            "created/modified files; stable invocation or interface",
            "validation actually executed; runtime/field proof ceiling",
            "whether another graduation is now evidence-warranted",
            "Creating a wrapper, button, workbook element, or other surface is not completion unless it is proven to reach the canonical behavior",
        ):
            self.assertIn(phrase, content)
        for keyword in ("snippet hell", "snippet to tool", "durability graduation", "artifact graduation"):
            self.assertIn(keyword, prompt["keywords"])

    def test_p18_documents_the_durable_path_without_becoming_the_implementation_owner(self) -> None:
        prompt = self.raw["P18"]
        self.assertEqual(prompt["name"], "Documentation + Tutorial Executor")
        self.assertEqual(prompt["type"], "ENABLEMENT")
        content = prompt["copyContent"]
        for phrase in (
            "DURABILITY BOUNDARY — DOCUMENT THE DURABLE PATH",
            "they are not a substitute for repository tooling when the same operational sequence is recurring",
            "route the durable implementation to P07",
            "route a technician-facing launcher/terminal experience to P34",
            "teach the stable canonical entry point",
            "interface consumes the canonical implementation/data contract instead of duplicating its logic",
        ):
            self.assertIn(phrase, content)
        self.assertNotIn("REQUEST / EXPERIMENT -> SNIPPET -> REUSABLE EXECUTABLE", content)

    def test_p34_graduates_chat_commands_only_after_canonical_behavior_is_proven(self) -> None:
        prompt = self.raw["P34"]
        self.assertEqual(prompt["name"], "GNHF Technician Experience")
        self.assertEqual(prompt["type"], "ENABLEMENT + BUILD")
        content = prompt["copyContent"]
        for phrase in (
            "SNIPPET-TO-OPERATOR-PATH GRADUATION",
            "Repeated chat retrieval means the operator path is incomplete",
            "Reuse proven canonical behavior",
            "stable executable",
            "launcher, GUI/web control, spreadsheet, or artifact",
            "Never veneer an unproven snippet",
        ):
            self.assertIn(phrase, content)

    def test_combined_registry_retains_the_three_strengthened_owner_roles(self) -> None:
        for prompt_id, expected_name in (
            ("P07", "Repo Sprint Executor"),
            ("P18", "Documentation + Tutorial Executor"),
            ("P34", "GNHF Technician Experience"),
        ):
            self.assertEqual(self.effective[prompt_id]["name"], expected_name)
        self.assertIn("DURABILITY / GRADUATION GATE — NO SNIPPET HELL", self.effective["P07"]["copyContent"])
        self.assertIn("DURABILITY BOUNDARY — DOCUMENT THE DURABLE PATH", self.effective["P18"]["copyContent"])
        self.assertIn("SNIPPET-TO-OPERATOR-PATH GRADUATION", self.effective["P34"]["copyContent"])

    def test_generated_site_contains_every_strengthened_owner_marker(self) -> None:
        site = (REPO_ROOT / "web" / "prompt-kit" / "index.html").read_text(encoding="utf-8")
        for marker in (
            "DURABILITY / GRADUATION GATE — NO SNIPPET HELL",
            "DURABILITY BOUNDARY — DOCUMENT THE DURABLE PATH",
            "SNIPPET-TO-OPERATOR-PATH GRADUATION",
            "whether another graduation is now evidence-warranted",
            "Creating a wrapper, button, workbook element, or other surface is not completion unless it is proven to reach the canonical behavior",
        ):
            self.assertIn(marker, site)


if __name__ == "__main__":
    unittest.main()
