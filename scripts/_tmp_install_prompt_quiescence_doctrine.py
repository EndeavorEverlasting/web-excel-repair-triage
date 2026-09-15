#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
TEST = ROOT / "tests" / "test_actionable_prompt_registry.py"

SECTION = """NON-PROGRESS / QUIESCENCE CONTRACT
- Safe and executable is necessary but not sufficient for continuation. Remaining work must also be progress-bearing.
- Progress-bearing work must materially advance an acceptance criterion, proof state, implementation state, unresolved hypothesis, blocker, or required continuation artifact. Status narration, citation refresh, or rewriting the same blocker is not progress.
- Repository HEAD movement alone does not invalidate evidence. Revalidate only when a proof-relevant implementation, contract, schema, dependency, launcher, validator, environment assumption, or target changed.
- A documentation, ledger, citation, timestamp, or proof-SHA-only mutation MUST NOT trigger another runtime proof merely because that mutation changed repository HEAD. Never create a commit or PR whose only purpose is to replace an otherwise-valid proof citation with the newest repository tip.
- When the decisive remaining gate requires an unavailable environment, credential, physical machine, user action, review, or external event, persist the blocker once and enter a quiescent BLOCKED state. Do not manufacture repository mutations to remain active.
- Repeating the same blocker against an unchanged proof-relevance fingerprint is not a new evidence pass. Two consecutive materially identical blocker observations require a non-progress review before further mutation; if no new behavioral hypothesis or changed proof-relevant input exists, stop.
- A worker must not create work merely to satisfy a continuation rule. Exhaustive compute applies to useful hypothesis and evidence space, not bookkeeping churn."""


def update_policy() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    appendix = policy["copy_content_appendix"]

    if "NON-PROGRESS / QUIESCENCE CONTRACT" not in appendix:
        anchor = "\n\nEND-STATE CONTRACT HORIZON"
        if anchor not in appendix:
            raise SystemExit("quiescence insertion anchor missing")
        appendix = appendix.replace(anchor, f"\n\n{SECTION}{anchor}", 1)

    old_closeout = (
        "- SAFE & EXECUTABLE means work remains and the agent must continue. "
        "It is incompatible with `none; no safe actionable work remains`."
    )
    new_closeout = (
        "- SAFE & EXECUTABLE means progress-bearing work remains and the agent must continue. "
        "A merely runnable bookkeeping action is not SAFE & EXECUTABLE for continuation. "
        "It is incompatible with `none; no safe actionable work remains`."
    )
    if old_closeout in appendix:
        appendix = appendix.replace(old_closeout, new_closeout, 1)
    elif new_closeout not in appendix:
        raise SystemExit("SAFE & EXECUTABLE closeout sentence drifted")

    old_compute = (
        "Continue while another practical safe experiment can materially reduce uncertainty, "
        "falsify the current conclusion, cover an acceptance condition, or close an evidence gap."
    )
    new_compute = (
        "Continue while another practical safe, progress-bearing experiment can materially reduce uncertainty, "
        "falsify the current conclusion, cover an acceptance condition, or close an evidence gap."
    )
    if old_compute in appendix:
        appendix = appendix.replace(old_compute, new_compute, 1)
    elif new_compute not in appendix:
        raise SystemExit("compute continuation sentence drifted")

    old_exhaustive = (
        "while another practical pass can close a required contract, test or falsify a live hypothesis, "
        "cover an acceptance criterion, reduce material uncertainty, expose a regression, or strengthen proof."
    )
    new_exhaustive = (
        "while another practical progress-bearing pass can close a required contract, test or falsify a live hypothesis, "
        "cover an acceptance criterion, reduce material uncertainty, expose a regression, or strengthen proof."
    )
    if old_exhaustive in appendix:
        appendix = appendix.replace(old_exhaustive, new_exhaustive, 1)
    elif new_exhaustive not in appendix:
        raise SystemExit("exhaustive-compute continuation sentence drifted")

    policy["copy_content_appendix"] = appendix

    suffix_addition = (
        " Safe/executable is necessary but not sufficient for continuation: the next action must be progress-bearing. "
        "Repository HEAD movement alone does not invalidate proof when proof-relevant inputs are unchanged. "
        "If the same external blocker recurs against an unchanged proof-relevance fingerprint, persist it once and quiesce rather than creating citation-only, ledger-only, or bookkeeping work."
    )
    if "the next action must be progress-bearing" not in policy["next_step_suffix"]:
        policy["next_step_suffix"] = policy["next_step_suffix"].rstrip() + suffix_addition

    additions = [
        "create a commit or pull request whose only purpose is to refresh an otherwise-valid proof citation, timestamp, ledger tip, or proof SHA to the newest repository head",
        "repeat the same external blocker or runtime proof against an unchanged proof-relevance fingerprint without a new behavioral hypothesis or changed proof-relevant input",
    ]
    for item in additions:
        if item not in policy["forbidden_solo_actions"]:
            policy["forbidden_solo_actions"].append(item)

    POLICY.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def update_test() -> None:
    text = TEST.read_text(encoding="utf-8")
    if "def test_non_progress_quiescence_contract_prevents_proof_treadmills" in text:
        return

    anchor = "    def test_existing_work_and_pr_reuse_is_global_policy(self) -> None:\n"
    if anchor not in text:
        raise SystemExit("focused-test insertion anchor missing")

    method = '''    def test_non_progress_quiescence_contract_prevents_proof_treadmills(self) -> None:\n        appendix = self.policy["copy_content_appendix"]\n        for phrase in (\n            "NON-PROGRESS / QUIESCENCE CONTRACT",\n            "Safe and executable is necessary but not sufficient for continuation",\n            "Remaining work must also be progress-bearing",\n            "Repository HEAD movement alone does not invalidate evidence",\n            "proof-relevant implementation, contract, schema, dependency, launcher, validator, environment assumption, or target",\n            "documentation, ledger, citation, timestamp, or proof-SHA-only mutation",\n            "MUST NOT trigger another runtime proof",\n            "quiescent BLOCKED state",\n            "proof-relevance fingerprint",\n            "Two consecutive materially identical blocker observations",\n            "must not create work merely to satisfy a continuation rule",\n            "not bookkeeping churn",\n        ):\n            self.assertIn(phrase, appendix)\n\n        suffix = self.policy["next_step_suffix"]\n        for phrase in (\n            "the next action must be progress-bearing",\n            "Repository HEAD movement alone does not invalidate proof",\n            "unchanged proof-relevance fingerprint",\n            "quiesce rather than creating citation-only, ledger-only, or bookkeeping work",\n        ):\n            self.assertIn(phrase, suffix)\n\n        forbidden = "\\n".join(self.policy["forbidden_solo_actions"])\n        self.assertIn("only purpose is to refresh an otherwise-valid proof citation", forbidden)\n        self.assertIn("repeat the same external blocker or runtime proof", forbidden)\n\n        by_id = {prompt["id"]: prompt for prompt in self.prompts}\n        for prompt_id in ("P07", "P08", "P100"):\n            with self.subTest(prompt=prompt_id):\n                self.assertIn("NON-PROGRESS / QUIESCENCE CONTRACT", by_id[prompt_id]["copyContent"])\n                self.assertIn("progress-bearing", by_id[prompt_id]["nextStep"])\n\n'''
    TEST.write_text(text.replace(anchor, method + anchor, 1), encoding="utf-8")


def main() -> int:
    update_policy()
    update_test()
    print("prompt-quiescence doctrine staged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
