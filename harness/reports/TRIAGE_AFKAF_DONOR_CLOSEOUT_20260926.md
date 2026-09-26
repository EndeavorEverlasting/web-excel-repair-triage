# Triage AFKAF donor closeout — 20260926

**Sprint:** `TRIAGE-AFKAF-DONOR-CLOSEOUT-20260926`
**Program:** `AFK-FACTORY-CONVERGENCE-2026-09-22`
**Donor repo:** `EndeavorEverlasting/web-excel-repair-triage`
**Destination authority:** `EndeavorEverlasting/TokenCorridor` → `plans/active/AFK-FACTORY-CONVERGENCE.*` + `plans/active/M2-PROMPT-KIT-MIGRATION-STATE-PRESENTATION.*`
**Evidence floor at classification:** Triage `origin/main@0fd4c578610f1c3ae81fadd795ace3bb97d7ebc3` (contains merged #650)

## Current-state table (T0)

| Owner | Current state | Unique work | Collision | Exact next action |
| --- | --- | --- | --- | --- |
| PR #651 typed operator-state presentation | MERGED on Triage main@f395a5b4 | Sync A / PK-B01A floor | none | TC consumes PK-B01A packet |
| PR #650 mutation non-weakening lifecycle | MERGED | none remaining | none | do not redo |
| PR #600 PK-B02C routing-decision | CLOSED_UNMERGED after TC #42 | contained | none | receipt `pk-b02c-containment.v1.json` |
| PR #619→#631 PK-B02A capability-watch | CLOSED_UNMERGED after TC #41 | contained (intent chain) | none | receipt `pk-b02a-containment.v1.json` |
| PR #630→#636 PK-B02B findability | CLOSED_UNMERGED after TC #43 | contained (intent chain) | none | receipt `pk-b02b-containment.v1.json` |
| P66 ledger `.ai/WORK_QUEUE.md` | continuity index refreshed | TRQ-023 READY; TRQ-007 OPERATOR; TRQ-020 DONE; TRQ-025 READY | none | merge floor-clear ledger PR |
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

- **Sync A:** #651 merges → refresh PK-B01A packet with integrated main SHA + merge SHA. **Done** on Triage `main@f395a5b4` (merge `e46499fe` + #652/#653/#656/#657).
- **Sync B/C/D:** TokenCorridor B02 containment **proven** — TC PR #41 (B02A / #619→#631), #42 (B02C / #600), #43 (B02B / #630→#636) with receipts `artifacts/convergence/pk-b02{a,b,c}-containment.v1.json` on TC main ≥ `9295edd2`. Triage donors CLOSED_UNMERGED 2026-09-26.
- **Floor-clear continuation 2026-09-26:** STALE #260/#243; SUPERSEDED NEW=0 #561/#393/#313/#257; finish-pass: all 38 remaining opens classified (PORT=21 / RETAIN=17); no further NEW=0 PK closes; no Prompt Kit donor merges; site mirror ≠ M4; TC floor `5691e887`.

## Amendment — classifier rejoin (2026-09-26)

Subagent rejoin after initial closeout proved two material gaps vs the first packet/disposition draft:

1. **Intent-chain anatomy** — `#619` is not a git ancestor of `#631`; `#630` is not a git ancestor of `#636`; path sets are disjoint. Packets `PK-B02A` / `PK-B02B` now state this explicitly with transplant rules. `#600` packet now forbids tip-blob `harness/test-floor.v1.json` transplant.
2. **Under-classified PORT rows** — disposition amended so unique NEW-file PRs are not marked STALE/SUPERSEDED: `#113`, `#119`, `#156`, `#240`, `#245`, `#284`, `#399`, `#431`, `#491`, `#606`, `#625`, `#629` (plus ACTIVE_COLLISION on test-floor/P143 cluster).

Evidence: [Classify open Prompt Kit PRs](de1fe02b-0809-4383-bc58-931f5295fe23), [Extract known donor deltas](cda084bb-3dfd-4464-ad65-93e6c0117b11).
**No M4 authority-cutover claimed.**
