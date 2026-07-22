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

    def test_canonical_governance_file_exists(self) -> None:
        self.assertTrue(GOVERNANCE.is_file())
        self.assertTrue(self.text.startswith("# Agent Governance Contract"))
        self.assertIn("single repository governance authority", self.text)

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

    def test_sprint_declaration_and_completion_fields_are_required(self) -> None:
        declaration = self._section("## 3. Mandatory sprint declaration", "## 4.")
        for item in (
            "repository and branch or worktree",
            "lane and mission",
            "owned scope and forbidden scope",
            "expected artifacts",
            "validation commands and their order",
            "proof ceiling",
        ):
            self.assertIn(item, declaration)

        completion = self._section("## 4. Completion standard", "## 5.")
        for item in (
            "exact files changed",
            "validation commands actually run",
            "commit SHA",
            "push state",
            "PR URL and state",
            "one exact next command",
        ):
            self.assertIn(item, completion)

    def test_forbidden_behaviors_are_enforced(self) -> None:
        section = self._section("## 5. Forbidden behaviors", "## 6.")
        for phrase in (
            "acknowledge without making the authorized mutation",
            "return a plan when implementation is authorized and safe",
            "claim completion without running the stated checks",
            "expose secrets",
            "force-push",
            "delete branches, worktrees, PRs, or unique commits before preservation proof",
        ):
            self.assertIn(phrase, section)

    def test_technician_clone_or_update_surface_is_governed(self) -> None:
        section = self._section("## 7. Technician acquisition and update surface", "## 8.")
        for phrase in (
            "mouse-accessible Windows CMD entry point",
            "repository is absent, clone",
            "fetch and fast-forward",
            "refuse to reset, overwrite, or discard dirty or divergent local work",
            "open the current Prompt Kit website or generator selection GUI only after",
            "presented through a GUI rather than command-line questions",
        ):
            self.assertIn(phrase, section)

    def test_local_and_remote_live_cert_topologies_are_governed(self) -> None:
        section = self._section("## 8. Live certification execution topology", "## 9.")
        for phrase in (
            "Local live certification remains a supported execution topology",
            "repository-owned launcher, script, validator, or exact bounded command",
            "identify the repository, commit, target, phase, expected artifacts, and proof ceiling",
            "run a dry run first when the operation can mutate a target",
            "propagate nonzero exit codes and name the failed phase",
            "write only non-sensitive logs, receipts, and reports to repository-approved output locations",
            "distinguish process start, command acknowledgment, observed behavior, local runtime proof, and production proof",
            "Remote-branch live certification remains a supported execution topology",
            "create or reuse one isolated branch owned by the cert lane",
            "commit the implementation, generated output, validators, and safe evidence",
            "push normally and report the exact branch and commit SHA",
            "copy-paste pull-and-test snippet",
            "fetch without force",
            "pin the exact commit SHA",
            "preserve a dirty primary checkout",
            "run the exact validator or test",
            "propagate its exit code",
            "must not execute production by default",
            "refuse to publish secrets, credentials, private evidence, protected inputs, or unsafe production artifacts",
            "Remote branch proof is not local or target-runtime proof",
        ):
            self.assertIn(phrase, section)

    def test_collaborator_prompt_contribution_is_governed(self) -> None:
        section = self._section("## 9. Collaborator prompt contribution governance", "## 10.")
        for phrase in (
            "canonical prompt registry source",
            "never by editing generated HTML directly",
            "inspect existing governance, prompt IDs and sequences, registry extensions, builders, schemas, skills, capabilities, triggers, validators",
            "a unique identifier and sequence",
            "a clear name, type, class, deterministic use condition, and keywords",
            "owned scope, forbidden scope, expected artifacts, validation order, and proof ceiling",
            "complete copy-safe prompt content",
            "focused tests that reject duplicate identity, incomplete records, stale generated output, and ownership drift",
            "reusable prompt-contribution skill",
            "prompt-contribution capability",
            "deterministic trigger",
            "skills describe reusable workflow guidance",
            "capabilities expose reusable operations",
            "triggers route deterministic conditions",
            "The live-cert prompt must support both local and remote-branch",
            "canonical source changes, focused validation, deterministic regeneration, Git diff review, commit, push, and PR evidence",
            "validated for exact parity",
        ):
            self.assertIn(phrase, section)

    def test_prompt_panels_and_chats_share_parallel_execution_contract(self) -> None:
        section = self._section(
            "## 10. Prompt panels, chats, and parallel execution", "## 11."
        )
        for phrase in (
            "A prompt panel is a copyable transport container",
            "A chat is the execution instance",
            "functionally equivalent to one independently schedulable execution unit",
            "Parallelism may be expressed as multiple panels in one parallel group",
            "one panel goes into one new chat",
            "Every panel must be self-contained",
            "The same dependencies, proof gates, lane ownership, branch and worktree isolation",
            "Different panel titles do not prove that concurrent writes are safe",
            "collision risks and the single owner for every shared surface",
            "must be serialized or assigned to one explicit writer",
            "General build prompts, including P07",
            "Parallel execution does not lower proof requirements",
            "final convergence unit",
        ):
            self.assertIn(phrase, section)

    def test_existing_domain_and_source_rules_remain_present(self) -> None:
        for phrase in (
            "Roster Log to Admin Sheet",
            "Roster Log to Task Tracker",
            "Task Tracker to Roster Log",
            "Candidates/` and `Active/` are read-only operator inputs",
            "Never set `--output` equal to `--input`",
        ):
            self.assertIn(phrase, self.text)

    def test_numbered_governance_sections_are_unique(self) -> None:
        numbers = re.findall(r"^## (\d+)\.", self.text, flags=re.MULTILINE)
        self.assertEqual(numbers, [str(number) for number in range(1, 13)])

    def _section(self, start: str, next_prefix: str) -> str:
        self.assertIn(start, self.text)
        tail = self.text.split(start, 1)[1]
        marker = re.search(rf"^{re.escape(next_prefix)}", tail, flags=re.MULTILINE)
        return tail[: marker.start()] if marker else tail


if __name__ == "__main__":
    unittest.main()
