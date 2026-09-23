portableContractRef: RepoLedgerInteroperability.v1@429237aa41d8712d71859865c9be407ca23d8580
canonicalContractCommit: 429237aa41d8712d71859865c9be407ca23d8580
localAuthority: AGENTS.md

# Web Excel Repair Triage shared work ledger

This is the repository-local coordination ledger for unfinished triage and Prompt Kit work. It routes work; it does not replace `AGENTS.md`, source, tests, builders, generated-artifact contracts, PRs, CI, or browser/runtime evidence. BlacksmithGuild owns the portable ledger compatibility contract; this repository owns TRQ task state and all local product/artifact truth.

Continuation states are not stopping states.
PR opened is not completion.
DONE is strict.
Canonical terminal action: none; no safe actionable work remains

## TRQ-001 — Initial repository work ledger adoption

- **Status:** DONE
- **Priority:** P1
- **Owner:** chatgpt-cross-repo-ledger-20260809
- **Branch / PR:** main / #160 merged
- **Scope:** historically add a triage-local work ledger, adoption manifest, validator, positive/negative tests, CI, and existing hook integration; the original AgentSwitchboard portable-authority pin is superseded by BlacksmithGuild RepoLedgerInteroperability.v1 and reconciled by TRQ-002
- **Forbidden:** copying AxTask `AXQ-*` tasks; changing Prompt Kit product behavior; treating ledger prose as browser/runtime proof; weakening `AGENTS.md`; fetching or executing a remote validator at validation time
- **Dependencies:** none
- **References:** `AGENTS.md`, `.ai/work-ledger-adoption.json`, `scripts/validate_repository_work_ledger.py`, `tests/test_repository_work_ledger.py`
- **Acceptance gate:** historical local implementation merged with local validator/tests, CI, and existing Git hooks; the original portable authority is separately reconciled by TRQ-002
- **Gate:** none
- **Last proof:** workflow:31331837078 passed the final triage ledger contract; workflow:31331837062 passed operational harness contracts; workflow:31331837072 passed artifact engine tests; merge:189be37114ef2eb11015b0d962eb23e5d12f1ccc merged triage PR #160
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-08-09T19:49:00Z

## TRQ-002 — Reconcile portable ledger authority to BlacksmithGuild

- **Status:** DONE
- **Priority:** P1
- **Owner:** chatgpt-blacksmith-ledger-authority-reconcile-20260809
- **Branch / PR:** main / #162 merged
- **Scope:** repoint the existing triage adoption manifest, queue header, validator, and tests directly to BlacksmithGuild RepoLedgerInteroperability.v1 while preserving the repository-local TRQ ledger, CI, hooks, Prompt Kit authority, and artifact-engine boundaries
- **Forbidden:** changing Prompt Kit product behavior; changing workbook/artifact engines; adopting AgentSwitchboard Work class/frontier as a portable requirement; copying AxTask domain tasks; executing remote BlacksmithGuild or AgentSwitchboard validators
- **Dependencies:** BlacksmithGuild portable contract merge 429237aa41d8712d71859865c9be407ca23d8580 and authority-registry reconciliation merge ecf0718556e77f10747a997d2cb0173af81b3d29
- **References:** `.ai/work-ledger-adoption.json`, `scripts/validate_repository_work_ledger.py`, `tests/test_repository_work_ledger.py`, `.github/workflows/repository-work-ledger-contract.yml`, `.githooks/pre-commit`, `.githooks/pre-push`
- **Acceptance gate:** the existing local ledger workflow passes; validator enforces exact Blacksmith portable pin, verified AxTask donor provenance, local references, continuation/DONE rules, and stale symbolic-ref rejection; existing hooks remain wired; PR contains no Prompt Kit or artifact-engine product mutation
- **Gate:** none
- **Last proof:** workflow:31332698254 passed the repository work-ledger contract with 14 local contract tests and patch hygiene; workflow:31332698237 passed artifact engine tests; merge:da8d9dae9b615301dffc4d280eb7969e0ff4f5ff merged PR #162; artifact:.ai/work-ledger-adoption.json artifact:scripts/validate_repository_work_ledger.py artifact:tests/test_repository_work_ledger.py
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-08-09T19:55:00Z

## TRQ-003 — Add repository work ledger stewardship prompt to Prompt Kit

- **Status:** DONE
- **Priority:** P1
- **Owner:** chatgpt-prompt-ledger-p66-20260809
- **Branch / PR:** main / #163 merged
- **Scope:** add P66 Repository Work Ledger Steward as a versioned prompt extension, integrate it with registry loading and both interactive and copyable guided discovery, add focused regression coverage, regenerate the canonical Prompt Kit website, and preserve the existing safe Windows acquisition route
- **Forbidden:** changing BlacksmithGuild RepoLedgerInteroperability.v1 or repository-local ledger semantics; changing AxTask or AgentSwitchboard domain authority; unrelated Prompt Kit UX; hand-editing generated `web/prompt-kit/index.html`; hard-coded Windows usernames; destructive checkout cleanup
- **Dependencies:** TRQ-001, TRQ-002
- **References:** `registry/prompts/repository-work-ledger-prompts.v1.json`, `registry/prompts/tutorial-discovery-prompts.v1.json`, `scripts/build_prompt_kit_registry.py`, `registry/prompts/prompt-display-order.v1.json`, `docs/prompt-kit-guided-recommendations.js`, `tests/test_repository_work_ledger_prompt.py`, `web/prompt-kit/index.html`, `scripts/Acquire-LatestPromptKit.ps1`
- **Acceptance gate:** P66 loads through the combined registry with unique ID/sequence, interactive and copyable P65 discovery can route repository-ledger intent to P66, focused tests pass, the checked-in website exactly matches the canonical builder output and contains P66, Prompt Kit and ledger CI pass against current repository authority, concurrent TRQ blocks are preserved, and the merged site remains retrievable through the repository-owned Windows quick-open acquisition path
- **Gate:** none
- **Last proof:** workflow:31333483267 passed repository work-ledger contract on the final PR head; workflow:31333483288 passed Prompt Kit web contracts including exact generated-site parity and acquisition checks; workflow:31333483286 passed skill prompt registry and generator UX; workflow:31333483282 passed Prompt Kit GitHub Pages; workflow:31333483297 passed operator documentation contracts; workflow:31333483289 passed artifact engine tests; merge:d4c10a0def8a1ba4ccb7009db7ddfd4f9bba82dd merged PR #163
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-08-09T20:10:00Z

## TRQ-004 — Build Lua embedding-readiness operational harness

- **Status:** DONE
- **Priority:** P1
- **Owner:** chatgpt-lua-harness-20260810
- **Branch / PR:** main / #167 merged
- **Scope:** build a tracked Lua embedding-readiness harness with codebase map, workflow, artifact/validator/capability/trigger registries, explicit host-controlled design contract, scoped skill, focused hook fragments, operator report, fail-closed validator/tests, CI report artifact, and root harness registration while preserving the concurrent Prompt Kit release-identity harness dependency
- **Forbidden:** changing `AGENTS.md`; implementing a Lua interpreter, host binding, native module, or `.lua` product behavior; selecting a product host runtime without a product lane; secrets; destructive cleanup; force-push; claiming runtime proof from static harness evidence
- **Dependencies:** PR #166 / merge:aadf9765ba3f5a8b5df30d7d40232cff8dc646f4
- **References:** `harness/lua/manifest.v1.json`, `harness/lua/contracts/lua-embedding-readiness.v1.json`, `harness/lua/WORKFLOW.md`, `harness/lua/ARTIFACT_REGISTRY.md`, `harness/lua/reports/CURRENT_STATE.md`, `.ai/skills/lua-embedding-readiness/SKILL.md`, `scripts/validate_lua_harness.py`, `tests/test_lua_harness_contract.py`, `.github/workflows/lua-harness-contract.yml`, `harness/manifest.v1.json`
- **Acceptance gate:** every Lua harness component is tracked and registered; host-owned execution, independent VM states, explicit state release, host-caught errors/rollback, runtime type discipline, optional JIT, default-deny OS/IO/native loading, allow-listed host APIs, 1-based Lua semantics, conceptual minimalism, and AI auditability are fail-closed contract requirements; focused validator/tests, root harness, artifact hygiene, and patch hygiene pass; PR is merged without product/runtime Lua changes; runtime remains explicitly `not_implemented`
- **Gate:** none
- **Last proof:** commit:4747efe470c10b9a2f240eb71d9e838d25f82651 built the operational Lua harness; workflow:31420050622 passed the dedicated Lua embedding-readiness harness and uploaded the machine report; workflow:31420050626 passed operational harness contracts; workflow:31420050714 passed Prompt Kit web contracts; workflow:31420050637 passed artifact engine tests; merge:8a29a34f445c4ddf0a5b2d71af6bca57f767fa40 merged PR #167
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-08-10T14:41:00-04:00

## TRQ-005 — Make P02 previous-chat execution-first and restore full All view

- **Status:** DONE
- **Priority:** P1
- **Owner:** chatgpt-prompt-kit-chat-continuation-all-reset-20260810
- **Branch / PR:** main / #169 merged
- **Scope:** replace effective P02 with a stable-identity Previous Chat → Active Sprint Executor that takes only the previous chat name and drives unfinished work through implementation; add explicit versioned prompt-override authority; make Favorites → All an atomic full-filter reset for click and keyboard `1`; add filtering, override-identity, raw-language-audit, generated-site, and CI regressions; regenerate the canonical Prompt Kit; and publish that exact artifact through GitHub Pages
- **Forbidden:** changing `AGENTS.md`; unrelated prompt rewrites; workbook/artifact-engine product behavior; Lua runtime/harness changes; secrets; destructive cleanup; force-push; claiming interactive browser behavior from static tests alone
- **Dependencies:** TRQ-004; main@02eb09a3d3bf364b4a705a3a475f2b9c862e94c2 at sprint start
- **References:** `registry/prompts/prompt-overrides.v1.json`, `scripts/build_prompt_kit_registry.py`, `scripts/evaluate_prompt_language.py`, `docs/prompt-kit-polish.js`, `harness/contracts/prompt-kit-filtering.v1.json`, `tests/test_prompt_kit_filtering_access.py`, `tests/test_skill_prompt_registry.py`, `tests/test_prompt_language_audit.py`, `.github/workflows/prompt-kit-web.yml`, `web/prompt-kit/index.html`, `.github/workflows/prompt-kit-pages.yml`
- **Acceptance gate:** effective P02 keeps `P02`/`02`, contains exactly one operator placeholder `xyz_previous_chat_name`, retrieves the named prior chat and is execution-first rather than launch-pack-only; prompt overrides cannot drift stable ID casing/sequence and are included in raw/effective language audit; selecting Favorites then All by click or `4` then `1` clears section, type, color, search, and collapse state and renders the complete prompt stream; checked-in website equals the canonical builder output; final PR head passes Prompt Kit, skill-registry, operational-harness, documentation, Pages-build, and artifact-engine gates; PR merges; main Pages build and deployment succeed for the merge commit
- **Gate:** none
- **Last proof:** commit:def92656a582d7c8ad7ee233ae599eebf5c3a12c regenerated `web/prompt-kit/index.html` only through the registered builder; commit:3e4175ee1ea92d8a86759ffa4cfdf8f6897100d7 closed review gaps for exact override identity and raw language-audit authority; workflow:31423160675 passed Prompt Kit web contracts on final PR head; workflow:31423160691 passed skill prompt registry and generator UX; workflow:31423160714 passed operational harness contracts; workflow:31423160681 passed operator documentation contracts; workflow:31423160676 passed PR Pages build/parity; workflow:31423160720 passed artifact engine tests; merge:6d6d1b3f2aaf46d2353f7b411e1f36c3ef278733 merged PR #169; workflow:31423332238 built the exact main artifact and successfully deployed GitHub Pages for merge 6d6d1b3f2aaf46d2353f7b411e1f36c3ef278733
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-08-10T15:18:00-04:00

## TRQ-006 — Add safe Prompt Kit browser-proof scratch cleanup harness

- **Status:** DONE
- **Priority:** P1
- **Owner:** chatgpt-browser-proof-cleanup-harness-20260810
- **Branch / PR:** main / #171 merged
- **Scope:** classify and safely remove only detached `prompt-kit-browser-proof-*` directories directly under the OS temp root through a preview-first, explicit-apply PowerShell runner; build the subordinate codebase map/workflow/artifact/validator/trigger/hook/skill/report harness; register the capability in canonical root discovery; preserve previous cleanup receipts before replacement; and prove test-owned preview/retention/apply behavior without changing Prompt Kit product behavior
- **Forbidden:** changing `AGENTS.md`; broad `%TEMP%` cleanup; deleting canonical repository checkouts or unrelated `Outputs/` evidence; clearing browser profile data, cookies/cache/history, localStorage, or Prompt Kit Favorites; product-code changes; secrets; force-push; claiming native P-Top deletion from CI fixtures
- **Dependencies:** TRQ-005; main@5f9c17224fae59d91ccd9b3e5a62fb350cdf0768 at sprint start
- **References:** `harness/browser-proof-cleanup/manifest.v1.json`, `harness/browser-proof-cleanup/CODEBASE_MAP.md`, `harness/browser-proof-cleanup/WORKFLOW.md`, `harness/browser-proof-cleanup/artifacts.v1.json`, `harness/browser-proof-cleanup/validators.v1.json`, `harness/browser-proof-cleanup/triggers.v1.json`, `harness/browser-proof-cleanup/reports/CURRENT_STATE.md`, `harness/browser-proof-cleanup/reports/P_TOP_ACCEPTANCE_20260810.md`, `.ai/skills/prompt-kit-browser-proof-cleanup/SKILL.md`, `scripts/Clear-PromptKitBrowserProofScratch.ps1`, `scripts/validate_prompt_kit_browser_proof_cleanup.py`, `tests/test_prompt_kit_browser_proof_cleanup_harness.py`, `.github/workflows/prompt-kit-browser-proof-cleanup.yml`, `harness/manifest.v1.json`, `harness/capabilities.v1.json`, `harness/triggers.v1.json`
- **Acceptance gate:** cleanup is canonical-discoverable; preview is default and never deletes; apply requires the exact eligible target; candidate must be a direct OS-temp child matching the browser-proof regex, non-reparse, contain `web/prompt-kit/index.html`, and meet minimum age; report stays under `Outputs/`; previous stable receipt is backed up before overwrite; focused/root validators and tests pass; dedicated CI proves preview + receipt retention + explicit deletion against a test-owned fixture; PR merges; sanitized tracked operator evidence records a native P-Top explicit-apply run with one eligible candidate, one deletion, zero failures, and a target-absent postcondition
- **Gate:** none
- **Last proof:** commit:0805b511e46f46c44c2ab84cbebe8b25f6c79e04 created the requested operational harness infrastructure; commit:ba5f2297d1c53d18ae74e6523d3ed57592272d01 registered canonical discovery and durable receipt retention; workflow:31429055030 passed the dedicated browser-proof cleanup harness on final head; workflow:31429054930 passed operational harness contracts; workflow:31429054925 passed Prompt Kit web contracts; workflow:31429055021 passed Lua embedding-readiness harness; workflow:31429054944 passed artifact engine tests; merge:a2d59efafe951350428eac880c8203ecfc7c9eef merged PR #171; operator-proof:harness/browser-proof-cleanup/reports/P_TOP_ACCEPTANCE_20260810.md records native P-Top apply with candidate=1 eligible=1 deleted=1 failed=0 and target absent after cleanup
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-08-10T18:20:00-04:00

## TRQ-007 — Measure Prompt Kit compute-authority effectiveness on external agents

- **Status:** READY
- **Priority:** P1
- **Owner:** P67 / skill-evaluation
- **Branch / PR:** main; Sprint 1+2+Gen2+ADP-00 INTEGRATED; observed pilot UNPROVEN_RUNTIME
- **Scope:** build and execute the bounded paired A/B evaluation that measures whether the strengthened Prompt Kit compute-authority contract increases decision-relevant useful compute, defect/contract discovery, evidence honesty, parallelism when available, and fixed-point quality without widening mutation scope or rewarding endless churn
- **Forbidden:** changing Prompt Kit treatment behavior inside the frozen study; duplicating the P67 eval framework or skill-evaluation identity; modifying separately owned #431/#462/#242 surfaces outside an explicit reconciliation; secrets/private transcripts/personal data; promoting static proof to observed external-agent effectiveness
- **Dependencies:** Sprint 1 integrated by PR #464 / merge `43b1953092b518fe3a76b5fe0bfab179f730e849`; Sprint 2 integrated by PR #530 / merge `300d949fdcf79bbac018440a85052302d575bd2c`; Gen2 generation support by PR #557 / merge `e0038eec048af029f6f27bb2f0dc70f875e09e06`; ADP-00 neutral capture authority by PR #598 / merge `0733897c0bde4bd0dc48e8aab9b043e9e62bc7aa`; Sprint 3 must reconcile #450-owner collision surfaces (PR #450 CLOSED not merged); #596 salvaged stateless route receipts
- **References:** `harness/evals/COMPUTE_AUTHORITY_EVALUATION_SPRINT_PLAN.md`, `harness/evals/compute-authority/manifest.json`, `harness/evals/compute-authority/README.md`, `harness/evals/repository-ai-evals.v1.json`, `.ai/skills/skill-evaluation/SKILL.md`, `harness/contracts/prompt-outcome-receipt.schema.v1.json`
- **Acceptance gate:** three-sprint program completes its deterministic gold-fixture floor, 16-run paired pilot, shared-registry reconciliation, 48 valid-run main study, blinded scoring and mechanical thresholds; observed effectiveness is promoted only when exact runtime evidence satisfies the canonical plan
- **Gate:** Sprint 2 repository/runtime-harness implementation is SAFE & EXECUTABLE; provider credentials or an accessible external-agent runtime may block only the observed pilot and must remain `UNPROVEN_RUNTIME` rather than a synthetic PASS
- **Last proof:** merge:43b1953092b518fe3a76b5fe0bfab179f730e849 integrated PR #464 Compute-Authority Sprint 1; merge:300d949fdcf79bbac018440a85052302d575bd2c integrated PR #530 Sprint 2 runtime harness; merge:e0038eec048af029f6f27bb2f0dc70f875e09e06 integrated PR #557 Gen2 generation support; merge:0733897c0bde4bd0dc48e8aab9b043e9e62bc7aa integrated PR #598 ADP-00 neutral capture authority; artifact:harness/evals/compute-authority/runtime/adapter-contract.v2.json present on refreshed default branch
- **Next action:** Execute ADP-04 (observed adapter smoke) from `harness/evals/COMPUTE_AUTHORITY_EVALUATION_SPRINT_PLAN.md` §16 adapter phase map when operator provider auth and workstation access are available; ADP-01/02/03 INTEGRATED; ADP-04 blocked on operator provider authentication/workstation configuration; observed pilot remains gated on ADP-05
- **Updated:** 2026-09-19T21:50:00Z

## TRQ-008 — Execute Prompt Execution Evidence Spine sprint map

- **Status:** DONE
- **Priority:** P1
- **Owner:** Prompt Topology / P95 lifecycle architecture coordinator
- **Branch / PR:** main / #471 merged; Waves 0–2 landed via #467/#477, #473, #474/#475
- **Scope:** index the canonical three-wave Evidence Spine execution map covering PR #467 autonomous-dispatch floor repair and convergence, P95 lifecycle/state-owner architecture, then only the runtime routing/observation/recurrence-to-work/agent-continuation seams admitted by P95
- **Forbidden:** replacing the canonical sprint map with this row; duplicating PR #467/#450/#431 owners; production Phase D; generic event bus; raw prompt/response/clipboard/transcript telemetry; hosted telemetry/vector DB; hand-editing generated Prompt Kit output; promoting static design to runtime adoption proof
- **Dependencies:** current `main`; PR #467/#477 dispatch floor; `harness/prompt-topology/POST_PHASE_C_STRATEGIC_SCOUT.md`; merged P99/P115 outcome semantics; merged PR #466 local retention/privacy lifecycle; integrated P95 architecture #473; runtime collision/runtime PRs #474/#475
- **References:** `harness/prompt-topology/EVIDENCE_SPINE_SPRINT_MAP.md`, `harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md`, `harness/prompt-topology/POST_PHASE_C_STRATEGIC_SCOUT.md`, `harness/contracts/prompt-outcome-classification.v1.json`, `.ai/skills/prompt-kit-feedback-afk-routing/SKILL.md`
- **Acceptance gate:** Panel 1 repairs and integrates the exact validated #467 owner; Panel 2 integrates `harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md` with explicit lifecycle ownership and donor dispositions; Panel 3 implements only admitted seams, reconciles/retire donor work without duplicate ownership, proves privacy-bounded recurrence/next-action behavior with fixtures/validators/runtime evidence actually available, and converges validated authorized work onto refreshed default branch
- **Gate:** none
- **Last proof:** merge:86edababd71117afbaffad92b7ef2ee4ae9426a7 integrated planning PR #471; merge:a1e9caa17c6a979a3747edb71632a66c9406af00 integrated #467; merge:d8ef87ebb0f98fb49061429f9561ed3781556f44 integrated #477; architecture/runtime merges #473/#474/#475 on main; artifact:harness/prompt-topology/EVIDENCE_SPINE_SPRINT_MAP.md and artifact:harness/prompt-topology/EVIDENCE_SPINE_ARCHITECTURE.md present on refreshed default branch
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-09-14T13:00:00-04:00

## TRQ-009 — Prompt Compilation & Adaptive Language Architecture Sprint 1

- **Status:** DONE
- **Priority:** P1
- **Owner:** prompt-compilation-sprint1-20260914
- **Branch / PR:** main / #483 merged
- **Scope:** formalize Prompt Compilation as a bounded prompt-compilation subsystem with `prompt-semantics/v1`, `prompt-context/v1`, `prompt-execution-profile/v1`, language compiler contract, effective-prompt build receipt, modality/non-weakening validator, deterministic improvement-candidate format, TC06 parallelism-modality fixtures, durable architecture/sprint map, and focused tests while preserving P95 adapter-only Evidence Spine boundaries
- **Forbidden:** UI Compute Mode toggle; PR #450/#431 donor work; raw conversation/transcript ingestion; new Evidence Spine event types; universal event bus; automatic source mutation; automatic PR merge; model-generated policy promotion; mutating TRQ-007 frozen prompt identities; hand-editing generated Prompt Kit output
- **Dependencies:** TRQ-008 DONE; P95 Evidence Spine architecture on main; Sprint 1 base floor `d3accd1835a097a51a850ad9909672167f96ffdd`
- **References:** `harness/prompt-compilation/PROMPT_COMPILATION_ARCHITECTURE.md`, `harness/prompt-compilation/PROMPT_COMPILATION_SPRINT_MAP.md`, `harness/contracts/prompt-semantics.v1.json`, `harness/contracts/prompt-execution-profile.v1.json`, `harness/contracts/prompt-context.v1.json`, `harness/contracts/prompt-build-receipt.v1.json`, `harness/contracts/prompt-improvement-candidate.v1.json`, `harness/contracts/prompt-language-compiler-policy.v1.json`, `scripts/prompt_language_compiler.py`, `tests/test_prompt_compilation.py`
- **Acceptance gate:** Sprint 1 contracts/compiler/fixtures/tests validate; architecture and sprint map persist P95 separation from Evidence Spine and TRQ-007; non-weakening validator rejects permissive MUST regressions; improvement candidates require `reviewed_pr_only`; exact validated head integrates to current default branch
- **Gate:** none
- **Last proof:** commit:36f31a987048829824a7759189a28609e55fe695; merge:04e4a77d261d0bd0388daa6d56f38e113cdf79fa integrated PR #483; local:python -m unittest tests.test_prompt_compilation (13 OK); local:python scripts/prompt_language_compiler.py validate-fixtures --summary; workflow deterministic-test-floor + operational-harness + ledger contract green on PR head; artifact:harness/prompt-compilation/PROMPT_COMPILATION_ARCHITECTURE.md present on refreshed default branch
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-09-14T14:40:00-04:00

## TRQ-010 — Prompt Compilation Sprint 2 context adapters + profile precedence

- **Status:** DONE
- **Priority:** P1
- **Owner:** prompt-compilation-sprint2-20260914
- **Branch / PR:** main / #485 merged
- **Scope:** implement thin read-only Context Engine adapters that project dispatch receipts, continuation dispositions, P99 outcome receipts, and recurrence findings into `prompt-context/v1`, plus deterministic execution-profile precedence (`run > prompt > user > product`) and focused tests, without owning lifecycle events
- **Forbidden:** UI Compute Mode toggle; PR #450/#431 donor work; raw conversation ingestion; new Evidence Spine event types; universal event bus; automatic source mutation; automatic PR merge; model-generated policy promotion; hand-editing generated Prompt Kit output
- **Dependencies:** TRQ-009 DONE; Sprint 2 base floor `602df5086c61d81382eb2835dcb119eaa71d4ae5`
- **References:** `harness/prompt-compilation/PROMPT_COMPILATION_SPRINT_MAP.md`, `scripts/prompt_context_engine.py`, `tests/test_prompt_context_engine.py`, `scripts/prompt_language_compiler.py`
- **Acceptance gate:** adapters produce valid `prompt-context/v1`; precedence resolver is deterministic; projected context compiles through Language Engine for TC06 parallel MUST; no event-bus fields; exact validated head integrates to current default branch
- **Gate:** none
- **Last proof:** commit:05fb419d6da7344a562f654385132f3c54dd4116; merge:86044bfb27de95fbf60d29adf2ce54689b09c303 integrated PR #485; local:python -m unittest tests.test_prompt_compilation tests.test_prompt_context_engine (20 OK); CI deterministic-test-floor + ledger contract green on PR head; artifact:scripts/prompt_context_engine.py present on refreshed default branch
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-09-14T14:50:00-04:00

## TRQ-011 — Prompt Kit UI format alignment ledger and Storage repair

- **Status:** DONE
- **Priority:** P1
- **Owner:** cursor-ui-format-alignment-20260915
- **Branch / PR:** main / #498 merged
- **Scope:** repair Storage header control to the Resources formatting sequence; install UI format-alignment contract, aligned/deferred ledger, fail-closed validator, focused tests, regenerate Prompt Kit site; coerce lazy unclassed UI into deferred ledger fodder
- **Forbidden:** unrelated redesign; privacy/storage policy mutation; force-push; hand-editing generated HTML without builder; weakening storage lifecycle or header protected contracts
- **Dependencies:** origin/main floor containing Storage lifecycle runtime
- **References:** `docs/PROMPT_KIT_UI_FORMAT_ALIGNMENT_PLAN.md`, `harness/contracts/prompt-kit-ui-format-alignment.v1.json`, `harness/prompt-kit-ui-format-alignment/ledger.v1.json`, `scripts/validate_prompt_kit_ui_format_alignment.py`, `docs/prompt-kit-storage-lifecycle.js`
- **Acceptance gate:** Storage uses `operant-resource-button` + styled `prompt-storage-*` surface; validator PASS; deferred coercion test PASS; storage lifecycle + header protected tests PASS; generated site parity; PR integrated to current default branch when gates allow
- **Gate:** none
- **Last proof:** merge:c385735fa1b44f96392d6e07c67cf69a0b909a4e integrated PR #498; local:python scripts/validate_prompt_kit_ui_format_alignment.py --summary PASS; local:python -m unittest tests.test_prompt_kit_ui_format_alignment tests.test_prompt_kit_storage_lifecycle_runtime PASS; workflow:ui-format-alignment green on PR head; artifact:docs/prompt-kit-storage-lifecycle.js uses operant-resource-button on refreshed default branch
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-09-15T06:45:00Z

## TRQ-012 — Prompt Compilation Sprint 3 Improvement Compiler program design

- **Status:** DONE
- **Priority:** P1
- **Owner:** design/prompt-compilation-program-20260916
- **Branch / PR:** main / #515 merged
- **Scope:** revise Prompt Compilation program design so Sprint 3 owns Improvement-Candidate Compiler call-stack prototypes (success + failure) before UI; persist architecture module/ownership/call-stack/alternatives evidence; add hypothesis catalog, journey fixtures, `scripts/prompt_improvement_compiler.py`, focused tests; reorder sprint map so UI Compute Mode is Sprint 4; preserve P95 adapter-only and `reviewed_pr_only` boundaries
- **Forbidden:** UI Compute Mode toggle; PR #450/#431 donor work; raw conversation ingestion; new Evidence Spine event types; universal event bus; automatic source mutation; automatic PR merge; model-generated policy promotion; mutating TRQ-007 frozen prompt identities; hand-editing generated Prompt Kit output
- **Dependencies:** TRQ-010 DONE; P95 Evidence Spine architecture on main; planning floor `de42daf148a2f09754b3eb2f7fd88799162d1e05`
- **References:** `harness/prompt-compilation/PROMPT_COMPILATION_ARCHITECTURE.md`, `harness/prompt-compilation/PROMPT_COMPILATION_SPRINT_MAP.md`, `scripts/prompt_improvement_compiler.py`, `harness/prompt-compilation/improvement-hypothesis-catalog.v1.json`, `tests/test_prompt_improvement_compiler.py`
- **Acceptance gate:** architecture records SUCCESS/FAILURE call stacks and alternatives; sprint map places Improvement Compiler before UI; IJ01 journey emits reviewed_pr_only candidate with TC06 eval; failure gates fail closed; Sprint 1–2 tests remain green; exact validated head integrates to current default branch
- **Gate:** none
- **Last proof:** commit:4d98a77369fe64f42a7be6cb79ea71dd6bbbeea1; merge:50229c36e21a32d8541ddfe2c957cf9095ce3546 integrated PR #515; local:python -m unittest tests.test_prompt_compilation tests.test_prompt_context_engine tests.test_prompt_improvement_compiler (29 OK); workflow:deterministic-test-floor + operational-harness + ledger contract green on PR head; artifact:scripts/prompt_improvement_compiler.py present on refreshed default branch
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-09-16T19:10:00-04:00

## TRQ-013 — Prompt Compilation Sprint 4 wiring + Compute Mode

- **Status:** DONE
- **Priority:** P1
- **Owner:** feat/prompt-compilation-sprint4-wiring-20260916
- **Branch / PR:** main / #519 merged
- **Scope:** wire Language Engine compiled effective prompts into Prompt Kit builder for semantics-backed prompts (P07); add Compute Mode runtime (Exhaustive/Efficient) with run>prompt>user>product precedence and personal-state storage keys; route polish copy through Compute Mode; regenerate site via builder; focused tests; update sprint map
- **Forbidden:** weakening safety gates; bypassing builder-owned generation; auto-promotion of improvement candidates; PR #450/#431 donor work; mutating TRQ-007 frozen prompt identities; hand-editing generated HTML outside the builder; new Evidence Spine event types; universal event bus
- **Dependencies:** TRQ-012 DONE; Sprint 3 on main; planning floor `93a8886d77e043023eeecca05f5e2e8e13b89f06`
- **References:** `harness/prompt-compilation/PROMPT_COMPILATION_SPRINT_MAP.md`, `docs/prompt-kit-compute-mode.js`, `scripts/build_prompt_kit_registry.py`, `harness/prompt-compilation/semantics/P07.json`, `tests/test_prompt_kit_compute_mode.py`
- **Acceptance gate:** P07 carries compiledEffectivePrompts for exhaustive and efficient; builder embeds Compute Mode runtime; human copy routing preserves canonical copyContent when present; compiledEffectivePrompts remain execution-profile metadata/fallback and never replace the operator-visible canonical prompt; focused + Sprint 1–3 compilation tests green; builder --check parity; exact validated head integrates to current default branch
- **Gate:** none
- **Last proof:** commit:10167b309612e6e42aeceda4a1ca379db82939f3; merge:c4d065facd8fb647b7416d7741532d33466379d8 integrated PR #519; local:python -m unittest tests.test_prompt_kit_compute_mode (6 OK) + compilation suite; local:builder --check PASS; workflow required checks green on PR head; artifact:docs/prompt-kit-compute-mode.js and compiled P07 present on refreshed default branch
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-09-16T22:35:00-04:00

## TRQ-014 — Prompt Compilation Sprint 5 eval-loop hardening

- **Status:** DONE
- **Priority:** P1
- **Owner:** feat/prompt-compilation-sprint5-eval-hardening-20260916
- **Branch / PR:** main / #522 merged
- **Scope:** broaden improvement hypothesis/fingerprint catalog; add TC07 mainline-convergence gold fixture and IJ03 journey; optional Outputs/prompt-improvement-drafts retention; emit P115-compatible work-request handoff without absorbing P115; keep reviewed_pr_only; focused tests; update sprint map
- **Forbidden:** auto-merge; model-only policy promotion; Evidence Spine event invention; absorbing P115 ownership; PR #450/#431 donor work; mutating TRQ-007 frozen prompt identities; hand-editing generated Prompt Kit HTML
- **Dependencies:** TRQ-013 DONE; Sprint 4 on main; planning floor `d0442d3d193a8b78cb4d4c8b12e8add3b4414c10`
- **References:** `harness/prompt-compilation/PROMPT_COMPILATION_SPRINT_MAP.md`, `scripts/prompt_improvement_compiler.py`, `harness/prompt-compilation/improvement-hypothesis-catalog.v1.json`, `harness/prompt-compilation/fixtures/TC07-mainline-convergence-proof/`, `tests/test_prompt_improvement_compiler.py`
- **Acceptance gate:** catalog covers >=8 identities including TC07; journey emits P115 handoff with absorbs_p115_ownership=false; optional Outputs retention stays under Outputs/; focused compilation + improvement tests green; exact validated head integrates to current default branch
- **Gate:** none
- **Last proof:** commit:97dc0b62cc915ffcbbe40c166912e2f00a0578d0; merge:5f55e2a922534e7cae5087309fc2da296892af3d integrated PR #522; local:python -m unittest tests.test_prompt_improvement_compiler (12 OK) on refreshed default; local:validate-fixtures cases=2; workflow required checks green on PR head `2e844f44`; artifact:TC07 + P115 handoff present on refreshed default branch
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-09-16T23:20:00-04:00

## TRQ-015 — Define and prove P123 source-coverage scoring harness

- **Status:** DONE
- **Priority:** P1
- **Owner:** feat/p123-source-coverage-proof-20260917
- **Branch / PR:** main / #527 merged
- **Scope:** durable P123 full-source/tail coverage proof plan; versioned coverage contract; deterministic coverage-receipt scorer; gold partial fixture derived from `7UyhyhxdFsQ` quality evidence; synthetic COMPLETE candidate; focused tests; deterministic test-floor registration; keep document-identity receipt unpromoted for coverage
- **Forbidden:** claiming provider OBSERVED complete coverage from synthetic PASS; mutating Gemini/Drive live artifacts in this lane; absorbing PR #450/#524/#526 surfaces; rewriting P123 prompt copy unless scorer evidence requires it; inventing unrepresented-tail facts
- **Dependencies:** main@c0090aa285fe0580ff19c26c1e1de0d7e95506bc; P123 identity receipt field/20260916/p123-gemini-drive-title; quality fixture drive_7UyhyhxdFsQ_20260910
- **References:** `harness/evals/P123_SOURCE_COVERAGE_PROOF_PLAN.md`, `harness/contracts/p123-source-coverage-proof.v1.json`, `scripts/evaluate_p123_source_coverage.py`, `tests/fixtures/p123_source_coverage/drive_7UyhyhxdFsQ_20260910.v1.json`, `tests/test_p123_source_coverage_eval_prompt.py`, https://github.com/EndeavorEverlasting/web-excel-repair-triage/pull/527
- **Acceptance gate:** baseline partial FAIL with declared classes; synthetic COMPLETE PASS only when accounting agrees; overclaim/fabrication/extent mismatch fail closed; focused unittest green; plan remains canonical for Phase B/C successors
- **Gate:** none
- **Last proof:** commit:80ea088185a36583fa5fe4c2cf62d3c73f85d6c0; merge:2fb9d5a004d6f7dcdfd186591e9a353ed6994634; workflow:35230472016 deterministic-test-floor SUCCESS; workflow:35230472014 Repository AI Eval Gate SUCCESS; local:python -m unittest tests.test_p123_source_coverage_eval_prompt (11 OK) on refreshed main; artifact:harness/evals/P123_SOURCE_COVERAGE_PROOF_PLAN.md
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-09-17T14:05:00Z

## TRQ-016 — Prompt Compilation Sprint 6 Compute Mode observed browser proof

- **Status:** DONE
- **Priority:** P1
- **Owner:** test/prompt-compilation-compute-mode-browser-proof-20260916
- **Branch / PR:** main / #524 merged
- **Scope:** close the explicit Sprint 4 Compute Mode runtime proof gap with an exact-head Playwright journey covering product default, persisted user default, per-prompt override, explicit run override, and canonical P07 clipboard identity while Compute Mode remains execution-profile metadata; register the proof in the existing observed-behavior harness and preserve Sprint 6 plan continuity
- **Forbidden:** changing Compute Mode semantics or precedence merely to make proof pass; new Evidence Spine events or lifecycle ownership; PR #450/#431 donor work; mutating TRQ-007 frozen identities; raw conversation/transcript persistence; automatic improvement promotion/merge; hand-editing generated Prompt Kit HTML
- **Dependencies:** TRQ-013 DONE; TRQ-014 DONE; observed-behavior proof harness present on current main; refreshed floor includes #521 outcome receipts without overlapping Prompt Compilation/browser-proof mutations
- **References:** `harness/prompt-compilation/PROMPT_COMPILATION_SPRINT_MAP.md`, `tests/prompt_kit_compute_mode_browser_proof.py`, `harness/observed-proof/manifest.v1.json`, `.github/workflows/prompt-kit-observed-browser-proof.yml`, `tests/test_observed_behavior_proof_harness.py`
- **Acceptance gate:** exact PR head passes deterministic observed-proof/Compute Mode tests, the retained `tests/test_p07_effective_prompt_identity.py` regression, and generated-site parity; Chromium journey emits a valid `browser_runtime_observed` receipt proving run > prompt > user > product precedence while every P07 copy surface preserves canonical `copyContent`; compiled profiles remain metadata/fallback only; required PR checks/reviews are green; exact validated head integrates to current default branch with containment proof
- **Gate:** none
- **Last proof:** merge:33a2296426c018c6652b6d925a434274f39b1b33 / PR #541 established canonical P07 copy identity; merge:3644dd3bdf2f89dccfb07f554f753c93c917e65e / PR #524 later proved Compute Mode precedence but reintroduced compiled-first clipboard routing. workflow:35302530685 remains valid for profile-precedence/browser execution only, not clipboard identity. artifact:tests/test_p07_effective_prompt_identity.py is the retained canonical-copy regression and the current #607 recovery registers it in deterministic semantic discovery while restoring canonical-first routing.
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-09-19T21:24:00Z

## TRQ-017 — Prompt Semantic Capability Coverage program

- **Status:** DONE
- **Priority:** P1
- **Owner:** P79 + Prompt Topology + Prompt Quality History + Prompt Strength
- **Branch / PR:** main / #588 #591 #592 #594 merged
- **Scope:** protect Prompt Kit behavior across ADD, EDIT/STRENGTHEN, and RETIRE by making each prompt's accepted semantic capabilities versioned repository truth; add canonical prompt-by-capability matrix as a deterministic projection of versioned profiles; detect when a change preserves syntax/ID/generated-site parity while silently removing existing behavior; integrate Sprint 1A baseline semantic capability profiles, Sprint 1B semantic diff validator + lifecycle engine, and Sprint 2 semantic coverage lifecycle + required checks
- **Forbidden:** replacing Prompt Kit identity/Prompt Strength/Prompt Quality History; letting generated topology artifacts become prompt-registry authority; unrelated prompt behavior mutation; secrets; hand-editing generated Prompt Kit output
- **Dependencies:** P79 prompt identity/admission/topology; P13 recurring-process hardening; P94 retained regression interpretation; Prompt Quality History canonical prompt text/history; Prompt Strength global shared execution-strength floor; planning floor `main@42c53fa6445d39aa74dabdfeec4eb45bfa5d7a4d`
- **References:** `harness/prompt-topology/PROMPT_SEMANTIC_CAPABILITY_COVERAGE_SPRINT_MAP.md`, `harness/prompt-topology/semantic-capability-catalog.v1.json`, `harness/contracts/prompt-semantic-coverage.v1.json`, `scripts/validate_prompt_semantic_coverage.py`, `tests/test_prompt_semantic_coverage.py`, `.ai/skills/prompt-semantic-coverage/SKILL.md`
- **Acceptance gate:** Sprint 1A baseline semantic capability profiles and accepted matrix integrated; Sprint 1B semantic diff validator + lifecycle engine integrated; Sprint 2 semantic coverage lifecycle + required checks integrated; validator detects when a change preserves syntax/ID/generated-site parity while silently removing existing capability; deterministic matrix projection validated; focused tests + operational harness + repository work ledger + diff hygiene pass; exact validated heads integrate to current default branch
- **Gate:** none
- **Last proof:** merge:66064394fe0632c6abecf16f23fe9b20bd94e654 integrated PR #592 Sprint 1B semantic diff validator + lifecycle engine; merge:92d077ca1f46d4ea7ece85b5f20ff1e0fa01e9e7 integrated PR #591 Sprint 1A baseline semantic capability profiles and accepted matrix; merge:7ecbf642a04ad92d8b17f17f40ad1c4fb0cc1c22 integrated PR #594 Sprint 2 semantic coverage lifecycle + required checks; workflow:35287857041 deterministic-test-floor SUCCESS; workflow:35287857045 operational-harness SUCCESS; artifact:harness/prompt-topology/PROMPT_SEMANTIC_CAPABILITY_COVERAGE_SPRINT_MAP.md present on refreshed default branch
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-09-19T21:24:00Z

## TRQ-018 — Prompt Runtime Compliance Sprint 4 deterministic floor convergence

- **Status:** DONE
- **Priority:** P1
- **Owner:** runtime-compliance-sprint4-safe-convergence-20260919
- **Branch / PR:** main / #585 merged
- **Scope:** converge runtime-compliance Sprint 4 deterministic floor onto refreshed main containing #524 browser proof; preserve Compute Mode profile precedence without treating #524's compiled-first clipboard regression as authority; preserve frozen Gen1 treatment; keep validator/pilot UNPROVEN_RUNTIME honest; preserve runtime-compliance planning authority; integrate exact validated head to current default branch
- **Forbidden:** changing frozen Gen1 treatment prompt identity; claiming OBSERVED effectiveness from deterministic floor alone; weakening runtime-compliance validator; absorbing separately-owned browser-proof or compute-authority surfaces; product runtime behavior mutation outside reconciliation scope; secrets
- **Dependencies:** TRQ-016 DONE (PR #524 merged); runtime-compliance Sprint 1-3 on main; Compute Mode profile precedence from #524 remains valid while clipboard identity is governed by the canonical-first P07 invariant from #541 and its retained regression; refreshed floor `main@3644dd3bdf2f89dccfb07f554f753c93c917e65e`
- **References:** `harness/evals/PROMPT_RUNTIME_COMPLIANCE_PILOT_PLAN.md`, `harness/evals/compute-authority/scripts/runtime_adapter.py`, `tests/test_compute_authority_runtime_harness.py`, `scripts/validate_prompt_runtime_compliance_receipt.py`
- **Acceptance gate:** Sprint 4 floor integrates without weakening; resolveCopyContent precedence reconciled; validator detects negative/ambiguous/pending cases; Gen1 frozen treatment preserved; focused Sprint 4 tests + runtime-compliance validator + deterministic floor + operational harness green; exact validated head integrates to current default branch
- **Gate:** none
- **Last proof:** merge:d63c04426d7f65e39d30819a0cc5a48ba51b3bb1 integrated PR #585 runtime-compliance Sprint 4 safe convergence; workflow:35302530688 deterministic-test-floor SUCCESS; workflow:35302530689 prompt-runtime-compliance SUCCESS; workflow:35302530692 operational-harness SUCCESS; local:python -m unittest tests.test_compute_authority_runtime_harness (3 OK); artifact:harness/evals/PROMPT_RUNTIME_COMPLIANCE_PILOT_PLAN.md present on refreshed default branch
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-09-19T21:24:00Z

## TRQ-019 — FirstMate + AgentSwitchboard + Prompt Kit durable vision & owner map

- **Status:** READY
- **Priority:** P1
- **Owner:** vision-map-firstmate-asb-prompt-kit-20260919
- **Branch / PR:** `cursor/firstmate-asb-prompt-kit-vision-map-5b39` / PR pending
- **Scope:** persist canonical one-page vision + owner/phase map under Triage plan conventions so Agent Flow family and peers share one durable authority surface; state completion definition (FirstMate parallel with ASB consuming Prompt Kit panels/manifests as machine inputs); paint proven/unproven boundaries; map authority (Triage doctrine, ASB consumer, FirstMate crew runtime); index collision ledger and phase ladder with honest gates
- **Forbidden:** claiming live dual-path complete or live lane dispatch PASS without observed runtime evidence; mutating ASB repo, FirstMate product, g3 live-dispatch surfaces, generated Prompt Kit HTML, SSH sprint map, or #320 deliverables
- **Dependencies:** ASB #320 merged @ `a483853d`; ADP-01/02/03 INTEGRATED; planning floor `main@b87ad29ea0e78fddb1f26b1f0a10b6efd2c94adb`
- **References:** `docs/plans/FIRSTMATE_ASB_PROMPT_KIT_VISION_OWNER_MAP.md`, `docs/plans/SSH_LOCAL_EXECUTION_BRIDGE_SPRINT_MAP.md`, `harness/evals/COMPUTE_AUTHORITY_EVALUATION_SPRINT_PLAN.md`, ASB-ADR-2026-09-FIRSTMATE-CREW-RUNTIME
- **Acceptance gate:** vision map tracked under `docs/plans/`; states NOT complete and no live dual-dual claim; owner/phase map separates g3 ASB-link mutation lane from FirstMate-parallel and vision-map; collision ledger explicit; phase ladder honest (TRACKED PLAN current state); PR opened with exact planning-floor SHA; local proof + merge-gate pass; merge when gates allow
- **Gate:** none
- **Last proof:** artifact:`docs/plans/FIRSTMATE_ASB_PROMPT_KIT_VISION_OWNER_MAP.md` created on branch; planning floor pinned; awaiting commit/push/PR
- **Next action:** commit, push, open PR, run local proof, merge if gates pass
- **Updated:** 2026-09-19T21:54:00Z

## TRQ-020 — Upstream capability watch + prompt impact sprint map

- **Status:** READY
- **Priority:** P1
- **Owner:** upstream-capability-watch-20260920
- **Branch / PR:** `plan/upstream-capability-watch-20260920` / #611 open
- **Scope:** classify the missed Matt Pocock `teach` signal; add capability-level identity and observed-vs-processed watch state; preserve external-resource intake as donor discovery authority; add deduped source-change events, impact edges, review-required promotion policy, and P115 visibility routing; reconcile P96/P98/P65 only from evidence; research and then admit authoritative design/skill-authoring donor surfaces; expose receipt-derived capability status; prove synthetic A→B routing and dedupe
- **Forbidden:** second donor registry; browser telemetry as provider polling; raw donor-body persistence; automatic prompt rewrite/promotion; P79 bypass; human scheduling as the primary parallel-dispatch path; claiming due-time AFK observation from schedule configuration; overwriting open PR #431/#561/#600/#606 owned surfaces without refresh/reconciliation
- **Dependencies:** `main@70178017ffa5c27f4428d6aae733a61113a6f4ad`; `harness/contracts/operant-external-resource-intake.v1.json`; `.github/workflows/operant-external-resource-refresh.yml`; P102 polling semantics; P115 AFK coordinator; P79 upstream prior-art gate
- **References:** `docs/plans/UPSTREAM_CAPABILITY_WATCH_SPRINT_MAP.md`, `Outputs/prompt-parallel-dispatch/manifest.json`, `scripts/prompt_kit_afk_signal_router.py`, `registry/prompts/tutorial-discovery-prompts.v1.json`, `web/prompt-kit/resources.v1.json`
- **Acceptance gate:** five forensic dispositions evidence-typed; per-capability immutable identity tracked separately from repository revision; `last_observed_identity` cannot advance `last_processed_identity` before durable routing; one A→B transition yields one event; zero-impact retains a diagnosable event; P115 receives bounded actionable change evidence; promotion remains review-required; teaching/design changes require owner/semantic proof; user-visible status reads canonical watch/review state; exact green result converges to refreshed main
- **Gate:** current ChatGPT environment has no exposed native/local autonomous repo worker or workflow-dispatch action; manifest graph width is 2 and records DEGRADED execution with an explicit autonomy gap
- **Last proof:** plan:78809b8cb264715731d4dbb57824385566ce0ece; dispatch-manifest:74d9196c3f88f5f81f5607d3a9871a758d3f6903; provider evidence confirms registered Matt donor, daily drift-proof schedule, current `teach` resource with null local target, and read-only workflow with no P115 routing
- **Next action:** Execute U0A's evidence-backed missed-`teach` forensic lane and write `harness/reports/UPSTREAM_CAPABILITY_WATCH_FORENSICS.md`; dispatch U0B authoritative design/skill-authoring source research in parallel when an autonomous adapter is available; start U1 only after U0A establishes the exact failure boundary
- **Updated:** 2026-09-20T20:00:00Z

## TRQ-021 — P55 repository bootstrap recovery and mainline convergence

- **Status:** DONE
- **Priority:** P1
- **Owner:** p55-repository-bootstrap-recovery-20260922
- **Branch / PR:** `feat/p55-provider-neutral-repo-bootstrap-20260920` / #623 merged as `5e129012221f3108e03bda129084b616e8ffd50b`
- **Scope:** reconcile the existing P55 provider-neutral repository bootstrap strengthening onto current main; repair REMOTE_ONLY continuation and identity-manifest status vocabulary; regenerate P55 lifecycle/profile/history state from current canonical authority; preserve current P65/test-floor/generated-site state; run exact-head deterministic/provider proof; integrate the exact green result; then close stale donor PR #367
- **Forbidden:** new P55 prompt identity; overwriting current P65 migration/test-floor/site state; hand-editing generated Prompt Kit as source; weakening lifecycle/test-floor validators; overwriting TRQ-020 `Outputs/prompt-parallel-dispatch/manifest.json`; force-reset/force-push; closing #367 before replacement integration; claiming runtime GitHub/Entire field proof from repository CI
- **Dependencies:** canonical plan `docs/plans/P55_REPOSITORY_BOOTSTRAP_RECOVERY_SPRINT_MAP.md`; planning floor `main@bd5136561466b31f8623ca3f9a61020cb9ced5f7`; PR #623 donor head `373019f33b0ef577443f7e56bdd441c06c203814` before plan synchronization; prompt-semantic lifecycle owner; deterministic test floor; current Prompt Kit builder
- **References:** `docs/plans/P55_REPOSITORY_BOOTSTRAP_RECOVERY_SPRINT_MAP.md`, `docs/plans/P55_REPOSITORY_BOOTSTRAP_RECOVERY_SPRINT_PACK.md`, PR #623, PR #367, `docs/prompts.json:P55`, `scripts/prompt_registry_ops.py`, `tests/test_p55_repository_bootstrap.py`, `harness/prompt-compilation/prompt-semantic-migrations.v1.json`, `harness/prompt-topology/prompt-capability-migrations.v1.json`, `harness/prompt-topology/prompt-capability-profiles.v1.json`, `harness/test-floor.v1.json`, `web/prompt-kit/index.html`
- **Acceptance gate:** current-main-based final P55 uses one manifest status vocabulary; REMOTE_ONLY/LOCAL_ONLY/local-root continuations are executable; lifecycle/profile/history records are regenerated from final current-main authority; focused P55 and deterministic-floor tests pass; generated site is exact; all actionable review threads are resolved with evidence; exact head is mergeable and provider checks green; #623 integrates to refreshed main; #367 closes only after replacement containment is proven
- **Gate:** CLOSED — strengthened P55 is integrated on refreshed main; #623 is merged; exact-head review is green; superseded #367 is closed.
- **Last proof:** provider recovery run `35812547079` SUCCESS; deterministic floor `42/42`; generated Prompt Kit parity PASS; exact reconciled head `c56ce33e63642dce844e31bc2fc83bca08213511` CodeRabbit SUCCESS with zero unresolved review threads; merge `5e129012221f3108e03bda129084b616e8ffd50b` equals refreshed main; authoritative P55 read-back PASS; donor PR #367 closed.
- **Next action:** none; no safe actionable P55 recovery work remains. Future repository-bootstrap work uses integrated P55 from main.
- **Updated:** 2026-09-23T03:06:00Z

## TRQ-022 — Converge reviewed P143 repository planner contracts

- **Status:** VERIFY
- **Priority:** P1
- **Owner:** p143-review-contract-convergence-20260923
- **Branch / PR:** `converge/p143-review-contracts-20260923` / #640 open
- **Scope:** converge the reviewed P143 Repository Convergence Planner onto current main; preserve integrated provider-neutral P55; close P143 search/routing, durable-plan authority, typed P55 handoff, provider-state, capability-ownership, deterministic-regression, generated-site, review, and integration gates
- **Forbidden:** roll back or semantically weaken integrated P55; create or mutate a destination repository; execute donor convergence; modify unrelated donor-resource projections; hand-edit generated Prompt Kit HTML as canonical source; force-push/reset; weaken semantic/test-floor validators
- **Dependencies:** `main@adb26cb5df57e5fe50b0befc72c14f18da10555c`; PR #632 and `repair/p143-review-contracts-20260922@26a0e030e36daacbe7551f54d451fbc69ca30714` as donor/review evidence only; canonical Prompt Kit builder; prompt semantic lifecycle; deterministic test floor
- **References:** PR #640, PR #632, `registry/prompts/repository-work-ledger-prompts.v1.json:P143`, `harness/contracts/p55-bootstrap-handoff.v1.json`, `scripts/p55_bootstrap_handoff.py`, `tests/test_p143_repository_convergence_prompt.py`, `tests/test_p55_bootstrap_handoff.py`, `harness/prompt-topology/prompt-capability-profiles.v1.json`, `harness/test-floor.v1.json`, `web/prompt-kit/index.html`
- **Acceptance gate:** current-main P55 identity remains authoritative; P143 has safe global synonyms and real generated-JS precedence regression; proposal/provider/authority states are orthogonal; durable plan authority is validated; `p55-bootstrap-handoff/v1` has a versioned contract and executable validator; P143 guards but does not primarily own mainline convergence; focused and deterministic gates pass; generated site is exact; actionable review is empty; exact green head merges into refreshed main; #632 closes only after replacement containment is proven
- **Gate:** PR #640 exact-head CI/review and refreshed-main integration are pending
- **Last proof:** current-main-based semantic commit `09f1d67599f94d534b222bd35306c7e7f1646610`; repository-native generator commit `c40fc9b5cf5b1b039f880f4fc7fee1ae7d9606ff` regenerated `web/prompt-kit/index.html` and removed its temporary workflow; compare against main is 2 ahead / 0 behind before this ledger update
- **Next action:** Run the exact-head PR #640 repository validators and review gates; repair any current finding, then merge the exact green head into refreshed main and close superseded #632 after containment proof
- **Updated:** 2026-09-23T14:36:00-04:00
