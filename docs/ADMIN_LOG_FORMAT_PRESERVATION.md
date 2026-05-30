# Admin Log Format Preservation

## Purpose

The admin log copy is an internal working copy intended to remain paste-ready against the real admin log. Its structure and visual layout matter. A workbook can be structurally intact and still fail the operator if the generated copy visually drifts from the control workbook.

## Rule

When generating or updating an admin log copy, prefer modifying the uploaded/control workbook in place over reconstructing it from a blank workbook.

Reconstruction is allowed only when the generator can deliberately reproduce:

- sheet order,
- sheet names,
- merged cells,
- row heights,
- column widths,
- number/date/time formats,
- fonts,
- fills,
- borders,
- frozen panes,
- filters/tables,
- formulas,
- data validation,
- conditional formatting,
- tab colors,
- hidden rows/columns,
- notes/comments where applicable.

## Required behavior

### Admin copy workflow

1. Load the latest uploaded admin copy as the base workbook.
2. Resolve target rows/cells from headers and date/tech mappings.
3. Write only the required values/formulas into target cells.
4. Preserve existing visual formatting unless an explicit format patch is requested.
5. Export a new internal copy with a clear filename.

Suggested name:

```text
INTERNAL_Admin_Log_Copy_FORMAT_PRESERVED_<date>_WEBSAFE.xlsx
```

### Formatting diff workflow

If a generated admin copy visually differs from the control workbook, produce a formatting-diff report before attempting another rebuild.

The report should identify:

- changed column widths,
- changed row heights,
- changed number formats,
- changed fills/fonts/borders,
- missing frozen panes,
- missing filters/tables,
- missing data validation,
- missing conditional formatting,
- missing charts/drawings if expected.

## Stop-ship checks

Do not bless an admin log copy if:

- the structure is valid but the visual layout no longer matches the control workbook,
- formulas were replaced with static values without explicit approval,
- paste-ready target cells moved,
- the workbook no longer resembles the real admin log copy operators are using,
- or Excel for Web repairs the file.

## Implementation guidance

The generator should expose two modes:

```bash
python -m triage.admin_log_format apply \
  --base-admin-copy Candidates/admin_copy.xlsx \
  --updates Outputs/admin_updates.json \
  --out Outputs/INTERNAL_Admin_Log_Copy_FORMAT_PRESERVED_WEBSAFE.xlsx
```

```bash
python -m triage.admin_log_format diff \
  --control Candidates/admin_copy.xlsx \
  --candidate Outputs/generated_admin_copy.xlsx \
  --out Outputs/admin_format_diff.json
```

## Relationship to billing context artifacts

Leadership-facing billing summaries may use generated layouts. Internal admin log copies should preserve the uploaded control workbook format unless explicitly told otherwise.

Contextual billing summaries and the static HTML dashboard are review surfaces. The admin log copy is a paste-ready operational surface.
