# Prompt Compilation & Adaptive Language — Canonical Sprint Map

**Status:** TRACKED / SPRINTS 1–3 INTEGRATED; SPRINT 4 IMPLEMENTED ON ISOLATED VALIDATION LANE
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Planning floor:** refreshed `main@50229c36e21a32d8541ddfe2c957cf9095ce3546` (provider refresh 2026-09-16)
**Architecture authority:** `harness/prompt-compilation/PROMPT_COMPILATION_ARCHITECTURE.md`
**P95 constraint floor:** `harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md` (adapter-only; no universal envelope/bus)
**Ledger index:** TRQ-009 (Sprint 1), TRQ-010 (Sprint 2), TRQ-012 (Sprint 3 design/prototypes), TRQ-013 (Sprint 4 product wiring)

This file is the durable phase map for Prompt Compilation. Chat is not the canonical plan surface.

## Requested outcome

Move Prompt Kit from a library of hand-maintained English prompts toward a **self-improving prompt compiler**:

- semantic obligations live in `prompt-semantics/v1`;
- compute preference lives in `prompt-execution-profile/v1`;
- bounded compilation context lives in `prompt-context/v1`;
- Language Engine emits effective prompt + build receipt;
- defective instruction construction yields deterministic improvement candidates for reviewed Git PRs only.

## Collision ownership

- **Evidence Spine / P95 owns lifecycle state owners and continuation.** Prompt Compilation must not add event types or a bus.
- **TRQ-007 owns compute-authority A/B measurement.** Do not mutate frozen control/treatment identities inside that study from this lane.
- **PR #450 / #431 remain separately owned donors.** Forbidden until a later authorized reconciliation.
- **Generated `web/prompt-kit/index.html` is builder-owned.** Do not hand-edit.

## Phase map

### Sprint 1 — Contracts, compiler, non-weakening gate, fixtures

**Status:** INTEGRATED on `main` via #483 (`04e4a77d`)

**Owned scope:**

- `prompt-semantics/v1`
- `prompt-context/v1`
- `prompt-execution-profile/v1`
- language compiler contract + CLI
- effective-prompt build receipt
- modality / non-weakening validator
- deterministic improvement-candidate format
- fixtures proving the parallelism modality regression cannot return
- durable architecture + sprint map + ledger index

**Forbidden scope:**

- UI toggle implementation
- #450 / #431 donor work
- raw conversation ingestion
- new Evidence Spine event types
- automatic source mutation
- automatic PR merge
- model-generated policy promotion
- universal event bus

**Validation:**

1. `python -m unittest tests.test_prompt_compilation -v`
2. `python scripts/prompt_language_compiler.py validate-fixtures --summary`
3. `python scripts/validate_repository_work_ledger.py`
4. `git diff --check`

**Proof ceiling:** repository/static VALIDATED + INTEGRATED on default branch. No claim that Prompt Kit UI emits compiled prompts in production.

### Sprint 2 — Thin read-only context adapters + profile resolution

**Status:** INTEGRATED on `main` via #485 (`86044bfb`)

**Owned:** adapters that project dispatch receipts, continuation dispositions, P99 outcome receipts, and recurrence findings into `prompt-context/v1`; profile precedence resolver (`run > prompt > user > product`); focused tests; ledger index TRQ-010.

**Forbidden:** event ownership; UI product surface; auto-promotion; #450/#431 donor salvage; new Evidence Spine event types.

### Sprint 3 — Improvement-Candidate Compiler call-stack prototypes

**Status:** INTEGRATED on `main` via #515 (`50229c36`)

**Dependency:** Sprint 2 INTEGRATED; P95 adapter-only floor present on main.

**Owned:**

- program-design sections in architecture (vocabulary, module map, ownership, call stacks, alternatives)
- phase reorder: Improvement Compiler before UI
- `scripts/prompt_improvement_compiler.py` executable journey
- deterministic hypothesis catalog
- IJ01 success + IJ02 failure journey fixtures
- focused tests for success and consequential failure stacks
- ledger index TRQ-012

**Forbidden:**

- UI Compute Mode toggle / product surface
- #450 / #431 donor work
- raw conversation ingestion
- new Evidence Spine event types / universal event bus
- automatic source mutation
- automatic PR merge
- model-generated policy promotion
- mutating TRQ-007 frozen prompt identities
- hand-editing generated Prompt Kit output

**Expected artifacts:**

- updated `PROMPT_COMPILATION_ARCHITECTURE.md` + this sprint map
- `scripts/prompt_improvement_compiler.py`
- `harness/prompt-compilation/improvement-hypothesis-catalog.v1.json`
- `harness/prompt-compilation/improvement-journeys/IJ01-*`, `IJ02-*`
- `tests/test_prompt_improvement_compiler.py`
- TRQ-012 ledger row

**Validation:**

1. `python -m unittest tests.test_prompt_compilation tests.test_prompt_context_engine tests.test_prompt_improvement_compiler -v`
2. `python scripts/prompt_language_compiler.py validate-fixtures --summary`
3. `python scripts/prompt_improvement_compiler.py run-journey --finding harness/prompt-compilation/improvement-journeys/IJ01-modality-recurrence/finding.json --summary`
4. `python scripts/validate_repository_work_ledger.py`
5. `git diff --check`

**Proof ceiling:** DESIGNED/TRACKED + locally VALIDATED prototypes; INTEGRATED when merged to default branch. No production UI wiring; no auto-PR creation; no claim of observed self-improvement in the field.

**UI Compute Mode remains deferred** to Sprint 4.

### Sprint 4 — Prompt Kit wiring + Compute Mode product surface

**Status:** IMPLEMENTED / VALIDATION PENDING on `feat/prompt-compilation-compute-mode-20260916`

**Owned:** wire compiler into effective-prompt generation path; user-facing Compute Mode (Exhaustive/Efficient) with per-prompt overrides; preserve builder-owned generation.

**Implementation slice:** compiler-owned context-free profile overlays; global user default plus per-prompt override with `run > prompt > user > product` resolver parity; Efficient removes only the shared `EXHAUSTIVE AVAILABLE COMPUTE RULE` section while preserving every other canonical prompt contract; content-only prompts remain unchanged; canonical website regeneration remains builder-owned.

**Forbidden:** weakening safety gates; bypassing builder-owned generation; auto-promotion of improvement candidates.

### Sprint 5 — Improvement-candidate production eval loop hardening

**Status:** PLANNED (dependency: Sprint 3 prototypes + recurrence evidence owners)

**Owned:** broaden fingerprint catalog; optional `Outputs/` draft retention; tighter P115 work-request handoff without absorbing P115 ownership; still `reviewed_pr_only`.

**Forbidden:** auto-merge; model-only policy promotion; Evidence Spine event invention.

## Acceptance for Sprint 3

- Architecture records module map, ownership, SUCCESS CALL STACK, FAILURE CALL STACK, and alternatives compared.
- Sprint map places Improvement Compiler before UI and keeps UI forbidden for Sprint 3.
- IJ01 journey emits candidate + TC06 eval pass + PR draft with `auto_merge=false`.
- IJ02 / missing-evidence / self-authorizing promotion failures fail closed.
- Existing Sprint 1–2 tests remain green.
- Exact validated head integrates to current default branch when gates allow.
