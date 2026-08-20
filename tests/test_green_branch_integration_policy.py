from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry

POLICY_PATH = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
BASE_PROMPTS = ROOT / "docs" / "prompts.json"

EXPECTED_GREEN_MERGE_CONDITIONS = [
    "the exact current head is the head that was validated",
    "all required repository checks are passing",
    "the owning harness validators and focused validators are passing",
    "declared dependencies are satisfied or already included in the merge target",
    "no unresolved blocking review, merge conflict, branch-protection gate, or required approval remains",
    "the merge contains only reviewed owned or intentionally integrated scope",
    "the acting agent has repository merge authority and the user has not explicitly prohibited merge",
]
EXPECTED_MERGE_EXCEPTIONS = [
    "the user explicitly requested that the branch remain unmerged",
    "a required check, owning validator, dependency, review, conflict, branch-protection rule, or approval is pending or failing",
    "the branch head moved after the evidence used to declare it green",
    "the merge would include unrelated, unreviewed, unsafe, secret, private, or forbidden-scope work",
    "the repository or provider denies merge authority",
]


class GreenBranchIntegrationPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = build_prompt_kit_registry.load_actionability_policy()
        cls.prompts = {
            prompt["id"]: prompt
            for prompt in build_prompt_kit_registry.load_prompt_registry()
        }
        raw_prompts = json.loads(BASE_PROMPTS.read_text(encoding="utf-8"))
        cls.raw_p07 = next(prompt for prompt in raw_prompts if prompt["id"] == "P07")

    def test_policy_defines_structured_fail_closed_default_branch_merge_gate(self) -> None:
        self.assertEqual(
            self.policy["integration_marker"],
            "GREEN BRANCH INTEGRATION CONTRACT",
        )
        self.assertIn("main", self.policy["integration_target"])
        self.assertIsInstance(self.policy["green_merge_conditions"], list)
        self.assertIsInstance(self.policy["merge_exceptions"], list)
        self.assertEqual(
            self.policy["green_merge_conditions"],
            EXPECTED_GREEN_MERGE_CONDITIONS,
        )
        self.assertEqual(
            self.policy["merge_exceptions"],
            EXPECTED_MERGE_EXCEPTIONS,
        )
        self.assertEqual(
            len(self.policy["green_merge_conditions"]),
            len(set(self.policy["green_merge_conditions"])),
        )
        self.assertEqual(
            len(self.policy["merge_exceptions"]),
            len(set(self.policy["merge_exceptions"])),
        )

    def test_production_loader_rejects_malformed_integration_lists(self) -> None:
        original_policy_path = build_prompt_kit_registry.ACTIONABILITY_POLICY
        baseline = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        try:
            with tempfile.TemporaryDirectory() as tmp:
                bad_path = Path(tmp) / "actionability.json"
                build_prompt_kit_registry.ACTIONABILITY_POLICY = bad_path
                for field in ("green_merge_conditions", "merge_exceptions"):
                    with self.subTest(field=field, shape="not-list"):
                        payload = dict(baseline)
                        payload[field] = "not-a-list"
                        bad_path.write_text(json.dumps(payload), encoding="utf-8")
                        with self.assertRaisesRegex(SystemExit, field):
                            build_prompt_kit_registry.load_actionability_policy()
                    with self.subTest(field=field, shape="blank-entry"):
                        payload = dict(baseline)
                        payload[field] = [""]
                        bad_path.write_text(json.dumps(payload), encoding="utf-8")
                        with self.assertRaisesRegex(SystemExit, field):
                            build_prompt_kit_registry.load_actionability_policy()
        finally:
            build_prompt_kit_registry.ACTIONABILITY_POLICY = original_policy_path

    def test_raw_p07_is_mainline_first_without_policy_injection(self) -> None:
        content = self.raw_p07["copyContent"]
        self.assertEqual(self.raw_p07["name"], "Repo Sprint Executor")
        self.assertIn("MAINLINE CONVERGENCE", content)
        self.assertIn(
            "Do not create a new feature branch or pull request merely because repository work was requested",
            content,
        )
        self.assertIn("temporary execution/review lane", content)
        self.assertIn("merge the exact validated head", content)
        self.assertIn("verify the current default branch contains the intended change", content)
        self.assertNotIn("Do the repo work. Commit it. Then stop.", content)
        self.assertIn("integrated into the current default branch", self.raw_p07["expectedOutput"])
        self.assertIn("branch or PR alone is insufficient", self.raw_p07["proofGate"])

    def test_every_effective_prompt_encourages_same_run_default_branch_merge(self) -> None:
        marker = self.policy["integration_marker"]
        for prompt in self.prompts.values():
            with self.subTest(prompt=prompt["id"]):
                copy_content = str(prompt["copyContent"])
                next_step = str(prompt["nextStep"]).lower()
                self.assertIn(marker, copy_content)
                self.assertIn(
                    "merge it into the current default branch in the same run",
                    next_step,
                )
                self.assertIn("required checks", next_step)
                self.assertIn("owning harness validators", next_step)

    def test_effective_p07_preserves_explicit_mainline_completion(self) -> None:
        p07 = self.prompts["P07"]
        content = p07["copyContent"]
        self.assertEqual(p07["name"], "Repo Sprint Executor")
        self.assertIn("MAINLINE CONVERGENCE", content)
        self.assertIn("P07 MAINLINE CONVERGENCE OVERRIDE", content)
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
        self.assertIn(
            "open pr, pushed feature branch, or green status is not a valid terminal state",
            appendix,
        )
        self.assertIn("normal completion state", appendix)

    def test_new_branch_requires_evidence_that_existing_owner_cannot_carry_work(self) -> None:
        reuse = self.policy["existing_work_reuse"]
        rule = reuse["rule"].lower()
        self.assertIn("before creating a new branch or pull request", rule)
        self.assertIn("reuse, repair, update, retarget, or extend", rule)
        self.assertIn("integrate", rule)
        allowed = "\n".join(reuse["new_pr_allowed_when"]).lower()
        self.assertIn("no suitable existing owner exists", allowed)
        self.assertIn("scope isolation requires a distinct writer", allowed)


if __name__ == "__main__":
    unittest.main()
