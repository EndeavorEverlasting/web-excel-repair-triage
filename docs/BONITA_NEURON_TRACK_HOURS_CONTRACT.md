# Bonita Neuron Track Hours — Generator Contract

## Purpose

Produce a clean, **submission-grade** Bonita workbook from the Active Roster
Log: exactly two tabs (`Apr 26` / `May 26`), two-line headers, one row per
included Neuron shift, values only. This is the **Roster Log → Admin Sheet**
one-shot output path — admin-facing, narrow, and clean. No private notes, no
confidence fields, no internal exception machinery leak into the workbook.

The generator lives in-package at `triage/nw_prj_neuron_track_hours/` and reuses
the proven reader (note-aware punch parsing, clock helpers) and the private
inlineStr repair, adding three new modules:

| Module | Role |
| --- | --- |
| `bonita_resolver.py` | Per-date Neuron-project resolver + classification + review trail |
| `bonita_exporter.py` | Clean two-tab `Apr 26` / `May 26` workbook (values only) |
| `bonita_cli.py` | CLI + manifest / review-queue / preflight sidecars |

## Inclusion rule (project-driven)

A tech/date shift enters the workbook **only** when the resolved project for
that date is the Neuron project. Resolution precedence:

```text
Worked Projects cell  >  Assignments override  >  Live default project
```

- The default project counts unless that day is overwritten to a non-Neuron
  project; a default non-Neuron day counts only when overwritten to Neuron.
- `ASSIGNMENT TYPE` (e.g. `Neuron Installation`, `Delivery / Transport /
  Disposal`) is an activity sub-label **within** the Neuron project and still
  counts.
- April spans the full month (Apr 1–30) and May spans the roster-supported
  range, derived from the `Live - {Month}` date headers — never a stale tracker
  tab.

## Exclusions (parsed, recorded in review, never counted)

| Case | Behavior |
| --- | --- |
| `/ Bonita` and other off-project coverage punches | Parse time, keep note in review sidecar, do not count |
| Non-work markers (`PTO` / `NON-PTO` / `N/A` / `out sick` / `vacation` / `off …`) | Skipped to review |
| Excluded names (`Yostinn Minaya`, `Steven Marques` / `Inventory`) | Never counted; recorded for traceability |

## Project + assignment classification

- `PROJECT NAME` is a **display alias**: internal `Neuron Deployments` →
  client-facing `Northwell - Neurons`.
- `ASSIGNMENT TYPE` is **operator-classified** and is *not* reliably encoded in
  the per-date tabs. The engine defaults to `Neuron Installation`, accepts an
  explicit `Delivery / Transport / Disposal` signal from worked-project activity
  text or a punch note, and routes anything ambiguous to the review sidecar
  rather than fabricating a Delivery/Transport label. This is the main fidelity
  gap vs the hand-made tracker.

## Workbook layout

- Tabs: exactly `Apr 26` and `May 26`.
- Two-line headers with a day/date locator column:

```text
DATE  | TECH | START | END  | TOTAL | PROJECT | ASSIGNMENT
(DAY) | NAME | TIME  | TIME | HOURS | NAME    | TYPE
```

- Values only — no formulas, no notes/commentary in cells.
- inlineStr repair applied for Web Excel safety.

## Sidecars (next to the workbook, all gitignored)

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

## Tests

`tests/test_nw_prj_neuron_track_hours_bonita.py` — 13 fixture-only cases
covering both tabs, full-month April span, note-bearing punches, non-work
markers, worked-project and Assignments overrides, long shift, excluded names,
populated-row completeness, manifest counts/totals, preflight, and `/ Bonita`
off-project exclusion.

```powershell
python -m pytest tests/test_nw_prj_neuron_track_hours_bonita.py -q
```
