# Bonita Neuron Track Hours — Generator Contract

## Purpose

Produce a clean, **submission-grade** Bonita workbook from the Active Roster
Log: exactly two tabs (`Apr 26` / `May 26`), two-line headers, one row per
included Neuron shift, values only. This is the **Roster Log → Admin Sheet**
one-shot output path — admin-facing, narrow, and clean. No private notes, no
confidence fields, no internal exception machinery leak into the workbook.

This contract reflects the submitted April/May 2026 color-coded candidate. The
hard lesson is simple: **attendance and assignment are separate facts**.

- Live tabs prove clock-in / clock-out truth.
- Worked Projects and Assignments prove whether that day belonged to Neurons.
- Assignment classification rules map included Neuron time into Bonita umbrella
  categories.

The generator lives in-package at `triage/nw_prj_neuron_track_hours/` and reuses
the proven reader (note-aware punch parsing, clock helpers) and the private
inlineStr repair, adding three Bonita-specific modules:

| Module | Role |
| --- | --- |
| `bonita_resolver.py` | Per-date Neuron-project resolver + classification + review trail |
| `bonita_exporter.py` | Clean two-tab `Apr 26` / `May 26` workbook (values only) |
| `bonita_cli.py` | CLI + manifest / review-queue / preflight sidecars |

## Final source hierarchy

A tech/date shift enters the workbook **only** when the final source hierarchy
says that specific person/date belongs to the Neuron project.

```text
1. Live - {Month}
   Source of clock truth only.
   Use it for start/end times and gross hours.
   Do not use the Live default project as proof when better assignment data exists.

2. Assignments - {Month} override table
   Highest-priority reviewed correction.
   This can include a day that Worked Projects/default would exclude, or exclude
   a day that a default project would otherwise pull into Neurons.

3. Worked Projects - {Month}
   Primary per-tech/per-date project assignment when no override exists.
   This is what prevents stale broad-team/default labels from becoming Neuron hours.

4. Assignments - {Month} main grid
   Fallback project context behind Worked Projects.

5. Live default project column
   Last-resort fallback only.
   Never enough by itself when Worked Projects or an override exists.

6. Punch-note project tags
   Conflict evidence. Tags like / Neha, / Bonita, or / Josh exclude the row from
   Neuron submission unless the Assignments override table explicitly confirms
   Neuron work.
```

### Canonical failure this prevents

A person can have valid punches on a date and still be off-Neuron. For example,
Patricia Marrero on 2026-04-23 had a roster punch, but the day was Neha work,
not Neuron work. A generator that trusts the Live/default Neuron label will
produce a false Bonita row. The correct generator excludes the row and keeps the
reason in the review sidecar.

## Exclusions

Parsed, recorded in review where useful, never counted in the submitted month
tabs:

| Case | Behavior |
| --- | --- |
| `/ Neha`, `/ Bonita`, `/ Josh` and similar off-project punch tags | Parse time, keep note in review sidecar, do not count unless explicit Neuron override exists |
| Non-work markers (`PTO` / `NON-PTO` / `N/A` / `out sick` / `vacation` / `off …`) | Skipped to review |
| Excluded names (`Yostinn Minaya`, `Steven Marques` / `Inventory`) | Never counted; recorded for traceability when they otherwise resolve to Neuron |

## Project + assignment classification

`PROJECT NAME` is a display alias:

```text
internal: Neuron Deployments
client-facing: Northwell - Neurons
```

`ASSIGNMENT TYPE` is derived after a row is already included as Neuron work. It
must not be used to decide Neuron eligibility.

### Bonita umbrella categories

Use only the agreed umbrella labels:

- Configurations
- Inventory Management
- Logistics
- Deployments
- Ticket Forwarding
- Client Coordination
- Documentation
- Troubleshooting / Incident Response

### April / May distribution rules

These rules fill classification gaps when the activity sample timing does not
line up cleanly with the roster punches.

| Context | Classification rule |
| --- | --- |
| April evening hours | Most often Deployments, secondarily Logistics |
| April weekend hours | Deployments, occasionally Logistics |
| May weekend hours | Mostly Configurations and Inventory Management |
| May evening hours | Mostly Configurations; occasionally Inventory Management; least often Deployments or Logistics, with May 6 as a known exception pattern |
| Daily hours | Generally Configurations, Inventory Management, Ticket Forwarding, Client Coordination, and Logistics, in that practical order unless stronger evidence exists |

### Client Coordination and Ticket Forwarding restrictions

- Geoff Gerber may receive Client Coordination in April.
- Geoff was pulled to another project in May.
- In May, only these people may receive Client Coordination or Ticket Forwarding:
  - Khadejah Harrison
  - Alejandro Perales
  - Rich Perez / Richard Perez
- Other May Client Coordination or Ticket Forwarding evidence routes to a safer
  operational fallback and low-confidence review, unless an approved override
  explicitly says otherwise.

## Workbook layout

- Tabs: exactly `Apr 26` and `May 26`.
- Two-line headers with a day/date locator column:

```text
DATE  | TECH | START | END  | TOTAL | PROJECT | ASSIGNMENT
(DAY) | NAME | TIME  | TIME | HOURS | NAME    | TYPE
```

- Values only — no formulas, no notes/commentary in cells.
- Start and End are real Excel time values with `h:mm AM/PM` formatting.
- Total Hours is numeric.
- No populated row may have blank TECH, START, END, TOTAL, PROJECT, or ASSIGNMENT.
- No `########` time overflow and no negative time serials.
- inlineStr repair is applied for Web Excel safety.

## Sidecars

Sidecars live next to the workbook under `Outputs/` and are gitignored.

```text
Bonita_Neuron_Track_Hours_April_May_2026.xlsx
Neuron_Track_Hours_April_May_2026_manifest.json     # inputs, sheets used, per-month rows+totals, timestamp
Neuron_Track_Hours_April_May_2026_review_queue.csv  # off-project, markers, excluded names, long shifts, source cells
Neuron_Track_Hours_April_May_2026_preflight.json    # zip/package + Web Excel checks
```

## CLI

```powershell
python -m triage.nw_prj_neuron_track_hours.bonita_cli `
  --roster-log <roster.xlsx> `
  --admin-log <admin.xlsx> `      # reconciliation context only, never workbook truth
  --template <template.xlsx> `    # optional, style only
  --months 2026-04 2026-05 `
  --out-dir "Outputs\neuron_track_hours_2026_06_02" `
  --websafe
```

## Preflight pass criteria (Bonita)

The Bonita workbook is intentionally minimal (values-only), so its preflight is
focused rather than the richer dashboard preflight:

- Valid zip package
- No `inlineStr`, no `ns0:` / `xmlns:ns0`
- No `calcChain.xml`
- No external links
- SharedStrings declared count matches actual worksheet references
- Semantic gate passes
- Required populated-row fields are nonblank

## Tests

Protected fixture-only coverage includes:

- `tests/test_nw_prj_neuron_track_hours_bonita.py`
- `tests/test_bonita_source_hierarchy.py`
- `tests/test_neuron_work_context_rules.py`

Required behavior:

- April spans full month, not Apr 1-4.
- Note-bearing punches parse start/end but do not leak notes into the workbook.
- Non-work markers route to review.
- Assignments override table can include a reviewed Neuron correction.
- Worked Projects can exclude a stale Live/default Neuron label.
- Off-project punch tags exclude unless an explicit Neuron override exists.
- Long shifts are included and review-flagged.
- Excluded names never count.
- Start/end/total/project/assignment cannot be blank on populated rows.
- Start/end cells are real time values.

```powershell
python -m pytest tests/test_nw_prj_neuron_track_hours_bonita.py tests/test_bonita_source_hierarchy.py tests/test_neuron_work_context_rules.py -q
```
