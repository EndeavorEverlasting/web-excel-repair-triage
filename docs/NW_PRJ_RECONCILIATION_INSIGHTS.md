# NW PRJ Reconciliation Insights

Lessons from v6.5 (roster-confirmed, reduced noise) and v6.6 (full artifact comparison) dashboard generations.

## Three-way comparison

The comparison engine reconciles:

1. Latest dashboard (manual review truth)
2. Latest roster log (punch evidence)
3. Latest manual admin scratch copy (admin hours truth)

Optional: official admin workbook for leadership-facing cross-check only.

## Wrong authority (corrected)

The false-positive engine once treated the admin workbook `Project Team` tab as project assignment authority. **It is not.** Use roster defaults, worked-project tabs, notes, and `Team Scope` instead.

## Admin scratch targeting

Tell operators to update the **manual admin scratch** copy first. Do not redirect them to the official admin workbook while scratch is still the checkpoint.

## Queue reduction

Resolved, skipped, and gray rows MUST demote to `Resolved_Archive` so active tabs show fewer flags. v6.5 proved noise reduction is a feature, not a loss of coverage.

## Rich Guard compression

When roster is incomplete but admin scratch shows a full/long day, emit a purple guardrail row for review — do **not** propose lower hours. Wording:

```text
Preserve admin full/long-day hours unless explicit short-day evidence exists.
```

## Partial-hour compression

Collapse duplicate partial flags per tech/date. Classify as amber `Needs Review` unless Column A already resolved.

## Lingering flags

After comparison, emit a summary of:

- Rows still active after manual done (carry-forward bug)
- Gray rows resurrected in active queues (archive bug)
- Roster/admin hour mismatches with no Column A resolution
- Repaired-filename inputs used in the run (STOP-SHIP)

## Note-bearing punch cells

Punch cells may contain notes; parse with note-tolerant roster doctrine. Preserve note text in `Roster Check Notes`; extract clean times for `Roster Latest In` / `Out`.

## Comparator module

Implementation: `triage/nw_prj_artifact_compare.py`  
CLI entry: `python -m triage.nw_prj_artifact_compare`
