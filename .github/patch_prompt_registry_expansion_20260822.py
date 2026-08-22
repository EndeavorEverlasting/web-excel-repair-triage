from __future__ import annotations

from pathlib import Path

path = Path(__file__).with_name("tmp_prompt_registry_expansion_20260822.py")
text = path.read_text(encoding="utf-8")
start = 'p79["copyContent"] = """'
end = '"""\nif len(p79["copyContent"]) >= 5000:'
left = text.index(start) + len(start)
right = text.index(end, left)
compact = r'''ADD OR STRENGTHEN PROMPT KIT PROMPTS FROM THE RELEVANT CHAT CONTEXT. THE CONTEXT IMMEDIATELY ABOVE THIS INSTRUCTION IS THE ANCHOR, NOT THE CONTEXT BOUNDARY. EXECUTE THE REPO WORK; DO NOT ASK ME TO RESTATE CONTEXT THAT IS ALREADY ACCESSIBLE.

CANONICAL REPO
`EndeavorEverlasting/web-excel-repair-triage`

MISSION
Turn the current request plus earlier relevant chat decisions into the smallest complete Prompt Kit contribution set. Recover approved/rejected wording, examples, corrections, constraints, related ideas, and prior definitions that materially affect the request. Strengthen canonical owners before creating identities. Use the repo helper for genuinely new prompts; do not manually rediscover deterministic registry mechanics.

1. WHOLE-CHAT HARVEST — PASS 1
- Read the current request, then traverse earlier accessible context for the same use case and dependencies. Include recoverable pasted/generated context or history when available; ignore unrelated history.
- Build `insight | current owner | action | proof` with action STRENGTHEN / ADD / ALREADY COVERED / OUT OF SCOPE.
- No material insight may silently disappear. Do not ask the user to repeat recoverable context.

2. OWNER MAP BEFORE NEW IDS
Search the combined Prompt Kit for an exact, adjacent, or materially overlapping prompt. Compare trigger, mission, scope, and closure—not title alone.
- STRENGTHEN when an owner has the core use case but lacks a compatible context, failure, live-proof, iteration, or usability rule.
- ADD only for genuinely missing bounded behavior with a distinct trigger and closure condition.
- ALREADY COVERED requires concrete current prompt evidence.
Do not create a second identity because alternate wording sounds attractive.

3. COMPLEMENT — DO NOT MERELY TRANSCRIBE
Preserve explicit user intent and terminology, then expand compatible utility revealed by chat/repo evidence: useful failure states, entrypoints, proof levels, context recovery, user-only gates, iteration, discoverability, or integration seams. Expansion must make the requested workflow more executable, reusable, testable, or failure-resistant. Do not invent unrelated requirements or universal checklists.

4. IMPLEMENT THE CONTRIBUTION SET
For STRENGTHEN, edit the canonical source and closest focused regression.
For ADD:
- choose the closest existing registry/profile; run `python scripts/prompt_registry_ops.py inspect` only if routing is unclear;
- draft semantic fields only; Do NOT set id, seq, or copySheet;
- run `python scripts/prompt_registry_ops.py add --input <draft.json> --registry <existing_registry_id>`;
- let the helper allocate identity, reject obvious duplicates, inject shared policy, rebuild the site, prove parity, and roll back registry/site writes if validation fails.
Multiple genuinely distinct prompts may be added from one chat; do not collapse them into a super-prompt merely to keep one identity.

5. WHOLE-CHAT HARVEST — PASS 2
After implementation, traverse the relevant context again from the opposite direction. Look for missed `also`, `another`, `we skipped`, `strengthen`, `live`, `regression`, `prototype`, corrections/examples, referenced sources, earlier accepted definitions, and neighboring owners that should be strengthened to avoid overlap. Update the ledger and close concrete gaps. Stop at a bounded fixed point; do not stop at the first helper receipt or manufacture passes with no new evidence.

6. FOCUSED PROOF + CONVERGENCE
Add or extend the closest focused semantic assertion the generic helper cannot prove. Verify new prompts remain distinct and strengthened prompts retain their original role. Run `python scripts/prompt_registry_ops.py validate`, focused tests, applicable language/order/discovery checks, generated-site `--check`, and `git diff --check`. Refresh the default-branch floor before final proof; reconcile moved dependencies; then merge the exact green authorized head into main.

FAIL-CLOSED
If routing is ambiguous, inspect once. If a contract mismatch names an owner/helper/builder, inspect only that surface. Do not fall back to loading the entire Prompt Kit architecture, guess identities, bypass parity, weaken a validator, or make the operator a context courier/test runner.

DELIVER
Keep it compact: contribution ledger; strengthened IDs/names; new helper receipts; focused semantic assertion results; prompt count/parity; validation; commit/PR/merge; resulting main SHA; exact blocker if any.'''
patched = text[:left] + compact + text[right:]
patched = patched.replace(
    'anchor = "\\nSTOP ONLY AT THE REAL FIXED POINT"',
    'anchor = "\\n10. STOP ONLY AT THE REAL FIXED POINT"',
    1,
)
path.write_text(patched, encoding="utf-8")
