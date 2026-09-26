# Open PR disposition — Prompt Kit / AFKAF / retained Triage

**Classification floor:** `origin/main@0fd4c578610f1c3ae81fadd795ace3bb97d7ebc3`
**Post-Sync-A note:** `#651`/`#652`/`#653`/`#656` later integrated; re-verify three-dot unique paths before closing any PORT row.
**Method:** refreshed `gh pr list`; unique deltas via `git diff --name-only origin/main...<head>` + NEW/DIFF blob presence; known donor chains preserved as **intent chains** (not git-stacked).
**Classifier evidence:** [Classify open Prompt Kit PRs](de1fe02b-0809-4383-bc58-931f5295fe23); [Extract known donor deltas](cda084bb-3dfd-4464-ad65-93e6c0117b11).
**Amendment 2026-09-26:** corrected under-classified PORT rows and explicit intent-chain anatomy after classifier/donor-delta rejoin.

## Prompt Kit / AFKAF dispositions

| PR | Disposition | Unique behavior | Destination/owner | Gate |
| --- | --- | --- | --- | --- |
| 651 | SUPERSEDED_CONTAINED (was ACTIVE) | typed operator-state presentation + Operant projection; appendix upgrade via #652 | TokenCorridor PK-B01A floor on Triage main | Sync A done; TC consumes PK-B01A packet |
| 650 | SUPERSEDED_CONTAINED | mutation non-weakening lifecycle | main (pre-floor) | already merged; do not redo |
| 600 | PORT_TO_TOKENCORRIDOR / CLOSE_AFTER_TOKENCORRIDOR_CONTAINMENT | routing-decision compiler; Evidence Spine correlation; test-floor +1 entry | TokenCorridor PK-B02C | destination containment; CONFLICTING — replay; tip test-floor exclude |
| 619 | PORT_TO_TOKENCORRIDOR / CLOSE_AFTER_TOKENCORRIDOR_CONTAINMENT | upstream capability-watch contract/runtime/validator/tests; impact edges; refresh workflow wiring | TokenCorridor PK-B02A Slice A | intent chain with #631; **not** git ancestor of #631 |
| 631 | PORT_TO_TOKENCORRIDOR / CLOSE_AFTER_TOKENCORRIDOR_CONTAINMENT | source-floor freshness/recovery F0–F6 sprint-map sections only | TokenCorridor PK-B02A Slice B | docs-only; does **not** carry #619 code |
| 630 | PORT_TO_TOKENCORRIDOR / CLOSE_AFTER_TOKENCORRIDOR_CONTAINMENT | findability/agent-readability design intent (plan) | TokenCorridor PK-B02B Slice A | intent chain; **not** git ancestor of #636 |
| 636 | PORT_TO_TOKENCORRIDOR / CLOSE_AFTER_TOKENCORRIDOR_CONTAINMENT | F0 wayfinding baseline + A1 donor prior-art route; evals/fixtures; CONTEXT tests | TokenCorridor PK-B02B Slice B | F0+A1 only; preserve #630 intent |
| 629 | PORT_TO_TOKENCORRIDOR / ACTIVE_COLLISION | **NEW** `tests/test_repository_organization_prompt.py`; DIFF capability migrations + test-floor | TokenCorridor registry (P144) | collide #399/#606 on test-floor/P143 |
| 625 | PORT_TO_TOKENCORRIDOR | **NEW** `harness/contracts/ux-interaction-language.v1.json` + interaction/discovery validator deltas | TokenCorridor interface UX | collide on shared prompt-kit.js/contracts |
| 606 | PORT_TO_TOKENCORRIDOR / ACTIVE_COLLISION | P143 SSH setup re-admit; **NEW** ssh setup test; DIFF capability migrations + test-floor | TokenCorridor registry; Triage owns test-floor until split | collide #399/#629/#600 |
| 561 | SUPERSEDED_CONTAINED | context-to-artifact recovery | floor already has P56 + `tests/test_context_to_artifact_prompt.py` | close after empty unique-delta re-proof |
| 491 | PORT_TO_TOKENCORRIDOR | **NEW** `tests/test_p13_owner_displacement.py` (+ tmp proof workflow) | TokenCorridor registry ops | PK-B01 displacement proof |
| 431 | PORT_TO_TOKENCORRIDOR / CLOSE_AFTER_TOKENCORRIDOR_CONTAINMENT | **NEW** `tests/test_prompt_finder_observation_pipeline.py` + feedback-hook deltas | TokenCorridor / P141 scout consumers | do not merge merely to clean Triage |
| 399 | PORT_TO_TOKENCORRIDOR / ACTIVE_COLLISION | **NEW** `tests/test_repository_ssh_setup_prompt.py`; P143 registry delta; shares test-floor | TokenCorridor registry + Triage test-floor until split | collide #606/#629/#600 |
| 393 | SUPERSEDED_CONTAINED | tutorial gaps → external resources | operant intake on main | close after empty unique delta |
| 324 | SUPERSEDED_CONTAINED | private feedback transport bridge | floor AFK router + validate owners | close after empty unique delta |
| 317 | SUPERSEDED_CONTAINED | tutorial outcome-driven | floor discovery/tutorial owners | close after empty unique delta |
| 313 | SUPERSEDED_CONTAINED | P114 network posture | floor canary/registry owners | close after empty unique delta |
| 284 | PORT_TO_TOKENCORRIDOR | profile/modality prototype + design docs/workflows | TokenCorridor interface | design→impl gate |
| 274 | RETAIN_IN_TRIAGE | canonical path seam / Triage harness | Triage harness | not AFKAF product port |
| 263 | SUPERSEDED_CONTAINED | route coverage tutorial | floor discovery owners | close after empty unique delta |
| 260 | STALE_NO_UNIQUE_DELTA | hierarchy state-transition trigger file only | n/a | safe close |
| 259 | SUPERSEDED_CONTAINED | tutorial routing coverage | floor discovery owners | close after empty unique delta |
| 257 | SUPERSEDED_CONTAINED | P77 operator closeout requirement | closeout contract on main | close after empty unique delta |
| 245 | PORT_TO_TOKENCORRIDOR | unique `docs/prompt-kit-preference-gameplay.js` + related UI/tests | TokenCorridor interface/promptkit UX | PK-B01/B02 UX packet |
| 243 | STALE_NO_UNIQUE_DELTA | only tmp carrier scripts (`.github/workflows/tmp-creative-*`, `scripts/tmp_*`) | n/a | safe close |
| 242 | SUPERSEDED_CONTAINED | favorite gameplay dashboard | superseded by #245 / floor favorites | close after #245 disposition |
| 240 | PORT_TO_TOKENCORRIDOR | **NEW** `scripts/prompt_registry_grounding.py` + test | TokenCorridor promptkit builders | collide w/ #629 on ops surfaces |
| 156 | PORT_TO_TOKENCORRIDOR | **NEW** profile-qualified routing contract/scripts/tests | TokenCorridor interface/harness | active-writer scan before port |
| 119 | PORT_TO_TOKENCORRIDOR | **NEW** `registry/prompts/preservation-closeout-prompts.v1.json` | TokenCorridor interface/promptkit/registry | PK-B01 registry packet |
| 113 | PORT_TO_TOKENCORRIDOR | prompt passage/canary/efficiency eval skills + harness eval surface | TokenCorridor harness / interface evals | PK-B04 validator split |
| 87 | SUPERSEDED_CONTAINED (draft) | V38 machine-readable registry | current registry builders | draft close |
| 66 | SUPERSEDED_CONTAINED (draft) | V33 GNHF generator | current Prompt Kit registry/site | draft close |
| 57 | SUPERSEDED_CONTAINED (draft) | V21 consolidator | current registry pipeline | draft close |

## Retained Triage-domain (non-AFKAF product)

| PR | Disposition | Unique behavior | Destination/owner | Gate |
| --- | --- | --- | --- | --- |
| 217 | RETAIN_IN_TRIAGE / CONFLICTING | roster ledger range validation | Triage attendance/roster | rebase/reconcile on Excel domain |
| 146 | RETAIN_IN_TRIAGE (draft) | crash-safe PowerShell runner | Triage harness | draft until Excel/ops need |
| 140 | RETAIN_IN_TRIAGE (draft) | workbook visual integrity | Triage Excel/OOXML | draft until domain need |
| 135 | RETAIN_IN_TRIAGE (draft) | delivery sign-off packages | Triage ops | draft |
| 118 | RETAIN_IN_TRIAGE (draft) | device transfer sign-off | Triage ops | draft |
| 110 | RETAIN_IN_TRIAGE (draft) | NTH monthly artifact harness | Triage billing/artifacts | draft |
| 89 | RETAIN_IN_TRIAGE (draft) | accessible dark theme | Triage UI | draft |
| 65 | RETAIN_IN_TRIAGE (draft) | neuron-hours billing evidence | Triage billing | draft |
| 59 | RETAIN_IN_TRIAGE | run-context artifact registry spine | Triage harness | not AFKAF port |
| 55 | RETAIN_IN_TRIAGE (draft) | Bonita Neuron Track Hours rules | Triage billing | draft |
| 50 | RETAIN_IN_TRIAGE (draft) | NW PRJ admin log generator | Triage roster/ops | draft |
| 48 | RETAIN_IN_TRIAGE (draft) | Neuron Track Hours golden profile | Triage billing | draft |
| 45 | RETAIN_IN_TRIAGE (draft) | Candidate Neuron Track Hours | Triage billing | draft |
| 40 | RETAIN_IN_TRIAGE (draft) | client coordination roles docs | Triage ops docs | draft |
| 34 | RETAIN_IN_TRIAGE (draft) | April/May billing summary engines | Triage billing | draft |

## ACTIVE_COLLISION evidence

1. **test-floor / P143 cluster** — Shared `harness/test-floor.v1.json` writers: **#399, #600, #606, #629**. Shared P143/ssh test + capability migration/profile files: **#399 ↔ #606 ↔ #629**.
2. **UI/contract swarm** — `web/prompt-kit/index.html` / shared JS-contracts touched by multiple PORT UX PRs (`#245`, `#625`, historical #651 floor). Treat generated site as builder-owned.
3. **#651** — was ACTIVE during sprint; now SUPERSEDED_CONTAINED on main after merge + #652 appendix.

## Count by disposition (Prompt Kit/AFKAF focus)

- PORT_TO_TOKENCORRIDOR / CLOSE_AFTER_TOKENCORRIDOR_CONTAINMENT: #600, #619, #631, #630, #636, #113, #119, #156, #240, #245, #284, #399, #431, #491, #606, #625, #629
- ACTIVE_COLLISION (serialize writers): #399, #606, #629 (+ #600 test-floor)
- SUPERSEDED_CONTAINED / STALE_NO_UNIQUE_DELTA: older consolidators, discovery/P77/P56/AFK-router equivalents, #243 tmp-only, #260 trigger-only
- RETAIN_IN_TRIAGE: billing/roster/Excel/harness drafts + #59/#274

**Rule:** do not merge Prompt Kit branches merely to clean Triage. Close STALE/SUPERSEDED only after `git diff --name-only origin/main...<head>` proves empty unique behavior or destination containment. Do not treat `#619→#631` or `#630→#636` as git-stacked cherry-pick chains.
