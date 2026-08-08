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


if __name__ == "__main__":
    unittest.main()
