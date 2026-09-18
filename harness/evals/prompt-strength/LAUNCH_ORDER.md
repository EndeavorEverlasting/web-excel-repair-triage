# Launch Order — Open Items Closeout

## Wave A / Parallel Group 1

1. **Lane 01 — Repair #537 semantic core**
2. **Lane 04 — Close #543 effective-P07 local-proof continuity**
3. **Lane 05 — Add systemic CRLF / line-ending prevention**

## Wave B

4. **Lane 06 — Repair donor projection drift and integrate #542**

Lane 06 may diagnose #542 read-only immediately, but mutation/integration waits for Lane 04 and Lane 05 so it can refresh the newest main and own the final generated/resource projections once.

## Wave C

5. **Lane 07 — Reconcile and merge #537**

## Wave D

6. **Lane 08 — Verify Pages publication and refresh/merge #538**

## Wave E

7. **Lane 09 — Execute P67 observed external-agent pilot**

## Retired lanes

- Lane 02 — RETIRED: concurrent #542 work closed all core review threads at `c6e330fe...`.
- Lane 03 — RETIRED: concurrent #542 work closed all privacy-observatory review threads at the same head.

Do not launch retired lanes from stale copies.

## Waiting / collision rules

- Lane 01 may repair #537 semantic files now but MUST NOT resolve `harness/test-floor.v1.json` until Lane 07.
- Lane 04 integrates before Lane 06 because both can affect generated Prompt Kit state.
- Lane 05 integrates before Lane 06 so #542 exact proof runs under the final repository line-ending policy.
- Lane 07 is the singular final #537 main-reconciliation writer.
- #538 remains downstream; never use it as an early semantic carrier.

The machine dispatch manifest is the orchestration authority. Manual chat scheduling is fallback only when no autonomous adapter can carry the active lanes.
