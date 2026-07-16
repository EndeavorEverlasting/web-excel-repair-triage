# Neuron Billing Evidence Pack

## Purpose

Generate the granular billing artifact that accompanies a populated Neuron roster log when an administrator needs date-by-date evidence for technician hours.

The evidence pack adds the two strongest audit surfaces from the historical March workbook:

- **Daily Narrative Log** — readable manager-facing context, one row per technician shift.
- **Event Log** — atomic, case-linked evidence, one row per technician shift.

It also includes the monthly Neuron Track Hours tab, Visual Summary, and Executive Dashboard. A separate **Task Summary** tab is intentionally omitted because the Visual Summary already contains the task allocation rollup.

## Source hierarchy

The generator follows this precedence and fails rather than silently changing it:

1. **Populated roster log** — authoritative for technician, date, start/end time, included Neuron scope, and billed hours.
2. **Optional local allocation workbook** — authoritative for `TASK / ASSIGNMENT TYPE` only after an exact one-to-one `Date + Tech + Hours` reconciliation.
3. **Repo or local monthly allocation policy** — distributes only remaining heuristic task labels. It never overwrites a high-confidence local allocation row.
4. **Deterministic narrative templates** — explain the selected workstream without inventing operational facts.

The historical March workbook is a structural and narrative-pattern reference only. Its sites, devices, incidents, quantities, case IDs, and ticket details are never copied into a later month.

## July 2026 policy

The sanitized repo policy at `configs/neuron_billing_evidence_pack/monthly_allocation_policies.json` codifies the accepted July order for roster-only runs:

1. Configurations — weight 16;
2. Inventory Management — weight 9;
3. Survey — weight 7;
4. Ticket Forwarding — weight 3.

For 36 equal eight-hour shifts, this produces 17/9/7/3 when there is no explicit deployment evidence, or 16/9/7/3 plus one preserved explicit deployment shift. Deployment is never created by the ratio allocator and the July policy fails when more than one explicit deployment shift is present.

A private local policy may add `deployment.eligible_techs` to restrict that explicit deployment row to an approved technician without committing employee names to the public repository.

## Evidence boundary

The generated workbook must not invent:

- hospital/site or room;
- device counts or serials;
- ticket, REQ, RITM, or incident IDs;
- hostnames;
- deployment claims not present in explicit roster evidence or the reconciled allocation source;
- travel duration, complexity, disruption, or modeled hours.

When the roster does not contain a field, the workbook says **Not recorded in roster** or leaves the modeled field blank.

Raw punch notes are not copied into the admin-facing workbook. They remain available to the existing internal review queue.

## Command

Roster-only generation using the repo July policy:

```powershell
python -m triage.nw_prj_neuron_track_hours.evidence_pack_cli `
  --roster-log ".\Candidates\Active Roster Log.xlsx" `
  --months 2026-07 `
  --out-dir ".\Outputs\neuron_billing_evidence_pack\2026-07"
```

Use a reviewed Neuron Track Hours workbook as the higher-priority assignment authority:

```powershell
python -m triage.nw_prj_neuron_track_hours.evidence_pack_cli `
  --roster-log ".\Candidates\Active Roster Log.xlsx" `
  --allocation-source ".\Candidates\Neuron Track Hours - July 2026.xlsx" `
  --months 2026-07 `
  --out-dir ".\Outputs\neuron_billing_evidence_pack\2026-07"
```

Use a private local monthly policy when deployment eligibility or another operator-specific constraint must stay outside Git:

```powershell
python -m triage.nw_prj_neuron_track_hours.evidence_pack_cli `
  --roster-log ".\Candidates\Active Roster Log.xlsx" `
  --allocation-policy ".\Candidates\neuron-july-policy.local.json" `
  --months 2026-07 `
  --out-dir ".\Outputs\neuron_billing_evidence_pack\2026-07"
```

`--allocation-source` is strict by default. Every roster-derived shift must reconcile exactly. Use `--allow-unmatched-allocation` only for an explicit review run; unmatched shifts retain policy/classifier labels and are recorded in manifest warnings. `--no-monthly-policy` disables the month policy for diagnostic comparison.

## Output workbook

Ordered tabs:

1. one full-month tab per requested month, such as `July 2026`;
2. `Visual Summary`;
3. `Executive Dashboard`;
4. `Daily Narrative Log`;
5. `Event Log`.

The monthly tab uses these fields:

```text
DATE
DAY
TECH NAME
START TIME
END TIME
TOTAL HOURS
PROJECT NAME
TASK / ASSIGNMENT TYPE
SUPPORTING WORK / NOTES
```

The Daily Narrative Log preserves the March field grammar:

```text
Date
Day
Person
Site
Primary Workstream
Method / Detail
Record State
```

The Event Log preserves the March atomic-event field grammar. `Actual Billed Hours` is populated from the roster; modeled and suggested-hour fields remain blank.

## Validation gates

The CLI writes a workbook, manifest JSON, and preflight JSON. The preflight fails unless all of the following are true:

- XLSX ZIP package is valid;
- no `inlineStr`, `ns0`, calc chain, or external-link hazard is present;
- shared-string counts reconcile;
- workbook tab order matches the evidence-pack contract;
- `Task Summary` is absent;
- monthly shift rows equal roster-derived shifts;
- monthly hours equal roster-derived hours;
- Daily Narrative Log rows equal roster-derived shifts;
- Event Log rows and Actual Billed Hours equal roster-derived shifts and hours.

The CLI also rebuilds both Visual Summary chart references after workbook generation so the technician chart reads the technician table and the assignment chart reads the task-mix table.

The proof ceiling is **fixture/package-level** until the generated workbook is manually opened and accepted in Excel for Web.

## Privacy and repository hygiene

- Real roster logs, allocation workbooks, local policy files, and generated billing workbooks stay local under gitignored operator folders.
- Do not commit employee attendance, private notes, customer workbook bytes, or runtime evidence.
- `Candidates/` and `Active/` remain read-only inputs.
- Generated artifacts belong under `Outputs/`.
