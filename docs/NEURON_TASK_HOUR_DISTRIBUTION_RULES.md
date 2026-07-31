# Neuron Task Hour Distribution Rules

## Purpose

The Active Roster Log proves who worked and when. Exact task attribution must come from task evidence, declared fallback rules, or a bounded configuration-count model.

## Task lanes

Supported lanes:

- Configurations
- Deployments
- Logistics
- Inventory Management
- Documentation
- Client Coordination
- Ticket Forwarding
- Troubleshooting / Incident Response
- Warehouse Maintenance
- Survey

## General support distribution

For genuinely thin-context Neuron support days only:

| Task lane | Share |
| --- | ---: |
| Configurations | 55% |
| Deployments | 5% |
| Logistics | 20% |
| Inventory Management | 10% |
| Documentation | 5% |
| Client Coordination | 5% |

This fallback must yield to stronger dated/configuration evidence.

## May evidence precedence

For May, use this order:

1. exact historical labor record for the artifact being reconstructed;
2. explicit dated non-Configuration evidence;
3. confirmed configuration counts translated through `triage/nth_configuration_time_model.py`;
4. install/deployment chronology as continuity evidence only;
5. generic task percentages only when the above are insufficient.

## Source classifications

Configuration-authoritative count sources:

- `configuration_list`
- `dated_configuration_record`
- `operator_confirmed_configuration_count`

Forbidden as Configuration multipliers:

- `device_testing`
- `idt_testing`
- `testing_remaining`
- `install_date_only`

A source may still support chronology/status while being forbidden as a Configuration count.

## May 38 correction

The All-Wave `38 remaining` figure is **device-testing / IDT scope**.

Do not:

- treat it as 38 workstations to configure;
- double it into 76 configured devices;
- apply a generic 2h/device rule;
- use it to defend 152h or 104.78h of Configuration.

The previous `38 workstations × 2 devices × 2h = 152h` example is superseded and must appear only in deprecated/audit history.

## Device-specific Configuration timing

### Neuron

- normalized allocation: **1.5h / device**;
- detailed process: **56-88 min**;
- optional separate rename: **+5-10 min**;
- detailed range including rename: **61-98 min**.

### Cybernet

- detailed process: **118-156 min** = approximately **1.97-2.60h**.

### Paired workstation

For a **confirmed** Cybernet+Neuron configuration pair:

```text
1.50h + 1.97-2.60h = 3.47-4.10h direct Configuration
```

## Install dates

Install dates may establish that production continued into a period. They do not create configuration counts or exact task timestamps.

For May, a CCMC `05/26` installation anchor supports continuing production inside the questioned window, but the exact Configuration count remains unresolved unless stronger device-level evidence is recovered.

## Historical May 26-29 artifact

The old tracker remains:

```text
135.00h total
104.78h Configuration label
20.65h Inventory
5.24h Deployment
4.33h Logistics
```

This is historical state, not the new ratio target.

Packet M must lower the Configuration share from the old 77.61% unless supported configuration counts justify otherwise.

Scenario translations for paired configurations against 135h:

| Confirmed pairs | Direct Configuration | Share |
| ---: | ---: | ---: |
| 1 | 3.47-4.10h | 2.6%-3.0% |
| 2 | 6.93-8.20h | 5.1%-6.1% |
| 4 | 13.87-16.40h | 10.3%-12.1% |
| 6 | 20.80-24.60h | 15.4%-18.2% |
| 8 | 27.73-32.80h | 20.5%-24.3% |
| 10 | 34.67-41.00h | 25.7%-30.4% |

Do not select a scenario row without a confirmed count.

## Implementation contract

Primary timing/source-classification helper:

```text
triage/nth_configuration_time_model.py
```

Outer labor/workload ceiling helper:

```text
triage/nth_evidence_bounded_allocation.py
```

Shared fallback distribution implementation:

```text
triage/neuron_task_hour_distribution_rules.py
```

Generators should:

1. resolve the historical labor source;
2. classify each evidence source;
3. reserve explicit non-Configuration work;
4. reject testing/install-only counts as Configuration multipliers;
5. translate confirmed Cybernet/Neuron configuration counts using the device-specific timing model;
6. enforce the outer labor ceiling;
7. use generic percentages only for unresolved thin-context residuals;
8. preserve source classification and timing basis in the internal audit;
9. keep management-facing sheets clean.

## Non-negotiables

- Do not convert testing counts into Configuration.
- Do not equate install date with configuration timestamp.
- Do not use the old generic 2h/device basis for Neurons.
- Do not fabricate a single Cybernet normalized value from the 118-156 minute range without a separate approved rule.
- Do not preserve the historical 77.61% Configuration share merely because it already exists.
- Do keep Configuration and Deployment separate.
- Do keep conflicting historical labor records distinct.
