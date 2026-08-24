from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

policy_path = ROOT / "registry/prompts/actionable-next-step-policy.v1.json"
policy = json.loads(policy_path.read_text(encoding="utf-8"))

policy["next_step_suffix"] = (
    "Do not leave the next step empty or generic: identify the first executable, dependency-aware action that advances or consumes the canonical artifact or proof; PR, status, branch, or log inspection alone is invalid when safe executable work remains. "
    "Before claiming completion, reconstruct the original requested/owned scope and disposition every material item as PROVEN DONE, SAFE & EXECUTABLE, BLOCKED, UNSAFE, or OUT OF SCOPE. Any SAFE & EXECUTABLE item disproves `none; no safe actionable work remains` and must be advanced. UNSAFE requires the exact action, concrete hazard and evidence, consequence, and safer alternative or gate; missing tools, credentials, approval, or access is BLOCKED rather than unsafe, and uncertainty or inconvenience alone is not danger. OUT OF SCOPE requires an explicit scope boundary. "
    "If the exact current head is the head that was validated, the owned branch or pull request is mergeable, all required checks and owning harness validators are green, dependencies are satisfied, no blocking review, conflict, branch-protection, or required-approval gate remains, the acting agent has merge authority, and the user has not prohibited merge, merge it into the current default branch in the same run using a repository-accepted merge method; do not stop at PR-open or green-status reporting unless a named external gate actually blocks integration. "
    "Before stopping, emit a compact evidence-bearing closeout: what is completed/proven, changed surfaces and produced artifacts, commands/examples actually verified when applicable, remaining gaps/risks/blockers, unproven runtime or field steps, review/reconciliation state when relevant, proof ceiling, integration state, and the first executable continuation. Spend words on decisions, evidence, uncertainty, and continuation rather than narrating tool use or repeating the plan. "
    "After an integration SHA has been proven, a later default-branch advance is not a failure by itself: verify that the proven merge or commit is an ancestor of the refreshed default branch and rerun only proof affected by intervening changes; do not require the refreshed default-branch head to equal the historical integration SHA."
)

marker = "OPERATIONAL CLOSEOUT / GAP-RISK CONTRACT\n"
appendix = policy["copy_content_appendix"]
if marker not in appendix:
    raise SystemExit("closeout marker missing from policy appendix")
prefix = appendix.split(marker, 1)[0]
closeout = marker + """- Before any legitimate stop, report these fields explicitly: COMPLETED / PROVEN; REMAINING GAPS; RISKS; BLOCKERS; PROOF CEILING; INTEGRATION STATE; NEXT ACTION / NEXT STEPS.
- EVIDENCE-BEARING CLOSEOUT: treat the final report as a compact evidence packet, not a narration of tool use. Spend words on decisions, evidence, uncertainty, and continuation. Required sections may be one line when empty, but use `none — <evidence or reason>` rather than silently omitting them.
- Under COMPLETED / PROVEN, name the applicable CHANGED SURFACES / ARTIFACTS and the strongest current evidence for each: files/help/code changed; commands or examples actually verified; generated artifacts, screenshots, logs, receipts, or reports produced; validation/checks observed; and commit/PR/merge/mainline identity. Do not list a command under COMMANDS / EXAMPLES VERIFIED unless it actually ran or its execution is independently evidenced.
- Separate UNPROVEN RUNTIME / FIELD STEPS from ordinary remaining implementation gaps. Repository/static/CI proof must not silently become browser/device/production/operator acceptance. Put inaccessible live proof under PROOF CEILING and name the exact observation or operator gate still required.
- When review comments, CI findings, failed checks, or an earlier design materially changed the work, include REVIEW / RECONCILIATION: finding -> repair/disposition -> rerun evidence. A stale or superseded finding may be closed with current evidence; it may not disappear silently.
- For repository work, INTEGRATION STATE should include the target branch, pre/post default-branch SHA when available, PR/merge state, and containment/content proof that the intended change is on the refreshed default branch.
- Reconstruct the original request, owned scope, explicit constraints, acceptance criteria, and proof requirements before declaring scope exhausted. Disposition every material item exactly once as PROVEN DONE, SAFE & EXECUTABLE, BLOCKED, UNSAFE, or OUT OF SCOPE.
- SAFE & EXECUTABLE means work remains and the agent must continue. It is incompatible with `none; no safe actionable work remains`.
- BLOCKED means the item remains in scope but cannot advance because of a named dependency, permission, credential, review, protected runtime, user-only decision, or unavailable external system. Missing access is not evidence that the work is unsafe.
- UNSAFE is a narrow evidence-bearing classification. Name the exact action that would be unsafe, the concrete hazard, supporting evidence, likely consequence, and the safer alternative or gate. Do not relabel uncertainty, inconvenience, time cost, lack of tools, missing credentials, or ordinary review requirements as danger.
- OUT OF SCOPE requires an explicit scope boundary from the request, governing contract, or forbidden scope. Do not move unfinished requested work out of scope merely to close the task.
- A gap, risk, or blocker must name the affected scope, evidence, consequence, and the action that reduces or closes it. Do not hide known uncertainty behind `looks good`, `green`, `ready`, or an empty section.
- NEXT ACTION must be the first executable continuation, with owner, dependency, exact command or operator action, expected artifact/proof, and completion gate. If several actions remain, order them by dependency and keep executing agent-capable steps instead of merely listing them.
- If continuation will cross into another agent/chat and useful work remains, append HANDOFF as one self-contained copy-paste continuation containing the canonical source/repo, exact branch/PR/SHA or artifact identity, proven floor, remaining gap/blocker, forbidden scope, and first executable action. Do not add a ceremonial handoff when no continuation remains.
- Use `none; no safe actionable work remains` only when every material requested-scope item has a supported terminal disposition, no SAFE & EXECUTABLE item remains, the owned acceptance criteria are proven, authorized integration is complete or explicitly blocked, and remaining gaps/risks are closed, explicitly accepted by scope, BLOCKED, UNSAFE with evidence, or OUT OF SCOPE with a cited boundary.
"""
policy["copy_content_appendix"] = prefix + closeout
policy_path.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

ledger_path = ROOT / "registry/prompts/repository-work-ledger-prompts.v1.json"
ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
p83 = next(p for p in ledger["prompts"] if p["id"] == "P83")

p83["useWhen"] = (
    "Another agent, chat, handoff, branch, PR, report, artifact, or implementation claims work is complete or partially complete—including `none; no safe actionable work remains`—and you need a fresh agent to verify the real state, audit requested-scope exhaustion, repair errors, advance unfinished work, expand useful in-scope coverage, and report what changed without repeatedly asking the user to mediate."
)
p83["expectedOutput"] = (
    "An evidence-backed continuation that distinguishes verified facts from inherited claims, reconstructs the original requested scope, dispositions every material item as PROVEN DONE / SAFE & EXECUTABLE / BLOCKED / UNSAFE / OUT OF SCOPE, closes safe in-scope gaps through repeated verify/repair/advance/revalidate passes, preserves stronger correct work, integrates authorized green work when appropriate, and reports progress, corrections, remaining gaps, risks, blockers, proof ceiling, integration state, and the first executable continuation."
)
p83["nextStep"] = (
    "Resolve the exact prior work and current repository floor, reconstruct the original requested scope and acceptance criteria, build a scope-item/evidence/disposition matrix, execute the highest-value SAFE & EXECUTABLE item, validate it, critique the new evidence, integrate any independently verified green slice, refresh main/evidence, and repeat until every material scope item has a supported terminal disposition or a genuine external gate remains. Report the current gap/risk/blocker and then execute the first safe dependency-aware continuation; do not stop at status-only reporting while agent-capable work remains."
)
extra_proof = (
    " Scope-exhaustion proof additionally requires every material requested-scope item to be classified as PROVEN DONE, SAFE & EXECUTABLE, BLOCKED, UNSAFE, or OUT OF SCOPE; any SAFE & EXECUTABLE item invalidates a terminal `none` claim; UNSAFE names the exact action, concrete hazard/evidence/consequence, and safer alternative or gate; BLOCKED is not mislabeled unsafe merely because tools, credentials, access, approval, or a protected runtime are missing; and OUT OF SCOPE cites an explicit boundary rather than convenience."
)
if extra_proof not in p83["proofGate"]:
    p83["proofGate"] = p83["proofGate"].rstrip() + extra_proof

section = """

SCOPE-EXHAUSTION AUDIT — CHALLENGE `NONE`
If prior work says `none; no safe actionable work remains`, reconstruct the original requested scope and disposition every material item as PROVEN DONE, SAFE & EXECUTABLE, BLOCKED, UNSAFE, or OUT OF SCOPE. Any SAFE & EXECUTABLE item disproves closure and must be advanced. UNSAFE requires the exact action, concrete hazard/evidence/consequence, and safer alternative or gate. Missing tools, credentials, approval, or access is BLOCKED—not unsafe; uncertainty or inconvenience alone is not danger. OUT OF SCOPE requires an explicit boundary.
"""
if "SCOPE-EXHAUSTION AUDIT — CHALLENGE `NONE`" not in p83["copyContent"]:
    anchor = "\n\nSTOP ONLY AT THE REAL FIXED POINT"
    if anchor not in p83["copyContent"]:
        raise SystemExit("P83 stop-condition anchor not found")
    p83["copyContent"] = p83["copyContent"].replace(anchor, section + anchor, 1)

for keyword in (
    "no safe actionable work remains",
    "scope exhaustion",
    "premature closeout",
    "what is unsafe",
    "unfinished requested scope",
):
    if keyword not in p83["keywords"]:
        p83["keywords"].append(keyword)

if len(p83["copyContent"]) >= 8000:
    raise SystemExit(f"P83 anti-bloat ceiling exceeded: {len(p83['copyContent'])}")
ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

test_path = ROOT / "tests/test_operational_closeout_contract.py"
text = test_path.read_text(encoding="utf-8")

# Count both the nested closeout marker and the primary shared-policy marker.
count_line = "                self.assertEqual(content.count(MARKER), 1)\n"
if count_line in text and "content.count(self.policy[\"marker\"])" not in text:
    text = text.replace(
        count_line,
        count_line + "                self.assertEqual(content.count(self.policy[\"marker\"]), 1)\n",
        1,
    )

if "def test_scope_exhaustion_requires_supported_residual_classification" not in text:
    insertion = '''\n    def test_scope_exhaustion_requires_supported_residual_classification(self) -> None:\n        appendix = self.policy["copy_content_appendix"]\n        for phrase in (\n            "Reconstruct the original request, owned scope",\n            "PROVEN DONE, SAFE & EXECUTABLE, BLOCKED, UNSAFE, or OUT OF SCOPE",\n            "SAFE & EXECUTABLE means work remains",\n            "Missing access is not evidence that the work is unsafe",\n            "UNSAFE is a narrow evidence-bearing classification",\n            "OUT OF SCOPE requires an explicit scope boundary",\n            "Do not move unfinished requested work out of scope",\n            "no SAFE & EXECUTABLE item remains",\n        ):\n            self.assertIn(phrase, appendix)\n\n        p83 = self.ledger["P83"]\n        for phrase in (\n            "SCOPE-EXHAUSTION AUDIT — CHALLENGE `NONE`",\n            "Any SAFE & EXECUTABLE item disproves closure",\n            "Missing tools, credentials, approval, or access is BLOCKED—not unsafe",\n            "OUT OF SCOPE requires an explicit boundary",\n        ):\n            self.assertIn(phrase, p83["copyContent"])\n        self.assertIn("no safe actionable work remains", p83["keywords"])\n        self.assertIn("scope exhaustion", p83["keywords"])\n        self.assertLess(len(p83["copyContent"]), 8000)\n\n'''
    anchor = "    def test_live_cert_domain_law_requires_actionable_closeout(self) -> None:\n"
    if anchor not in text:
        raise SystemExit("operational closeout test insertion anchor missing")
    text = text.replace(anchor, insertion + anchor, 1)

test_path.write_text(text, encoding="utf-8")

print(json.dumps({
    "p83_raw_size": len(p83["copyContent"]),
    "scope_exhaustion_owner": "P83",
    "shared_owner": policy["policy_id"],
}, indent=2))
