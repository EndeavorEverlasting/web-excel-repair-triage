from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE = ROOT / "AGENTS.md"


class GovernanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = GOVERNANCE.read_text(encoding="utf-8")

    def test_canonical_governance_is_universal_bounded_and_tracked(self) -> None:
        self.assertTrue(GOVERNANCE.is_file())
        self.assertTrue(self.text.startswith("# Agent Governance Contract"))
        self.assertIn("single repository governance authority", self.text)
        self.assertLessEqual(len(self.text), 5200)
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "AGENTS.md"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(tracked.returncode, 0, tracked.stderr or tracked.stdout)

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
            "This governance contract.",
            "Task-specific prompts and sprint instructions.",
            "Generic agent defaults.",
        )
        positions = [section.index(item) for item in expected]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("Binding domain specs are subordinate implementation law", section)

    def test_sprint_and_completion_contracts_remain_binding(self) -> None:
        declaration = self._section("## 3. Mandatory sprint declaration", "## 4.")
        self.assertIn("Every writing sprint must state", declaration)
        for phrase in (
            "repository and branch or worktree",
            "lane and mission",
            "owned scope and forbidden scope",
            "expected artifacts",
            "validation commands and their order",
            "proof ceiling",
        ):
            self.assertIn(phrase, declaration)
        completion = self._section("## 4. Completion standard", "## 5.")
        self.assertIn("A task is complete only when", completion)
        for phrase in (
            "exact files changed",
            "validations run",
            "commit SHA",
            "push state",
            "PR/integration state",
            "one exact next command",
            "fetch without force",
            "isolated worktree",
            "propagate nonzero exit codes",
            "must not execute production by default",
        ):
            self.assertIn(phrase, completion)

    def test_overlapping_work_requires_fresh_ancestry_proof(self) -> None:
        section = self._section("## 3. Mandatory sprint declaration", "## 4.")
        for phrase in (
            "Before modifying or integrating overlapping prior work",
            "refresh the default branch",
            "Prove each required integrated slice is an ancestor",
            "git merge-base --is-ancestor <required-sha> <refreshed-default>",
            "still materially present using current content plus its owning validator",
            "Ancestry alone cannot prove current content after a revert",
            "Any failed check requires reconciliation",
            "fresh proof before mutation or integration",
        ):
            self.assertIn(phrase, section)

    def test_forbidden_behaviors_remain_explicit(self) -> None:
        section = self._section("## 5. Safety and mutation boundaries", "## 6.")
        for phrase in (
            "acknowledgment without mutation",
            "plans without execution",
            "summaries without proof",
            "completion claims without running checks",
            "secret or credential exposure",
        ):
            self.assertIn(phrase, section)

    def test_repository_identity_keeps_triage_spreadsheet_first(self) -> None:
        section = self._section(
            "## 6. Repository identity and product boundary", "## 7."
        )
        for phrase in (
            "core product domain is **spreadsheet intelligence**",
            "Web Excel compatibility, billing",
            "roster/time evidence",
            "began here as a spreadsheet",
        ):
            self.assertIn(phrase, section)

    def test_prompt_kit_separation_is_explicit_and_transition_safe(self) -> None:
        section = self._section(
            "## 6. Repository identity and product boundary", "## 7."
        )
        for phrase in (
            "dedicated repository under `UnderDeskDev`",
            "not yet named or created",
            "must not invent its name",
            "Prompt Kit sources here remain operationally authoritative",
            "must not be silently moved",
            "source, pin, mirror, package, link to, or consume Prompt Kit releases",
            "must not become a competing Prompt Kit authority",
            "cross-repo dependencies explicit and versioned",
        ):
            self.assertIn(phrase, section)

    def test_progressive_disclosure_is_governed(self) -> None:
        section = self._section("## 7. Progressive disclosure", "## 8.")
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
        self.assertEqual(numbers, [str(number) for number in range(1, 8)])

    def _section(self, start: str, next_prefix: str) -> str:
        self.assertIn(start, self.text)
        tail = self.text.split(start, 1)[1]
        marker = re.search(rf"^{re.escape(next_prefix)}", tail, flags=re.MULTILINE)
        return tail[: marker.start()] if marker else tail


if __name__ == "__main__":
    unittest.main()
