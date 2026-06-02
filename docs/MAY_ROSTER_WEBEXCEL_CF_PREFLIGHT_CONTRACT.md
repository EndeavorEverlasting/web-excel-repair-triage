# May Roster Web Excel CF Preflight & Repair-Free QA Contract

Module: `triage.may_roster_webexcel`
Sprint: May 2026 roster workbook forensics + (gated) repair-free patching.

## Core doctrine

A workbook that opens only because Excel for Web **repaired** it is not a
success. It is evidence of a structural defect. The sprint target is
repair-free Web Excel compatibility plus correct conditional-formatting
behavior.

Reports never claim "Excel for Web opened cleanly" unless an actual Microsoft
Graph / Web Excel open check was performed. Package preflight only certifies:

> Package preflight passed. Excel for Web manual open confirmation still required.

## What the engine does

| Mode | Command | Output |
|------|---------|--------|
| inspect | `python -m triage.may_roster_webexcel.cli inspect --candidate <bad>.xlsx --reference <good>.xlsx --out-dir <dir>` | `cf_diff_report.json`, `package_preflight.json`, `sunday_bleed_report.json`, `overnight_punch_report.json`, `unassigned_hours_report.csv`, `carryover.md`, `inspect_manifest.json` |
| patch | `python -m triage.may_roster_webexcel.cli patch --base <safe>.xlsx --reference <good>.xlsx --out-dir <dir> --as-of 2026-06-02` | A repair-free workbook **only if every gate passes**, else `repairfree_manifest.json` with `result: REFUSED` and no workbook. |

## 1. Sunday/Monday conditional-formatting bleed

Symptom: an extra Sunday cell highlights when the following Monday weekday
cell is populated.

The checker (`cf_inspector.sunday_bleed_report`) is **month-aware**: it derives
every Sunday/Monday boundary in the month from the live-sheet date headers
(`"May 17 - Clock In"` etc.) and maps each date to its clock-in/out columns. It
does not hardcode a single column pair. For May 2026 the boundaries are:

```
2026-05-03 -> 2026-05-04
2026-05-10 -> 2026-05-11
2026-05-17 -> 2026-05-18   (Sunday cols AI/AJ, Monday cols AK/AL)
2026-05-24 -> 2026-05-25
2026-05-31 -> (no in-sheet Monday)
```

It flags three defect classes:

- `sunday_rule_references_monday` - a CF rule on Sunday columns whose formula
  references a Monday column.
- `always_true_blanket_over_sunday` - an always-true rule (`1` / `TRUE`) that
  paints Sunday columns regardless of content.
- `merged_range_crosses_sunday_monday` - a single `sqref` range spanning both
  a Sunday and Monday column.

Observed on the real May candidate: an always-true `1` blanket rule over each
weekend column group (`E:H`, `S:V`, `AG:AJ`, `AU:AX`, `BI:BL`). This is the
prime Sunday-bleed root cause.

### Patch rules

- Blank Sunday punch cells must remain neutral.
- Weekend no-work must not be treated as malformed.
- Sunday rules must not reference Monday punch cells.
- Do not delete all conditional formatting as a shortcut.
- Do not broadly rewrite worksheet XML. Patch only the minimum broken CF, and
  only when the package preflight of the patched workbook passes.

## 2. Overnight punch classification

After-midnight clock-outs are **not** automatically malformed. When
`clock_out < clock_in` the shift is overnight; gross duration is
`(24 - clock_in) + clock_out` (equivalently `(1 - clock_in) + clock_out` in
day-fraction form).

A row is malformed **only** when:

- exactly one punch is present (single missing punch),
- a punch value is non-empty but not parseable as a time,
- clock-in equals clock-out (zero/ambiguous duration),
- the computed duration exceeds the absurd threshold (default 20h).

Anchors confirmed on the real workbook (both correctly classified overnight,
not malformed):

| Tech | Date | Punches | Gross | Classification |
|------|------|---------|-------|----------------|
| Alejandro Perales | 2026-05-09 | 8:30 AM -> 1:00 AM | 16.5 | Overnight / Needs Confirmation |
| Julio Mojica | 2026-05-06 | 5:15 PM -> 12:00 AM | 6.75 | Overnight / Needs Confirmation |

Live roster punch cells are never modified.

## 3. Unassigned-hours detail (name names)

A row/date is unassigned when:

1. actual paid hours > 0,
2. project/assignment is blank, unknown, weakly mapped, `0`, or not billable,
3. the entry is not clearly PTO, unpaid, off-project, or weekend **no-work**.

Weekend *no-work* is exempt (paid hours = 0). Paid weekend work with no project
is genuinely unassigned and is reported. The summary names tech, date, hours,
and current assignment with status `Unassigned / Needs Project`.

Confirmed on the real workbook (gross hours; net may differ from prior passes):

| Tech | Date | Gross Paid Hours | Assignment |
|------|------|------------------|------------|
| Md Suhan Newaz | 2026-05-02 | 11.5 | 0 |
| Md Suhan Newaz | 2026-05-09 | 10.0 | 0 |

## 4. Web Excel package safety

`package_checks.run_package_preflight` wraps `triage.gate_checks.run_all` and
adds: namespace leakage (`ns0:`/`ns1:`/`ns2:`, `xmlns:ns0`), undeclared
`mc:Ignorable` prefixes, `_xlfn.`/`_xludf.`/`_xlpm.`, `inlineStr`, duplicate
workbook rel IDs, unresolved sheet `r:id`, content-type coverage, stale
`calcChain.xml`, and (share-safe) no formulas / no external links.

A ZIP/XML pass is necessary but not sufficient. The report wording is honest
and never claims a confirmed Web Excel open.

## Share-safe output

`summary_builder.build_sharesafe_summary` writes a values-only workbook with:
Executive Summary, Project Summary, Tech Project Summary, Daily Summary,
Exceptions Summary, Unassigned Hours Summary. It must contain no formulas, no
external links, and no hidden internal tabs.

## Private data

Real `.xlsx` workbooks live only in `Candidates/`, `Repaired/`, and `Outputs/`
and are gitignored. Tests use synthetic fixtures generated into a tmp dir at
test time; no real workbook is ever committed.
