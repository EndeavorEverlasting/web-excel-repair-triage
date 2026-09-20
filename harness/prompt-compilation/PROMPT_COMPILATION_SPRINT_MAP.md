# Prompt Compilation & Adaptive Language — Canonical Sprint Map

**Status:** TRACKED / SPRINTS 1–6 INTEGRATED; P07 CANONICAL-COPY RECOVERY INTEGRATED VIA #607; SPRINT 7 IMPLEMENTING
**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Planning floor:** refreshed `main@6330440281d7d970db726140b44f033be819c9d0` (provider refresh 2026-09-17)
**Architecture authority:** `harness/prompt-compilation/PROMPT_COMPILATION_ARCHITECTURE.md`
**P95 constraint floor:** `harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md` (adapter-only; no universal envelope/bus)
**Ledger index:** TRQ-009 (Sprint 1), TRQ-010 (Sprint 2), TRQ-012 (Sprint 3), TRQ-013 (Sprint 4 wiring), TRQ-014 (Sprint 5 eval hardening), TRQ-015 (Sprint 6 browser proof)

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

**Status:** INTEGRATED on `main` via #519 (`c4d065fa`)

**Dependency:** Sprint 3 INTEGRATED on main (`50229c36` / TRQ-012).

**Owned:**

- `docs/prompt-kit-compute-mode.js` (user default + prompt overrides + run override; Exhaustive/Efficient UI)
- storage lifecycle personal-state keys for Compute Mode
- polish copy routing through `PromptKitComputeMode.resolveCopyContent` while preserving operator-visible canonical `copyContent`; global/user/run execution-profile resolution may not replace a present canonical body, and a compiled Efficient variant may replace canonical copy only after an explicit per-prompt Efficient choice
- builder Language Engine attachment of `compiledEffectivePrompts` for semantics-backed prompts (P07)
- `harness/prompt-compilation/semantics/P07.json` + `build-context/default.v1.json`
- regenerate `web/prompt-kit/index.html` via `scripts/build_prompt_kit_registry.py`
- focused tests `tests/test_prompt_kit_compute_mode.py`
- ledger index TRQ-013

**Forbidden:** weakening safety gates; bypassing builder-owned generation; auto-promotion of improvement candidates; #450/#431 donor work; mutating TRQ-007 frozen prompt identities; hand-editing generated HTML outside the builder.

**Validation:**

1. `python -m unittest tests.test_prompt_kit_compute_mode tests.test_prompt_compilation tests.test_prompt_context_engine tests.test_prompt_improvement_compiler -v`
2. `python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check`
3. `python scripts/validate_repository_work_ledger.py`
4. `git diff --check`

**Proof ceiling:** repository/static VALIDATED + INTEGRATED when merged. Browser/operator UX acceptance of the Compute Mode control remains UNPROVEN_RUNTIME until a live browser proof is recorded.

### Sprint 5 — Improvement-candidate production eval loop hardening

**Status:** INTEGRATED on `main` via #522 (`5f55e2a9`)

**Dependency:** Sprint 3 INTEGRATED; Sprint 4 INTEGRATED on main (`c4d065fa` / TRQ-013).

**Owned:**

- broaden fingerprint / hypothesis catalog across language-engine, execution-profile, prompt-context, prompt-semantics, and fixtures authorities
- gold fixture `TC07-mainline-convergence-proof` plus journey `IJ03-mainline-proof-recurrence`
- optional `Outputs/prompt-improvement-drafts/` draft retention (`--retain-draft`; paths must stay under `Outputs/`)
- tighter P115-compatible work-request handoff (`evidence-spine-p115-work-request/v1` shape) without absorbing P115 ownership
- still `reviewed_pr_only`; focused tests; ledger index TRQ-014

**Forbidden:** auto-merge; model-only policy promotion; Evidence Spine event invention; absorbing P115 ownership; #450/#431 donor work; mutating TRQ-007 frozen prompt identities.

**Validation:**

1. `python -m unittest tests.test_prompt_improvement_compiler tests.test_prompt_compilation tests.test_prompt_context_engine -v`
2. `python scripts/prompt_improvement_compiler.py run-journey --finding harness/prompt-compilation/improvement-journeys/IJ03-mainline-proof-recurrence/finding.json --summary`
3. `python scripts/validate_repository_work_ledger.py`
4. `git diff --check`

**Proof ceiling:** repository/static VALIDATED + INTEGRATED when merged. Live P115 recovery queue consumption and operator draft retention in production remain UNPROVEN_RUNTIME.

### Sprint 6 — Compute Mode observed browser proof

**Status:** HISTORICAL SPRINT COMPLETE; canonical-copy acceptance corrected by the P07 recovery lane after #524 reintroduced compiled-copy routing.

**Dependency:** Sprint 4 Compute Mode product surface INTEGRATED; Sprint 5 hardening INTEGRATED; existing observed-behavior proof harness present on current main.

**Owned:**

- exact-head Playwright proof of Compute Mode product default, persisted user default, per-prompt override, explicit run override, and canonical P07 clipboard identity while profile resolution remains observable metadata
- `browser_runtime_observed` receipt + screenshot under CI `Outputs/observed-proof/`
- observed-proof manifest registration, exact-head preflight regression, and owning workflow execution
- Sprint-6 plan/ledger continuity only; no product behavior mutation unless the observed proof exposes an in-scope defect

**Forbidden:**

- changing Compute Mode semantics or profile precedence merely to make the proof pass
- new Evidence Spine events or lifecycle ownership
- #450/#431 donor work
- mutating TRQ-007 frozen control/treatment identities
- raw conversation/transcript/clipboard persistence outside the ephemeral browser assertion
- auto-promotion/auto-merge of improvement candidates
- hand-editing generated `web/prompt-kit/index.html`

**Expected artifacts:**

- `tests/prompt_kit_compute_mode_browser_proof.py`
- `Outputs/observed-proof/compute-mode-receipt.json` and screenshot as untracked CI artifacts
- updated `harness/observed-proof/manifest.v1.json`
- updated `.github/workflows/prompt-kit-observed-browser-proof.yml`
- focused exact-head harness regression
- ledger index TRQ-015

**Validation:**

1. `python -m unittest tests.test_observed_behavior_proof_harness tests.test_prompt_kit_compute_mode tests.test_p07_effective_prompt_identity -v`
2. `python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check`
3. `python tests/prompt_kit_compute_mode_browser_proof.py --receipt Outputs/observed-proof/compute-mode-receipt.json --screenshot Outputs/observed-proof/compute-mode.png`
4. `python scripts/validate_observed_behavior_receipt.py Outputs/observed-proof/compute-mode-receipt.json --expected-sha "$(git rev-parse HEAD)" --summary`
5. `python scripts/validate_repository_work_ledger.py`
6. `git diff --check`

**Proof ceiling:** exact-head headless Chromium may promote the Compute Mode browser journey to `browser_runtime_observed`. It does not prove public-Pages deployment, physical-device/operator acceptance, external-agent behavior, or live P115 consumption.

### Sprint 7 — Explicit per-prompt content variants

**Status:** IMPLEMENTING on PR #608 from recovered `main@1ea0e465ab20b8fcb7a6071d85345e0c3916eabb`.

**Dependency:** #607 restored canonical P07 copy identity and retained it in the deterministic floor. Sprint 7 may expose compiled variants again only behind an explicit prompt-level user choice; it may not reintroduce compiled-first clipboard routing.

**Product contract:**

- Exhaustive is the product/default prompt-content variant and maps to the full canonical `copyContent` when canonical content exists.
- Efficient is an optional shorter compiled variant and is selected only by an explicit per-prompt control in that prompt's detail panel.
- Global Compute Mode user preference and explicit run profile remain execution-policy metadata; neither may silently change the clipboard body of a canonical prompt.
- Selecting Efficient stores only that prompt's sparse override. Selecting Exhaustive clears the prompt override and returns to the full canonical body.
- The detail control mounts lazily only for a prompt that actually exposes at least two usable variants. Prompts without variants render no per-prompt variant control.
- Catalog size must not create one persistent UI control or stored override per prompt. Variant UI cost follows the opened detail/variant-bearing prompt, not total catalog size.

**Owned:**

- `docs/prompt-kit-compute-mode.js` explicit variant discovery, copy resolution, lazy detail control, and sparse override behavior
- retained P07 copy-identity regression in `tests/test_p07_effective_prompt_identity.py`
- focused Compute Mode regression in `tests/test_prompt_kit_compute_mode.py` and deterministic-floor registration
- exact-head browser journey proving visible variant selection, preview, clipboard, sparse storage, reset-to-Exhaustive, and no selector on a non-variant prompt
- canonical builder regeneration of `web/prompt-kit/index.html`

**Forbidden:**

- rewriting canonical P07 content or weakening its execution contract
- changing PromptSemantics/compiler obligations merely to make a UI test pass
- global/user/run profile changes that silently select Efficient prompt content
- eager per-card/per-catalog variant controls or preallocated override state
- hand-editing generated `web/prompt-kit/index.html`

**Validation:**

1. `python -m unittest tests.test_p07_effective_prompt_identity tests.test_prompt_kit_compute_mode -v`
2. `python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check`
3. `python tests/prompt_kit_compute_mode_browser_proof.py --receipt Outputs/observed-proof/compute-mode-receipt.json --screenshot Outputs/observed-proof/compute-mode.png`
4. `python scripts/validate_observed_behavior_receipt.py Outputs/observed-proof/compute-mode-receipt.json --expected-sha "$(git rev-parse HEAD)" --summary`
5. `python scripts/run_deterministic_test_floor.py --summary`
6. `git diff --check`

**Proof ceiling:** repository tests and generated parity prove the explicit variant contract statically; exact-head headless Chromium may prove it at `browser_runtime_observed`. Neither proves physical-device/operator acceptance or external-agent behavior.

**Review reconciliation:**

- Fixed variant eligibility so a prompt exposes Efficient only when a real compiled Efficient body exists; canonical fallback no longer creates a phantom Efficient option on every copyable prompt.
- Normalized explicit prompt-profile casing before content selection, so `Efficient` and `efficient` cannot diverge.
- Proved card/detail clipboard convergence through the final `docs/prompt-kit-polish.js` `window.copyPrompt` owner, which delegates to `PromptKitComputeMode.resolveCopyContent`; no duplicate detail-copy implementation was introduced.
- Regenerated the checked-in Prompt Kit only through `scripts/build_prompt_kit_registry.py`; temporary provider materialization infrastructure is not retained.

## Acceptance for Sprint 3

- Architecture records module map, ownership, SUCCESS CALL STACK, FAILURE CALL STACK, and alternatives compared.
- Sprint map places Improvement Compiler before UI and keeps UI forbidden for Sprint 3.
- IJ01 journey emits candidate + TC06 eval pass + PR draft with `auto_merge=false`.
- IJ02 / missing-evidence / self-authorizing promotion failures fail closed.
- Existing Sprint 1–2 tests remain green.
- Exact validated head integrates to current default branch when gates allow.
