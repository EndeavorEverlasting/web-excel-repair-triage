# Artifact Format Profile Contract

## Purpose

The repo must be able to reproduce the formatting posture of approved generated artifacts without committing private workbooks.

Formatting profiles define the expected workbook shape, visible headers, submission-safety boundaries, and forbidden internal language for each artifact family.

## Why this exists

Recent manually accepted outputs had a better formatting standard than older repo-generated workbooks. The repo should emulate that standard through code and profiles rather than requiring repeated chat instructions.

## Core rules

- Submission artifacts are clean and narrow.
- Internal review, confidence, rule names, and exception details stay in internal artifacts or sidecars.
- Client/submission trackers must not contain `Bonita-friendly`, heuristic/confidence language, raw note explanations, or `ColumnN` corpse headers.
- Workbooks should use stable, Excel-for-Web-compatible features: values, tables, charts where needed, frozen panes, filters, readable widths, and no macros or external links.
- Profiles are committed; private approved reference workbooks remain gitignored.

## Profile files

```text
configs/artifact_profiles/bonita_neuron_track_hours.json
configs/artifact_profiles/admin_billing_summary.json
```

## Helper module

```text
triage/artifact_format_profiles.py
```

The helper provides:

- `load_profile(path)`
- `apply_submission_sheet_format(ws, header_row, ...)`
- `assert_no_forbidden_submission_text(values, forbidden)`

## Submission-safe expectations

### Bonita Neuron Track Hours

- Exactly two visible sheets: `Apr 26`, `May 26`
- Two-line tracker header
- Required visible fields: date/day, tech, start, end, total, project, assignment
- Assignment values are task categories from `triage/neuron_work_context_rules.py`
- No notes, confidence, rule names, or internal review explanations in the workbook

### Admin Billing Summary

- Clear front-facing dashboard/summary structure
- Monthly, project, tech, and tech-project summary tabs
- Review and exception detail only in internal variants
- Charts and tables should be native Excel structures, not pasted screenshots

## Future implementation targets

- Existing exporters should load these profiles instead of hardcoding style choices.
- Semantic gates should use profile `required_headers`, `sheets`, and `forbidden_text`.
- Artifact comparison should use these profiles when comparing candidate outputs to approved reference workbooks.
