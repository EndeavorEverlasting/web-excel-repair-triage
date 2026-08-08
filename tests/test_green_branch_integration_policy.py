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
    def setUp(self) -> None:
        self.policy = json.loads(
            (
                ROOT
                / "registry"
                / "prompts"
                / "actionable-next-step-policy.v1.json"
            ).read_text(encoding="utf-8")
        )

    def test_policy_defines_fail_closed_green_merge_gate(self) -> None:
        self.assertEqual(
            self.policy["integration_marker"],
            "GREEN BRANCH INTEGRATION CONTRACT",
        )
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

    def test_every_effective_prompt_encourages_same_run_green_merge(self) -> None:
        prompts = build_prompt_kit_registry.load_prompt_registry()
        self.assertGreater(len(prompts), 0)
        marker = self.policy["integration_marker"]
        for prompt in prompts:
            with self.subTest(prompt=prompt["id"]):
                copy_content = str(prompt["copyContent"])
                next_step = str(prompt["nextStep"]).lower()
                self.assertIn(marker, copy_content)
                self.assertIn("merge it in the same run", next_step)
                self.assertIn("required checks", next_step)
                self.assertIn("owning harness validators", next_step)
                self.assertIn("green", next_step)

    def test_green_pr_status_is_explicitly_not_a_terminal_action(self) -> None:
        forbidden = "\n".join(self.policy["forbidden_solo_actions"]).lower()
        self.assertIn("report that a pull request is green without merging it", forbidden)
        appendix = self.policy["copy_content_appendix"].lower()
        self.assertIn("do not merely report that it is green", appendix)
        self.assertIn("bounded implementation scope limits what may be changed", appendix)

    def test_harness_workflows_own_green_integration(self) -> None:
        payload = json.loads(
            (ROOT / "harness" / "workflows.v1.json").read_text(encoding="utf-8")
        )
        workflows = {item["id"]: item for item in payload["workflows"]}
        pr_floor = workflows["pr-floor-integration"]
        self.assertIn("ready to integrate", pr_floor["trigger"].lower())
        self.assertIn(
            "merge execution for exact validated green heads",
            pr_floor["owned_scope"],
        )
        self.assertIn("merge in dependency order in the same run", pr_floor["failure_policy"].lower())

        for workflow_id in (
            "prompt-kit-change",
            "harness-infrastructure",
            "artifact-engine-change",
            "prompt-language-audit",
            "skill-evaluation",
        ):
            with self.subTest(workflow=workflow_id):
                owned = workflows[workflow_id]["owned_scope"]
                self.assertIn("integration of the exact validated owned PR head", owned)

    def test_harness_skills_do_not_stop_at_green_pr_handoff(self) -> None:
        prompt_skill = (
            ROOT / ".ai" / "skills" / "prompt-language-audit" / "SKILL.md"
        ).read_text(encoding="utf-8")
        harness_skill = (
            ROOT / ".ai" / "skills" / "harness-infrastructure-maintenance" / "SKILL.md"
        ).read_text(encoding="utf-8")
        for content in (prompt_skill, harness_skill):
            lowered = content.lower()
            self.assertIn("merge it in the same run", lowered)
            self.assertIn("exact validated", lowered)
            self.assertIn("required checks", lowered)
            self.assertIn("owning", lowered)


if __name__ == "__main__":
    unittest.main()
