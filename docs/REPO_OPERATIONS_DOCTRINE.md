# Repo Operations Doctrine

## Anchor before action

Before modifying code, capture the current repo state.

```bash
pwd
git remote -v
git branch --show-current
git status --short --untracked-files=all
git fetch origin --prune
git branch -vv
git rev-list --left-right --count origin/main...HEAD
git log --oneline --decorate -12
```

## Baseline before blame

Run targeted tests before judging a scoped change. Run the full suite only to
classify broader repo health.

```bash
python -m pytest tests/test_roster_parser.py tests/test_attendance_report.py \
    tests/test_billing_summary_generator.py -q
```

Baseline for the merged roster/billing safeguard work (PR #5 + PR #6):

```text
91 passed in ~10s
```

Reference: `docs/reviews/BASELINE_TEST_RESULTS_2026-05-04.md`

## Separate old failures from new failures

If the full suite is already red, document failure clusters and do not block
scoped work on unrelated failures. Known pre-existing failure clusters:

- Billing regression layout mismatches (`test_billing_regression.py`)
- Invoice DOCX fixture/package read errors (`test_invoice_parser.py`)
- Older malformed-row expectations that predate annotated-clock-cell doctrine

## Review agent triage

Classify review comments by severity before acting on them:

| Priority | Category |
|----------|----------|
| P0 | Security, data loss, destructive behavior |
| P1 | Build or deploy breakage |
| P2 | Output correctness |
| P3 | Edge-case correctness |
| P4 | Maintainability |
| P5 | Style |

## Checkpoint rules

Before commit:

```bash
git status --short --untracked-files=all
git diff --stat
git diff --check
```

After staging:

```bash
git diff --cached --stat
git diff --cached --check
```

## Generated artifact policy

Do not commit generated billing workbooks or runtime outputs.

Ignored paths:

```text
billing_runs/
billing_runs_tmp/
```

## Platform-portability rule

Do not use Linux-only `strftime` format codes (`%-d`, `%-m`) in shared code.
Use `str(int(d.strftime("%d")))` to strip leading zeros cross-platform.

## Billing parser doctrine

Annotated clock cells are valid input when they contain a parseable time value.

Examples:

```text
9:28:00 AM / Bonita
9:28 AM - off-project coverage
17:30 / inventory follow-up
6:00 PM
```

Rules:

- Extract the clock time.
- Preserve useful note context where internal outputs support it.
- Do not silently reclassify admin output from raw notes alone.
- Approved overrides beat raw notes.
- Resolved project logic beats assumptions.

## Overnight and long-shift doctrine

- Overnight shifts must not silently undercount gross hours.
- Long shifts above the configured threshold (`long_shift_threshold_hours`,
  default `12.0`) require separate review visibility.
- Long-shift styling takes precedence over regular overnight styling.
- Suspicious output must be visible in scripts, reports, and tests.
- Overnight note formatter must not emit invalid times (e.g. `08:60`); minutes
  must wrap correctly via `total_minutes % (24 * 60)`.

## Invoice pivot doctrine

- Sheet 2 "Totals by Category" must key by invoice category, not vendor.
- Current template exposes: Invoice Category | Invoice Count | Trucking | Labor | Total.
- `Courier` and `Other` are included in Total but have no dedicated display
  columns — this mirrors the Agilant reference template.
- Do not add Courier/Other columns without confirming template contract first.

## Follow-up lane discipline

Open separate branches and PRs for each cleanup lane. Do not bundle:

| Lane | Branch prefix | Scope |
|------|---------------|-------|
| Billing regression layout | `cleanup/billing-regression-layout` | `test_billing_regression.py` |
| Invoice DOCX fixtures | `cleanup/invoice-docx-fixtures` | `test_invoice_parser.py` |
| Malformed-row expectations | `cleanup/malformed-row-expectations` | annotated-clock tests |
| Category display columns | `followup/invoice-category-display-columns` | Sheet 2 column semantics |

## PR body template

```markdown
## Summary
<What this PR does.>

## Scope
- <Scoped change 1>

## Out of Scope
- Full-suite cleanup outside this lane.
- Unrelated workbook layout changes.
- Generated billing artifacts.

## Validation
```bash
<commands run>
```
Result:
```text
<result>
```

## Baseline Notes
docs/reviews/BASELINE_TEST_RESULTS_2026-05-04.md

## Risks
- <Template drift risk>
- <Web Excel compatibility risk>

## Review Focus
- <Files reviewers should inspect first>
```
