from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE = ROOT / "AGENTS.md"


class GovernanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = GOVERNANCE.read_text(encoding="utf-8")

    def test_canonical_governance_is_universal_and_bounded(self) -> None:
        self.assertTrue(self.text.startswith("# Agent Governance Contract"))
        self.assertIn("single repository governance authority", self.text)
        self.assertLessEqual(len(self.text), 5200)

    def test_required_operating_principles_are_explicit(self) -> None:
        for principle in (
            "Evidence before action",
            "Floor before furniture",
            "Bounded sprints",
            "One writer per branch",
            "Reuse before replacing",
            "No completion without proof",
        ):
            self.assertIn(principle, self.text)

    def test_instruction_precedence_is_ordered(self) -> None:
        section = self._section("## 2. Instruction precedence", "## 3.")
        expected = (
            "Platform, security, legal, and repository-owner instructions.",
            "This governance contract",
            "Task-specific prompts and sprint instructions.",
            "Generic agent defaults.",
        )
        positions = [section.index(item) for item in expected]
        self.assertEqual(positions, sorted(positions))

    def test_sprint_and_completion_contracts_remain_binding(self) -> None:
        declaration = self._section("## 3. Mandatory sprint declaration", "## 4.")
        for phrase in (
            "repository and branch or worktree",
            "owned scope and forbidden scope",
            "validation commands and their order",
            "proof ceiling",
        ):
            self.assertIn(phrase, declaration)
        completion = self._section("## 4. Completion standard", "## 5.")
        for phrase in (
            "exact files changed",
            "commit SHA",
            "push state",
            "one exact next command",
            "fetch without force",
            "isolated worktree",
            "propagate nonzero exit codes",
            "must not execute production by default",
        ):
            self.assertIn(phrase, completion)

    def test_progressive_disclosure_is_governed(self) -> None:
        section = self._section("## 6. Progressive disclosure", "## 7.")
        self.assertIn("harness/CONTEXT.md", section)
        self.assertIn("Do **not** preload", section)
        self.assertIn("Escalate context only", section)

    def test_domain_law_is_incorporated_without_eager_loading(self) -> None:
        for path in (
            "harness/specs/operator-delivery.md",
            "harness/specs/prompt-operations.md",
            "harness/specs/billing-artifact-safety.md",
        ):
            self.assertIn(path, self.text)
            self.assertTrue((ROOT / path).is_file(), path)

    def test_operator_delivery_rules_survived_factoring(self) -> None:
        text = (ROOT / "harness/specs/operator-delivery.md").read_text(encoding="utf-8")
        for phrase in (
            "mouse-accessible CMD entry point",
            "fetch, and fast-forward only",
            "Live evidence is separate from CI",
            "Remote-branch green proof is not target-runtime or production proof",
            "HARs, credentials, private workbooks",
        ):
            self.assertIn(phrase, text)

    def test_prompt_operations_rules_survived_factoring(self) -> None:
        text = (ROOT / "harness/specs/prompt-operations.md").read_text(encoding="utf-8")
        for phrase in (
            "never edit generated HTML as the source of truth",
            "Sequence identity is append-only",
            "python scripts/evaluate_prompt_language.py --summary",
            "effective combined registry rather than a sample",
            "Parallel execution does not weaken ownership or proof",
        ):
            self.assertIn(phrase, text)

    def test_billing_and_input_rules_survived_factoring(self) -> None:
        text = (ROOT / "harness/specs/billing-artifact-safety.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "Candidates/` and `Active/` are read-only operator inputs",
            "Never set `--output` equal to `--input`",
            "Roster Log to Admin Sheet",
            "Roster Log to Task Tracker",
            "Task Tracker to Roster Log",
            "Do not fabricate hours",
        ):
            self.assertIn(phrase, text)

    def test_numbered_governance_sections_are_unique(self) -> None:
        numbers = re.findall(r"^## (\d+)\.", self.text, flags=re.MULTILINE)
        self.assertEqual(numbers, [str(number) for number in range(1, 7)])

    def _section(self, start: str, next_prefix: str) -> str:
        self.assertIn(start, self.text)
        tail = self.text.split(start, 1)[1]
        marker = re.search(rf"^{re.escape(next_prefix)}", tail, flags=re.MULTILINE)
        return tail[: marker.start()] if marker else tail


if __name__ == "__main__":
    unittest.main()
