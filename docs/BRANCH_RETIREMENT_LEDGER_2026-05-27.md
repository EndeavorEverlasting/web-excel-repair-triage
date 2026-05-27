# Branch Retirement Ledger — 2026-05-27

## Scope

Remote branch review for **Web Excel Triage** after syncing `main` to `origin/main` (`470486a`). Commands:

```bash
git fetch --all --prune
git branch -r --sort=-committerdate
# For each non-main remote branch:
git log --oneline origin/main..<branch>
git diff --stat origin/main...<branch>
```

No branches were deleted.

## Repository note (plan vs actual)

The convergence sprint plan references **SysAdminSuite** branches (`feature/nmap-cybernet-target-audit`, `harvest/neuron-runtime-current-main-v2`, `docs/post-convergence-audit-2026-05-27`, etc.). Those remotes **do not exist** on this origin. Ledger entries below are **only** branches present on `origin` for Web Excel Triage.

### Cross-repo historical notes (SysAdminSuite sprint)

| Item | Note |
| --- | --- |
| PR #10 | Superseded by PR #36 |
| PR #32 | Superseded by PR #35 |
| PR #6 | Stale / historical Neuron harvest source |
| PR #34 | Carried registry payload despite docs-oriented title |

## Branch summaries

### `origin/docs/weekly-attendance-dashboard-contract`

- **Commits ahead of main:** `a922d03`, `b91587f`, `52122dd`
- **Diff stat:** `docs/README.md`, `docs/WEEKLY_ATTENDANCE_DASHBOARD_CONTRACT.md`, `docs/WORKBOOK_GENERATION_INSIGHTS.md` (+595)
- **Classification:** `needs_validation_before_delete`

### `origin/docs/nw-prj-websafe-insights-2026-05-26`

- **Commits ahead of main:** `b91587f`, `52122dd`
- **Diff stat:** docs index + workbook generation insights (+282)
- **Classification:** `needs_validation_before_delete`

### `origin/feature/2026-05-20-admin-billing-schema-inspector`

- **Commits ahead of main:** `549e9ef`, `65ff5b6`
- **Diff stat:** `scripts/inspect_admin_billing_workbook.py`, tests (+426)
- **Classification:** `needs_validation_before_delete` (inspector not present on `origin/main`)

### `origin/docs-note-tolerant-roster-parsing`

- **Commits ahead of main:** four doc commits through `74ccddd`
- **Diff stat:** `AGENTS.md`, billing pipeline + note-tolerant parsing specs (+468)
- **Classification:** `needs_validation_before_delete`

### `origin/docs-billing-pipeline-contract`

- **Commits ahead of main:** `f94451f`, `4b48d6d`, `6835a26`
- **Diff stat:** agent + pipeline contract docs (+396)
- **Classification:** `needs_validation_before_delete`

### `origin/feature/2026-05-20-admin-billing-context-pipeline`

- **Commits ahead of main:** six feature/doc commits (`1fa925a` … `4d21a2b`)
- **Diff stat (three-dot):** admin context scripts/rules (+772) — **but equivalent functionality exists on `main`** (`triage/admin_billing_context_rules.py` at `470486a` with a squashed merge history).
- **Classification:** `absorbed_in_main` (stale branch tip; not a merge-base ancestor)

### `origin/docs/billing-roster-websafe-insights-2026-05-22`

- **Commits ahead of main:** none
- **Diff stat:** none
- **Classification:** `absorbed_in_main` (merge-base ancestor of `origin/main`)

### `origin/candidate/2026-05-04-web-excel-triage-suite`

- **Commits ahead of main:** eight commits (roster safeguards, billing tests, large triage changes)
- **Diff stat:** +2923 / −494 across triage and tests (no tmp xlsx in final commit range vs codex branch)
- **Classification:** `historical_checkpoint_only`

### `origin/codex/address-review-findings-on-pr-#5`

- **Commits ahead of main:** seven commits (overlaps candidate branch) plus **`billing_runs_tmp/.../billing_summary_2026-04.xlsx`** in diff
- **Diff stat:** +2935 / −494
- **Classification:** `do_not_delete_yet` (contains generated billing artifact in tree; audit before retirement)

### `origin/work`

- **Commits ahead of main:** none
- **Diff stat:** none
- **Classification:** `absorbed_in_main`

## Classification rollup

| Label | Count |
| --- | ---: |
| `absorbed_in_main` | 3 |
| `needs_validation_before_delete` | 5 |
| `historical_checkpoint_only` | 1 |
| `do_not_delete_yet` | 1 |
| `superseded_by_replacement_pr` | 0 |
| `safe_to_delete_after_tag` | 0 |

## Verdict

**Partial** — `main` is current; several doc/feature branches remain unmerged or stale; one remote branch still carries generated billing binaries. Safe bulk deletion is **not** recommended until validations and tagging on follow-up branch `chore/delete-retired-branches-2026-05-27`.
