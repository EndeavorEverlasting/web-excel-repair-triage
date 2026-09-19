# Prompt Semantic Capability Coverage — Sprint Map

## Status

TRACKED / PLANNED / NOT YET IMPLEMENTED

Repository: `EndeavorEverlasting/web-excel-repair-triage`

Planning floor refreshed through: `main@42c53fa6445d39aa74dabdfeec4eb45bfa5d7a4d`

Primary owners:

- prompt identity/admission/topology: P79 + executable Prompt Topology;
- recurring-process hardening: P13;
- retained regression interpretation: P94;
- canonical prompt text/history: Prompt Quality History;
- global shared execution-strength floor: Prompt Strength.

This program adds a missing semantic-history layer. It does **not** create a new Prompt Kit identity, replace Prompt Strength, replace Prompt Quality History, or let generated topology artifacts become prompt-registry authority.

## Mission

Protect Prompt Kit behavior across ADD, EDIT/STRENGTHEN, and RETIRE by making each prompt's accepted semantic capabilities versioned repository truth.

A prompt change must be evaluated against the previous accepted capability profile, not against a freshly regenerated model opinion. The system must detect when a change preserves syntax, prompt ID, generated-site parity, or superficial length while silently removing an existing behavior.

The human-friendly prompt-by-capability matrix is a deterministic projection of canonical versioned profiles.

## Why this layer is needed

Current protections prove important but different things:

1. Prompt Quality History: canonical prompt text/source history did not silently drift.
2. Prompt Strength: global shared semantic dimensions required across operational execution profiles are not weakened.
3. Prompt Topology/P79: identity, similarity, overlap, family/cluster, and strengthen-before-add admission are governed.
4. Prompt Language Audit: canonical/effective coverage, fields, actionability language, and registry parity are complete.
5. Regression Safety/P94: recurring defects become retained fixtures and canonical-owner repairs.
6. Runtime Compliance: selected execution behavior can be observed against exact model/config/runtime evidence.

Missing layer:

> What specific use cases, qualities, obligations, and ownership relationships did each accepted prompt provide, and did that set weaken, disappear, transfer, or become redundantly crowded after a change?

## Current defects this program must close

### D1 — base registry is outside Prompt Quality History

`docs/prompts.json` is the canonical base registry but is not currently present in `harness/contracts/prompt-quality-history.v1.json:canonical_body_sources`.

The dedicated `.github/workflows/prompt-quality-history.yml` path filter also does not include `docs/prompts.json`.

The quality-history validator must derive/compare its protected source set against the complete canonical prompt-source set from current product boundaries/builder truth so future registries cannot silently fall outside history protection.

### D2 — removal/retirement is not a first-class lifecycle operation

`scripts/prompt_registry_ops.py` supports inspect/prior-art/add/validate but no canonical RETIRE operation. A removed prompt can therefore lose unique semantic coverage without a universal successor/transfer calculation.

### D3 — semantic migrations describe text/source transitions, not per-prompt capability transitions

`prompt-semantic-migrations/v1` records affected IDs, source hashes, rationale, and tests, but does not prove which prompt capabilities were preserved, strengthened, transferred, or intentionally removed.

### D4 — no accepted per-prompt semantic prior

Prompt Topology can derive similarity/cluster evidence and Prompt Strength defines shared dimensions, but no canonical tracked artifact says, for every prompt, “these are the capabilities this accepted version provides.”

Without that prior, a later agent can re-interpret a weakened candidate as equally strong.

## Canonical architecture

```text
Canonical Prompt Registry
        |
        +--> Prompt Quality History
        |    protects canonical source/text lineage
        |
        +--> Prompt Topology canonical record
        |    supplies stable prompt identity + canonical content hash
        |
        v
Semantic Capability Catalog
        |
        v
Accepted Prompt Capability Profiles
        |
        +--> Prompt x Capability Matrix (derived)
        +--> Global Coverage / Overlap Report (derived)
        |
        v
Capability Migration Chain
ADD / STRENGTHEN / CHANGE / TRANSFER / RETIRE
        |
        v
Semantic Coverage Validator
        |
        +--> P79 admission/edit/retirement gate
        +--> P94/P13 retained regression loop
        +--> Prompt Quality History semantic-migration gate
        +--> optional Runtime Compliance calibration
```

## Authority boundary

The new semantic-coverage layer is canonical governance metadata, not generated prompt text.

It also composes with `prompt-kit-ontology-evidence/v1`. Where evidence/history records already exist, profile evidence references should reuse the repository chain `capability -> skill -> implementation/prompt -> invocation/run -> evidence -> proof ceiling` rather than creating a second runtime/evidence-history store.

Recommended canonical tracked owners:

- `harness/contracts/prompt-semantic-coverage.v1.json`
- `harness/prompt-topology/semantic-capability-catalog.v1.json`
- `harness/prompt-topology/prompt-capability-profile.schema.v1.json`
- `harness/prompt-topology/prompt-capability-profiles.v1.json`
- `harness/prompt-topology/prompt-capability-migrations.v1.json`

Derived/reconstructable views:

- `artifacts/prompt-semantic-coverage/matrix.v1.json`
- `artifacts/prompt-semantic-coverage/coverage-report.v1.json`
- `artifacts/prompt-semantic-coverage/overlap-report.v1.json`
- optional CSV/Markdown human projection.

The generated matrix must never become a second editable source of truth.

## Capability-cell model

Do not encode semantic state as a single Boolean.

Each prompt/capability assignment must separate:

- **presence**: `NONE | AWARE | SUPPORT | REQUIRED`
- **ownership**: `NONE | SECONDARY | PRIMARY`
- **capability_relation**: `IMPLEMENTS | ROUTES_TO | TESTS | GUARDS | FORBIDDEN`
- **delivery_source**: `CANONICAL_BODY | SHARED_POLICY | COMPILER_OVERLAY | ROUTED_OWNER | TEST_GUARD`
- **evidence_refs**: one or more repository-owned proof references for material assignments
- **rationale**: short bounded explanation for PRIMARY/REQUIRED/FORBIDDEN assignments

`capability_relation` describes how one prompt relates to one capability; it is **not** a new prompt-to-prompt topology edge vocabulary.

Prompt-to-prompt behavioral relationships must reuse the executable Prompt Topology reserved channels:

- `CO_USAGE`
- `TRANSITION`
- `SUBSTITUTION`
- `COMPLEMENT`

A semantic-coverage implementation may derive or validate those channels from accepted profiles, but must not introduce competing synonyms for the same prompt-to-prompt concepts.

Direct versus inherited semantics:

- direct assignments are owned by the prompt profile;
- shared-policy/compiler assignments may be referenced through versioned inherited-source records instead of copied N times across every prompt;
- the derived matrix expands those inherited sources so every prompt still receives a complete visible cell;
- a shared source revision change invalidates/revalidates every dependent derived cell without pretending each prompt body changed;
- PRIMARY ownership should normally remain with the canonical direct owner even when many prompts inherit REQUIRED behavior from a shared source.

The familiar display label may project:

- PRIMARY when ownership=PRIMARY;
- REQUIRED when presence=REQUIRED;
- SUPPORT when presence=SUPPORT;
- AWARE when presence=AWARE;
- NONE otherwise.

This avoids pretending PRIMARY and REQUIRED are one ordinal concept.

## Capability catalog contract

Every capability definition must include:

- stable `capability_id`;
- title and definition;
- class/domain;
- aliases/search terms;
- admissible relations;
- evidence requirements;
- global coverage policy;
- overlap policy;
- seed/provenance references.

Suggested global coverage policies:

- `AT_LEAST_ONE_PRIMARY`
- `AT_LEAST_ONE_REQUIRED_OR_PRIMARY`
- `OPTIONAL`
- `EXACTLY_ONE_PRIMARY`

Evidence lineage rules:

- a prompt profile may identify the prompt as the capability implementation locator;
- static repository proof may reference focused tests/contracts directly;
- observed/runtime evidence should reference existing ontology-evidence/proof receipts when available;
- preference, critique, or feedback records do not automatically prove a capability assignment;
- candidate inference is evidence input only and cannot mutate accepted profile history.

Suggested overlap policies:

- `OVERLAP_EXPECTED`
- `OVERLAP_ALLOWED_WITH_RATIONALE`
- `PRIMARY_CROWDING_WARNING`
- `PRIMARY_CROWDING_FAIL`

Prompt Strength dimensions are a seed vocabulary for shared execution behavior, not the whole catalog. Additional capability IDs come from current prompt use cases, topology roles, existing prompt tests/contracts, registered harness use cases, and reviewed retrospective evidence.

## Prompt capability profile contract

Every current prompt receives exactly one accepted profile.

Required fields include:

- `prompt_id`
- `profile_version`
- `profile_sha256`
- canonical prompt record hash / source identity
- acceptance commit/revision
- direct assignment list
- inherited semantic-source identity/revision list
- semantic dependency fingerprint
- evidence references
- profile status
- prior profile reference when version > 1

Allowed statuses:

- `PROVISIONAL`
- `REVIEW_READY`
- `ACCEPTED`
- `RETIRED`

Only `ACCEPTED` profiles are regression priors.

A proposal generator may suggest assignments, but may never overwrite an ACCEPTED profile.

## Capability migration contract

Every lifecycle transition after baseline acceptance must be explicit.

Body-changing capability migrations must cross-reference the corresponding `prompt-semantic-migrations/v1` source-history transition instead of becoming an independent competing record. The two ledgers must agree on prompt IDs and source hashes.

Migration kinds:

- `ADD`
- `STRENGTHEN`
- `NO_CAPABILITY_CHANGE`
- `INTENTIONAL_CHANGE`
- `TRANSFER`
- `RETIRE`
- `RESTORE`

Required fields:

- migration ID;
- prompt ID;
- old/new canonical prompt hash where applicable;
- from/to profile version and profile hash;
- capability deltas;
- rationale;
- evidence refs;
- focused tests;
- successor/transfer targets when responsibility moves;
- coverage-before and coverage-after fingerprint;
- review/acceptance state.

Migration history is append-only. A later accepted transition chains from the current accepted profile hash.

## Non-weakening rules

Initial semantic rules:

- **PSC001 PROFILE_COVERAGE_COMPLETE** — every current prompt has exactly one ACCEPTED profile before strict enforcement may activate.
- **PSC002 PROFILE_BINDS_CANONICAL_PROMPT** — accepted profile binds to exact prompt identity and canonical record hash.
- **PSC003 KNOWN_CAPABILITY_ONLY** — every assignment references the stable catalog.
- **PSC004 REQUIRED_PRESENCE_NON_WEAKENING** — REQUIRED may not fall to SUPPORT/AWARE/NONE without an explicit accepted migration.
- **PSC005 PRIMARY_OWNERSHIP_NON_WEAKENING** — PRIMARY may not fall to SECONDARY/NONE unless responsibility is explicitly transferred or intentionally retired with coverage proof.
- **PSC006 TRANSFER_EQUAL_OR_STRONGER** — a transfer is accepted only when successor coverage is equal-or-stronger for the protected capability and required proof exists.
- **PSC007 RETIRE_NO_COVERAGE_HOLE** — retirement fails if it produces an uncovered previously protected capability.
- **PSC008 ADD_REQUIRES_DISTINCT_RESIDUAL** — P79 cannot ADD when topology/profile overlap shows an existing owner can absorb the use case without a reviewed distinct residual.
- **PSC009 BODY_CHANGE_REQUIRES_PROFILE_DISPOSITION** — any changed canonical prompt body must have a capability migration or an exact no-capability-change attestation bound to focused proof.
- **PSC010 SAME_AGENT_RESCORING_CANNOT_RESET_PRIOR** — generated/proposed candidate profiles cannot replace accepted history.
- **PSC011 NEW_PRIMARY_OR_REQUIRED_REQUIRES_PROOF** — strengthening claims need evidence, not just a higher self-assigned rating.
- **PSC012 GLOBAL_PRIMARY_CROWDING_REVIEW** — unexpected multiple PRIMARY owners trigger configured warning/fail policy.
- **PSC013 SOURCE_HISTORY_COMPLETE** — every canonical prompt body source, including `docs/prompts.json`, is covered by Prompt Quality History.
- **PSC014 LIFECYCLE_TRANSITION_ATOMIC** — ADD/STRENGTHEN/RETIRE cannot leave registry, profile, migration, generated site, or required semantic proof mutually inconsistent.
- **PSC015 SOURCE_AND_CAPABILITY_MIGRATION_LINK** — body-changing profile transitions must reference the matching Prompt Quality History semantic migration and agree on source hashes/affected IDs.
- **PSC016 INHERITED_SOURCE_INTEGRITY** — shared policy/compiler capability inheritance is versioned by source identity/revision; dependent matrix cells cannot remain accepted against a changed inherited source without revalidation.

## Lifecycle semantics

### ADD

P79 remains admission owner.

Required sequence:

1. current internal topology/profile overlap;
2. registered external prior-art;
3. distinct residual proof;
4. candidate semantic profile;
5. capability-overlap/coverage simulation plus existing Prompt Topology CO_USAGE/SUBSTITUTION/COMPLEMENT evidence;
6. identity allocation through `prompt_registry_ops.py`;
7. ADD capability migration;
8. quality-history source migration;
9. focused semantic tests;
10. generated-site parity;
11. required checks/integration.

A candidate highly overlapping an existing PRIMARY owner defaults to STRENGTHEN/ROUTE, not CREATE_NEW.

### EDIT / STRENGTHEN

Before changing text:

1. load the accepted profile as immutable prior;
2. bind the candidate prompt hash plus inherited semantic-source fingerprint;
3. compute declared direct/inherited capability deltas;
4. run every proof attached to protected PRIMARY/REQUIRED assignments;
5. reject unexplained downgrade;
6. require migration when responsibility changes;
7. retain history after integration.

A longer prompt, valid JSON, passing builder, or preserved ID is never sufficient semantic proof.

### RETIRE

Retirement becomes a first-class `prompt_registry_ops.py retire` or equivalent canonical operation.

Before removal:

1. load accepted profile;
2. enumerate every PRIMARY/REQUIRED capability;
3. calculate current alternate owners and existing SUBSTITUTION/COMPLEMENT topology edges;
4. require successor transfer for coverage that would otherwise disappear, recording TRANSITION/SUBSTITUTION relationships through the existing topology vocabulary;
5. run global coverage simulation;
6. scan discovery/routing/topology/test references;
7. write RETIRE migration + tombstone profile;
8. remove registry identity only after semantic/routing gates pass;
9. rebuild and validate site;
10. retain historical profile/migration forever.

A retired P-number is never silently reused.

## Baseline bootstrapping

The first accepted matrix is special.

Do **not** ask a model to regenerate canonical truth from scratch and then treat its output as proof.

Bootstrap pipeline:

1. load every canonical prompt through Prompt Topology canonical records;
2. seed candidate capability vocabulary from:
   - Prompt Strength dimensions as inherited/shared obligations where appropriate, not falsely attributed direct ownership;
   - registry `useWhen`, `sprintRole`, `expectedOutput`, `proofGate`;
   - existing prompt-specific tests;
   - existing harness capabilities/use cases;
   - topology relationships, including reserved CO_USAGE/TRANSITION/SUBSTITUTION/COMPLEMENT channels;
   - existing ontology-evidence capability lineage;
   - reviewed retrospective evidence;
3. emit **PROVISIONAL** profile proposals only;
4. attach evidence refs to every proposed PRIMARY/REQUIRED assignment;
5. produce ambiguity/coverage/crowding report;
6. resolve all required ambiguities;
7. accept one complete baseline matrix at an exact repository revision;
8. freeze its profile hashes as the first regression prior.

No strict candidate-change gate activates until PSC001 baseline completeness is proven.

## Agent-harness factoring

### Existing skill: `prompt-language-audit`

Disposition: KEEP.

It owns wording/actionability/coverage audit. It does not become semantic capability history.

### Existing skill: `skill-evaluation`

Disposition: KEEP.

It owns executable effectiveness/runtime evaluation. It may later consume semantic profile IDs as experiment targets but does not own profile truth.

### Existing P79 prompt/topology route

Disposition: KEEP + REWIRE.

P79 remains identity/admission owner. Add/strengthen/retire operations must call the semantic coverage gate instead of relying only on text overlap/prior-art.

### New skill: `prompt-semantic-coverage`

Disposition: CREATE.

Activation:

- canonical prompt ADD/EDIT/RETIRE;
- semantic migration touching prompt behavior;
- capability catalog/profile/migration changes;
- validator reports a semantic coverage regression.

Inputs:

- canonical registry;
- current accepted profiles;
- capability catalog;
- candidate prompt/migration;
- topology/prior-art evidence;
- focused tests.

Outputs:

- semantic diff;
- coverage/overlap report;
- migration disposition;
- PASS/FAIL receipt;
- exact proof ceiling.

Guardrails:

- no automatic ID allocation outside P79;
- no accepted-profile overwrite from generated inference;
- no runtime-behavior claim from static evidence;
- no raw/private transcript persistence.

### New capability: `prompt-semantic-coverage`

Disposition: CREATE.

Implementation owners:

- profile/matrix builder;
- semantic coverage validator;
- lifecycle bridge in `prompt_registry_ops.py`.

### New trigger: `prompt-semantic-lifecycle-change`

Disposition: CREATE.

Conditions:

- canonical prompt body added/edited/removed;
- prompt semantic migration changes;
- profile/catalog/migration changes;
- retirement/admission requested.

Forbidden conditions:

- generated-site-only rebuild;
- documentation-only change;
- runtime observation with no canonical prompt mutation;
- unrelated registry metadata presentation changes proven semantically inert.

## Sprint map

### Sprint 0 — History completeness + semantic coverage contract floor

Classification: floor / harness spine.

Owned scope:

- `harness/contracts/prompt-quality-history.v1.json`
- `scripts/validate_prompt_quality_history.py`
- `tests/test_prompt_quality_history.py`
- `.github/workflows/prompt-quality-history.yml`
- new semantic coverage contract/schema/catalog/profile/migration owners under `harness/contracts/` and `harness/prompt-topology/`
- contract-focused tests

Mission:

1. bring `docs/prompts.json` under Prompt Quality History;
2. make the validator fail if protected canonical source paths do not equal actual builder/product-boundary prompt sources;
3. establish exact semantic capability/profile/migration schemas and PSC rules;
4. preserve Prompt Strength and Prompt Topology authority boundaries.

Forbidden:

- populating the full baseline profile matrix;
- P79 wording changes;
- root harness/validator registration while PR #584 owns shared harness files;
- `.ai/WORK_QUEUE.md`;
- generated Prompt Kit HTML.

Completion gate:

- source-history set parity is exact;
- base registry is history-protected;
- synthetic contract fixtures prove weakening/transfer/retirement rule shapes;
- no profile inference is promoted to accepted truth.

Proof ceiling: VALIDATED contract/history floor, not full Prompt Kit semantic coverage.

### Sprint 1A — Baseline profile extraction and accepted matrix

Classification: validation / data-model population.

Dependencies: Sprint 0 integrated.

Safe parallel sibling: Sprint 1B.

Owned scope:

- proposal/baseline builder;
- `prompt-capability-profiles.v1.json`;
- derived matrix/coverage/overlap artifacts;
- profile evidence mapping and baseline acceptance tests.

Mission:

1. produce PROVISIONAL profiles for every canonical prompt;
2. bind assignments to evidence;
3. resolve ambiguity and crowding;
4. accept one complete baseline matrix;
5. prove deterministic derived matrix reconstruction.

Forbidden:

- semantic validator/lifecycle engine implementation owned by Sprint 1B;
- P79 registry mutations;
- root harness registries;
- altering prompt bodies merely to make classification easier.

Completion gate:

- every current prompt has exactly one ACCEPTED profile;
- profile count equals canonical prompt count;
- every PRIMARY/REQUIRED assignment is evidence-backed;
- derived matrix and reports are deterministic;
- no unexplained coverage holes remain.

Proof ceiling: accepted static semantic baseline only.

### Sprint 1B — Semantic diff validator + lifecycle engine

Classification: validation / integration seam.

Dependencies: Sprint 0 integrated.

Safe parallel sibling: Sprint 1A.

Owned scope:

- `scripts/validate_prompt_semantic_coverage.py`
- semantic diff/coverage engine;
- focused positive/negative fixtures;
- `prompt_registry_ops.py` lifecycle extensions;
- synthetic profile/migration fixtures.

Mission:

1. enforce PSC001–PSC014 against synthetic fixtures;
2. implement ADD/STRENGTHEN/NO_CHANGE/TRANSFER/RETIRE semantics;
3. reject downgrade without migration;
4. reject retirement holes;
5. reject unproved new PRIMARY/REQUIRED assignments;
6. enforce append-only profile/migration history;
7. simulate global coverage before mutation.

Forbidden:

- editing the real accepted baseline profile file owned by Sprint 1A before convergence;
- root harness registrations;
- generated website hand edits;
- automatic runtime claims.

Completion gate:

- negative fixtures fail for silent weakening, last-owner deletion, fake strengthening, self-rescoring baseline reset, and invalid transfer;
- positive controls pass for strengthening, no-capability-change edit, equal-or-stronger transfer, and valid retirement.

Proof ceiling: executable static semantic-regression engine against fixtures.

### Sprint 2 — P79 lifecycle convergence + required-check enforcement

Classification: harness convergence / integration.

Dependencies:

- Sprint 1A integrated;
- Sprint 1B integrated;
- refresh/reconcile PR #584 before touching `harness/manifest.v1.json` or `harness/validators.v1.json`.

Convergence owner: Sprint 1B owner or dedicated coordinator after both lanes return.

Owned shared surfaces after dependency refresh:

- `scripts/prompt_registry_ops.py` final current-baseline wiring;
- P79 canonical prompt source + focused tests if wording must expose the machine gate;
- `harness/capabilities.v1.json`
- `harness/triggers.v1.json`
- `harness/workflows.v1.json`
- `WORKFLOW.md`
- `harness/validators.v1.json`
- `harness/test-floor.v1.json`
- `harness/manifest.v1.json` only after PR #584 reconciliation;
- artifact registry for derived matrix/report;
- dedicated workflow/required-check registration;
- generated Prompt Kit site only through canonical builder if P79 text changes.

Mission:

1. wire accepted baseline + validator into every canonical prompt lifecycle mutation path;
2. make semantic coverage a blocking required check for relevant Prompt Kit changes;
3. register the new skill/capability/trigger;
4. require profile/migration consistency in P79 ADD/EDIT/RETIRE operations;
5. prove existing ADD path still works;
6. prove deliberate RETIRE path preserves or transfers coverage;
7. run complete Prompt Kit parity/quality/strength/topology/semantic-coverage checks;
8. integrate exact green candidate.

Completion gate:

- direct unsupported registry edit that weakens a protected profile fails;
- P79 helper cannot add without candidate profile and distinct residual;
- retire cannot remove the final protected owner;
- body edit cannot merge without capability disposition;
- root required-check profile includes semantic coverage;
- generated website equals canonical builder output;
- exact validated candidate is integrated into refreshed default branch.

Proof ceiling: INTEGRATED repository/static semantic lifecycle enforcement; downstream model behavior remains separate runtime proof.

## Dependency graph

```text
Sprint 0
   |
   +------------------+
   |                  |
Sprint 1A          Sprint 1B
   |                  |
   +--------+---------+
            |
         Sprint 2
```

Maximum meaningful graph width after Sprint 0: 2.

## Parallel execution posture

Current planning runtime evidence:

- no native child/sub-agent API is exposed;
- no repository-local autonomous coding worker is available to this coordinator;
- AgentSwitchboard/FirstMate remains an identified autonomy gap rather than a working adapter here;
- connected GitHub provider can inspect/mutate known repository objects but is not an independent implementation worker;
- CI can execute deterministic checks but cannot author the semantic baseline/validator lanes;
- no local concurrent process/worktree execution surface is mounted here.

Therefore, when Sprints 1A and 1B become dependency-ready:

`PARALLEL EXECUTION: DEGRADED`

AUTONOMY_GAP:

`Provide an evidenced repository/local agent worker capable of consuming the prompt-parallel-dispatch lane contract, owning an isolated branch/worktree, authoring code/data, and returning an exact-head receipt. Until then, portability panels are fallback rather than automation-complete dispatch.`

## Global dispatch manifest collision

Current `Outputs/prompt-parallel-dispatch/manifest.json` belongs to run:

`ssh-local-execution-bridge-floor-20260918`

It must not be silently overwritten while that orchestration remains the active owner.

This semantic-coverage plan therefore preserves the intended lane graph here until the global manifest owner releases or converges. At activation time the coordinator must:

1. refresh current manifest/run ownership;
2. preserve/close the prior run safely;
3. materialize this program into `Outputs/prompt-parallel-dispatch/manifest.json`;
4. validate it with `scripts/prompt_parallel_dispatch.py validate`;
5. dispatch only through an actually available adapter;
6. require `observed_parallelism=true` for a clean width-2 parallel PASS.

## Shared-file / PR collision ledger

### PR #584

Current state after refresh: open and mergeable; head `ee0c89d58139300e251b5187ad189e91b6d808c7`.

Owns shared:

- `harness/manifest.v1.json`
- `harness/validators.v1.json`
- `scripts/validate_harness.py`
- root hooks/tests.

Rule:

Sprint 2 must refresh/reconcile #584 before modifying those surfaces. Do not stack stale assumptions on the current PR head.

### PR #570

Current state after refresh: merged on 2026-09-19 as part of current main.

No remaining semantic-coverage shared-file collision.

### PR #524

Current state after refresh: open and merge-conflicted/diverged from current main; remains a stale shared-file owner for `.ai/WORK_QUEUE.md`.

Still changes `.ai/WORK_QUEUE.md`.

Rule:

Do not write the P66 ledger path from this program while #524 remains an unresolved writer. After it is closed/superseded/reconciled, index this plan rather than duplicating it.

### PR #544

Current state after refresh: open and currently non-mergeable/diverged; owns observatory + root harness files.

No semantic-profile mutation overlap, but Sprint 2 must refresh shared harness ownership before convergence.

## P66 continuity

Desired ledger entry after the ledger path is released:

- plan: `harness/prompt-topology/PROMPT_SEMANTIC_CAPABILITY_COVERAGE_SPRINT_MAP.md`
- owner: P79/topology + P94 regression interpretation
- current phase
- strongest proof
- next executable action
- exact blockers/collisions.

The ledger is an index only; this document remains the complete phase map.

## Validation strategy

### Contract/floor

- Prompt Quality History validator and tests;
- source-set mutation fixture proving `docs/prompts.json` omission fails;
- profile/catalog/migration schema tests;
- patch hygiene.

### Baseline

- profile count == canonical prompt count;
- stable prompt hash binding;
- all capability IDs known;
- PRIMARY/REQUIRED evidence refs resolve;
- deterministic matrix/report regeneration;
- topology/current registry parity.

### Lifecycle engine

Mutation cases:

1. REQUIRED -> SUPPORT without migration => FAIL.
2. PRIMARY -> NONE without successor => FAIL.
3. RETIRE last protected owner => FAIL.
4. RETIRE after equal/stronger transfer => PASS.
5. ADD near-duplicate profile without distinct residual => FAIL.
6. ADD distinct capability residual => PASS admission gate.
7. prompt body changes but no capability disposition => FAIL.
8. prompt body changes with NO_CAPABILITY_CHANGE + focused proof + matching source-history migration => PASS.
9. shared policy revision changes while inherited profile fingerprint remains stale => FAIL/revalidation required.
10. generated proposal attempts to overwrite ACCEPTED prior => FAIL.
11. new PRIMARY claim with no evidence => FAIL.
12. unexpected PRIMARY crowding => WARN/FAIL per catalog policy.
13. prompt source missing from history source set => FAIL.

### Convergence

- new semantic coverage validator;
- Prompt Quality History;
- Prompt Strength;
- Prompt Language Audit;
- Prompt Topology;
- P79 focused tests;
- prompt registry validation;
- generated-site parity;
- required-check profile;
- patch/artifact hygiene.

## Runtime relationship

Runtime Compliance is downstream evidence, not the semantic matrix authority.

Later P94/P67 calibration may select high-value PRIMARY/REQUIRED capabilities and verify actual model behavior. Runtime findings can trigger capability/regression review, but an individual runtime model result cannot rewrite accepted profile history automatically.

## Definition of done

The first semantic-coverage program is complete when:

1. all canonical prompt body sources are history-protected;
2. exact catalog/profile/migration contracts are integrated;
3. every current prompt has an accepted evidence-backed capability profile;
4. the derived prompt x capability matrix is deterministic;
5. silent protected-capability downgrade fails;
6. ADD uses profile overlap + existing P79 prior-art/topology admission;
7. RETIRE is first-class and cannot create a coverage hole;
8. profile history cannot be reset by candidate inference;
9. semantic coverage is a blocking relevant Prompt Kit check;
10. P79 lifecycle route and generated site remain valid;
11. exact validated work is integrated into refreshed default branch;
12. P66 indexes the canonical plan after its shared path is released.

## Deferred work

Not required for first completion:

- UI heatmap/dashboard;
- interactive 3D matrix visualization;
- statistical weighting of capability importance;
- automatic capability creation from LLM output;
- cross-model runtime calibration of every cell;
- automatic prompt merge/consolidation;
- automatic retirement based on similarity alone.

## First executable implementation transition

Owner: P07 / Prompt Topology semantic-coverage floor.

Dependency: refreshed current `main` and no newer owner already implementing this exact layer.

Action:

Execute Sprint 0.

First proof targets:

- add `docs/prompts.json` to history protection;
- make history source coverage equal the actual canonical prompt source set;
- create the exact semantic coverage contract/catalog/profile/migration schemas and focused contract tests.

Completion gate:

- Prompt Quality History passes on complete source coverage;
- a mutation fixture that removes any canonical source from history fails;
- semantic coverage schemas parse and reject malformed weakening/transfer structures;
- no full profile baseline is falsely claimed yet.
