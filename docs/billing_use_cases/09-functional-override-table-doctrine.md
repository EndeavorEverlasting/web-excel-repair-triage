# Use Case: Functional Override Table Doctrine

Captured: 2026-06-03

## Problem

Override tables are not decorative. They are the mechanism that prevents the billing pipeline from silently applying bad defaults after attendance has already been validated.

The override table must be functional, reviewable, and protected from regression.

## Required behavior

The workbook generator and inspector must verify override-table function before declaring a roster/billing workbook operational.

## Minimum checks

For each month:

- override sheet exists when expected
- override input range exists
- formulas reference the override range
- date matching handles date/time fragments safely
- override entries are not hidden in inaccessible helper cells
- blank override table is allowed only when no overrides are needed

## Formula safety

Date comparisons should use safe date coercion when applicable, such as:

```text
INT(date_value)
```

This avoids failing matches when Excel stores dates with hidden time fragments.

## Override priority

Use this priority order:

1. Approved override
2. Latest validated project assignment
3. Worked Projects tab
4. Note-derived evidence
5. Default assignment

## Output behavior

Internal review output should show:

- override applied
- affected staff
- affected date
- original inferred project
- resolved project
- reason/source

Share-ready output should show only final resolved totals unless exceptions remain unresolved.

## Test expectations

Synthetic tests should cover:

- override table missing
- override table present but not referenced
- override table referenced correctly
- date matching with time fragments
- approved override beating default project assignment

## Practical rule

If the override table is broken, the artifact can look polished and still be wrong. Pretty wrong is still wrong.
