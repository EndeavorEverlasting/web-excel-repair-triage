from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry


class GreenBranchIntegrationPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(
            (
                ROOT
                / "registry"
                / "prompts"
                / "actionable-next-step-policy.v1.json"
            ).read_text(encoding="utf-8")
        )
        cls.prompts = {
            prompt["id"]: prompt
            for prompt in build_prompt_kit_registry.load_prompt_registry()
        }

    def test_policy_defines_fail_closed_default_branch_merge_gate(self) -> None:
        self.assertEqual(
            self.policy["integration_marker"],
            "GREEN BRANCH INTEGRATION CONTRACT",
        )
        self.assertIn("main", self.policy["integration_target"])
        conditions = "\n".join(self.policy["green_merge_conditions"]).lower()
        for phrase in (
            "exact current head",
            "required repository checks",
            "owning harness validators",
            "dependencies",
            "blocking review",
            "merge authority",
        ):
            self.assertIn(phrase, conditions)

        exceptions = "\n".join(self.policy["merge_exceptions"]).lower()
        for phrase in (
            "user explicitly requested",
            "pending or failing",
            "head moved",
            "unrelated",
            "denies merge authority",
        ):
            self.assertIn(phrase, exceptions)

    def test_every_effective_prompt_encourages_same_run_default_branch_merge(self) -> None:
        marker = self.policy["integration_marker"]
        for prompt in self.prompts.values():
            with self.subTest(prompt=prompt["id"]):
                copy_content = str(prompt["copyContent"])
                next_step = str(prompt["nextStep"]).lower()
                self.assertIn(marker, copy_content)
                self.assertIn("merge it into the current default branch in the same run", next_step)
                self.assertIn("required checks", next_step)
                self.assertIn("owning harness validators", next_step)

    def test_p07_explicitly_supersedes_branch_only_legacy_completion(self) -> None:
        p07 = self.prompts["P07"]
        content = p07["copyContent"]
        self.assertEqual(p07["name"], "Repo Sprint Executor")
        self.assertIn("P07 MAINLINE CONVERGENCE OVERRIDE", content)
        self.assertIn("Any earlier legacy sentence", content)
        self.assertIn("Do the repo work. Commit it. Then stop.", content)
        self.assertIn("is superseded by this section", content)
        self.assertIn("must not create a feature branch merely because repository mutation is requested", content)
        self.assertIn("open pull request", content)
        self.assertIn("intermediate evidence only", content)
        self.assertIn("None is sufficient completion", content)
        self.assertIn("integration target", content)
        self.assertIn("pre/post default-branch SHA", content)
        self.assertIn("exact blocking gate", content)

    def test_green_pr_status_is_explicitly_not_a_terminal_action(self) -> None:
        forbidden = "\n".join(self.policy["forbidden_solo_actions"]).lower()
        self.assertIn("report that a pull request is green without merging it", forbidden)
        appendix = self.policy["copy_content_appendix"].lower()
        self.assertIn("do not merely report that it is green", appendix)
        self.assertIn("open pr, pushed feature branch, or green status is not a valid terminal state", appendix)
        self.assertIn("normal completion state", appendix)

    def test_new_branch_requires_evidence_that_existing_owner_cannot_carry_work(self) -> None:
        reuse = self.policy["existing_work_reuse"]
        rule = reuse["rule"].lower()
        self.assertIn("before creating a new branch or pull request", rule)
        self.assertIn("reuse, repair, update, retarget, integrate, or extend", rule)
        allowed = "\n".join(reuse["new_pr_allowed_when"]).lower()
        self.assertIn("no suitable existing owner exists", allowed)
        self.assertIn("scope isolation requires a distinct writer", allowed)


if __name__ == "__main__":
    unittest.main()
