# Prompt Compilation & Adaptive Language — Canonical Sprint Map

**Status:** TRACKED / SPRINT 1 INTEGRATED ON MAIN VIA #483
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Planning floor:** refreshed `main@04e4a77d261d0bd0388daa6d56f38e113cdf79fa` (provider refresh 2026-09-14)
**Architecture authority:** `harness/prompt-compilation/PROMPT_COMPILATION_ARCHITECTURE.md`
**P95 constraint floor:** `harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md` (adapter-only; no universal envelope/bus)
**Ledger index:** TRQ-009

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
- **PR #450 / #431 remain separately owned donors.** Forbidden in Sprint 1.
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

**Expected artifacts:**

- architecture + sprint map under `harness/prompt-compilation/`
- schemas under `harness/contracts/`
- compiler/validator under `scripts/prompt_language_compiler.py`
- gold fixture `TC06-parallelism-modality`
- focused unit tests
- TRQ-009 ledger row

**Validation:**

1. `python -m unittest tests.test_prompt_compilation -v`
2. `python scripts/prompt_language_compiler.py validate-fixtures --summary`
3. `python scripts/validate_repository_work_ledger.py`
4. `git diff --check`

**Proof ceiling:** repository/static VALIDATED + INTEGRATED on default branch. No claim that Prompt Kit UI emits compiled prompts in production.

### Sprint 2 — Thin read-only context adapters + profile resolution

**Status:** PLANNED (dependency: Sprint 1 integrated)

**Owned:** adapters that project dispatch receipts, continuation dispositions, P99/P115/eval/recurrence artifacts into `prompt-context/v1`; profile precedence resolver (`run > prompt > user > product`).

**Forbidden:** event ownership; UI product surface; auto-promotion.

### Sprint 3 — Prompt Kit wiring + Compute Mode product surface

**Status:** PLANNED (dependency: Sprint 2)

**Owned:** wire compiler into effective-prompt generation path; user-facing Compute Mode (Exhaustive/Efficient) with per-prompt overrides.

**Forbidden:** weakening safety gates; bypassing builder-owned generation.

### Sprint 4 — Improvement-candidate eval loop

**Status:** PLANNED (dependency: Sprint 1 fixtures + recurrence evidence owners)

**Owned:** recurrence → candidate → gold fixture → deterministic eval → PR draft path; still reviewed_pr_only.

**Forbidden:** auto-merge; model-only policy promotion.

## Acceptance for Sprint 1

- Architecture and sprint map are tracked and reference P95 constraints.
- Three IRs + build receipt + improvement-candidate schemas validate examples.
- Language Engine rejects weakening language for MUST + exhaustive + parallel-ready context.
- Language Engine accepts imperative dispatch semantics with typed failure + proof requirement.
- Improvement candidate format requires evidence refs, affected authority, required regressions, and `reviewed_pr_only`.
- No forbidden-scope mutations appear in the Sprint 1 diff.
