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

- **Status:** VERIFY
- **Priority:** P1
- **Owner:** chatgpt-blacksmith-ledger-authority-reconcile-20260809
- **Branch / PR:** chore/blacksmith-ledger-authority-reconcile-20260809 / pending
- **Scope:** repoint the existing triage adoption manifest, queue header, validator, and tests directly to BlacksmithGuild RepoLedgerInteroperability.v1 while preserving the repository-local TRQ ledger, CI, hooks, Prompt Kit authority, and artifact-engine boundaries
- **Forbidden:** changing Prompt Kit product behavior; changing workbook/artifact engines; adopting AgentSwitchboard Work class/frontier as a portable requirement; copying AxTask domain tasks; executing remote BlacksmithGuild or AgentSwitchboard validators
- **Dependencies:** BlacksmithGuild portable contract merge 429237aa41d8712d71859865c9be407ca23d8580 and authority-registry reconciliation merge ecf0718556e77f10747a997d2cb0173af81b3d29
- **References:** `.ai/work-ledger-adoption.json`, `scripts/validate_repository_work_ledger.py`, `tests/test_repository_work_ledger.py`, `.github/workflows/repository-work-ledger-contract.yml`, `.githooks/pre-commit`, `.githooks/pre-push`
- **Acceptance gate:** the existing local ledger workflow passes; validator enforces exact Blacksmith portable pin, verified AxTask donor provenance, local references, continuation/DONE rules, and stale symbolic-ref rejection; existing hooks remain wired; PR contains no Prompt Kit or artifact-engine product mutation
- **Gate:** none
- **Last proof:** artifact:.ai/work-ledger-adoption.json artifact:scripts/validate_repository_work_ledger.py artifact:tests/test_repository_work_ledger.py
- **Next action:** run the existing repository-work-ledger contract workflow, inspect exact-head failures, and repair any owned compatibility regression before merge
- **Updated:** 2026-08-09T19:49:00Z
