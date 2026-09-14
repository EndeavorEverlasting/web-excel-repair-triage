# Prompt Compilation & Adaptive Language Architecture

**Status:** DESIGNED / TRACKED / SPRINT 1 INTEGRATED ON MAIN
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Owner:** Prompt Compilation subsystem (Prompt Kit / P79 strengthening lane)
**Evidence floor:** refreshed `main@04e4a77d261d0bd0388daa6d56f38e113cdf79fa` (contains PR #483 Sprint 1)
**Predecessor:** P95 Evidence Spine adapter-only architecture (`harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md`); TRQ-008 DONE
**Sibling (separate program):** TRQ-007 Compute Authority evaluation (`harness/evals/COMPUTE_AUTHORITY_EVALUATION_SPRINT_PLAN.md`)
**Canonical sprint map:** `harness/prompt-compilation/PROMPT_COMPILATION_SPRINT_MAP.md`
**Decision date:** 2026-09-14

## 1. Decision (one line)

**Accepted architecture:** Prompt Compilation is a bounded **prompt compilation and improvement** subsystem. It consumes owner-native artifacts through **thin read-only adapters**, builds a temporary deterministic **Context IR**, and emits an **effective prompt + build receipt**. It does **not** own lifecycle events, introduce a universal envelope, or become a competing Evidence Spine.

## 2. Problem separation (preserves P95)

| System | Questions it answers |
|---|---|
| Evidence Spine (existing owners + adapters) | What happened? What evidence exists? What remains? Is this complete, recoverable, blocked, recurrent? |
| Prompt Compilation (this subsystem) | Given semantic prompt contract + execution preference + bounded context, what exact effective instruction should be emitted? When evidence shows instruction construction is defective, what deterministic improvement candidate should be proposed? |

## 3. Architecture diagram

```text
Existing semantic owners
P99 / P115 / dispatch / continuation / usage / route
              │
              │ thin read-only adapters
              ▼
        CONTEXT ENGINE
              │
              ▼
      Canonical Context IR
              │
      ┌───────┴────────┐
      │                │
Prompt Semantic IR   Execution Profile
                      │
                EXHAUSTIVE
                 EFFICIENT
      │                │
      └───────┬────────┘
              ▼
        LANGUAGE ENGINE
              │
              ▼
      Effective Prompt
       + build receipt
              │
              ▼
            AGENT
              │
              ▼
       Existing evidence
            owners
              │
              ▼
    recurrence / eval evidence
              │
              ▼
  IMPROVEMENT-CANDIDATE COMPILER
              │
              ▼
 deterministic Git candidate
       + tests + provenance
              │
              ▼
             PR
```

## 4. Canonical intermediate representations

| IR | Schema id | Role |
|---|---|---|
| Prompt Semantic IR | `prompt-semantics/v1` | Authority underneath English prompt text (goals, obligations, invariants) |
| Execution Profile | `prompt-execution-profile/v1` | Exhaustive vs Efficient compute policy; may not weaken safety/evidence/privacy/scope/gates |
| Prompt Context IR | `prompt-context/v1` | Bounded compilation context from owner-native artifacts (not conversation dumps) |
| Build receipt | `prompt-build-receipt/v1` | Provenance for one `render(...)` result |
| Improvement candidate | `prompt-improvement-candidate/v1` | Deterministic self-building proposal; promotion = reviewed PR only |

English prompt prose is a **render target**, not the canonical requirement representation.

## 5. Language Engine contract

```text
render(
    prompt_semantics,
    execution_profile,
    prompt_context,
    language_policy_revision
) → effective_prompt + prompt-build-receipt/v1
```

Machine-enforced non-weakening rule: when an obligation has `modality = MUST` and the compiled context satisfies its `when` predicate, the effective prompt MUST NOT contain permissive weakening constructs such as "consider", "where useful", "if appropriate", "could", or "may" for that action. Exhaustive mode with safe parallel width must emit imperative dispatch semantics, typed failure disposition, and a dispatch proof requirement.

## 6. Compute Mode (user-facing product surface — later sprint)

Do **not** maintain `P07-exhaustive.md` / `P07-efficient.md` pairs.

Compile:

```text
prompt semantics × execution mode × context × language compiler revision
```

Precedence for execution profile resolution:

```text
explicit run override > prompt override > user default > product default
```

Neither profile may weaken: safety, evidence truth, destructive-operation rules, privacy, explicit user scope, required acceptance gates.

## 7. Improvement Compiler (self-building without self-authorizing)

```text
evidence → context normalization → contract failure fingerprint → recurrence threshold
  → improvement hypothesis → candidate Semantic IR / Language rule delta
  → gold regression fixture → deterministic evaluation → Git tree/blob → PR
```

Candidates never auto-mutate source, auto-merge PRs, or promote model-generated policy. Git remains the promotion boundary (`promotion_authority = reviewed_pr_only`).

## 8. Explicit non-goals (Sprint 1 and until separately authorized)

- UI Compute Mode toggle implementation
- PR #450 / #431 donor salvage or merge
- Raw conversation / transcript / clipboard ingestion
- New Evidence Spine event types or universal event bus
- Automatic source mutation or automatic PR merge
- Model-generated policy promotion
- Competing lifecycle envelope or outcome/recovery classifier

## 9. Relationship to TRQ-007

TRQ-007 measures whether exhaustive-compute **language** improves agent behavior under frozen prompt identities.

This subsystem answers how that language is **deterministically produced and evolved** from semantic policy.

Future cleaner experiment (out of Sprint 1 mutation scope):

```text
same semantic IR × same case × same model/runtime × same repo floor
  EFFICIENT compiler vs EXHAUSTIVE compiler
```

## 10. Proof typing

`PLANNED/DESIGNED → TRACKED → IMPLEMENTED → WIRED/REACHABLE → VALIDATED → INTEGRATED → DEPLOYED → OBSERVED`

Sprint 1 proves through VALIDATED/INTEGRATED for contracts, compiler, non-weakening validator, and fixtures only. It does not prove production Prompt Kit emission wiring or observed external-agent improvement.
