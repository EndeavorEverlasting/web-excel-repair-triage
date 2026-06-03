# Use Case: Dashboard Charts Must Be Present and Populated

Captured: 2026-06-03

## Problem

The billing summary output looked close, but the executive summary and dashboard areas were missing or empty charts. That weakens the artifact, especially when the dashboard is expected to carry the first visual read.

## Required behavior

Billing summary generation must treat charts as first-class output, not decoration.

Every billing summary workbook should include:

- month-level KPI block
- technician-hours chart
- project-hours chart
- clean versus review/excluded rows chart when useful
- chart source tables stored locally in the workbook

## Chart safety rules

- Charts must use local workbook ranges only.
- Charts must not depend on external links.
- Chart source tables must be visible or clearly discoverable.
- Charts must be validated after export.
- Empty charts are a generation failure unless the source month has no billable data.

## Verification

The generator should inspect the finished workbook and confirm:

- each required dashboard has at least one chart object
- each chart has a non-empty source range
- each source range has non-empty values
- dashboard totals match summary totals

## Test expectations

Synthetic tests should create billing rows and assert that:

- charts exist
- source data exists
- summary totals populate
- zero-data cases show an intentional no-data message instead of blank visuals

## Implementation note

Do not rely on Excel opening/recalculating the workbook to populate dashboards. Source tables should be value-backed during generation.
