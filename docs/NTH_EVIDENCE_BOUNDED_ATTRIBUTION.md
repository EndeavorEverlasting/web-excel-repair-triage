# NTH Evidence-Bounded Attribution Contract

## Purpose

Neuron Track Hours reconstruction sometimes has a known labor total but incomplete intra-day task labels. Stronger operational evidence can bound task attribution, but only when the source actually has authority for the quantity being multiplied.

This contract prevents three errors:

1. creating labor by multiplying target/testing counts by a duration;
2. treating testing / IDT remaining scope as Configuration population;
3. preserving a historical Configuration ratio merely because an older tracker labeled it that way.

## Fail-closed Configuration-count rule

Configuration timing may only be multiplied by an independently supported **Configuration count**.

The following are **not** Configuration counts unless a separate source explicitly resolves them as such:

- device-testing / IDT remaining counts;
- target counts;
- installation counts or installation dates;
- generic remaining-work counts;
- deployment status percentages.

The reusable calculator requires callers to declare:

```python
scope_kind="configuration_count"
```

Any other scope kind fails closed.

## Selected historical labor remains the labor ceiling

A valid Configuration count can establish a task-capacity envelope. It never creates attendance.

```text
configuration workload envelope
  = confirmed configuration population
  × direct configuration timing

labor remaining for Configuration
  = selected historical labor total
  - explicitly supported non-Configuration hours

maximum defensible Configuration allocation
  = min(configuration workload envelope,
        labor remaining for Configuration)
```

The maximum is a **ceiling, not a target**. Stronger dated evidence can require a lower allocation.

## May 26–29 correction

The historical tracker/model associated with the approximately 105 Configuration-hour question remains preserved as audit state:

- tracker total: **135.00h**;
- Configuration label: **104.78h**;
- Inventory Management: **20.65h**;
- Deployments: **5.24h**;
- Logistics: **4.33h**.

The visible All-Wave / Risk Summary total of **38 remaining** is now classified as **device-testing / IDT remaining scope**.

Therefore both prior calculations are deprecated:

```text
38 × 2h = 76h
```

and

```text
38 workstations × 2 devices × 2h = 152h
```

The 38 must not be passed to the bounded Configuration helper.

## Installation chronology

The Risk Summary separately preserves installation chronology across May, including:

- LIJ Forest Hills — 05/06;
- Glen Cove — 05/11–05/12 installation / IDT activity;
- LIJ Valley Stream — 05/13;
- LIJ — 05/22;
- NSUH / Schwartz — 05/22;
- CCMC — **05/26**.

The 05/26 anchor reaches the questioned May 26–29 window and supports the statement that configuration production continued ahead of installation.

Boundary: an installation date is chronology evidence, not an exact Configuration timestamp, configured-device count, or labor-hours source.

## Device-specific Configuration timing

### Neuron

Current normalized allocation:

```text
1.50 technician-hours / 90 minutes per confirmed Neuron configuration
```

Technician detailed process estimate:

```text
56–88 minutes
```

When a separate rename step applies:

```text
+5–10 minutes
61–98 minutes total detailed range
```

The normalized 1.50h value is an allocation standard inside the technician process range, not an SLA.

### Cybernet

Technician detailed process estimate:

```text
118–156 minutes
= approximately 1.97–2.60 technician-hours per confirmed Cybernet configuration
```

Do not collapse this to a new single normalized Cybernet value without a separately approved rule.

### Confirmed Cybernet + Neuron pair

For one independently confirmed paired configuration:

```text
1.50h Neuron
+ 1.97–2.60h Cybernet
= 3.47–4.10h direct Configuration
```

Against a 135h historical labor surface, each confirmed pair represents approximately **2.6%–3.0%** of that total.

Scenario examples for audit only:

| Confirmed paired configurations | Direct Configuration range | Share of 135h |
| ---: | ---: | ---: |
| 1 | 3.47–4.10h | 2.6%–3.0% |
| 2 | 6.93–8.20h | 5.1%–6.1% |
| 4 | 13.87–16.40h | 10.3%–12.1% |
| 6 | 20.80–24.60h | 15.4%–18.2% |
| 8 | 27.73–32.80h | 20.5%–24.3% |
| 10 | 34.67–41.00h | 25.7%–30.4% |

Do not select a scenario row without a supported count.

## Multiple historical records must not collapse

The May 26–29 evidence family contains distinct historical hour surfaces:

- **135.00h historical tracker/model** — record paired with the approximately 105h Configuration question;
- **125.00h / 13 shifts later NTH reconstruction** — separate retrospective record;
- **147.00 net project hours June 4 billing-thread record** — another separate historical scope.

The helper accepts a selected labor total as an input. The caller is responsible for choosing the correct authority for the requested artifact and recording provenance.

## Current implementation

Reusable module:

```text
triage/nth_evidence_bounded_allocation.py
```

### Bounded confirmed-population helper

```python
EvidenceBoundedAllocation(
    workstations=...,
    devices_per_workstation=...,
    direct_hours_per_device=...,
    attendance_hours=...,
    scope_kind="configuration_count",
    explicit_non_configuration_hours=...,
)
```

The field remains named `attendance_hours` for API compatibility; the audit must state which historical labor source supplied it.

### Device-specific timing helper

```python
ConfirmedConfigurationTiming(
    neuron_count=...,
    cybernet_count=...,
)
```

Outputs include:

- normalized Neuron hours;
- Cybernet minimum / maximum hours;
- total direct Configuration minimum / maximum;
- paired-workstation count;
- audit record with timing inputs.

## Packet M workbook audit requirement

The internal audit surface must preserve:

- selected historical labor source and total;
- competing historical records and why they were not selected;
- the fact that `38 remaining` is testing/IDT scope;
- installation chronology as chronology only;
- confirmed configured-device counts, if recovered;
- source authority for those counts;
- Neuron 1.50h normalized allocation;
- Neuron 56–88 min detailed range and optional 5–10 min rename;
- Cybernet 118–156 min range;
- direct Configuration range from confirmed counts;
- actual chosen Configuration allocation;
- explanation when a scenario is shown because the count remains open.

The management-facing sheet should show the resulting clean allocation without internal mechanics unless specifically requested.

## Validation

```powershell
python -m pytest tests/test_nth_evidence_bounded_allocation.py -q
```

Regression requirements:

- testing/IDT counts fail closed as Configuration multipliers;
- installation counts fail closed as Configuration multipliers;
- one confirmed Cybernet+Neuron pair yields approximately 3.47–4.10h;
- two confirmed pairs yield approximately 6.93–8.20h;
- the former 38/76/152 regression is absent from active tests.
