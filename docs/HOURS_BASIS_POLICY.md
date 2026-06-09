# Hours Basis Policy

This is the canonical rule for roster-derived artifact generators.

## Policy

| Artifact family | Purpose | Hours basis |
|---|---|---|
| Billing Summary | Admin/client billing math | Net hours |
| Delta Dashboard | Compare roster/admin owed hours to Paylocity-derived paid hours | Net hours |
| Neuron Track Hours | Track tech activity and operational coverage | Gross hours |

## Lunch deduction policy

Roster-derived net hours use the standard lunch deduction:

| Gross shift span | Deduction | Net calculation |
|---:|---:|---|
| `>= 8.0` hours | `1.0` hour | `gross - 1.0` |
| `>= 6.0` and `< 8.0` hours | `0.5` hour | `gross - 0.5` |
| `< 6.0` hours | `0.0` hours | `gross` |

## Generator contract

1. Billing artifacts must use **net hours** for billable totals.
2. Delta dashboards must compare roster/admin **net hours** against Paylocity-derived paid hours.
3. Operational tracking artifacts, including Neuron Track Hours, must preserve **gross hours** unless explicitly emitting a separate billing-support net column.
4. Do not silently normalize Neuron Track Hours into net billing hours. Its job is to show which techs worked on Neuron activity and when.
5. If an artifact displays both bases, the columns must be labeled explicitly as `Gross Hours`, `Lunch Deducted`, and `Net Hours`.

Implementation anchor: `triage/hours_basis_policy.py`.

## Stop-ship examples

| Bad behavior | Why it fails |
|---|---|
| Billing Summary totals use `Gross Hours` | Inflates billable/client totals. |
| Delta Dashboard compares raw roster span to paid work hours | Creates a false shortage when lunch should be deducted. |
| Neuron Track Hours removes gross span and only shows net | Destroys operational tracking value. |
| A workbook says `Hours` without basis | Ambiguous and not submission-ready. |
