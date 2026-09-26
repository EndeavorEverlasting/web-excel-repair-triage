# Triage AFKAF donor closeout — 20260926

**Sprint:** `TRIAGE-AFKAF-DONOR-CLOSEOUT-20260926`
**Program:** `AFK-FACTORY-CONVERGENCE-2026-09-22`
**Donor repo:** `EndeavorEverlasting/web-excel-repair-triage`
**Destination authority:** `EndeavorEverlasting/TokenCorridor` → `plans/active/AFK-FACTORY-CONVERGENCE.*` + `plans/active/M2-PROMPT-KIT-MIGRATION-STATE-PRESENTATION.*`
**Evidence floor at classification:** Triage `origin/main@0fd4c578610f1c3ae81fadd795ace3bb97d7ebc3` (contains merged #650)

## Current-state table (T0)

| Owner | Current state | Unique work | Collision | Exact next action |
| --- | --- | --- | --- | --- |
| PR #651 typed operator-state presentation | OPEN MERGEABLE; repair head pushed | shared actionability policy + builder appendix upgrade + closeout tests | Operant refresh path-triggers on builder/index; projection already refreshed on branch | wait required checks; merge; emit Sync A PK-B01A handoff |
| PR #650 mutation non-weakening lifecycle | MERGED into main@0fd4c578 | none remaining | none | do not redo |
| PR #600 PK-B02C routing-decision | OPEN CONFLICTING | routing compiler/runtime + Evidence Spine tests | test-floor / Evidence Spine writers | emit packet; TokenCorridor PK-B02C containment |
| PR #619→#631 PK-B02A capability-watch | OPEN MERGEABLE chain | #619 contract/runtime/validator/tests; #631 freshness recovery plan | intake contract / refresh workflow | emit chain packet; preserve predecessor→successor |
| PR #630→#636 PK-B02B findability | OPEN MERGEABLE chain | #630 plan; #636 F0+A1 wayfinding evals/context | CONTEXT.md / operant intake skill | emit chain packet; preserve #630 intent with #636 impl |
| P66 ledger `.ai/WORK_QUEUE.md` | continuity index; stale PK refs possible | Triage-domain TRQ-023 READY; TRQ-007 OPERATOR; TRQ-020 BLOCKED | none for ledger write after #651 | reconcile against current PRs/packets |
| Generated Prompt Kit site | builder-owned | none for this sprint beyond #651 regen | one writer: `scripts/build_prompt_kit_registry.py` | never hand-edit `web/prompt-kit/index.html` |
| Operant external resources | tracked projection refreshed on #651 | donor pin drift detector | scheduled refresh vs PR path trigger | keep sync via `scripts/sync_operant_external_resources.py` |

## #651 diagnosis (T1)

- Failing CI step observed historically: `Compare live donor candidate with tracked projection` (`cmp` byte 228 / line 8 on `resources.v1.json`).
- Cause class: **legitimate tracked projection drift** (live donor candidate vs tracked sidecar), **not** a typed-state presentation regression.
- #651 owned paths do not include resource index semantics; path filter fires because builder/`index.html` changed.
- Branch already contains `362f920c` Operant projection refresh; this sprint added appendix upgrade fix `c638fbc7`.
- CodeRabbit major finding closed: legacy appendices missing `OPERATOR STATE PRESENTATION CONTRACT` now force appendix replacement.

## Disposition summary (T3)

See `harness/reports/TRIAGE_OPEN_PR_DISPOSITION_20260926.md`.

## Transplant packets (T4)

| Packet | Path |
| --- | --- |
| PK-B01A (post-#651 Sync A) | `harness/reports/packets/PK-B01A-operator-state-presentation.packet.md` |
| PK-B02A | `harness/reports/packets/PK-B02A-upstream-capability-watch.packet.md` |
| PK-B02B | `harness/reports/packets/PK-B02B-prompt-findability.packet.md` |
| PK-B02C | `harness/reports/packets/PK-B02C-routing-decision.packet.md` |

## Compatibility (T7)

- Legacy routes `/prompt-kit/` and `/operant/` remain compatibility surfaces per `harness/contracts/operant-product-identity.v1.json`.
- Combined builder remains compatibility composition until M5 gate.
- Removable under named M5 cleanup only after TokenCorridor publishes destination website + consumer rewiring.
- **No M4 authority-cutover claimed.**

## Sync events

- **Sync A:** #651 merges → refresh PK-B01A packet with integrated main SHA + merge SHA.
- **Sync B/C/D:** owned by TokenCorridor containment evidence; Triage closes corresponding donors only after destination proof.
