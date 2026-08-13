# NTH Month Operation Readiness — 2026-08-12

## Purpose

Provide a safe execution path for later Neuron Track Hours billing periods without silently reusing the legacy April/May workbook assumptions.

This lane does **not** reinterpret evidence. FUN remains authoritative for attendance/evidence truth and final artifact acceptance. Triage owns workbook production and structural/Web Excel checks.

## New execution path

Check a source before building:

```bash
python scripts/build_nth_month.py --roster-log <active-roster.xlsx> --month 2026-08 --check-only
```

A source is `READY` only when the requested month has a `Live - <Month YYYY>`-compatible attendance surface with at least one paired `Clock In` / `Clock Out` date.

Presence-only matrices such as `August 2026 - Attendance (Automated)` are explicitly detected but return `NO_GO`. A worked/not-worked flag may corroborate presence; it does not establish paid hours.

Build after readiness passes:

```bash
python scripts/build_nth_month.py \
  --roster-log <active-roster.xlsx> \
  --month 2026-08 \
  --out-dir Outputs/nth-month-2026-08
```

The builder creates:

- `Neuron_Track_Hours_August_2026_WEBSAFE.xlsx`;
- `nth_month_artifact_2026-08.json`.

The generated workbook is a month-specific working artifact with:

- `Start Here`;
- `August 2026 Neuron Hours`;
- `Tech Summary`;
- `Review Flags`;
- `CF Dictionary`;
- `WebExcel QC`.

The existing April/May engine is left unchanged for historical reproducibility.

## Reused implementation

The month builder reuses the existing:

- Active Roster Log reader and per-day project resolution;
- review classifier;
- NTH table/conditional-formatting helpers;
- shared-string repair used to avoid Excel-for-Web repair signatures;
- NTH preflight validator.

No device count, delivery count, assignment quantity, inventory count, survey target, or management ratio can satisfy the month-source readiness gate.

## Current August operation result

The currently recovered Drive roster artifact exposes an `August 2026 - Attendance (Automated)` presence matrix rather than a clock-in/clock-out `Live - August 2026` paid-hours surface. Under this contract it is intentionally **NO_GO for final August NTH generation**.

That is a source-data blocker, not a workbook-engine blocker: once the authoritative August Live attendance is supplied, this branch can generate and structurally validate the month-specific artifact without modifying code or substituting April/May assumptions.

## Validation

Focused validation:

```bash
python -m pytest tests/test_nth_monthly_artifact.py -q
python -m py_compile triage/nth_month_readiness.py triage/nth_monthly_artifact.py scripts/build_nth_month.py
```

Repository-wide artifact-engine CI remains the compatibility gate.

## Proof ceiling

A green month build proves:

- source structural readiness for paid-hour parsing;
- roster-derived row/hour calculation through the established reader;
- generation of a fresh single-month working workbook;
- static Web Excel preflight.

It does **not** prove FUN evidence acceptance, final billing allocation, client acceptance, or that a presence-only sheet is an attendance-hours source.
