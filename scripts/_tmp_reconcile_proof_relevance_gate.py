#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
GREEN_TEST = ROOT / "tests" / "test_green_branch_integration_policy.py"
ACTION_TEST = ROOT / "tests" / "test_actionable_prompt_registry.py"

GREEN_OLD = "the exact current head is the head that was validated"
GREEN_NEW = "the exact current head is the head that was validated, or intervening head movement is proven proof-irrelevant by an unchanged proof-relevance fingerprint"
EXC_OLD = "the branch head moved after the evidence used to declare it green"
EXC_NEW = "the branch head moved after the evidence used to declare it green and proof-relevant inputs changed or proof relevance cannot be established"
SUFFIX_OLD = "If the exact current head is the head that was validated, the owned branch or pull request is mergeable"
SUFFIX_NEW = "If the current head is the validated head, or intervening head movement is proven proof-irrelevant by an unchanged proof-relevance fingerprint, and the owned branch or pull request is mergeable"
FINGERPRINT_RULE = (
    "- PROOF-RELEVANCE FINGERPRINT: represent the proof inputs as a canonical ordered set of identity/revision pairs for the behavioral implementation, governing contracts and schemas, direct dependencies, launcher and validator, target/environment assumptions, and acceptance/proof inputs actually used. Persist that set in the proof, receipt, or ledger when a durable evidence owner exists; otherwise include it in the evidence-bearing closeout. Compare exact canonical entries: any added, removed, or changed entry invalidates the affected proof; repository HEAD movement with an unchanged set does not. If the fingerprint cannot be reconstructed or compared, freshness is UNKNOWN and the affected proof must be rerun or fail closed."
)


def require_replace(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"{label} anchor missing")
    return text.replace(old, new, 1)


def update_policy() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    policy["green_merge_conditions"] = [GREEN_NEW if item == GREEN_OLD else item for item in policy["green_merge_conditions"]]
    policy["merge_exceptions"] = [EXC_NEW if item == EXC_OLD else item for item in policy["merge_exceptions"]]
    if GREEN_NEW not in policy["green_merge_conditions"]:
        raise SystemExit("green merge condition not updated")
    if EXC_NEW not in policy["merge_exceptions"]:
        raise SystemExit("merge exception not updated")

    suffix = policy["next_step_suffix"]
    suffix = require_replace(suffix, SUFFIX_OLD, SUFFIX_NEW, "next-step merge gate")
    policy["next_step_suffix"] = suffix

    appendix = policy["copy_content_appendix"]
    if "PROOF-RELEVANCE FINGERPRINT:" not in appendix:
        anchor = "\n- A documentation, ledger, citation, timestamp, or proof-SHA-only mutation MUST NOT trigger another runtime proof"
        if anchor not in appendix:
            raise SystemExit("quiescence fingerprint insertion anchor missing")
        appendix = appendix.replace(anchor, "\n" + FINGERPRINT_RULE + anchor, 1)
    policy["copy_content_appendix"] = appendix
    POLICY.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def update_green_test() -> None:
    text = GREEN_TEST.read_text(encoding="utf-8")
    text = text.replace(f'    "{GREEN_OLD}",', f'    "{GREEN_NEW}",')
    text = text.replace(f'    "{EXC_OLD}",', f'    "{EXC_NEW}",')
    if "test_proof_irrelevant_head_movement_does_not_reopen_validation" not in text:
        anchor = "    def test_production_loader_rejects_malformed_integration_lists(self) -> None:\n"
        method = '''    def test_proof_irrelevant_head_movement_does_not_reopen_validation(self) -> None:\n        green = "\\n".join(self.policy["green_merge_conditions"])\n        exceptions = "\\n".join(self.policy["merge_exceptions"])\n        suffix = self.policy["next_step_suffix"]\n        appendix = self.policy["copy_content_appendix"]\n\n        self.assertIn("proof-irrelevant by an unchanged proof-relevance fingerprint", green)\n        self.assertNotIn("the exact current head is the head that was validated\\n", green + "\\n")\n        self.assertIn("proof-relevant inputs changed or proof relevance cannot be established", exceptions)\n        self.assertNotIn("the branch head moved after the evidence used to declare it green\\n", exceptions + "\\n")\n        self.assertIn("current head is the validated head, or intervening head movement is proven proof-irrelevant", suffix)\n        for phrase in (\n            "PROOF-RELEVANCE FINGERPRINT",\n            "canonical ordered set of identity/revision pairs",\n            "Persist that set in the proof, receipt, or ledger",\n            "any added, removed, or changed entry invalidates the affected proof",\n            "repository HEAD movement with an unchanged set does not",\n            "freshness is UNKNOWN",\n            "must be rerun or fail closed",\n        ):\n            self.assertIn(phrase, appendix)\n\n'''
        if anchor not in text:
            raise SystemExit("green-test insertion anchor missing")
        text = text.replace(anchor, method + anchor, 1)
    GREEN_TEST.write_text(text, encoding="utf-8")


def update_action_test() -> None:
    text = ACTION_TEST.read_text(encoding="utf-8")
    anchor = '            "proof-relevance fingerprint",\n'
    additions = (
        '            "PROOF-RELEVANCE FINGERPRINT",\n'
        '            "canonical ordered set of identity/revision pairs",\n'
        '            "Persist that set in the proof, receipt, or ledger",\n'
        '            "freshness is UNKNOWN",\n'
    )
    if '            "canonical ordered set of identity/revision pairs",\n' not in text:
        if anchor not in text:
            raise SystemExit("action-test fingerprint anchor missing")
        text = text.replace(anchor, anchor + additions, 1)
    ACTION_TEST.write_text(text, encoding="utf-8")


def main() -> int:
    update_policy()
    update_green_test()
    update_action_test()
    print("proof-relevance merge gate reconciled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
