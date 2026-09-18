# Launch Order — Open Items Closeout

1. **Wave A / Parallel Group 1**
   1. Lane 01 — Repair #537 semantic core.
   2. Lane 02 — Close #542 execution-boundary core review.
   3. Lane 03 — Close #542 privacy-observatory review.
   4. Lane 04 — Close #543 effective-P07 local-proof continuity.
   5. Lane 05 — Add systemic CRLF / line-ending prevention.
2. **Wave B**
   - Lane 04 and Lane 05 integrate as soon as exact candidates are green.
   - Lane 06 — Converge #542 after Lanes 02–03 and refresh onto the newest main.
3. **Wave C**
   - Lane 07 — Reconcile and merge #537 after Lane 06.
4. **Wave D**
   - Lane 08 — Refresh #538, publish final main through Pages, complete Operant release gates.
5. **Wave E**
   - Lane 09 — P67 observed external-agent pilot after publication and treatment freeze.

## Waiting rules

- Lane 01 may repair #537-owned semantic files immediately but MUST NOT resolve `harness/test-floor.v1.json` until Lane 07.
- Lane 06 is the only #542 convergence writer. Lane 02 and Lane 03 must work in isolated branches/worktrees based on the exact refreshed #542 head and return commits/artifacts to Lane 06.
- Lane 07 is the only final #537 main-reconciliation writer.
- Generated `web/prompt-kit/index.html` is rebuilt only by the canonical builder and regenerated again whenever a later source-owning lane rebases on newer main.
- #538 is downstream. Never merge a stale release carrier ahead of the semantic lanes.

The machine dispatch manifest is the orchestration authority. Manual chat scheduling is fallback only when no autonomous local adapter is available.
