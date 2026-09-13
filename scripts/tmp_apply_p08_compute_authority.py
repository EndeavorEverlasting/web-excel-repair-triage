#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

POLICY = Path("registry/prompts/actionable-next-step-policy.v1.json")
P08_TEST = Path("tests/test_prompt_registry_expansion_regression_design_teach.py")
POLICY_TEST = Path("tests/test_actionable_prompt_registry.py")

COMPUTE_MARKER = "COMPUTE AUTHORITY / SCOPE-BOUNDARY CONTRACT"
HORIZON_MARKER = "END-STATE CONTRACT HORIZON"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"{label}: anchor missing")
    return text.replace(old, new, 1)


def update_policy() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    suffix = (
        " A bounded sprint limits mutation scope, not useful compute volume: when broad compute/iteration authority is granted, "
        "continue safe evidence-reducing passes to a fixed point rather than stopping at the first pass. Before terminal closeout, "
        "emit the end-state contract horizon for the whole requested outcome, including required contracts owned outside the current "
        "slice without treating that visibility as mutation authority."
    )
    if "A bounded sprint limits mutation scope, not useful compute volume" not in policy["next_step_suffix"]:
        policy["next_step_suffix"] = policy["next_step_suffix"].rstrip() + suffix

    section = """
COMPUTE AUTHORITY / SCOPE-BOUNDARY CONTRACT
- A bounded sprint limits mutation ownership and blast radius; it does not imply minimal reasoning, one attempt, one test case, or the earliest passing stop.
- When the operator or execution environment grants broad compute/iteration authority, use as much safe available compute as is materially useful inside authorized surfaces: repeated evidence passes, variants, falsification, diagnostics, instrumentation, controlled retries, cross-checks, and independent validation. Prefer useful evidence volume over token-conserving minimalism.
- Treat the first PASS as a checkpoint, not an automatic stop signal. Continue while another practical safe experiment can materially reduce uncertainty, falsify the current conclusion, cover an acceptance condition, or close an evidence gap. Stop at an evidence-backed fixed point or exact blocker, not an arbitrary attempt count.
- Bounded waits/retries mean each wait, retry, mutation, and external action is bounded and observable; they do not impose a one-pass ceiling on the overall investigation.
- Broad compute authority never expands safety or mutation authority: it does not authorize unbounded spend, destructive or personal-data mutation, secret exposure, unrelated feature work, bypassing required approval, monopolizing shared resources, or crossing a forbidden scope.
- If deeper proof requires another canonical owner, invoke or route that owner when safely executable and then return to the current proof/acceptance gate. Routing is not terminal merely because the current bounded slice passed.

END-STATE CONTRACT HORIZON
- Before terminal closeout, identify the contracts that define the whole requested outcome, including contracts whose canonical owner or proof surface sits outside the bounded sprint that just ran. Local scope limits mutation; it does not erase downstream obligations from the completion picture.
- At minimum consider each applicable contract family: implementation/behavior; regression/protected behavior; validation/evidence; integration/default-branch; deployment/environment; live runtime; operator/user acceptance; safety/privacy/data; durability/automation/observability; documentation/runbook/handoff.
- For every applicable contract, report: CONTRACT; canonical OWNER; STATUS as PROVEN, SAFE & EXECUTABLE, BLOCKED, UNPROVEN/UNKNOWN, NOT APPLICABLE, or OUT OF CURRENT SCOPE; strongest EVIDENCE; required NEXT TRANSITION; and the exact ACTION/GATE that closes or advances it.
- The contract horizon is broader than mutation authority. Do not modify unrelated or separately owned surfaces merely because they appear in the horizon, but do not call the whole outcome complete while a required contract remains unproven.
- Distinguish `LOCAL PROMPT CONTRACT CLOSED` from `WHOLE OUTCOME CONTRACT CLOSED`. A local pass may close the current prompt while deployment, runtime, acceptance, durability, or another required contract remains open.
- If a required contract outside the current slice is SAFE & EXECUTABLE now and an authorized canonical owner can advance it, continue into that successor owner instead of stopping at the local pass. If it is blocked, name the exact external/user-only gate and the action that advances it.
- Include a compact `CONTRACT HORIZON` table or equivalent structured block in the final response whenever more than one material completion contract applies.
""".strip()

    appendix = policy["copy_content_appendix"].rstrip()
    if COMPUTE_MARKER not in appendix:
        appendix += "\n\n" + section
    policy["copy_content_appendix"] = appendix
    POLICY.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def update_p08_regression() -> None:
    text = P08_TEST.read_text(encoding="utf-8")
    anchor = '        self.assertIn("After any runtime repair, rerun both paths", p08)\n'
    addition = '''        for phrase in (\n            "COMPUTE AUTHORITY / SCOPE-BOUNDARY CONTRACT",\n            "A bounded sprint limits mutation ownership and blast radius",\n            "Treat the first PASS as a checkpoint, not an automatic stop signal",\n            "END-STATE CONTRACT HORIZON",\n            "The contract horizon is broader than mutation authority",\n            "LOCAL PROMPT CONTRACT CLOSED",\n            "WHOLE OUTCOME CONTRACT CLOSED",\n            "CONTRACT HORIZON",\n        ):\n            self.assertIn(phrase, p08)\n        self.assertIn(\n            "A bounded sprint limits mutation scope, not useful compute volume",\n            self.full["P08"]["nextStep"],\n        )\n'''
    text = replace_once(text, anchor, anchor + addition, "P08 regression")
    P08_TEST.write_text(text, encoding="utf-8")


def update_policy_regression() -> None:
    text = POLICY_TEST.read_text(encoding="utf-8")
    anchor = "    def test_existing_work_and_pr_reuse_is_global_policy(self) -> None:\n"
    method = '''    def test_compute_authority_and_end_state_contract_horizon_are_global_policy(self) -> None:\n        appendix = self.policy["copy_content_appendix"]\n        for phrase in (\n            "COMPUTE AUTHORITY / SCOPE-BOUNDARY CONTRACT",\n            "bounded sprint limits mutation ownership and blast radius",\n            "use as much safe available compute as is materially useful",\n            "first PASS as a checkpoint",\n            "Broad compute authority never expands safety or mutation authority",\n            "END-STATE CONTRACT HORIZON",\n            "implementation/behavior",\n            "operator/user acceptance",\n            "durability/automation/observability",\n            "The contract horizon is broader than mutation authority",\n            "LOCAL PROMPT CONTRACT CLOSED",\n            "WHOLE OUTCOME CONTRACT CLOSED",\n            "CONTRACT HORIZON",\n        ):\n            self.assertIn(phrase, appendix)\n\n        self.assertIn(\n            "A bounded sprint limits mutation scope, not useful compute volume",\n            self.policy["next_step_suffix"],\n        )\n        by_id = {prompt["id"]: prompt for prompt in self.prompts}\n        self.assertIn("COMPUTE AUTHORITY / SCOPE-BOUNDARY CONTRACT", by_id["P08"]["copyContent"])\n        self.assertIn("END-STATE CONTRACT HORIZON", by_id["P08"]["copyContent"])\n\n'''
    text = replace_once(text, anchor, method + anchor, "shared policy regression")
    POLICY_TEST.write_text(text, encoding="utf-8")


def main() -> int:
    update_policy()
    update_p08_regression()
    update_policy_regression()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
