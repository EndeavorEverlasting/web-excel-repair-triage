contractRef: agentswitchboard.repository-work-ledger.v1@1.0.0
canonicalContractCommit: 62acecf4a590ecadf4a0b1ad1410e659b4e1b650
localAuthority: AGENTS.md

# Web Excel Repair Triage shared work ledger

This is the repository-local coordination ledger for unfinished triage and Prompt Kit work. It routes work; it does not replace `AGENTS.md`, source, tests, builders, generated-artifact contracts, PRs, CI, or browser/runtime evidence.

Continuation states are not stopping states.
PR opened is not completion.
DONE is strict.
Canonical terminal action: none; no safe actionable work remains

## TRQ-001 — Adopt the repository-family work ledger contract

- **Status:** VERIFY
- **Priority:** P1
- **Owner:** chatgpt-cross-repo-ledger-20260809
- **Branch / PR:** feat/repository-work-ledger-20260809 / #160
- **Scope:** add a triage-local work ledger, adoption manifest, validator, positive/negative tests, CI, and existing hook integration using the AgentSwitchboard portable contract
- **Forbidden:** copying AxTask `AXQ-*` tasks; changing Prompt Kit product behavior; treating ledger prose as browser/runtime proof; weakening `AGENTS.md`; fetching or executing a remote validator at validation time
- **Dependencies:** AgentSwitchboard contract is canonical on `main` at merge commit `62acecf4a590ecadf4a0b1ad1410e659b4e1b650`
- **References:** `AGENTS.md`, `.ai/work-ledger-adoption.json`, `scripts/validate_repository_work_ledger.py`, `tests/test_repository_work_ledger.py`
- **Acceptance gate:** local validator and positive/negative tests pass, hooks and CI invoke them, the adoption manifest pins the exact durable AgentSwitchboard canonical commit and AxTask donor provenance, and the PR contains no Prompt Kit product changes
- **Gate:** none
- **Last proof:** merge:62acecf4a590ecadf4a0b1ad1410e659b4e1b650 established the AgentSwitchboard canonical contract on `main`; commit:19c706a515258683cc7925f0c5dc69dd8291afce passed the triage ledger and broader harness workflows before canonical repin
- **Next action:** run `python scripts/validate_repository_work_ledger.py` and `python -m unittest tests.test_repository_work_ledger -v`, then inspect PR #160 exact-head checks and advance to the repository-owner merge gate only if the repinned head remains green
- **Updated:** 2026-08-09T19:28:00Z
