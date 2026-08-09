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

- **Status:** MERGE
- **Priority:** P1
- **Owner:** chatgpt-prompt-ledger-p66-20260809
- **Branch / PR:** feat/prompt-kit-repository-ledger-p66-20260809 / #163
- **Scope:** add P66 Repository Work Ledger Steward as a versioned prompt extension, integrate it with registry loading and both interactive and copyable guided discovery, add focused regression coverage, regenerate the canonical Prompt Kit website, and preserve the existing safe Windows acquisition route
- **Forbidden:** changing BlacksmithGuild RepoLedgerInteroperability.v1 or repository-local ledger semantics; changing AxTask or AgentSwitchboard domain authority; unrelated Prompt Kit UX; hand-editing generated `web/prompt-kit/index.html`; hard-coded Windows usernames; destructive checkout cleanup
- **Dependencies:** TRQ-001, TRQ-002
- **References:** `registry/prompts/repository-work-ledger-prompts.v1.json`, `registry/prompts/tutorial-discovery-prompts.v1.json`, `scripts/build_prompt_kit_registry.py`, `registry/prompts/prompt-display-order.v1.json`, `docs/prompt-kit-guided-recommendations.js`, `tests/test_repository_work_ledger_prompt.py`, `web/prompt-kit/index.html`, `scripts/Acquire-LatestPromptKit.ps1`
- **Acceptance gate:** P66 loads through the combined registry with unique ID/sequence, interactive and copyable P65 discovery can route repository-ledger intent to P66, focused tests pass, the checked-in website exactly matches the canonical builder output and contains P66, Prompt Kit and ledger CI pass against current repository authority, concurrent TRQ blocks are preserved, and the merged site remains retrievable through the repository-owned Windows quick-open acquisition path
- **Gate:** none
- **Last proof:** commit:7f884a4f50cf9a79a6279aefa3449ef644141a3f reconciled the nine-file P66 sprint onto current Blacksmith-authority main without replacing TRQ-001/TRQ-002; workflow:31333415602 passed the repository work-ledger contract; workflow:31333415653 passed Prompt Kit web contracts including exact generated-site parity; workflow:31333415601 passed skill prompt registry and generator UX; workflow:31333415617 passed Prompt Kit GitHub Pages; workflow:31333415628 passed operator documentation contracts; workflow:31333415619 passed artifact engine tests
- **Next action:** merge PR #163 at the current exact head after this queue-only continuation commit passes the repository work-ledger contract, then record the merge receipt in a strict-DONE closeout
- **Updated:** 2026-08-09T20:08:00Z
