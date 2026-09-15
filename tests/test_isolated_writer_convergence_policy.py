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

POLICY = ROOT / "registry/prompts/actionable-next-step-policy.v1.json"
MARKER = "ISOLATED WRITER / CONVERGENCE CONTRACT"

class IsolatedWriterConvergencePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))
        cls.prompts = build_prompt_kit_registry.load_prompt_registry()

    def test_policy_owns_writer_isolation_and_convergence(self) -> None:
        self.assertEqual(self.policy["isolation_marker"], MARKER)
        contract = self.policy["writer_isolation"]
        self.assertEqual(contract["marker"], MARKER)
        self.assertIn("worktree", contract["preferred_lane"].lower())
        self.assertIn("isolated", contract["fallback_lane"].lower())
        self.assertIn("dependency order", contract["local_convergence_rule"])
        self.assertIn("local convergence", contract["remote_only_rule"].lower())
        self.assertIn("unique commits", contract["cleanup_rule"].lower())

    def test_compiled_contract_covers_writer_safety_lifecycle(self) -> None:
        appendix = self.policy["copy_content_appendix"]
        for phrase in (
            MARKER,
            "each independent writer one isolated lane",
            "Never reuse or modify another writer's branch/worktree/workspace",
            "Git worktrees do not automatically isolate shared ports, databases, caches, lockfiles",
            "The first finisher",
            "must not reset, clean, delete, repurpose, overwrite, or merge-away unfinished sibling work",
            "CONVERGE LOCALLY BEFORE REMOTE DEFAULT",
            "integrate completed lanes in dependency order",
            "rerun the combined owning validators/build/tests",
            "provider-only or remote execution environment",
            "local convergence is unavailable",
            "Cleanup is last",
            "no unique unmerged commits, untracked artifacts, evidence, or operator-owned work",
        ):
            self.assertIn(phrase, appendix)

    def test_every_effective_prompt_inherits_contract_exactly_once(self) -> None:
        self.assertGreater(len(self.prompts), 1)
        for prompt in self.prompts:
            with self.subTest(prompt=prompt["id"]):
                self.assertEqual(prompt["copyContent"].count(MARKER), 1)

    def test_p07_inherits_contract_without_new_prompt_identity(self) -> None:
        by_id = {item["id"]: item for item in self.prompts}
        self.assertIn(MARKER, by_id["P07"]["copyContent"])
        self.assertIn(MARKER, by_id["P07"]["nextStep"])

    def test_reference_document_records_precedent_and_delta(self) -> None:
        text = (ROOT / "docs/PROMPT_KIT_ISOLATED_WRITER_CONVERGENCE.md").read_text(encoding="utf-8")
        for phrase in (
            "Michael Shimeles",
            "new-feature/SKILL.md",
            "Completed lanes converge in dependency order",
            "Provider-only / remote execution",
            "Why shared policy, not a new prompt",
        ):
            self.assertIn(phrase, text)

if __name__ == "__main__":
    unittest.main()
