# Billing Use Case Doctrine

Captured: 2026-06-03

These notes preserve billing, roster, dashboard, and attendance-validation use cases that were discovered during live workbook triage. They are intentionally split into small files so implementation agents can turn each doctrine into code, fixtures, and tests without guessing.

## Use cases

1. [Compare like-family roster logs](./01-roster-log-like-artifact-comparison.md)
2. [Choose leadership/admin share tabs](./02-leadership-admin-share-tab-boundary.md)
3. [Keep billing dashboard graphs primary](./03-dashboard-chart-first-billing-summaries.md)
4. [Avoid fragile external-link billing outputs](./04-values-only-no-external-link-submit-artifacts.md)
5. [Preserve the April 2 Cyen Bonita punch correction](./05-april-2-cyen-bonita-punch-correction.md)
6. [Attribute Rezaul Roman to Neuron when otherwise untracked](./06-rezaul-roman-neuron-project-attribution.md)
7. [Treat Patricia CASR issue as accepted day-off evidence](./07-patricia-casr-day-off-handling.md)
8. [Require latest source tracker for regenerated summaries](./08-latest-source-tracker-intake-for-regeneration.md)
9. [Keep override tables functional and reviewable](./09-functional-override-table-doctrine.md)
10. [Protect monthly headers and conditional formatting improvements](./10-monthly-header-and-cf-regression-guard.md)

## Non-negotiable theme

Validated attendance should reduce rework, not create new interpretive labor. Billing artifacts should be generated from the most current validated workbook state, then exported in a leadership-safe form with visual dashboards intact and private/internal detail excluded unless explicitly requested.
