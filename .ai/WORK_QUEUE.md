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

- **Status:** VERIFY
- **Priority:** P1
- **Owner:** chatgpt-prompt-ledger-p66-20260809
- **Branch / PR:** feat/prompt-kit-repository-ledger-p66-20260809 / #163
- **Scope:** add P66 Repository Work Ledger Steward as a versioned prompt extension, integrate it with registry loading and both interactive and copyable guided discovery, add focused regression coverage, regenerate the canonical Prompt Kit website, and preserve the existing safe Windows acquisition route
- **Forbidden:** changing BlacksmithGuild RepoLedgerInteroperability.v1 or repository-local ledger semantics; changing AxTask or AgentSwitchboard domain authority; unrelated Prompt Kit UX; hand-editing generated `web/prompt-kit/index.html`; hard-coded Windows usernames; destructive checkout cleanup
- **Dependencies:** TRQ-001, TRQ-002
- **References:** `registry/prompts/repository-work-ledger-prompts.v1.json`, `registry/prompts/tutorial-discovery-prompts.v1.json`, `scripts/build_prompt_kit_registry.py`, `registry/prompts/prompt-display-order.v1.json`, `docs/prompt-kit-guided-recommendations.js`, `tests/test_repository_work_ledger_prompt.py`, `web/prompt-kit/index.html`, `scripts/Acquire-LatestPromptKit.ps1`
- **Acceptance gate:** P66 loads through the combined registry with unique ID/sequence, interactive and copyable P65 discovery can route repository-ledger intent to P66, focused tests pass, the checked-in website exactly matches the canonical builder output and contains P66, Prompt Kit and ledger CI pass against current repository authority, concurrent TRQ blocks are preserved, and the merged site remains retrievable through the repository-owned Windows quick-open acquisition path
- **Gate:** none
- **Last proof:** commit:1ef71abc5eabad5dc4fa2b0174f2a96d7a47deef created P66; workflow:31332921524 regenerated and proved the exact 67-prompt site; commit:22ce22f5bd5bef76307176f255b0f92851be2e78 committed the generated site; workflow:31333012596 proved the P65 route, P66 tests, exact builder parity, and regenerated artifact; commit:324ad631683939c18bb7b54fd648e50449bb2011 added P66 to the copyable P65 routing map; merge:576f4596ab711b3b22321fcf90413b6eef2d6e5e advanced main with the completed Blacksmith authority reconciliation that this task now preserves as TRQ-002
- **Next action:** reconcile PR #163 against current main, run repository-work-ledger and Prompt Kit contract validation on the reconciled exact head, repair any owned failure, and merge only after the nine-file product/harness diff preserves current Blacksmith ledger authority and both existing DONE blocks
- **Updated:** 2026-08-09T20:02:00Z
