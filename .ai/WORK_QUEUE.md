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

- **Status:** OPERATOR
- **Priority:** P1
- **Owner:** chatgpt-cross-repo-ledger-20260809
- **Branch / PR:** feat/repository-work-ledger-20260809 / #160
- **Scope:** add a triage-local work ledger, adoption manifest, validator, positive/negative tests, CI, and existing hook integration using the AgentSwitchboard portable contract
- **Forbidden:** copying AxTask `AXQ-*` tasks; changing Prompt Kit product behavior; treating ledger prose as browser/runtime proof; weakening `AGENTS.md`; fetching or executing a remote validator at validation time
- **Dependencies:** AgentSwitchboard PR #105 must merge first; this consumer must then repin to the resulting canonical AgentSwitchboard `main` commit
- **References:** `AGENTS.md`, `.ai/work-ledger-adoption.json`, `scripts/validate_repository_work_ledger.py`, `tests/test_repository_work_ledger.py`
- **Acceptance gate:** local validator and positive/negative tests pass, hooks and CI invoke them, the adoption manifest pins the exact durable AgentSwitchboard canonical commit and AxTask donor provenance, and the PR contains no Prompt Kit product changes
- **Gate:** AgentSwitchboard PR #105 is not yet merged; `.ai/work-ledger-adoption.json` and `canonicalContractCommit` must be repinned to its resulting `main` commit before PR #160 may merge
- **Last proof:** commit:19c706a515258683cc7925f0c5dc69dd8291afce includes review-driven Python validator regressions; workflow:31331631248 passed the exact-head repository work ledger contract; workflows 31331631256 and 31331631252 also passed
- **Next action:** operator merge AgentSwitchboard PR #105 first; then update `.ai/work-ledger-adoption.json` and `.ai/WORK_QUEUE.md` in PR #160 to the resulting AgentSwitchboard `main` commit, rerun the local ledger validator and PR CI, and merge triage only after those gates pass
- **Updated:** 2026-08-09T19:27:00Z
