# NW PRJ Neuron Track Hours — Engine Contract

## Purpose

Prove **local generation** of `Neuron_Track_Hours_April_May_2026_WEBSAFE.xlsx`
from the private Active Roster Log in `Candidates/`, with row-level evidence,
the proven tab structure, and a passing Web Excel preflight.

This engine is intentionally self-contained (`triage/nw_prj_neuron_track_hours/`)
with its own preflight and inlineStr repair, so it merges cleanly alongside
other feature branches without touching shared helpers.

## Source of truth

| Input | Role |
| --- | --- |
| Active Roster Log (`Live - {Month YYYY}`) | Clock in/out per staff/date (wide form, row 2 headers) |
| `Worked Projects - {Month YYYY}` | Per-date project classification |
| Reference workbook (optional) | QC comparison only; never an input shape |
| Admin control (optional) | Rich Guard reconciliation |

## Neuron classification rule

For each staff/date, resolve the project as the **Worked Projects** cell when
present, otherwise the **Live default project** column. A staff/date enters
scope only when the resolved project is documented as a **Neuron Deployment**.

Never default a person to Neuron because they appear on the broader team. This
matches `TRUE_NEURON_RECON_POLICY` in `triage/billing_context/exporters.py`.

Verified against the real roster:

| Metric | Target | Engine |
| --- | ---: | ---: |
| Total Neuron roster hours | 1746.02 | 1746.02 |
| April Neuron hours | 1048.19 | 1048.19 |
| May Neuron hours | 697.83 | 697.83 |
| Go Live weekend rows | 2 | 2 |
| Go Live weekend hours | 22 | 22 |

(Month totals sum penny-rounded per-row values, matching the workbook display.)

## Required workbook sheets

```text
Start Here
April Neuron Hours
May Neuron Hours
Go Live Weekend
Tech Summary
Review Flags
CF Dictionary
WebExcel QC
```

## April / May columns

```text
Action Status | Review Result | Month | Date | Day | Tech | Project |
Clock In | Clock Out | Gross Hours | Weekend | Go Live Weekend | Live Sheet
```

`Action Status` and `Review Result` are manual carry-forward columns with
dropdown validations; preserve them on regeneration.

## Review semantics

- **PURPLE** Rich Guard preserves a confirmed admin full/long day; never downgrade.
- Pinned techs absent from the roster are **not** RED missing-roster failures.
- Note-bearing punches (e.g. `9:28:00 AM/ Bonita`) parse the time and preserve the note.

## Web Excel checks (preflight pass criteria)

- No `inlineStr`, no `ns0:` / `xmlns:ns0`, no `calcChain.xml`
- No `#REF!`, `#VALUE!`, and related error values
- Valid relationships
- Auto-filters present, frozen header rows present
- Conditional formatting present, dropdown validations present
- `CF Dictionary` present
- Expected sheets present

## CLI

```powershell
python -m triage.nw_prj_neuron_track_hours.cli `
  --roster-log "Candidates\attendacne artifacts 6-1-2026\INTERNAL_May_Billing_Active_Roster_Log_2026-06-01-update so that partial hours are flagged before submission.xlsx" `
  --reference "Candidates\attendacne artifacts 6-1-2026\Neuron_Track_Hours_April_May_2026_WEBSAFE.xlsx" `
  --out-dir "Outputs\nw_prj_neuron_track_hours_2026_06_01" `
  --months 2026-04 2026-05 `
  --websafe `
  --zip
```

`--admin-control` and `--reference` are optional. `--pinned` accepts pinned tech names.

## Outputs

```text
Outputs\nw_prj_neuron_track_hours_2026_06_01\
  Neuron_Track_Hours_April_May_2026_WEBSAFE.xlsx
  neuron_track_hours_reconciliation.json
  neuron_track_hours_review_queue.csv
  neuron_track_hours_webexcel_preflight.json
  neuron_track_hours_manifest.json
  neuron_track_hours_carryover.md
  Neuron_Track_Hours_April_May_2026_WEBSAFE.zip
```

## Tests

`tests/test_nw_prj_neuron_track_hours.py` — synthetic fixtures plus a real-roster
regression. No xfails.

```powershell
python -m pytest tests/test_nw_prj_neuron_track_hours.py -q
```
