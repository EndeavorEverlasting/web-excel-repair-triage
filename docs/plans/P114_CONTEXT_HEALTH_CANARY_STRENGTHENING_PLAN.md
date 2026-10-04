# P114 Context-Health Canary Strengthening — P04 Remote Execution Plan

**Plan ID:** P114-CONTEXT-HEALTH-CANARY-2026-10-03  
**Status:** REMOTE STRATEGIC PLAN — READY FOR BOUNDED EXECUTION  
**Canonical donor repository:** `EndeavorEverlasting/web-excel-repair-triage`  
**Planning floor:** `main@ee2fa75c99306607062445a5653af19129ac7c54`  
**Destination convergence repository:** `EndeavorEverlasting/TokenCorridor`  
**Observed destination floor while planning:** `main@dc58cfcbd00792a18e141c9ac6e0ccf92cf1b6f3`  
**Strategic owner:** remote/frontier ChatGPT planning lane under `agent-execution-tiering/v1`  
**Execution agents:** Cursor/OpenCode as bounded implementation executors only  
**Prompt identity:** strengthen **P114 — Conversation Context Canary & Handoff Guard**; DO NOT allocate a new prompt identity.

## 1. Operator outcome

Whenever P114 is active, the Canary must perform a practical context-health check in addition to its existing identity/freshness duties.

The check must answer the operational question:

> Can this conversation safely continue, should execution-critical state be checkpointed now, or is a fresh-chat handoff required?

It must **not** pretend that model-visible prose equals the host context window, invent a token percentage, or become a second task report.

The strengthened system must preserve the lightweight first-line Canary while adding enough typed state to prevent the user from discovering context exhaustion only after continuity has degraded.

## 2. Existing ownership that MUST remain intact

This plan strengthens existing owners; it creates no competing continuity system.

- **P114** owns the lightweight per-query Canary, context-health sensing, re-anchor trigger, checkpoint/handoff trigger, and the operator-facing context-health classification.
- **P02** owns previous-chat recovery and resumed execution. P114 may create/refresh a P02-compatible checkpoint; it does not become the recovery executor.
- **`harness/conversation-continuity/checkpoint.schema.v1.json`** remains the canonical durable cross-chat checkpoint shape (`live-thread-p02-checkpoint/v1`).
- **`scripts/validate_conversation_handoff_checkpoint.py`** remains the checkpoint validator.
- **P76** owns repository spec/harness progressive disclosure and repository context-budget reduction. Its approximate repository-token budgets MUST NOT be promoted into live conversation-window telemetry.
- **P92** owns shell/kernel/runtime/path resolution.
- **P111/artifact-handoff** retain cloud synchronization/delivery ownership.
- **P13/P94** retain recurring-defect hardening/regression ownership.
- **TokenCorridor** remains the destination/cross-repository convergence authority. Triage remains donor-authoritative for P114 until the existing M2/M4 authority-transfer gates prove parity and explicitly downgrade donor authority.

## 3. Strategic semantic decision — LOCKED

Local implementation agents MUST NOT rename, add, remove, reinterpret, or reorder these states without returning to the strategic owner.

Every normal P114 Canary line gains one mandatory field:

```
CTX=<HEALTHY|LARGE|COMPACTION_RISK|HANDOFF_REQUIRED|UNKNOWN>
```

Canonical first-line form:

```
CANARY | ISSUED=<RFC3339-or-UNKNOWN> | PROFILE=<profile-or-UNKNOWN> | NETWORK=<required-network> | CTX=<state>
```

Existing optional EXEC / ACCOUNT / ROLE / CLOUD / REPO / BRANCH / LANE fields remain unchanged and follow current least-sensitive/materiality rules.

### CTX is NOT a context-window percentage

`CTX` means **operational continuity health**: whether the mission, authority, current proof, unresolved gate, and next action are recoverable enough to continue safely.

It is deliberately separate from exact context-capacity telemetry.

A conversation can therefore truthfully be:

```
CTX=HEALTHY
WINDOW_TELEMETRY=UNKNOWN
```

That means continuity is healthy; it does not claim how many tokens remain.

## 4. Context-health state machine — LOCKED

### HEALTHY

Use when all material execution-continuity facts are recoverable:

- current mission/disposition;
- current canonical owner(s);
- active repo/provider identity when material;
- last proven state/proof ceiling;
- first unproven gate/blocker;
- exact next useful action;
- no unresolved material Canary mismatch;
- reusable execution-critical state is already durable, or has not yet crossed an existing durability trigger.

`HEALTHY` is permission to continue. It is not proof of unused context capacity.

### LARGE

Use when continuity remains coherent but the conversation has materially accumulated complexity such that proactive state hygiene is useful.

Evidence can include:

- multiple active/recent work lanes whose distinctions matter;
- repeated large handoffs, evidence packets, artifacts, or source excerpts;
- several execution-critical facts still recoverable but expensive to reconstruct;
- authoritative host telemetry indicating rising context pressure without a critical condition;
- repeated evidence rehydration that has not yet produced contradiction or omission;
- durability coverage that is adequate but a new major execution phase would materially increase recovery cost.

`LARGE` does **not** mean a guessed token threshold. Continue work; ensure the next evidence-changing milestone is durably captured before opening another major lane.

### COMPACTION_RISK

Use when continuity is still recoverable but loss risk has become material enough that a checkpoint is required now.

Triggers include any of:

- authoritative host telemetry reports material/near-limit context pressure or an impending compaction condition;
- an execution-critical accepted decision/proof/blocker/next action has crossed the existing conversation-to-artifact durability trigger but remains chat-only;
- a first material re-anchor was required because the Canary omitted/contradicted a core fact;
- a compaction/summarization event has occurred and the post-compaction reconstruction has not yet been durably checkpointed;
- reconstruction cost or ambiguity has become high enough that another major lane should not begin before a checkpoint.

Required action:

1. Preserve the smallest canonical durable state owner for ordinary project/repository facts.
2. If cross-chat continuation is now plausibly useful, emit or refresh a `live-thread-p02-checkpoint/v1` payload.
3. Validate it with `scripts/validate_conversation_handoff_checkpoint.py` when repository execution is available.
4. Continue in the same chat after a successful checkpoint when continuity remains coherent. **COMPACTION_RISK does not automatically force a new chat.**

### HANDOFF_REQUIRED

Use only when a new conversation is now the safer execution surface.

Triggers include:

- authoritative host telemetry reports an actual critical/out-of-room/forced-handoff state;
- material drift repeats after the one allowed re-anchor;
- a compaction/recovery pass cannot reconstruct required execution-critical state without contradiction;
- core mission/authority/proof/next-action facts repeatedly conflict with stronger evidence;
- a required checkpoint cannot be made resumable while the current thread remains degraded.

Required action:

1. Produce/refresh the existing P02 checkpoint.
2. Validate it when possible.
3. Surface the first unproven gate and exact next action.
4. Route continuation to P02 in a fresh conversation.
5. Do not claim the current agent can open/terminate chats itself.

### UNKNOWN

Use when the agent cannot recover enough material continuity state to classify safely.

`UNKNOWN` blocks only dependent action.

Attempt one evidence-backed re-anchor using accessible current chat, repository, provider, checkpoint, artifact, or handoff evidence. If recovered, reclassify. If not recovered, escalate to `HANDOFF_REQUIRED` with UNKNOWN fields preserved honestly.

## 5. Capacity telemetry contract — LOCKED

P114 checks for authoritative telemetry every time it runs, but it only consumes telemetry the host/runtime actually exposes.

Potential host evidence classes include:

- API request usage plus the selected model's documented context capacity;
- host-provided context-window usage/pressure events;
- CLI/runtime status that explicitly reports current context use;
- UI context-usage indicators when that value is actually supplied to the agent/operator workflow.

Rules:

1. **Never infer exact conversation-window usage from visible message length, repository character counts, elapsed time, message count, attachment count, or P76's repository context estimator.**
2. Never claim a percentage unless both numerator and applicable capacity denominator are authoritative for the active host/model/request.
3. Hidden system/tool/reasoning/file context means a text-only estimate is never promoted to exact telemetry.
4. Provider-specific warning thresholds belong to the provider/adapter evidence layer; P114 consumes the normalized pressure fact rather than inventing a universal percentage.
5. When telemetry is absent, capacity is UNKNOWN but continuity health is still classifiable.
6. Exact numeric telemetry stays out of the ordinary one-line Canary unless explicitly requested or materially needed. The normal signal is `CTX`.

Public technical basis reviewed during planning:
- OpenAI conversation-state guidance: context window includes request input/output and reasoning as applicable; large prompts can exceed context and compaction is a separate mechanism.
- OpenAI token-counting guidance: API surfaces can provide actual input/output usage.
- OpenAI Live API: host events can expose context-window usage when available.

These references justify telemetry-first/fallback-to-continuity semantics; they do not hard-code OpenAI-specific behavior into P114.

## 6. Practical explicit context-check output

When the operator explicitly asks “how is our context window/context?”, or when `CTX != HEALTHY`, P114 may add one compact context-check block after the normal Canary:

```
CONTEXT CHECK
- continuity: <HEALTHY|LARGE|COMPACTION_RISK|HANDOFF_REQUIRED|UNKNOWN>
- window telemetry: <authoritative value/pressure state | UNKNOWN>
- durability: <ADEQUATE|PARTIAL|MISSING|NOT_APPLICABLE>
- action: <CONTINUE|CHECKPOINT_THEN_CONTINUE|HANDOFF_TO_P02|REANCHOR>
```

Rules:

- If telemetry is UNKNOWN, say so plainly.
- Do not substitute a guessed percentage.
- `durability=ADEQUATE` means the execution-critical decisions/proof/next action already have durable recoverable owners; it does not mean every sentence is persisted.
- This block is conditional. Normal P114 use remains one lightweight line.

## 7. Durability/checkpoint behavior

P114 must inspect whether execution-critical state is durable, not whether the full transcript is duplicated.

Durability set to evaluate when material:

- accepted/rejected decisions that constrain later work;
- current mission/disposition;
- canonical owner/path/plan identity;
- repo/branch/PR/SHA or provider revision needed to resume;
- last proven gate and proof ceiling;
- active blocker and owner;
- exact next action;
- unresolved successor obligation.

Prefer existing canonical project/repository/provider artifacts first.

Use `live-thread-p02-checkpoint/v1` when the risk is specifically **cross-conversation resumability**.

Do NOT create:

- raw transcript dumps;
- duplicate status documents;
- a second P02 handoff schema;
- a second P66/work ledger;
- a P114-specific recovery executor.

## 8. Required P114 prompt strengthening

Use `scripts/prompt_registry_ops.py edit --prompt-id P114 --disposition STRENGTHEN`.

The implementation must update P114 metadata and body so that:

- `sprintRole` explicitly includes practical context-health sensing and proactive checkpointing;
- `useWhen` includes explicit context-window/context-health questions and long/high-entropy threads;
- `expectedOutput` includes mandatory `CTX` and the conditional compact context-check block;
- `nextStep` routes HEALTHY/LARGE/COMPACTION_RISK/HANDOFF_REQUIRED/UNKNOWN exactly as defined above;
- `proofGate` includes telemetry/no-telemetry, durability, checkpoint, compaction, and recovery falsification;
- `copyContent` contains the locked state machine and owner boundaries without becoming a giant duplicate of P02 or P76.

### Representation constraint

P114 is already large. Use `--compression-disposition GROWTH_JUSTIFIED` only if the unique state-machine semantics cannot be introduced without net growth. Prefer compression of redundant existing prose so the prompt remains practical.

The local executor does not decide the semantics; it only implements this plan faithfully.

## 9. Context-health contract/helper

Add the smallest machine-readable helper under:

`harness/conversation-continuity/context-health.v1.json`

It must encode, at minimum:

- schema/version identifier;
- exact CTX enum;
- descriptions above;
- allowed action for each state;
- telemetry authority rules;
- prohibition on inferred percentages;
- checkpoint owner and validator paths;
- neighboring owner map;
- migration disposition.

This helper is a semantic contract for tests/tooling. It is **not** a second prompt, second handoff schema, token meter, or recovery engine.

Do not alter `checkpoint.schema.v1.json` unless implementation proves the existing schema cannot represent the required resumable packet. The current schema already carries source conversation state, decisions, evidence, validation, remaining work, next action, blocker, repository state, and route; the default expectation is **reuse without schema mutation**.

## 10. Regression matrix — required

Create a deterministic/adversarial matrix covering at least:

1. No capacity telemetry + coherent durable state → `CTX=HEALTHY`; exact percentage forbidden.
2. Large/high-entropy thread + coherent state + adequate durability → `CTX=LARGE`; continue.
3. Authoritative host pressure + coherent state → `COMPACTION_RISK`; checkpoint then continue.
4. Critical execution fact remains chat-only after durability trigger → `COMPACTION_RISK`.
5. First material Canary mismatch → re-anchor once; checkpoint when continuity risk warrants; no forced fresh chat merely for one recovered slip.
6. Repeated material drift after re-anchor → `HANDOFF_REQUIRED`.
7. Host reports actual context exhaustion/critical state → `HANDOFF_REQUIRED`.
8. Missing telemetry on explicit context question → answer UNKNOWN for capacity while still reporting continuity/durability.
9. P76 approximate repository token report presented as conversation telemetry → reject.
10. Visible-message character/token estimate presented as exact context usage → reject.
11. Valid `live-thread-p02-checkpoint/v1` generated for handoff → validator PASS.
12. Invalid/incomplete checkpoint → fail closed; do not claim resumability.
13. Successful checkpoint during `COMPACTION_RISK` → same-chat continuation permitted.
14. Legitimate fresh-chat P02 resume consumes checkpoint without replaying already-proven work.
15. Cloud artifact behavior from current P114 remains unchanged.
16. ACCOUNT/ROLE, NETWORK, EXEC, and ISSUED semantics remain unchanged.
17. Local implementation agent attempts to add/rename CTX states or reassign owners → regression FAIL.
18. Migration consumer attempts to implement a second TokenCorridor context-health authority before donor cutover → regression FAIL.

Use deterministic assertions for prompt/contract structure and a prompt-strength/eval matrix for judgment-heavy sequences.

## 11. Execution authority boundary

The semantics in this plan are strategically settled.

Cursor/OpenCode are **implementation executors**, not design authorities, for this sprint.

They MAY:

- inspect refreshed repository truth;
- implement the exact P114 strengthening through the registry helper;
- create the exact helper contract/regression fixtures/tests defined here;
- run builders/validators/tests;
- diagnose mechanical failures;
- make the smallest implementation repair that preserves this plan;
- commit/push/open/update the implementation PR;
- merge only after exact-head gates are green and current-main reconciliation succeeds.

They MUST NOT:

- create a P115/P146/etc. replacement;
- change CTX state names/semantics;
- invent percentage thresholds;
- move recovery ownership away from P02;
- move repository context factoring away from P76;
- alter the convergence destination/cutover model;
- redefine agent tiering;
- weaken validators or delete failing regression cases;
- modify this strategic plan or its dispatch manifest to make implementation easier;
- treat model/tool availability as authority.

Ambiguity in a locked semantic is an escalation to the strategic owner, not local design freedom.

## 12. P04 execution graph

### Wave 1 — parallel

#### Lane A — P114 canonical semantic implementation

**Owner:** bounded Cursor/OpenCode executor under this locked plan  
**Owns:** P114 canonical registry body + semantic migration/history record  
**Must use:** `scripts/prompt_registry_ops.py edit`  
**Forbidden:** context-health helper/tests; plan/manifest; P02/P76 semantics; migration authority

Output:
- strengthened P114 source;
- lifecycle/history migration proving STRENGTHEN with stable P114 identity;
- dry-run + focused prompt registry proof.

#### Lane B — context-health contract and regression floor

**Owner:** bounded Cursor/OpenCode executor under this locked plan  
**Owns:** new context-health helper contract, focused deterministic tests, prompt-strength/adversarial matrix  
**Forbidden:** canonical P114 source; plan/manifest; P02/P76 semantics; generated site

Output:
- exact enum/action contract;
- negative/positive fixtures;
- focused tests proving no fake telemetry and correct checkpoint routing.

### Wave 2 — convergence

#### Lane C — integration/build/migration-proof convergence

Dependencies: A + B.

Responsibilities:
- reconcile exact combined candidate;
- register new focused test/contract in existing deterministic floor only where repository convention requires;
- route the new helper through existing codebase/context indexes if necessary;
- run Prompt Kit canonical builder rather than hand-editing generated output;
- prove `live-thread-p02-checkpoint/v1` schema/validator unchanged unless a demonstrated incompatibility exists;
- run focused + broad Prompt Kit/registry/context/continuity gates;
- run patch hygiene;
- push/open implementation PR;
- reconcile review findings without changing locked semantics;
- merge exact green candidate;
- refresh main and prove containment + generated-site parity.

## 13. Validation floor

Minimum expected validation after combined implementation:

```text
python scripts/prompt_registry_ops.py inspect
python tests/test_p114_context_health_prompt.py
python tests/test_prompt_semantic_coverage.py
python tests/test_prompt_quality_history.py
python scripts/validate_conversation_handoff_checkpoint.py --schema-only
python scripts/validate_context_architecture.py --summary
python scripts/build_prompt_kit_registry.py
python scripts/build_prompt_kit_registry.py --check
git diff --check <base>...<head>
```

Also run the repository's registered Prompt Kit web/skill/operational harness floors that are required for the exact changed surfaces.

A first PASS is not closure: run the adversarial matrix and one residual-compute sweep for missing state/owner/migration cases.

## 14. Migration/convergence binding

This strengthening is intentionally compatible with the existing AFK Factory convergence plan.

Current migration rule remains:

```
Triage donor authority
→ M2 Prompt Kit extraction with deterministic parity
→ caller/site rewiring
→ M4 explicit authority cutover
→ donor downgrade
```

Therefore:

1. Implement and prove P114 here first because Triage remains donor-authoritative.
2. Record the strengthened P114/context-health helper as a Prompt Kit capability that **MUST migrate to TokenCorridor with semantic parity**.
3. Do not create a separate TokenCorridor context-health design.
4. During LM2 transplant/parity, consume the latest integrated donor P114, its context-health helper, regression matrix, and checkpoint-owner bindings.
5. TokenCorridor only becomes canonical for this capability after the existing authority-transfer gate is satisfied.
6. Donor cleanup/retirement must not remove P114 or its regression floor before cutover containment is proved.

This adds no new cross-repo dependency to ordinary P114 runtime behavior; it only protects the capability from being lost or forked during migration.

## 15. Collision analysis

Observed active Triage PR during planning:

- **#669 — Commitment Boundary governance**.

This plan does not own that PR and must not mutate its branch.

Implementation executors must refresh open PRs before mutation. If #669 or a later writer touches a planned mutation surface, preserve that writer and either stack/rebase safely or isolate the P114 lane.

The strategic plan and dispatch manifest are owned by this remote plan lane and are read-only inputs for local implementation agents.

## 16. Proof ceiling

This plan proves:

- strategic semantics are settled;
- ownership boundaries are settled;
- execution lanes, collision boundaries, tests, migration obligations, and completion gates are specified;
- local agents can implement without designing the strengthening.

This plan does **not** prove:

- P114 has been modified;
- the helper/tests exist;
- generated Prompt Kit parity;
- implementation CI;
- implementation PR merge;
- TokenCorridor M2 parity/cutover;
- real host context telemetry availability in any particular ChatGPT/Cursor/OpenCode surface.

## 17. Definition of done for the implementation sprint

Implementation is complete only when all are true:

1. P114 stable identity is preserved.
2. Mandatory CTX appears in effective P114 Canary semantics.
3. State machine exactly matches this plan.
4. No fake token/context percentage is permitted.
5. Authoritative telemetry is consumed when available and UNKNOWN otherwise.
6. Explicit context questions return practical continuity/window/durability/action status.
7. COMPACTION_RISK creates/refreshes durable state without forcing a new chat.
8. HANDOFF_REQUIRED uses the existing P02 checkpoint schema and recovery owner.
9. P76 repository context-budget estimates cannot masquerade as conversation telemetry.
10. Cloud/account/network/EXEC/ISSUED behavior is preserved.
11. Focused/adversarial/broad tests pass on exact candidate.
12. Generated Prompt Kit is rebuilt through the canonical builder and parity passes.
13. Exact implementation head is integrated into refreshed Triage main.
14. Post-merge main retains the strengthening.
15. Migration handoff records that TokenCorridor LM2 must carry the strengthened capability with parity.
16. No local agent has modified the strategic plan semantics.

## 18. First executable local action

The local executor starts from a fresh isolated worktree/branch at refreshed `origin/main`, reads this plan and the dispatch manifest, verifies no overlapping active writer owns its lane surfaces, then launches Wave 1 lanes without changing this plan.

The first semantic mutation MUST be produced through:

```
python scripts/prompt_registry_ops.py edit --prompt-id P114 --disposition STRENGTHEN ...
```

after a dry-run using the exact locked semantics above.


## 19. Exact P114 semantic capability delta — LOCKED

The local executor MUST use the following semantic direction for `--disposition STRENGTHEN`; it may update only evidence references mechanically when the named focused test is created, but it may not change capability IDs, presence, ownership, relation, or the ownership interpretation.

No semantic-capability catalog addition is authorized.

### Preserved assignments

Keep these assignments semantically unchanged:

- `strength.fresh_evidence_floor` — `REQUIRED / SECONDARY / GUARDS / CANONICAL_BODY`.
- `strength.proof_relevance_freshness` — `REQUIRED / SECONDARY / GUARDS / CANONICAL_BODY`.
- `strength.evidence_state_integrity` — `REQUIRED / SECONDARY / GUARDS / CANONICAL_BODY`.
- `execution.implementation` — `AWARE / NONE / ROUTES_TO / ROUTED_OWNER`.
- `process.recurring` — `AWARE / NONE / ROUTES_TO / ROUTED_OWNER`.

### Strengthening deltas

Apply exactly two semantic deltas:

1. Upgrade `strength.actionable_continuation` from `SUPPORT` to **`REQUIRED`**, preserving `SECONDARY / IMPLEMENTS / CANONICAL_BODY`.
   - Rationale: proactive checkpointing and fresh-chat handoff both require an executable, owner-assigned next action; P114 preserves/renders that continuation but still does not own resumed implementation.
2. Add `strength.plan_durability` as **`REQUIRED / SECONDARY / GUARDS / CANONICAL_BODY`**.
   - Rationale: P114 now checks whether execution-critical conversation state that crossed an existing durability trigger has a recoverable repository/provider/checkpoint owner before declaring context healthy. It guards durability; it does not become the plan owner.

### Required evidence references for the two strengthened assignments

Use the smallest applicable set from:

- `docs/plans/P114_CONTEXT_HEALTH_CANARY_STRENGTHENING_PLAN.md`
- `harness/conversation-continuity/checkpoint.schema.v1.json`
- `scripts/validate_conversation_handoff_checkpoint.py`
- `tests/test_conversation_context_canary_prompt.py`
- `tests/test_p114_context_health_prompt.py` once created by the parallel regression lane

The profile-level `evidence_refs` must retain the current P114 evidence set and add the strategic plan, checkpoint schema/validator, context-health helper, and focused context-health test after those paths exist.

Do not add a new PRIMARY capability. P114 remains a continuity sensor/guard and handoff trigger, not the canonical plan owner, recovery executor, or implementation owner.

