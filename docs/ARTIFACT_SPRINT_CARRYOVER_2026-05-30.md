# Artifact Sprint Carryover: 2026-05-30

Lessons from the May 2026 billing artifact sprint, encoded for the repo.

Related docs:

- [`BILLING_WORK_CONTEXT_RULES.md`](BILLING_WORK_CONTEXT_RULES.md)
- [`BILLING_SUMMARY_TEXT_QUALITY.md`](BILLING_SUMMARY_TEXT_QUALITY.md)
- [`ADMIN_LOG_FORMAT_PRESERVATION.md`](ADMIN_LOG_FORMAT_PRESERVATION.md)
- [`BILLING_CONTEXT_EXPORTER.md`](BILLING_CONTEXT_EXPORTER.md)

## Lessons

- Return one ZIP bundle when multiple artifacts are produced (`--zip`).
- Verify every linked output path exists before reporting it (manifest validation in CLI).
- Separate leadership artifacts from internal review artifacts (leadership XLSX vs `--internal-xlsx`).
- Leadership outputs must not expose raw provenance, confidence fields, private notes, or internal mismatch machinery.
- Work Context must be complete — no ellipses, no clipped generated text (see text-quality doc).
- Charts are required for monthly billing summaries.
- Static HTML dashboard is useful, but all workbook-sourced text must be escaped.
- CSV outputs must neutralize formula prefixes (`=`, `+`, `-`, `@`).
- Internal admin log copy formatting is a separate workflow and must preserve the uploaded control workbook (see admin log doc).
- Context rules must handle April Saturdays, May Saturdays, evenings, day hours, and warehouse/inventory logistics.
- Do not commit real billing workbooks — engines, docs, tests, and synthetic fixtures only.

## Leadership vs internal surfaces

| Surface | Includes | Excludes |
|---------|----------|----------|
| Leadership XLSX | Date, Tech, Hours, Work Context, charts | Source row/sheet, context reason, raw assignment, confidence |
| Internal XLSX / HTML / CSV | Full provenance, mismatches, reason, notes | — |

Tracker Import tab is internal-only unless `--include-tracker-import` is explicitly passed.
