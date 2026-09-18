# Execution Boundary Enforcement Architecture

## Mission

Turn blockers, boundaries, capability loss, validation failures, provider degradation, partial side effects, agent-chosen cessation, and other operationally meaningful transitions into **first-class execution state** instead of private scratchpad information.

The key rule is simple:

> Recovery does not cancel disclosure. A material change in execution viability is part of the public contract of the run.

This architecture is deliberately broader than exception handling. The governed object is **loss or change of forward execution**.

## Theorem

A workflow cannot guarantee the absence of unexplained stops unless every material non-normal execution transition is:

1. observable,
2. classifiable,
3. checkpointed,
4. publicly reportable,
5. recoverable or explicitly terminal,
6. durably attributable, and
7. externally supervised when the acting process can die before it reports for itself.

The seventh condition is the part prompts alone cannot solve. If the host kills the process before it can speak, only an out-of-process supervisor can turn that disappearance into an observable terminal event.

## Materiality boundary

“Internal operational information” is not a blanket private category.

An event becomes operator-visible when it changes any of these:

- viable execution path;
- proof state;
- mutation certainty;
- owned-scope disposition;
- authority, safety, or external-gate state;
- whether the run can complete, quiesce, hand off, or terminate;
- the mechanism whose success is part of the claimed outcome;
- recurrence/systemic-defect evidence.

Only bounded micro-retries that change none of those may stay internal.

If raw detail is unsafe, secret-bearing, private, or irrelevant, redact the detail. **Do not redact the existence of the boundary.**

## State machine

```text
OBJECTIVE_ACTIVE
  -> BOUNDARY_OBSERVED
  -> BOUNDARY_CLASSIFIED
  -> CHECKPOINTED
  -> PUBLIC_TRANSITION_EMITTED
  -> RECOVERY_SELECTED
  -> RECOVERING
     -> OBJECTIVE_ACTIVE_RESUMED
     -> BOUNDARY_OBSERVED
     -> QUIESCENT_BLOCKED
     -> FINALIZING
  -> FINALIZING
  -> COMPLETE

external supervisor only:
OBJECTIVE_ACTIVE + process disappears + no terminal event
  -> HARD_TERMINATED_SYNTHETIC
```

A material boundary cannot disappear from history because recovery succeeded. A recovered quota failure, partial write, changed branch floor, or degraded provider remains part of the run evidence.

## Enforcement layers

### 1. Objective contract

Bind mission, owned scope, acceptance criteria, authority, proof ceiling, and current state before mutation. This prevents the agent from redefining “done” after friction appears.

### 2. Boundary capture

Capture both explicit failures and semantic cessation:

- tool/provider/runtime errors;
- validation and proof failures;
- access/authority/safety gates;
- partial/uncertain mutation;
- capability disappearance;
- user interruption;
- agent-selected scope reduction or stopping even when no exception occurred.

The final item is essential: exception hooks alone cannot detect behavioral abandonment.

### 3. Normalizer/classifier

Translate raw incidents into a canonical class and typed operational impact. The taxonomy is a successor artifact, not improvised prose.

### 4. Append-only execution journal

Before retrying any boundary that may have side effects, record:

- operation attempted;
- confirmed side effects;
- possible/unknown side effects;
- last proven checkpoint;
- proof already obtained;
- recovery attempts and outcomes.

The journal is what makes recovery safe after partial mutation.

### 5. Public transition publisher

A material event emits:

```text
BOUNDARY: <what changed>
IMPACT: <what it means for the requested outcome>
PROVED: <last reliable state>
RECOVERY: <what is being done or why it cannot proceed>
NEXT: <first executable continuation>
```

This is not merely closeout formatting. It is a required transition in the run state machine.

### 6. Recovery router

Classification must determine continuation. The agent does not improvise whether to quit.

The future taxonomy maps classes to behaviors such as bounded retry, serialize, alternate adapter, local-proof substitution, refresh/reconcile, read-after-write, quiesce, explicit handoff, or true terminal block.

### 6A. Boundary-to-sprint continuation

Classification is **routing, not sprint eligibility**.

Every MATERIAL or CRITICAL boundary encountered while the requested objective is unfinished opens a bounded **primary recovery sprint**. This applies whether the boundary is already classified, unclassified, caused by an external provider, or created by the agent itself through an assumption, phase boundary, capability judgment, or newly noticed scope edge.

The sprint preserves the original outcome and binds only the recovery mechanics:

- triggering boundary/event;
- parent objective and preserved requested outcome;
- smallest owned recovery scope;
- first executable progress-bearing action;
- completion gate;
- return condition to the parent objective.

When a safe progress-bearing action exists, the agent executes that first action in the same run. A classification, explanation, plan, handoff, branch/PR status, or newly discovered boundary is not a terminal result by itself.

An exact external gate can quiesce the sprint, but the run must retain the blocker, resumption trigger, and next transition. Explicit operator cancellation and genuine safety/prohibition gates remain valid stop conditions; they do not license abandonment of other safe routes.

This is intentionally separate from systemic prevention. **Every material boundary gets the primary recovery sprint.** Only novel/unclassified, recurrent/systemic, or missing-prevention-invariant boundaries additionally get the second prevention sprint through P13/P94 and the canonical regression loop.

The deterministic oracle at `scripts/execution_boundary_engine.py` makes that rule executable rather than phrase-only: applicable cases must traverse `PRIMARY_RECOVERY_SPRINT_OPENED`, emit a typed `primary_recovery_sprint`, and mark the selected first action as required. The oracle proves sprint instantiation and action selection; it does **not** pretend that a third-party host executed the external action. Host/agent execution remains a separate runtime proof surface.

### 7. Repository publisher

When a relevant writable repository exists, material operational learning should become durable **through the repository’s existing authority surfaces**:

1. canonical contract/validator;
2. existing work ledger, incident, or receipt;
3. active owned PR / tracked plan;
4. smallest new repository-native artifact only if no owner exists.

Never dump private chat or secrets into a public repository. Never invent a second authority merely to prove that publication happened.

The primary user task remains first priority: publishing the incident must not become an excuse to stop recovering the requested outcome.

### 8. Regression learner

Compose with `prompt-regression-safety.v1.json`.

A structurally novel event may immediately expose a missing invariant. Repeated independent occurrences make the systemic classification mandatory. The retained loop is:

```text
repair instance
-> classify defect family
-> find canonical owner
-> negative fixture
-> positive control
-> strengthen owner
-> local proof
-> provider parity when applicable
-> integrate and retain
```

### 9. Finalization gate

No direct `OBJECTIVE_ACTIVE -> COMPLETE` transition exists.

Before completion, reconstruct the original requested outcome and disposition each material requirement using the canonical actionable-next-step semantics. A first pass, first green, open PR, reduced scope, or successful fallback is not automatically completion.

### 10. External supervisor

A host/runtime supervisor must observe:

- run/objective start;
- durable checkpoints;
- latest boundary/publication state;
- valid terminal event.

If the acting process vanishes without a valid terminal event, the supervisor synthesizes a `HARD_TERMINATED_SYNTHETIC` event with the last checkpoint and resumable continuation. This is the only way to close the “agent died before it could explain itself” gap.

## Prompt Kit composition

This should not become a 127-prompt copy-edit campaign.

The architecture composes through existing owners:

- **shared prompt policy:** `registry/prompts/actionable-next-step-policy.v1.json`
- **implementation execution:** P07
- **recurring process/system defect:** P13
- **regression design:** P94
- **prompt identity/topology:** P79
- **recurring defect retention:** `harness/contracts/prompt-regression-safety.v1.json`
- **provider/local proof continuity:** `harness/contracts/repository-local-proof-continuity.v1.json`
- **merge-specific gates:** `harness/contracts/pr-merge-gate.v1.json`
- **parallel capability/fallback:** `harness/contracts/prompt-parallel-dispatch.v1.json`
- **non-weakening semantic floor:** the prompt-strength contract once integrated.

The shared policy is the inheritance seam. P07/P13/P94 specialize behavior; they do not replace the global obligation.

## Required next phases

**Phase 2 — Canonical boundary taxonomy.** Define classes, severity/materiality, side-effect state, recovery dispositions, terminal dispositions, and mappings to existing contracts.

**Phase 3 — Positive and negative test floor.** Prove at minimum: explicit tool failure, silent agent abandonment, partially applied mutation, provider quota degradation, proof failure, authority gate, unsafe/private raw detail with safe public abstraction, successful recovery that still reports the boundary, repeated unchanged blocker quiescence, and supervisor-synthesized hard termination.

**Phase 4 — Prompt inheritance.** Strengthen the canonical shared policy and P07/P13/P94 composition; rebuild every effective/generated prompt representation and prove containment/non-weakening.

**Phase 5 — Integration proof.** Validate exact head, provider/local parity, generated-site parity, merge, refreshed-main containment, and retained regression coverage.

## Proof ceiling

The architecture, taxonomy, shared Prompt Kit inheritance seam, and deterministic regression contract are tracked and validating. They do **not** by themselves prove downstream model obedience, an implemented out-of-process host supervisor, or inheritance by every Prompt Kit representation. Those remain explicit proof limits.
