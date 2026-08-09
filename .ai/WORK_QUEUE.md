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

- **Status:** DONE
- **Priority:** P1
- **Owner:** chatgpt-cross-repo-ledger-20260809
- **Branch / PR:** main / #160 merged
- **Scope:** add a triage-local work ledger, adoption manifest, validator, positive/negative tests, CI, and existing hook integration using the AgentSwitchboard portable contract
- **Forbidden:** copying AxTask `AXQ-*` tasks; changing Prompt Kit product behavior; treating ledger prose as browser/runtime proof; weakening `AGENTS.md`; fetching or executing a remote validator at validation time
- **Dependencies:** AgentSwitchboard contract is canonical on `main` at merge commit `62acecf4a590ecadf4a0b1ad1410e659b4e1b650`
- **References:** `AGENTS.md`, `.ai/work-ledger-adoption.json`, `scripts/validate_repository_work_ledger.py`, `tests/test_repository_work_ledger.py`
- **Acceptance gate:** local validator and positive/negative tests pass, hooks and CI invoke them, the adoption manifest pins the exact durable AgentSwitchboard canonical commit and AxTask donor provenance, and the PR contains no Prompt Kit product changes
- **Gate:** none
- **Last proof:** merge:62acecf4a590ecadf4a0b1ad1410e659b4e1b650 established the portable AgentSwitchboard contract; workflow:31331837078 passed the final triage ledger contract; workflow:31331837062 passed operational harness contracts; workflow:31331837072 passed artifact engine tests; merge:189be37114ef2eb11015b0d962eb23e5d12f1ccc merged triage PR #160
- **Next action:** none; no safe actionable work remains
- **Updated:** 2026-08-09T19:32:00Z

## TRQ-002 — Add repository work ledger stewardship prompt to Prompt Kit

- **Status:** VERIFY
- **Priority:** P1
- **Owner:** chatgpt-prompt-ledger-p66-20260809
- **Branch / PR:** feat/prompt-kit-repository-ledger-p66-20260809 / #163
- **Scope:** add P66 Repository Work Ledger Steward as a versioned prompt extension, integrate it with registry loading and both interactive and copyable guided discovery, add focused regression coverage, regenerate the canonical Prompt Kit website, and preserve the existing safe Windows acquisition route
- **Forbidden:** changing the repository-work-ledger contract itself; changing AxTask or AgentSwitchboard authority; unrelated Prompt Kit UX; hand-editing generated `web/prompt-kit/index.html`; hard-coded Windows usernames; destructive checkout cleanup
- **Dependencies:** TRQ-001
- **References:** `registry/prompts/repository-work-ledger-prompts.v1.json`, `registry/prompts/tutorial-discovery-prompts.v1.json`, `scripts/build_prompt_kit_registry.py`, `registry/prompts/prompt-display-order.v1.json`, `docs/prompt-kit-guided-recommendations.js`, `tests/test_repository_work_ledger_prompt.py`, `web/prompt-kit/index.html`, `scripts/Acquire-LatestPromptKit.ps1`
- **Acceptance gate:** P66 loads through the combined registry with unique ID/sequence, interactive and copyable P65 discovery can route repository-ledger intent to P66, focused tests pass, the checked-in website exactly matches the canonical builder output and contains P66, Prompt Kit and ledger CI pass on the exact PR head, and the merged site remains retrievable through the repository-owned Windows quick-open acquisition path
- **Gate:** none
- **Last proof:** commit:1ef71abc5eabad5dc4fa2b0174f2a96d7a47deef created P66; commit:41986311dc6e2ef7f77b5610107617d9d321cd3e added focused CI ownership; workflow:31332845219 built a 67-prompt canonical preview and passed acquisition/portable checks through generated-site parity; workflow:31332921524 regenerated and proved the exact site; commit:22ce22f5bd5bef76307176f255b0f92851be2e78 committed that generated site; workflow:31333012596 proved the P65 route, P66 tests, exact builder parity, and regenerated artifact; commit:324ad631683939c18bb7b54fd648e50449bb2011 added P66 to the copyable P65 routing map and refreshed the site
- **Next action:** run the repository work-ledger, Prompt Kit web, skill-registry, operator-doc, Pages, and artifact-engine checks on the current exact PR #163 head, repair any owned failure, then advance TRQ-002 to MERGE only when the exact head is green
- **Updated:** 2026-08-09T19:59:00Z
