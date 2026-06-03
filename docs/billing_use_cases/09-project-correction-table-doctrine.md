# Use Case: Project Correction Table Doctrine

Captured: 2026-06-03

## Problem

Project correction tables are control surfaces. They prevent the billing pipeline from applying default project assignments after attendance has already been validated.

The correction table must be functional, reviewable, and protected from regression.

## Required behavior

The workbook generator and inspector must verify the correction table before declaring a roster or billing workbook operational.

## Minimum checks

For each month:

- correction sheet exists when expected
- correction input range exists
- formulas reference the correction range
- date matching handles date/time fragments safely
- correction entries are visible in review areas
- blank correction table is allowed only when no corrections are needed

## Formula safety

Date comparisons should use safe date coercion when applicable, such as:

```text
INT(date_value)
```

This avoids failed matches when Excel stores dates with hidden time fragments.

## Priority order

Use this priority order:

1. Approved manual correction
2. Latest validated project assignment
3. Worked Projects tab
4. Note-derived evidence
5. Default assignment

## Output behavior

Internal review output should show:

- correction applied
- affected staff
- affected date
- original inferred project
- resolved project
- reason/source

Share-ready output should show only final resolved totals unless exceptions remain unresolved.

## Test expectations

Synthetic tests should cover:

- correction table missing
- correction table present but not referenced
- correction table referenced correctly
- date matching with time fragments
- approved correction beating default project assignment

## Practical rule

If the correction table fails validation, the artifact should require review before use.
