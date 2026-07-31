# NTH Evidence-Bounded Attribution Contract

## Purpose

Reconstruction must separate four different things:

1. historical labor totals;
2. testing/validation counts;
3. installation/deployment chronology;
4. confirmed configuration counts and device-specific configuration time.

The core failure this contract prevents is converting a downstream testing queue into upstream Configuration labor.

## Source-classification rule

A count may drive Configuration hours only when its source is explicitly Configuration-authoritative, such as:

- `configuration_list`;
- `dated_configuration_record`;
- `operator_confirmed_configuration_count`.

The following classifications are forbidden as Configuration multipliers:

- `device_testing`;
- `idt_testing`;
- `testing_remaining`;
- `install_date_only`.

Implementation:

```text
triage/nth_configuration_time_model.py
```

The May `38 remaining` figure is classified as **device testing / IDT remaining** and therefore cannot produce Configuration counts or hours.

## Device-specific timing model

### Neuron

- normalized allocation: **1.5 technician-hours / 90 minutes**;
- technician detailed process: **56-88 minutes**;
- optional separate rename: **+5-10 minutes**;
- detailed process including rename: **61-98 minutes**.

### Cybernet

- technician detailed process: **118-156 minutes**;
- approximately **1.97-2.60 technician-hours**.

### Confirmed paired workstation

When independent evidence confirms one Cybernet plus one Neuron were configured:

```text
Neuron normalized allocation = 1.50h
Cybernet process range       = 1.97h to 2.60h
------------------------------------------------
paired Configuration range   = 3.47h to 4.10h
```

This model must not be multiplied by testing counts.

## Install-date rule

Installation dates are chronology evidence.

They can support the bounded statement that Configuration production must have preceded or accompanied deployment/install activity.

They cannot by themselves prove:

- exact Configuration timestamp;
- exact same-day configuration count;
- direct Configuration labor hours.

For May, the All-Wave chronology includes a `2026-05-26` CCMC installation anchor inside the questioned window. That is enough to preserve Configuration as an active workstream, but not enough to recover an exact May 26-29 Configuration count.

## Historical May 26-29 tracker

The historical artifact remains:

| Lane | Hours |
| --- | ---: |
| Configuration label | 104.78 |
| Inventory Management | 20.65 |
| Deployment | 5.24 |
| Logistics | 4.33 |
| **Total** | **135.00** |

The `104.78h / 77.61%` Configuration label is historical state, not the next reconstruction target.

The former active defense:

```text
38 workstations × 2 devices × 2h = 152h Configuration capacity
```

is deprecated because `38` is a testing count.

## Packet M scenario translation

Until an exact configured-device count is recovered, use scenario math only.

Against the 135h historical tracker:

| Confirmed paired configurations | Direct Configuration range | Share of 135h |
| ---: | ---: | ---: |
| 1 | 3.47-4.10h | 2.6%-3.0% |
| 2 | 6.93-8.20h | 5.1%-6.1% |
| 4 | 13.87-16.40h | 10.3%-12.1% |
| 6 | 20.80-24.60h | 15.4%-18.2% |
| 8 | 27.73-32.80h | 20.5%-24.3% |
| 10 | 34.67-41.00h | 25.7%-30.4% |

These rows are scenario translations, not recovered counts.

## Labor bounding

Once a confirmed Configuration count exists:

1. translate it through `nth_configuration_time_model.py`;
2. reserve stronger dated non-Configuration evidence;
3. use the selected historical labor record as the outer labor ceiling;
4. keep Configuration and Deployment distinct;
5. never increase total labor because a device count exists.

The generic outer-ceiling helper remains:

```text
triage/nth_evidence_bounded_allocation.py
```

It is not a source classifier. Callers must pass only independently supported workload counts.

## Workbook audit requirement

The internal audit must retain:

- historical labor source and total;
- source classification for every device count;
- testing count separately from configuration count;
- install date / chronology source;
- Cybernet configuration count if supported;
- Neuron configuration count if supported;
- timing basis used;
- normalized vs detailed estimate designation;
- resulting Configuration range/allocation;
- explicit non-Configuration reservations;
- explanation of any chosen point value inside a range.

## Validation

```powershell
python -m pytest \
  tests/test_nth_configuration_time_model.py \
  tests/test_nth_evidence_bounded_allocation.py -q
```

The regression suite must prove that `device_testing=38` fails closed as a Configuration multiplier and that the current Neuron/Cybernet timing model remains stable.
