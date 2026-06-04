# Candidate Neuron Track Hours Contract

This document defines the roster-derived **Candidate_Neuron Track Hours** artifact.

## Purpose

Generate the clean candidate workbook from the Active Roster Log without manually patching an old workbook.

The output workbook is named:

```text
Candidate_Neuron Track Hours_April-May_2026_Rezaul_ColorCoded.xlsx
```

## Command

```powershell
python -m triage.nw_prj_neuron_track_hours.candidate_cli ^
  --roster-log Candidates/INTERNAL_Active_Roster_Log.xlsx ^
  --months 2026-04 2026-05 ^
  --out-dir Outputs/candidate_neuron_track_hours_2026_06_04 ^
  --websafe
```

## Output files

```text
Candidate_Neuron Track Hours_April-May_2026_Rezaul_ColorCoded.xlsx
Candidate_Neuron Track Hours_April-May_2026_manifest.json
Candidate_Neuron Track Hours_April-May_2026_preflight.json
Candidate_Neuron Track Hours_April-May_2026_review_removed_rows.csv
```

## Workbook tabs

- `Apr 26`
- `May 26`
- `Rules & Legend`

No `Review Queue` tab is included in the clean workbook. Removed rows are written to the sidecar CSV instead.

## Client Coordination rule

Only the following people may remain classified as `Client Coordination` in clean candidate time sheets:

- Richard Perez / Rich Perez
- Khadejah Harrison
- Alejandro Perales
- Geoff Gerber

Any `Client Coordination` row for another technician is removed from the clean time sheets and written to the removed-rows CSV sidecar.

This is not a visual flagging rule. It is a clean-output rule.

## Rezaul Roman rule

Rezaul Roman's April 2026 Neuron work is represented as mixed work:

- Inventory Management
- Configurations

The generator splits each eligible Rezaul April shift deterministically at the midpoint of the time window when start/end times are available.

The split must preserve total hours and remain visible in the workbook through color coding and row styling.

## Formatting expectations

The candidate workbook uses the readable two-line tracker structure:

| Column | Meaning |
| --- | --- |
| A | Date locator |
| B | Technician name |
| C | Start time |
| D | End time |
| E | Total hours |
| F | Project name |
| G | Assignment type |

Assignment rows are color-coded by assignment type. Rezaul rows use emphasized styling so the mixed work is visible during review.

## Preflight

The generator runs the existing Bonita/Web Excel preflight path when `--websafe` is enabled.

A workbook is not release-ready until Excel for Web manual open proof is recorded in the release checklist.

## Repo hygiene

Source workbooks and generated outputs stay in ignored drop zones:

- inputs under `Candidates/`
- generated artifacts under `Outputs/`
- code, tests, configs, and sanitized docs belong in the repository
