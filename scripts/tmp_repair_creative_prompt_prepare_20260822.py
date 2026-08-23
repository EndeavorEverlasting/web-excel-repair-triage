#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TEST = ROOT / "tests" / "test_spec_architecture_prompt_registry.py"

payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
by_id = {prompt["id"]: prompt for prompt in payload["prompts"]}

p79 = by_id["P79"]
p79["copyContent"] = """ADD OR STRENGTHEN ONE OR MANY PROMPT KIT PROMPTS FROM THE RELEVANT CHAT CONTEXT. THE CONTEXT IMMEDIATELY ABOVE THIS INSTRUCTION IS THE ANCHOR, NOT THE CONTEXT BOUNDARY. EXECUTE THE REPO WORK; DO NOT ASK ME TO RESTATE CONTEXT THAT IS ALREADY ACCESSIBLE.

CANONICAL REPO
`EndeavorEverlasting/web-excel-repair-triage`

MISSION
Turn the request plus earlier relevant context into the smallest complete contribution set: zero or more STRENGTHEN actions and zero, one, or many ADD actions. Preserve user/source truth, create useful working context without masquerading it as user truth, strengthen owners before new identities, use deterministic helper mechanics, validate, and converge the exact green authorized result to main.

0. CONTEXT AUTHORITY
- USER / SOURCE-BOUND CONTEXT: supported facts, terminology, preferences, constraints, accepted/rejected wording, examples, files, and repository contracts. Preserve these.
- AGENT-GENERATED WORKING CONTEXT: owner maps, hypotheses, decompositions, candidate interpretations, and reversible assumptions created to make work executable. Generate this proactively when useful, keep it explicitly working/inferred, verify exact facts from deterministic sources, and revise it when contradicted. Never invent user history, preferences, approvals, exact values, or source claims.

1. FRESH FLOOR + PASS 1
Refresh remote/default-branch and overlapping Prompt Kit work before mutation. Traverse earlier accessible context for the same use case. Build:
`insight | authority/context source | current owner | action | proof`
with STRENGTHEN / ADD / ALREADY COVERED / OUT OF SCOPE. No material insight may silently disappear.

2. OWNER MAP BEFORE IDS
Search the combined Prompt Kit for an exact, adjacent, or materially overlapping prompt. Compare trigger, mission, scope, context contract, and closure—not title alone.
- STRENGTHEN when an owner has the core job but lacks compatible context, failure, iteration, proof, or usability behavior.
- ADD only for genuinely missing bounded behavior with a distinct trigger and closure.

3. IMPLEMENT THE WHOLE SET
For STRENGTHEN, edit canonical source plus the closest focused semantic assertion.
For ADD, use the closest existing registry/profile. Inspect routing once if unclear. Draft semantic fields only; Do NOT set id, seq, or copySheet.
Run:
`python scripts/prompt_registry_ops.py add --input <draft.json> --registry <existing_registry_id>`
Let the helper allocate identity, reject duplicates, inject shared policy, rebuild, prove parity, and roll back registry/site writes if validation fails.

Multiple prompts are first-class. Prepare drafts as one conceptual batch, but execute helper mutations SERIALly so every add observes current identity after the prior mutation. Never preassign batch P## values. Repair a failed add from current helper truth.

4. COMPLEMENT WITHOUT FABRICATION
Preserve explicit user intent, then add only compatible utility that makes the workflow more executable, reusable, testable, or failure-resistant.

5. P07-STYLE ITERATION AND PROGRESS
Use bounded IMPLEMENT -> VALIDATE -> INSPECT -> CRITIQUE -> IMPROVE passes. First green is evidence, not completion. After evidence-changing passes, report terse `CHANGED | PROVED | NEXT` and continue. Inspect effective prompt behavior and the diff; repair valid failures/review findings without weakening acceptance; preserve separately owned work.

6. PASS 2 + FOCUSED PROOF
Traverse relevant context again in the opposite direction for missed `also`, `another`, corrections, examples, prototype/live/regression needs, context distinctions, or neighboring owners. Run the focused semantic assertion, helper validation, applicable language/order/discovery checks, generated-site `--check`, and `git diff --check`. Prove strengthened prompts retain role and new prompts remain distinct.

7. MAINLINE CONVERGENCE IS PART OF COMPLETION
Refresh main before final proof; reconcile material movement and rerun affected checks. A commit, push, open PR, review-ready state, or green CI is intermediate evidence. When gates and authority permit, merge the exact green authorized head into current main and verify main contains the source. If blocked, name and advance the exact integration gate.

FAIL-CLOSED
Do not guess identities, bypass helper parity, weaken validators, fabricate context, or make the operator a context courier/test runner. Do not fall back to loading the entire Prompt Kit architecture when one owner/helper surface answers the question.

DELIVER
Report ledger, context-authority decisions, strengthened IDs, helper receipts, focused proof, prompt count/parity, commit/PR/merge, resulting main SHA, and exact blocker/next action."""

p82 = by_id["P82"]
start = "\n\nCREATIVE PROTOTYPE MODE"
end = "\n\n4. PRESERVE THE LAST KNOWN-GOOD STATE"
if start in p82["copyContent"]:
    before, rest = p82["copyContent"].split(start, 1)
    _, after = rest.split(end, 1)
    concise_creative = """

CREATIVE PROTOTYPE MODE
For creative artifacts, keep the user's brief, references, accepted/rejected examples, and explicit constraints authoritative; generated concepts and rationale are revisable working context. When uncertainty warrants divergence, make 2-4 materially distinct variants rather than cosmetic swaps. Critique every candidate against the same brief and record KEEP / COMBINE / REVISE / DISCARD. Use available creation tools directly when safe; ask the user only for a focused taste fork after concrete candidates exist. Final creative proof is fit-to-brief plus deliverable integrity; automated checks do not equal human acceptance."""
    p82["copyContent"] = before + concise_creative + end + after

REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

text = TEST.read_text(encoding="utf-8")
text = text.replace(
    'payload = json.loads(REGISTRY.read_text(encoding="utf-8"))',
    'payload = json.loads(RAW_REGISTRY.read_text(encoding="utf-8"))',
)
text = text.replace(
    'self.assertIn("CREATIVE PROTOTYPE", plan["copyContent"])',
    'self.assertIn("HAND OFF TO CREATIVE PROTOTYPING", plan["copyContent"])',
)
TEST.write_text(text, encoding="utf-8")

if len(p79["copyContent"]) >= 5000:
    raise SystemExit(f"P79 raw copyContent exceeds focused source budget: {len(p79['copyContent'])}")
if len(p82["copyContent"]) >= 8000:
    raise SystemExit(f"P82 raw copyContent exceeds source budget: {len(p82['copyContent'])}")
print(f"repaired source budgets: P79={len(p79['copyContent'])}, P82={len(p82['copyContent'])}")
