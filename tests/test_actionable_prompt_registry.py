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


class ActionablePromptRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy_path = (
            REPO_ROOT
            / "registry"
            / "prompts"
            / "actionable-next-step-policy.v1.json"
        )
        cls.policy = json.loads(cls.policy_path.read_text(encoding="utf-8"))
        cls.prompts = build_prompt_kit_registry.load_prompt_registry()

    def test_policy_is_tracked_and_complete(self) -> None:
        self.assertTrue(self.policy_path.is_file())
        self.assertEqual(
            self.policy["schema_version"], "prompt-next-action-policy/v1"
        )
        self.assertEqual(
            self.policy["policy_id"], "actionable-next-command/v1"
        )
        self.assertEqual(
            self.policy["allowed_none_value"],
            "none; no safe actionable work remains",
        )
        for phrase in (
            "ACTIONABLE NEXT COMMAND AND NEXT STEPS CONTRACT",
            "Do not leave NEXT COMMAND, NEXT ACTION, NEXT STEP, or NEXT STEPS blank",
            "Advance the work into the next useful unproven state",
            "opening or reopening a PR",
            "fetches without force",
            "verifies the exact branch and commit",
            "preserves dirty or separately owned work",
            "runs the owning validator, build, or launcher",
            "resolves the canonical artifact",
            "opens or prints that artifact",
            "propagates every nonzero exit code",
            "When no artifact exists yet",
            "A NEXT STEPS list must be ordered, dependency-aware, owner-assigned, executable, and specific",
            "none; no safe actionable work remains",
        ):
            self.assertIn(phrase, self.policy["copy_content_appendix"])

    def test_existing_work_and_pr_reuse_is_global_policy(self) -> None:
        reuse = self.policy["existing_work_reuse"]
        self.assertIn(
            "Before creating a new branch or pull request",
            reuse["rule"],
        )
        self.assertIn(
            "current, open, and recent pull requests, branches, worktrees, and commits",
            reuse["rule"],
        )
        self.assertIn(
            "Reuse, repair, update, retarget, or extend the existing owner",
            reuse["rule"],
        )
        allowed = "\n".join(reuse["new_pr_allowed_when"])
        for phrase in (
            "no suitable existing owner exists",
            "unsafe, irreparably stale, or intentionally superseded",
            "scope isolation requires a distinct writer",
        ):
            self.assertIn(phrase, allowed)
        self.assertIn("preserve every unique useful commit", reuse["preservation_rule"])
        self.assertIn("disposition", reuse["disposition_evidence"].lower())
        self.assertIn("where any unique useful work was preserved", reuse["disposition_evidence"])

    def test_combined_registry_applies_policy_to_every_prompt(self) -> None:
        marker = self.policy["marker"]
        suffix = self.policy["next_step_suffix"]
        policy_id = self.policy["policy_id"]
        self.assertGreater(len(self.prompts), 1)

        for prompt in self.prompts:
            with self.subTest(prompt=prompt["id"]):
                self.assertEqual(prompt["actionabilityPolicy"], policy_id)
                self.assertIn(marker, prompt["copyContent"])
                self.assertIn(suffix, prompt["nextStep"])
                self.assertTrue(prompt["nextStep"].strip())
                self.assertTrue(prompt["copyContent"].strip())

    def test_general_build_prompt_receives_the_actionability_contract(self) -> None:
        by_id = {prompt["id"]: prompt for prompt in self.prompts}
        p07 = by_id["P07"]
        self.assertEqual(p07["name"], "Repo Sprint Executor")
        self.assertIn(self.policy["marker"], p07["copyContent"])
        self.assertIn("first executable", p07["copyContent"])
        self.assertIn("canonical artifact", p07["copyContent"])
        self.assertIn("PR, status, branch, or log inspection alone is invalid", p07["nextStep"])

    def test_p50_executes_directory_gate_without_absorbing_p07(self) -> None:
        raw_prompts = json.loads(
            (REPO_ROOT / "docs" / "prompts.json").read_text(encoding="utf-8")
        )
        raw_p50 = next(prompt for prompt in raw_prompts if prompt["id"] == "P50")
        effective_p50 = {prompt["id"]: prompt for prompt in self.prompts}["P50"]

        self.assertEqual(raw_p50["name"], "Directory-First Repository Command Guard")
        self.assertEqual(raw_p50["type"], "ANALYZE + DIRECTORY")
        self.assertEqual(raw_p50["class"], "STANDARD AI / LOCAL-FIRST REPOSITORY INTAKE")
        self.assertEqual(raw_p50["copySheet"], "P50_COPY_SAFE")
        self.assertEqual(raw_p50["category"], "standard")

        for phrase in (
            "EXECUTE THE DIRECTORY GATE YOURSELF",
            "Do not merely print directory or verification commands",
            "execute the first safe repository-backed step that advances `xyz_task`",
            "asking for a genuinely user-only fact",
            "a plausible path is not proof",
        ):
            self.assertIn(phrase, raw_p50["copyContent"])

        self.assertNotIn(self.policy["marker"], raw_p50["copyContent"])
        self.assertIn(self.policy["marker"], effective_p50["copyContent"])
        for donor_role in (
            "ITERATIVE SPRINT FIXED-POINT",
            "MAINLINE CONVERGENCE",
            "merge the exact validated head",
        ):
            self.assertNotIn(donor_role, raw_p50["copyContent"])
        self.assertLessEqual(len(raw_p50["copyContent"]), 2200)

    def test_p34_preserves_terminal_evidence_without_hanging_automation(self) -> None:
        raw_prompts = json.loads(
            (REPO_ROOT / "docs" / "prompts.json").read_text(encoding="utf-8")
        )
        raw_p34 = next(prompt for prompt in raw_prompts if prompt["id"] == "P34")
        effective_p34 = {prompt["id"]: prompt for prompt in self.prompts}["P34"]

        self.assertEqual(raw_p34["name"], "GNHF Technician Experience")
        self.assertEqual(raw_p34["type"], "ENABLEMENT + BUILD")
        self.assertEqual(raw_p34["class"], "GNHF / TECHNICIAN UX")
        self.assertEqual(raw_p34["copySheet"], "P34_COPY_SAFE")
        self.assertEqual(raw_p34["category"], "gnhf")

        for phrase in (
            "TERMINAL SURVIVAL + EVIDENCE PERSISTENCE",
            "keep the terminal/window open after BOTH success and failure",
            "OUTER HUMAN LAUNCHER",
            "Noninteractive execution must fail nonzero rather than waiting for input",
            "real exit status",
            "durable log path",
            "noninteractive runs never hang",
            "PowerShell or Bash launcher",
        ):
            self.assertIn(phrase, raw_p34["copyContent"])

        self.assertIn("spawned/double-click", raw_p34["inspectFirst"])
        self.assertIn("original exit status is preserved", raw_p34["proofGate"])
        self.assertIn("terminal stays open", raw_p34["keywords"])
        self.assertIn("persistent logs", raw_p34["keywords"])
        self.assertNotIn(self.policy["marker"], raw_p34["copyContent"])
        self.assertIn(self.policy["marker"], effective_p34["copyContent"])
        self.assertNotIn("REMOTE FRESHNESS / BRANCH FLOOR CONTRACT", raw_p34["copyContent"])
        self.assertLessEqual(len(raw_p34["copyContent"]), 4200)

    def test_policy_rejects_an_empty_next_step(self) -> None:
        sample = {
            "id": "PX",
            "nextStep": "   ",
            "copyContent": "Perform the bounded work.",
        }
        with self.assertRaisesRegex(SystemExit, "empty nextStep"):
            build_prompt_kit_registry.apply_actionability_policy(sample, self.policy)

    def test_policy_rejects_empty_copy_content(self) -> None:
        sample = {
            "id": "PX",
            "nextStep": "Run the owning validator.",
            "copyContent": "   ",
        }
        with self.assertRaisesRegex(SystemExit, "empty copyContent"):
            build_prompt_kit_registry.apply_actionability_policy(sample, self.policy)

    def test_policy_application_is_idempotent(self) -> None:
        sample = {
            "id": "PX",
            "nextStep": "Build and open the canonical artifact.",
            "copyContent": "Perform the bounded work.",
        }
        once = build_prompt_kit_registry.apply_actionability_policy(sample, self.policy)
        twice = build_prompt_kit_registry.apply_actionability_policy(once, self.policy)
        self.assertEqual(once, twice)
        self.assertEqual(once["copyContent"].count(self.policy["marker"]), 1)
        self.assertEqual(
            once["nextStep"].count(self.policy["next_step_suffix"]), 1
        )

    def test_forbidden_solo_actions_cover_lazy_completion_patterns(self) -> None:
        joined = "\n".join(self.policy["forbidden_solo_actions"]).lower()
        for phrase in (
            "pull request",
            "suitable existing owner",
            "reused, repaired, updated, retargeted, or extended",
            "status",
            "branches or commits",
            "logs",
            "wait or continue later",
            "ask for permission",
            "repeat an artifact path",
            "generic verbs",
            "owner, command, dependency, artifact, and proof gate",
        ):
            self.assertIn(phrase, joined)

    def test_execution_brief_contract_is_global_for_operational_prompts(self) -> None:
        marker = "EXECUTION BRIEF / SOURCE / DONE / SELF-CHECK CONTRACT"
        appendix = self.policy["copy_content_appendix"]
        for phrase in (
            marker,
            "ROLE: Operate as the senior practitioner and execution owner",
            "WHERE TO LOOK: Start with explicit source, repository, context, plan, artifact, or path inputs",
            "DEFINITION OF DONE: Before mutation",
            "SELF-CHECK: Before any completion claim",
            "verify every material factual or quantitative claim",
            "Flag unsupported or stale claims",
        ):
            self.assertIn(phrase, appendix)
        for prompt in self.prompts:
            with self.subTest(prompt=prompt["id"]):
                self.assertIn(marker, prompt["copyContent"])

    def test_p07_carries_direct_execution_brief_for_raw_consumers(self) -> None:
        raw_prompts = json.loads((REPO_ROOT / "docs" / "prompts.json").read_text(encoding="utf-8"))
        p07 = next(prompt for prompt in raw_prompts if prompt["id"] == "P07")
        for phrase in (
            "EXECUTION BRIEF / EVIDENCE BINDING",
            "senior repository execution engineer/coordinator",
            "WHERE TO LOOK: Start with `Context or plan path`",
            "DEFINITION OF DONE: Before mutation",
            "SELF-CHECK: Before claiming completion",
            "Unsupported items are UNKNOWN or blockers",
        ):
            self.assertIn(phrase, p07["copyContent"])
        self.assertIn("current/open/recent overlapping branches and PRs", p07["inspectFirst"])
        self.assertIn("fixed point", p07["proofGate"])

if __name__ == "__main__":
    unittest.main()
