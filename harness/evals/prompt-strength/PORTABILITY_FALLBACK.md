# Portability Fallback — Open Items Closeout

The primary orchestration artifact is `Outputs/prompt-parallel-dispatch/manifest.json`. The tracked seed is byte-identical and exists so the manifest contract can be regression-tested. If a local autonomous adapter exists, consume the manifest directly. Do not ask the operator to manually schedule active lanes.

## Active portability prompts — launch order

1. `LANE_01_UPSTREAM_REFRESH.md` — repair #537 prompt-strength semantic core.
2. `LANE_04_SHARED_POLICY_CONVERGENCE.md` — close and integrate #543 effective-P07 local-proof continuity.
3. `LANE_05_LINE_ENDING_GUARD.md` — systemic CRLF/line-ending policy and regression.
4. `LANE_06_P542_CONVERGENCE.md` — repair current donor projection drift and integrate #542.
5. `LANE_07_P537_CONVERGENCE.md` — reconcile #537 to current main and merge.
6. `LANE_08_PUBLICATION_RELEASE.md` — verify Pages publication and refresh/merge #538.
7. `LANE_09_P67_OBSERVED_EFFECTIVENESS.md` — execute canonical P67 external-agent pilot.

## Retired portability prompts

- `LANE_02_ADVERSARIAL_FIXTURES.md` — RETIRED / do not launch.
- `LANE_03_DEPENDENCY_RECONCILIATION.md` — RETIRED / do not launch.

Concurrent #542 work at `c6e330fe...` resolved all review threads that those two lanes were created to repair.

## Required fallback behavior

A local agent assigned one active lane reads only that lane plus its declared read-first owners and refreshes remote/provider truth before mutation. It must not inherit sibling mutation authority merely because a sibling appears in the contract horizon.

When graph width is at least two but no adapter is available, report exactly:

`PARALLEL EXECUTION: DEGRADED — graph width 3; no safe bound autonomous local-agent adapter.`

Then record:

`AUTONOMY_GAP: bind Outputs/prompt-parallel-dispatch/manifest.json to an evidenced local repo runner and preserve a verify-receipt-compatible dispatch receipt.`

Manual copy/paste is recovery portability only and never counts as dispatch proof.
