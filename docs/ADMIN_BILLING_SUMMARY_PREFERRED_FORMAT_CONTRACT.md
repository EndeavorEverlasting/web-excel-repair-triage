# Admin Billing Summary — My Preferred Format Contract

## Purpose

Generate the admin-facing monthly billing summary in the user's "My Preferred
Format" (the April reference layout) from the Active Roster Log, with native
charts and an embedded Neuron Track Hours tracker tab. Built for emailing a
clean monthly summary that carries the Bonita monthly Neuron Track Hours as a
tab.

Engine: [triage/admin_billing_summary/](triage/admin_billing_summary/)
(`reader` -> `aggregator` -> `exporter` -> `cli`).

## Project resolution (multi-project, override-aware)

Per staff/date: `Assignments Override > Worked Projects cell > Assignments main
cell > Live default`. See
[docs/ACTIVE_ROSTER_LOG_MECHANICS.md](docs/ACTIVE_ROSTER_LOG_MECHANICS.md). This
fixes the prior hardcoded `Neuron Installation` assumption: a tech's project and
assignment now reflect what they actually worked each day.

Net hours = gross span − lunch (≥8h:1.0, ≥6h:0.5, else 0).

## Workbook tabs

| Tab | Content |
| --- | --- |
| `Executive Summary` | Total Net / Gross Span / Lunch / Techs / Projects / Neuron Net / Projects Team Net / Delivery-Transport Net |
| `Project Summary` | Project x (Tech Count, Worked Days, Gross Span, Lunch, Net) + **"Net Hours by Project"** bar chart |
| `Tech Summary` | Tech x (Project(s) list, Worked Days, Gross Span, Lunch, Net) |
| `Tech Project Summary` | Tech x Project rollup + **"Net Hours by Technician and Project"** bar chart |
| `Trucking Reference` | Delivery/Transport crew standard model |
| `Billing Bucket Snapshot` | Bucket x (Tech Count, Worked Rows, Billable Hours) |
| `Time Alignment` | Gross/Lunch/Net; submitted payroll feed informational |
| `Roster QA - Internal` | Parse warnings + malformed counts (hidden) |
| `Daily Detail - Internal` | Per-day resolved records (hidden) |
| `Build Notes` | Provenance (hidden) |
| `Next Chat Prompt` | Continuity note (hidden) |
| `Mon YY` (e.g. `May 26`) | Neuron-only Bonita Track Hours tracker, two-line header, built from the same resolved records |

Charts are native `openpyxl` `BarChart`s (editable in Excel for Web). The
tracker tab reuses the Bonita exporter format and resolver classification, so
the summary's Neuron Net and the tracker agree (one source of truth).

## CLI

```powershell
python -m triage.admin_billing_summary.cli `
  --roster-log "<roster>.xlsx" `
  --months 2026-04 2026-05 `
  --out-dir "Outputs\admin_billing_summary_2026_06_02" `
  --prior "<April preferred-format copy>.xlsx" `
  --websafe
```

Outputs per month (all under gitignored `Outputs/`):

```text
{Month}_{Year}_Admin_Billing_Summary_MyPreferredFormat.xlsx
{stem}_review_queue.csv      # long shifts, overrides applied, unassigned, malformed
{stem}_preflight.json        # Web Excel checks
{stem}_delta.json            # April only, when --prior given
admin_billing_summary_manifest.json
```

## Delta (refreshed month vs prior copy)

When `--prior` is given, the April run reads the prior copy's `Project Summary`
`Net Hours` column and emits per-project and total-net deltas. Differences are
expected (newer roster data) and are surfaced as deltas, not errors.

## Preflight

Reuses the focused Bonita preflight: valid zip, no `inlineStr` / `ns0:` /
`calcChain.xml` / external links.

## Tests

[tests/test_admin_billing_summary.py](tests/test_admin_billing_summary.py) — 13
fixture-only cases: override-beats-worked, worked-beats-default, net/lunch + long
shift, project / tech / tech-by-project rollups, executive metrics, tab set +
both charts, Neuron-only `Apr 26`/`May 26` trackers, preflight, and delta.

## Known gaps

- `Billing Bucket Snapshot` is a general bucket rollup over all resolved rows;
  the hand-made April snapshot was a narrower event-scoped subset.
- `Time Alignment` submitted Regular/OT hours come from an external payroll feed
  not present in the roster; reported as informational unless a feed is provided.
- Support tabs (`Build Notes`, `Next Chat Prompt`, `Trucking Reference`) reproduce
  structure and deterministic fields, not hand-written prose.
- `ASSIGNMENT TYPE` on the Neuron tracker remains operator-classified (default
  `Neuron Installation`; Delivery/Transport via activity signal).
