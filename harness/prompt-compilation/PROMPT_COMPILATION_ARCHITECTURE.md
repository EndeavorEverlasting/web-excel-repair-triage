# Prompt Compilation & Adaptive Language Architecture

**Status:** DESIGNED / TRACKED / SPRINTS 1–3 INTEGRATED ON MAIN
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Owner:** Prompt Compilation subsystem (Prompt Kit / P79 strengthening lane)
**Evidence floor:** refreshed `main@50229c36e21a32d8541ddfe2c957cf9095ce3546` (2026-09-16); contains PR #483/#485/#515
**Predecessor:** P95 Evidence Spine adapter-only architecture (`harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md`); TRQ-008 DONE
**Sibling (separate program):** TRQ-007 Compute Authority evaluation (`harness/evals/COMPUTE_AUTHORITY_EVALUATION_SPRINT_PLAN.md`)
**Canonical sprint map:** `harness/prompt-compilation/PROMPT_COMPILATION_SPRINT_MAP.md`
**Decision date:** 2026-09-14; **program-design revision:** 2026-09-16

## 1. Decision (one line)

**Accepted architecture:** Prompt Compilation is a bounded **prompt compilation and improvement** subsystem. It consumes owner-native artifacts through **thin read-only adapters**, builds a temporary deterministic **Context IR**, and emits an **effective prompt + build receipt**. Defective instruction construction yields a deterministic **improvement candidate** ending at a **reviewed Git PR draft**, never at auto-mutation. It does **not** own lifecycle events, introduce a universal envelope, or become a competing Evidence Spine.

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

## 6. Compute Mode (user-facing product surface — deferred Sprint 4)

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

UI Compute Mode remains deferred until Sprint 4; Sprint 3 proves the Improvement Compiler seams first.

## 7. Improvement Compiler (self-building without self-authorizing)

```text
evidence → context normalization → contract failure fingerprint → recurrence threshold
  → improvement hypothesis → candidate Semantic IR / Language rule delta
  → gold regression fixture → deterministic evaluation → Git tree/blob → PR
```

Candidates never auto-mutate source, auto-merge PRs, or promote model-generated policy. Git remains the promotion boundary (`promotion_authority = reviewed_pr_only`).

## 8. Explicit non-goals (until separately authorized)

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

Future cleaner experiment (out of current mutation scope for frozen study identities):

```text
same semantic IR × same case × same model/runtime × same repo floor
  EFFICIENT compiler vs EXHAUSTIVE compiler
```

## 10. Proof typing

`PLANNED/DESIGNED → TRACKED → IMPLEMENTED → WIRED/REACHABLE → VALIDATED → INTEGRATED → DEPLOYED → OBSERVED`

Sprints 1–2 prove through VALIDATED/INTEGRATED for contracts, Context Engine adapters, Language Engine, non-weakening validator, and fixtures. Sprint 3 proves DESIGNED/TRACKED + locally VALIDATED Improvement Compiler call stacks. It does not prove production Prompt Kit emission wiring or observed external-agent improvement.

---

## 11. Program design (2026-09-16 revision)

### 11.1 Governance vs harness vs program vs implementation

| Layer | What it owns here |
|---|---|
| **Governance** | `AGENTS.md`, P95 adapter-only constraint, evidence-state language, integration/freshness rules |
| **Harness** | Schemas under `harness/contracts/`, fixtures, sprint map, ledger indexes TRQ-009/010/012, validators/tests |
| **Program design** | Context Engine, Language Engine, ImprovementCandidateCompiler, profile precedence, failure classification, PR-draft package |
| **Implementation** | Production Prompt Kit wiring and Compute Mode UI remain Sprint 4+; not this design revision |

Harness documents are not a substitute for runtime ownership. Runtime modules must own decisions named below.

### 11.2 User outcomes and invariants

**User outcomes**

1. Given a semantic prompt contract, execution preference, and bounded context, emit one exact effective instruction plus a build receipt.
2. When recurrence evidence shows instruction construction is defective, emit one deterministic improvement candidate with required regressions.
3. Never silently weaken MUST obligations, safety, evidence truth, privacy, scope, or acceptance gates.
4. Never auto-authorize promotion: candidates stop at reviewed PR drafts.

**Invariants**

1. Context Engine does **not** own lifecycle events.
2. English is not authority; `prompt-semantics/v1` is.
3. Execution profiles cannot omit `non_weakenable_constraints`.
4. Improvement candidates require `reviewed_pr_only`.
5. TRQ-007 frozen prompt identities are not mutated by this lane.
6. No universal event bus / lifecycle envelope.

### 11.3 Domain vocabulary

| Term | Owns / means |
|---|---|
| **PromptSemantics** | Goals, obligations, invariants (`prompt-semantics/v1`) |
| **ExecutionProfile** | Exhaustive/Efficient compute policy (`prompt-execution-profile/v1`) |
| **PromptContext** | Temporary compilation context (`prompt-context/v1`) |
| **BuildReceipt** | Provenance of one render (`prompt-build-receipt/v1`) |
| **ImprovementCandidate** | Deterministic proposal (`prompt-improvement-candidate/v1`) |
| **FailureFingerprint** | Canonical hash of a contract failure identity |
| **RecurrenceGate** | Admission decision from owner-native finding state/threshold |
| **HypothesisCatalog** | Deterministic map from failure identity → rule + regressions |
| **PrDraftPackage** | reviewed_pr_only draft descriptor; `auto_merge=false` |
| **LanguageEngine** | `render(semantics, profile, context, policy) → prompt + receipt` |
| **ContextEngine** | Read-only adapters + profile precedence resolver |
| **ImprovementCandidateCompiler** | Journey orchestrator from finding → candidate → eval → PR draft |

### 11.4 Program module / interface map

| Module | Path | Public interface | Owned state | Side effects | Failure contract |
|---|---|---|---|---|---|
| Language Engine | `scripts/prompt_language_compiler.py` | `render`, `validate_*`, `compile_improvement_candidate`, fixture CLI | none durable; policy file is config | none (pure compile) | `PromptCompilationError` |
| Context Engine | `scripts/prompt_context_engine.py` | `project_prompt_context`, `resolve_execution_profile`, adapters | none; temporary Context IR only | none | `ContextEngineError` |
| Hypothesis Catalog | `harness/prompt-compilation/improvement-hypothesis-catalog.v1.json` | lookup by failure identity | durable catalog only | none | missing entry → fail closed / generic |
| ImprovementCandidateCompiler | `scripts/prompt_improvement_compiler.py` | `run_improvement_journey`, `recurrence_gate`, eval, PR draft | none durable product state | writes only when CLI `--output` requested | `ImprovementCompilerError` |
| Gold fixtures | `harness/prompt-compilation/fixtures/TC06-*` | consumed by Language Engine + Improvement eval | fixture inputs | none | missing fixture → fail closed |

### 11.5 Dependency direction

```text
owner-native artifacts (P99 / dispatch / continuation / recurrence)
        │ read-only
        ▼
 Context Engine ──► PromptContext
        │
 PromptSemantics + ExecutionProfile + PromptContext + LanguagePolicy
        │
        ▼
 Language Engine ──► EffectivePrompt + BuildReceipt
        │
        ▼
 (agent / external) ──► owner-native evidence (not owned here)
        │ read-only findings
        ▼
 ImprovementCandidateCompiler ──► ImprovementCandidate + eval + PrDraftPackage
        │
        ▼
 human review / Git PR   (promotion boundary; not this module)
```

Forbidden reverse edges: Improvement Compiler must not write Evidence Spine events; Language Engine must not open PRs; Context Engine must not mutate owners.

### 11.6 SUCCESS CALL STACK (Improvement journey)

```text
CLI/API finding JSON
  -> ImprovementCandidateCompiler.normalize_finding
  -> recurrence_gate (confirmed_recurrence | monitoring_reopened)
  -> resolve_hypothesis (catalog)
  -> LanguageEngine.compile_improvement_candidate
  -> evaluate_candidate_regressions (TC06 etc. via LanguageEngine.run_fixture)
  -> build_pr_draft_package (auto_merge=false, auto_mutate_source=false)
  -> operator-facing draft JSON
```

Proven by `tests/test_prompt_improvement_compiler.py` IJ01 and `python scripts/prompt_improvement_compiler.py run-journey ...`.

### 11.7 FAILURE CALL STACKS

| Failure | Classification | Surfacing |
|---|---|---|
| Finding state below threshold (`evidence_only`) | `recurrence_threshold_not_met` | gate rejects; journey raises; CLI exit 2 on gate command |
| Empty evidence refs | `missing_evidence_refs` | gate rejects |
| Count below owner threshold | `count_below_owner_threshold` | gate rejects |
| `promotion_authority != reviewed_pr_only` | domain rejection | `PromptCompilationError` / draft builder fail-closed |
| Missing required regression fixture | eval failure | `ImprovementCompilerError` |
| MUST-weakening in Language Engine path | non-weakening validator | `PromptCompilationError` (Sprint 1 seam; still enforced) |

### 11.8 Alternatives compared

| Candidate | Verdict | Why |
|---|---|---|
| **A. Separate ImprovementCandidateCompiler** (selected) | **KEEP** | Preserves Language Engine purity; promotion boundary explicit; testable journey; matches P95 “no bus” |
| **B. Fold improvement into Language Engine `render`** | REJECT | Mixes compile-time render with post-evidence promotion; grows interface; harder to forbid auto-apply |
| **C. GitOps auto-apply operator** | REJECT | Self-authorizing; violates `reviewed_pr_only` and “self-building without self-authorizing” |
| **D. LLM freeform prompt rewriter** | REJECT | Non-deterministic; English becomes authority again; cannot gold-fixture modality regressions |
| **E. Sprint 3 = UI Compute Mode first** (prior map) | REJECT for next sprint | Operator-refined forbidden scope still excludes UI; Improvement Compiler is the higher-risk unproven seam |

External prior-art patterns consulted at design time (no code copied): policy-as-code IR→renderer (OPA/Cedar class), prompt compilers (DSPy/Guidance class), GitOps promotion boundary. Selected recombination: **IR + deterministic renderer + catalogued improvement + Git PR gate**.

### 11.9 Deployment operating model

No new PaaS/K8s tier. This subsystem is **repository-local Python + tracked JSON contracts + unittest**. Durable app state is Git-tracked schemas/fixtures/catalogs. Telemetry/log exhaust is out of scope. Retain local CLI until a later product wiring sprint proves host need.

### 11.10 Implementation seam ready for next build sprint

After this design revision integrates:

1. **Build owner:** Prompt Compilation Sprint 3 implementation lane (TRQ-012) may harden catalog coverage, add more failure fingerprints, and optionally emit ephemeral fixture drafts under `Outputs/` only.
2. **Must preserve:** interfaces in §11.4, `reviewed_pr_only`, no event ownership, TC06 non-weakening.
3. **Must not absorb:** UI Compute Mode (Sprint 4), #450/#431, TRQ-007 frozen identities, auto-merge.

## 12. Second-pass critique (after prototypes)

| Question | Finding | Disposition |
|---|---|---|
| Did any interface leak implementation? | Catalog is a JSON file path known to compiler — acceptable config seam | Keep; do not inline hypotheses in code |
| Module knows too much? | Journey orchestrator knows fixture root — needed for eval | Keep bounded; do not learn Evidence Spine write APIs |
| State owned twice? | No durable candidate store; draft is ephemeral | Keep until a later artifact registry is authorized |
| Failure ownership clear? | Gate vs eval vs promotion errors are distinct codes/exceptions | Keep |
| Future change blast radius? | New failure identity = catalog entry + optional fixture | Low blast radius; preferred extension path |
