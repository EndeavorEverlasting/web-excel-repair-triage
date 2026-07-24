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

    def test_next_command_consumes_the_canonical_latest_artifact(self) -> None:
        section = self._section("## 4. Completion standard", "## 5.")
        for phrase in (
            "advance the operator from reported evidence to the next useful, unproven state",
            "consume, validate, launch, open, or otherwise exercise the work product",
            "merely reopens a PR",
            "not a valid next command",
            "fetch without force and identify the exact branch and commit",
            "preserve a dirty or separately owned primary checkout",
            "isolated worktree",
            "run the exact validation, build, or launcher",
            "open or print the canonical latest artifact",
            "artifact registry, manifest, builder, workflow, or operator documentation",
            "Do not guess from a generic filename",
            "search for an arbitrary `index.html`",
            "propagate failures and the final exit code",
            "must not execute production by default",
            "website, workbook, report, package, installer, binary, launcher, rendered documentation, test report",
            "`none; cleanup complete`",
            "PR review or merge is the actual blocking gate",
        ):
            self.assertIn(phrase, section)

    def test_forbidden_behaviors_are_enforced(self) -> None:
        section = self._section("## 5. Forbidden behaviors", "## 6.")
        for phrase in (
            "acknowledge without making the authorized mutation",
            "return a plan when implementation is authorized and safe",
            "claim completion without running the stated checks",
            "expose secrets",
            "force-push",
            "delete branches, worktrees, PRs, or unique commits before preservation proof",
            "offer a PR-opening, status-only, branch-listing, or log-view command as the sole next action",
            "guess the latest artifact from a generic filename",
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

    def test_prompt_language_audit_skill_capability_and_evals_are_governed(self) -> None:
        section = self._section("## 9. Collaborator prompt contribution governance", "## 10.")
        for phrase in (
            "one canonical prompt-language-audit skill",
            "one machine-readable prompt-language-audit capability",
            "one evaluation harness that passes through every prompt",
            "combined canonical base and extension registries",
            "A sampled review, policy-marker check, or audit of selected prompts is insufficient",
            "Every registered prompt must receive an explicit `pass`, `repair`, `defer`, or `not_applicable` disposition",
            "a skipped prompt must fail the audit",
            "reusable judgment and repair procedure",
            "prompt metadata and complete copy-safe content",
            "next commands, next-step lists, artifact references, validation language, ownership language, dependency language, and proof ceiling",
            "explicit machine-readable inputs and outputs",
            "complete prompt inventory, one disposition per prompt, stable rule identifiers, severity",
            "Audit-only and repair modes must be distinct",
            "repair mode must mutate canonical sources rather than generated HTML",
            "positive fixtures, negative fixtures, and mutation tests",
            "empty, placeholder, optional-only, or non-executable next commands and next steps",
            "PR-opening, status-only, branch-listing, log-viewing, waiting, monitoring, or permission-seeking",
            "without an owner, exact target, dependency, command or operation, and completion gate",
            "missing dirty-worktree preservation, validator, builder, launcher, artifact resolution",
            "require the operator or technician to reconstruct a workflow from command fragments",
            "contradictions between owned scope, forbidden scope, expected artifacts, validation, proof claims, and the proposed next action",
            "stale generated output, incomplete registry coverage, duplicate policy application, and non-idempotent regeneration",
            "disposition count equals that total",
            "all findings are repaired or explicitly deferred with an owner and blocking reason",
            "canonical generated surface is rebuilt, exact parity passes, patch hygiene passes",
            "They may not exist only as prose inside a prompt",
            "this governance-only sprint must not implement them",
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

    def test_neuron_monthly_task_distribution_doctrine_is_enforced(self) -> None:
        section = self._section(
            "### Neuron Track Hours monthly task-distribution doctrine", "## 12."
        )
        for phrase in (
            "Roster/attendance is the hours source of truth",
            "Device counts and device capacity are separate from labor hours",
            "Configuration and Deployment are distinct activities",
            "one dominant primary workstream",
            "Complimentary work may describe concurrent work but must not create additional hours",
            "Do not expose internal task percentages",
            "month-specific rule pack",
            "must not be silently carried into another month",
            "July 2026 rule pack",
            "60% Configuration / 40% other-work allocation",
            "reasonableness guardrail, not permission to overwrite stronger date-specific evidence",
            "one full Client Correspondence / Coordination day per week",
            "usually Thursday",
            "July 2",
            "July 23",
            "PM / Operational Control is real work but not a catch-all",
            "PM, client, and ticket work must not be mechanically spread across technicians",
            "July 3 is a holiday",
            "Alejandro Perales has no scheduled project hours on July 24",
            "Historical review language must not imply correction",
            "Executive Summary and the current NTH main sheet",
            "Semantic colors must correspond to the actual activity type",
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
