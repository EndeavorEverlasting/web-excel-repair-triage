contractRef: agentswitchboard.repository-work-ledger.v1@1.0.0
canonicalContractCommit: caa32133e67ed2fed7ed643e4bb05570a2ef392f
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
- **Branch / PR:** feat/repository-work-ledger-20260809 / pending
- **Scope:** add a triage-local work ledger, adoption manifest, validator, positive/negative tests, CI, and existing hook integration using the AgentSwitchboard portable contract
- **Forbidden:** copying AxTask `AXQ-*` tasks; changing Prompt Kit product behavior; treating ledger prose as browser/runtime proof; weakening `AGENTS.md`; fetching or executing a remote validator at validation time
- **Dependencies:** AgentSwitchboard portable contract commit `caa32133e67ed2fed7ed643e4bb05570a2ef392f`
- **References:** `AGENTS.md`, `.ai/work-ledger-adoption.json`, `scripts/validate_repository_work_ledger.py`, `tests/test_repository_work_ledger.py`
- **Acceptance gate:** local validator and positive/negative tests pass, hooks and CI invoke them, the adoption manifest pins the exact AgentSwitchboard contract commit and AxTask donor provenance, and the PR contains no Prompt Kit product changes
- **Gate:** none
- **Last proof:** artifact:.ai/work-ledger-adoption.json pins canonical portable contract and donor provenance; executable validation pending PR CI
- **Next action:** run `python scripts/validate_repository_work_ledger.py` and `python -m unittest tests.test_repository_work_ledger -v`, then inspect the exact PR head checks and repair any owned failure
- **Updated:** 2026-08-09T19:18:00Z
