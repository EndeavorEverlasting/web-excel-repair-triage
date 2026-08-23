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
- **Acceptance gate:** historical local implementation merged with local validator/tests, CI, and existing Git hooks; portable authority is separately reconciled by TRQ-002
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
