from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = {
    "index": ROOT / "docs" / "README.md",
    "quick_reference": ROOT / "docs" / "PROMPT_KIT_GENERATOR_OPERATOR_GUIDE.md",
    "technician": ROOT / "docs" / "TECHNICIAN_PROMPT_KIT_ACQUISITION_TUTORIAL.md",
    "generator": ROOT / "docs" / "PROMPT_KIT_GENERATOR_TUTORIAL.md",
    "administrator": ROOT / "docs" / "PROMPT_KIT_ADMIN_VERIFICATION.md",
}
ACQUISITION_CMD = ROOT / "Acquire-Latest-PromptKit.cmd"
ACQUISITION_PS1 = ROOT / "scripts" / "Acquire-LatestPromptKit.ps1"
GENERATOR_MANIFEST = ROOT / "configs" / "prompt_kit" / "generators.v1.json"


class OperatorDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = {
            name: path.read_text(encoding="utf-8")
            for name, path in DOCS.items()
        }
        cls.all_docs = "\n".join(cls.text.values())
        cls.acquisition_ps1 = ACQUISITION_PS1.read_text(encoding="utf-8")

    def test_required_documents_exist_and_are_substantial(self) -> None:
        for name, path in DOCS.items():
            with self.subTest(document=name):
                self.assertTrue(path.is_file(), f"missing operator document: {path}")
                self.assertGreater(path.stat().st_size, 500, f"operator document is too small: {path}")

    def test_documentation_index_routes_each_audience(self) -> None:
        index = self.text["index"]
        for phrase in (
            "Technician acquisition tutorial",
            "Generator tutorial",
            "Administrator verification runbook",
            "Prompt Kit operator guide",
            "Windows technician workstation",
            "Linux or CI",
            "Target machine",
        ):
            self.assertIn(phrase, index)

    def test_local_markdown_links_resolve(self) -> None:
        link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for name, path in DOCS.items():
            for target in link_re.findall(self.text[name]):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                relative = target.split("#", 1)[0]
                resolved = (path.parent / relative).resolve()
                with self.subTest(document=name, target=target):
                    self.assertTrue(resolved.exists(), f"broken local link in {path}: {target}")
                    self.assertTrue(resolved.is_relative_to(ROOT.resolve()))

    def test_acquisition_controls_match_tracked_gui(self) -> None:
        technician = self.text["technician"]
        for control in (
            "Get Latest Prompt Kit",
            "Destination folder",
            "Browse...",
            "Open Prompt Kit website",
            "Open generator selection GUI",
            "Get Latest and Open",
            "Close",
        ):
            self.assertIn(control, self.acquisition_ps1)
            self.assertIn(control, technician)

    def test_documented_acquisition_files_match_implementation(self) -> None:
        technician = self.text["technician"]
        required = (
            r"web\prompt-kit\index.html",
            r"Run-PromptKitGenerator.cmd",
            r"Build-PromptKitWebsite.cmd",
            r"configs\prompt_kit\generators.v1.json",
            r"scripts\build_prompt_kit_registry.py",
        )
        for item in required:
            self.assertIn(item, self.acquisition_ps1)
            self.assertIn(item, technician)

    def test_failure_messages_are_documented(self) -> None:
        technician = self.text["technician"]
        messages = (
            "Windows PowerShell was not found.",
            "Git was not found. Install Git for Windows and try again.",
            "Python 3 was not found. Install Python 3 and select Add Python to PATH.",
            "The destination exists but is not a Git repository:",
            "The existing repository has an unexpected origin:",
            "The repository has local modifications or untracked files.",
            "Local main contains",
            "Required Prompt Kit file is missing:",
            "Generator manifest schema is missing or unsupported.",
            "Prompt Kit exact-output validation failed.",
        )
        for message in messages:
            self.assertIn(message, self.acquisition_ps1)
            self.assertIn(message, technician)

    def test_safety_and_rollback_are_explicit(self) -> None:
        for phrase in (
            "fast-forward-only",
            "Do not run `git reset`",
            "Do not use `git reset` or `git clean`",
            "does not store credentials",
            "Candidates/",
            "Active/",
            "rollback",
        ):
            self.assertIn(phrase.lower(), self.all_docs.lower())

        forbidden_commands = ("git reset --hard", "git clean -fd", "git push --force")
        for command in forbidden_commands:
            self.assertNotIn(command, self.all_docs)

    def test_platform_boundaries_are_documented(self) -> None:
        for phrase in (
            "Windows technician workstation",
            "Browser",
            "Linux or CI",
            "Administrator box",
            "Remote target machine",
        ):
            self.assertIn(phrase, self.all_docs)

    def test_documentation_does_not_claim_unrun_runtime_proof(self) -> None:
        for phrase in (
            "Windows field proof",
            "field acceptance",
            "do not prove Windows GUI",
            "does not replace a technician's Windows mouse test",
        ):
            self.assertIn(phrase.lower(), self.all_docs.lower())

    def test_examples_reference_tracked_entry_points(self) -> None:
        for path in (
            ACQUISITION_CMD,
            ACQUISITION_PS1,
            ROOT / "Run-PromptKitGenerator.cmd",
            ROOT / "Build-PromptKitWebsite.cmd",
            ROOT / "scripts" / "build_prompt_kit_registry.py",
            ROOT / "scripts" / "validate_harness.py",
            ROOT / "tests" / "test_harness_contract.py",
            ROOT / "tests" / "test_skill_prompt_registry.py",
            ROOT / "tests" / "test_prompt_kit_header_contract.py",
            GENERATOR_MANIFEST,
            ROOT / "web" / "prompt-kit" / "index.html",
        ):
            self.assertTrue(path.is_file(), f"documented entry point is missing: {path}")

    def test_no_person_specific_path_is_presented_as_universal(self) -> None:
        for forbidden in (
            r"C:\Users\Cheex",
            r"C:\Users\Richard",
            "rperez",
        ):
            self.assertNotIn(forbidden.lower(), self.all_docs.lower())
        self.assertIn(r"%USERPROFILE%\Desktop\dev\web-excel-repair-triage", self.all_docs)

    def test_each_tutorial_contains_operational_sections(self) -> None:
        required_by_document = {
            "technician": ("What you need", "Troubleshooting", "Safe rollback and recovery", "Operator proof checklist"),
            "generator": ("Generator GUI prerequisites", "Troubleshooting", "Rollback and recovery", "Proof checklist"),
            "administrator": ("Prerequisite verification on Windows", "Failure triage", "Rollback policy", "Release proof gate"),
        }
        for name, headings in required_by_document.items():
            for heading in headings:
                with self.subTest(document=name, heading=heading):
                    self.assertIn(f"## {heading}", self.text[name])


if __name__ == "__main__":
    unittest.main()
