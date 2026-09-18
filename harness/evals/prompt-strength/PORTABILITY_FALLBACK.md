# Portability Fallback — Open Items Closeout

The primary orchestration artifact is `Outputs/prompt-parallel-dispatch/manifest.json`. The tracked seed is byte-identical and exists only so the manifest contract can be regression-tested. If a local autonomous adapter exists, consume the manifest directly. Do not ask the operator to manually schedule these lanes.

If no autonomous adapter can be bound, these files are the complete one-lane portability prompts, in launch order:

1. `LANE_01_UPSTREAM_REFRESH.md` — repair #537 prompt-strength semantic core.
2. `LANE_02_ADVERSARIAL_FIXTURES.md` — close #542 execution-boundary core review.
3. `LANE_03_DEPENDENCY_RECONCILIATION.md` — close #542 privacy-observatory review.
4. `LANE_04_SHARED_POLICY_CONVERGENCE.md` — close and integrate #543 effective-P07 local-proof continuity.
5. `LANE_05_LINE_ENDING_GUARD.md` — systemic CRLF/line-ending policy and regression.
6. `LANE_06_P542_CONVERGENCE.md` — converge #542 and merge.
7. `LANE_07_P537_CONVERGENCE.md` — reconcile #537 to current main and merge.
8. `LANE_08_PUBLICATION_RELEASE.md` — verify Pages publication and refresh/merge #538.
9. `LANE_09_P67_OBSERVED_EFFECTIVENESS.md` — execute the canonical P67 external-agent pilot.

## Required fallback behavior

A local agent assigned one lane reads only that lane file plus its declared read-first owners. It must still refresh remote/provider truth before mutation. It must not copy mutation authority from sibling lanes merely because those files are mentioned in the contract horizon.

When Wave A graph width is at least two but no adapter is available, report exactly:

`PARALLEL EXECUTION: DEGRADED — graph width 5; no safe bound autonomous local-agent adapter.`

Then record:

`AUTONOMY_GAP: bind Outputs/prompt-parallel-dispatch/manifest.json to an evidenced local repo runner and preserve a verify-receipt-compatible dispatch receipt.`

Manual copy/paste is recovery portability only and never counts as dispatch proof.
