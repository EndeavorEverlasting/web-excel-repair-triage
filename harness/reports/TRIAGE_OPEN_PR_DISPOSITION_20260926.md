# Open PR disposition — Prompt Kit / AFKAF / retained Triage

**Triage classification floor:** `origin/main@f395a5b485acbf0eff2a6d34576ef4ecd6721bf6` (post-#651/#652/#653/#656/#657)
**TokenCorridor floor (operator):** `5691e887855eb24021197da0d745496cab3939b5` (includes B02 + AWG-S3 + PK-WEB-FAST plan receipt)
**B02 containment receipts (TC):** `artifacts/convergence/pk-b02a-containment.v1.json` (PR #41), `pk-b02c-containment.v1.json` (PR #42), `pk-b02b-containment.v1.json` (PR #43)
**Public site mirror (≠ M4):** https://endeavoreverlasting.github.io/TokenCorridor-prompt-kit-site/
**Method:** `gh pr list` + `git diff --name-only origin/main...<head>` NEW vs DIFF blob presence.
**Snapshot open count:** **38** (2026-09-26 finish pass). Cumulative closes this day without Triage merges: STALE #260/#243; B02 donors #600/#619/#631/#630/#636; SUPERSEDED NEW=0 #561/#393/#313/#257.
**Finish-pass note:** re-scan of remaining Prompt Kit open PRs found **zero** NEW=0 candidates; no additional STALE/SUPERSEDED closes in this bounded batch.

## Closed this wave (do not reopen without new unique delta)

| PR | Class | Evidence |
| --- | --- | --- |
| 600 | CLOSE_AFTER_TOKENCORRIDOR_CONTAINMENT | TC #42 + `pk-b02c-containment.v1.json` |
| 619, 631 | CLOSE_AFTER_TOKENCORRIDOR_CONTAINMENT | TC #41 + `pk-b02a-containment.v1.json` (intent chain) |
| 630, 636 | CLOSE_AFTER_TOKENCORRIDOR_CONTAINMENT | TC #43 + `pk-b02b-containment.v1.json` (intent chain) |
| 260, 243 | STALE_NO_UNIQUE_DELTA | trigger/tmp carriers only |
| 561, 393, 313, 257 | SUPERSEDED_CONTAINED | NEW=0 vs Triage main; feature on floor |

## Remaining open — Prompt Kit / AFKAF

| PR | Class | NEW | Evidence / next |
| --- | --- | --- | --- |
| 629 | PORT_TO_TOKENCORRIDOR / ACTIVE_COLLISION | 3 | org-auditor + ssh test; collide #399/#606 |
| 625 | PORT_TO_TOKENCORRIDOR | 1 | `ux-interaction-language.v1.json` |
| 606 | PORT_TO_TOKENCORRIDOR / ACTIVE_COLLISION | 1 | P143 SSH re-admit test; collide #399/#629 |
| 544 | PORT_TO_TOKENCORRIDOR | 3 | Cursor failure observatory install |
| 491 | PORT_TO_TOKENCORRIDOR | 2 | P13 displacement test (+ tmp workflow) |
| 431 | PORT_TO_TOKENCORRIDOR | 2 | observation pipeline test (+ tmp workflow) |
| 399 | PORT_TO_TOKENCORRIDOR / ACTIVE_COLLISION | 1 | ssh setup test; collide #606/#629 |
| 324 | PORT_TO_TOKENCORRIDOR | 2 | feedback bridge script+test |
| 317 | PORT_TO_TOKENCORRIDOR | 1 | `validate_prompt_finder_outcomes.js` |
| 284 | PORT_TO_TOKENCORRIDOR | 5 | profile/modality prototype design+tests |
| 263 | PORT_TO_TOKENCORRIDOR | 2 | route analysis scripts |
| 259 | PORT_TO_TOKENCORRIDOR | 2 | tutorial-route validator+tests |
| 245 | PORT_TO_TOKENCORRIDOR | 3 | preference gameplay JS+tests; stacked on #242 |
| 242 | ACTIVE_COLLISION / PORT survivor=#245 | 3 | favorite dashboard; keep until #245 ported |
| 240 | PORT_TO_TOKENCORRIDOR | 3 | `prompt_registry_grounding.py`+test |
| 156 | PORT_TO_TOKENCORRIDOR | 6 | profile-qualified routing |
| 119 | PORT_TO_TOKENCORRIDOR | 1 | preservation-closeout prompts registry |
| 113 | PORT_TO_TOKENCORRIDOR | 29 | passage/canary/efficiency eval surface |
| 87 | PORT_TO_TOKENCORRIDOR (legacy draft) | 83 | V38 registry tree — unique; do not STALE-close |
| 66 | PORT_TO_TOKENCORRIDOR (legacy draft) | 52 | V33 GNHF — unique; do not STALE-close |
| 57 | PORT_TO_TOKENCORRIDOR (legacy draft) | 36 | V21 consolidator — unique; do not STALE-close |

## Remaining open — RETAIN_IN_TRIAGE (spreadsheet / ops / harness)

| PR | Class | Domain note |
| --- | --- | --- |
| 331 | RETAIN_IN_TRIAGE / CONFLICTING | billing hygiene |
| 274 | RETAIN_IN_TRIAGE | canonical path seam (Triage harness) |
| 217 | RETAIN_IN_TRIAGE / CONFLICTING | roster ledger range validation |
| 146 | RETAIN_IN_TRIAGE (draft) | crash-safe PowerShell runner |
| 140 | RETAIN_IN_TRIAGE (draft) | workbook visual integrity |
| 135 | RETAIN_IN_TRIAGE (draft) | delivery sign-off packages |
| 118 | RETAIN_IN_TRIAGE (draft) | device transfer sign-off |
| 110 | RETAIN_IN_TRIAGE (draft) | NTH monthly artifact harness |
| 89 | RETAIN_IN_TRIAGE (draft) | accessible dark theme |
| 65 | RETAIN_IN_TRIAGE (draft) | neuron-hours billing evidence |
| 59 | RETAIN_IN_TRIAGE | run-context / artifact registry spine |
| 55 | RETAIN_IN_TRIAGE (draft) | Bonita Neuron Track Hours rules |
| 50 | RETAIN_IN_TRIAGE (draft) | NW PRJ admin log generator |
| 48 | RETAIN_IN_TRIAGE (draft) | Neuron Track Hours golden profile |
| 45 | RETAIN_IN_TRIAGE (draft) | Candidate Neuron Track Hours |
| 40 | RETAIN_IN_TRIAGE (draft) | client coordination roles docs |
| 34 | RETAIN_IN_TRIAGE (draft) | April/May billing summary engines |

## Summary counts (open only, n=38)

| Class (mutually exclusive) | Count |
| --- | --- |
| PORT_TO_TOKENCORRIDOR (incl. legacy drafts #57/#66/#87 and #242/#245) | 21 |
| RETAIN_IN_TRIAGE | 17 |
| **Open total** | **38** |

ACTIVE_COLLISION overlays (subset of PORT, not extra opens): #399, #606, #629 (P143/test-floor); #242↔#245 stack.

Closed earlier today (not open): 11 — STALE #260/#243; B02 donors #600/#619/#631/#630/#636; SUPERSEDED #561/#393/#313/#257.

## Rules

1. Do **not** merge Prompt Kit donors into Triage merely to reduce open count.
2. Close STALE/SUPERSEDED only when NEW-file unique delta is 0 or destination containment is proven.
3. Leave RETAIN spreadsheet/ops/harness PRs open.
4. Site mirror ≠ M4 authority cutover.
