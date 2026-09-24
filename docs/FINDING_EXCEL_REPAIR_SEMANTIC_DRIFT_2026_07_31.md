# Finding: an Excel-repaired workbook can pass structural gates while reverting or deleting operational data

Date: 2026-07-31  
Status: confirmed from candidate/repaired workbook pair; semantic acceptance checker added  
Severity: stop-ship for promotion of a repaired copy when semantic findings are non-empty

## Executive finding

The Excel-repaired copy of the 2026-07-31 roster workbook is structurally cleaner than the candidate, but it is **not semantically equivalent** to the candidate.

A cell-level comparison found:

- **79 lost non-empty cell payloads** on `Assignment Ledger`;
- **8 changed table-header strings** (`Line`, `Location`, etc. became `Column1` … `Column8`);
- **30 changed attendance time values** on `Live - July 2026`.

The attendance drift is operationally significant. For three active technicians, the five Jul 27–31 clock-in/clock-out pairs changed from **08:00–17:00** in the candidate back to **09:00–18:00** in the repaired copy. Those 30 cells are ordinary numeric values, not formula cache changes.

The repaired copy therefore cannot be promoted merely because Excel opens it without the original repair condition.

## Assignment-ledger loss

The candidate stored the right-side assignment-detail payload in duplicate worksheet row records. Excel removed the duplicate row records during repair. The package became structurally valid, but cells that existed only in those duplicate row records disappeared.

Observed effects include:

- the assignment-detail heading at `Q24` disappeared;
- the 11-line device-detail payload across `Q26:X36` disappeared;
- the table headers at `Q25:X25` were regenerated as generic `Column1` … `Column8`.

This is direct evidence that **repair normalization can be destructive** even when the repaired workbook is easier for Excel to open.

## Attendance-value reversion

The candidate intentionally changed Jul 27–31 for three technicians to:

- clock in: `0.3333333333333333` = 08:00;
- clock out: `0.7083333333333334` = 17:00.

The repaired copy contains:

- clock in: `0.375` = 09:00;
- clock out: `0.75` = 18:00.

The affected cells are `BC:BL` on rows 8, 36, and 54. These are raw numeric attendance values. The original pre-edit workbook also contained 09:00–18:00 in those cells, so the repaired copy effectively reverted that intended candidate edit.

The mechanism of that reversion is not yet asserted as a root cause. The acceptance conclusion does not depend on mechanism: the repaired copy differs materially from the intended candidate and must fail promotion.

## New acceptance guard

`triage.semantic_preservation.compare_semantics()` compares same-named sheets and same cell coordinates between a candidate and a repaired copy.

It reports:

- missing sheets;
- lost non-empty cell payloads;
- lost formulas;
- changed explicit formula text;
- changed strings;
- materially changed numeric values;
- changed typed values.

It deliberately ignores:

- style-only cells;
- inline-string versus shared-string storage differences;
- tiny numeric serialization differences;
- formula cached-value changes caused by recalculation;
- shared-formula followers whose formula text is omitted but whose formula presence remains.

Run:

```bash
python -m triage.semantic_preservation candidate.xlsx repaired.xlsx --json
```

A semantically equivalent pair exits `0`; any material finding exits `1`.

## Harness rule

A repaired workbook is **diagnostic evidence, not automatically the next golden artifact**.

Promotion must require all of the following independently:

1. package / OOXML gates pass;
2. known repair-pattern gates pass;
3. candidate→repaired semantic-preservation comparison passes or every difference is explicitly reviewed and accepted;
4. Excel for Web acceptance passes;
5. operator acceptance passes in the real workbook workflow.

This closes the gap where an automated or Excel-produced repair can eliminate the structural symptom by silently deleting or reverting the user's intended data.

## Privacy / fixture policy

No field workbook or client data is committed. Regression tests synthesize tiny OOXML workbooks that exercise only semantic-loss and representation-equivalence rules.
