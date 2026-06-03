# Use Case: Timestamped Artifact Output Naming

Captured: 2026-06-03

## Problem

Generated billing artifacts should not use vague names like `LATEST`. That forces manual renaming and weakens context when several outputs are generated during the same day.

## Required behavior

Generated artifacts must include a timestamp in the filename so each output is unique and traceable without manual cleanup.

## Naming rule

Use local project time unless a run explicitly supplies another timezone.

Default timezone:

```text
America/New_York
```

Recommended timestamp format:

```text
YYYY-MM-DD_HHMM
```

Recommended pattern:

```text
{artifact_family}_{months_or_scope}_{YYYY-MM-DD_HHMM}_{mode}.{ext}
```

## Examples

```text
Billing_Summaries_April_May_2026_2026-06-03_1542_VALUES_ONLY_WITH_CHARTS.xlsx
Billing_Summaries_April_May_2026_2026-06-03_1542_VALUES_ONLY_WITH_CHARTS.zip
latest_billing_summary_totals_2026-06-03_1542.json
repo_billing_summary_handoff_2026-06-03_1542.md
```

## Forbidden by default

Avoid these names for generated deliverables:

```text
LATEST_*.xlsx
final.xlsx
output.xlsx
billing_summary.xlsx
new_version.xlsx
```

## Collision handling

If two artifacts are generated in the same minute, append seconds or a short run id:

```text
YYYY-MM-DD_HHMMSS
```

or

```text
YYYY-MM-DD_HHMM_run-02
```

## Provenance requirement

The generated provenance JSON should include:

```text
generated_at_local
generated_at_utc
timezone
filename_timestamp
artifact_paths
source_workbook
```

## Test expectations

Synthetic tests should verify:

- artifact names include the timestamp
- repeated runs do not overwrite previous outputs
- generated ZIP and XLSX names share the same timestamp token
- provenance JSON records the same timestamp token used in filenames

## Practical rule

The filename should explain when it was generated before anyone opens it.
