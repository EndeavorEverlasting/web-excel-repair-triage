# Packet M — May Configuration Recalibration

Status: **current math surface pending exact configured-device count**

Evidence contract owner: `EndeavorEverlasting/FUN` — device-testing / configuration-time correction.

## Historical questioned-week artifact

```text
May 26-29 historical tracker total = 135.00h
Historical Configuration label      = 104.78h / 77.61%
Inventory Management                = 20.65h
Deployment                          = 5.24h
Logistics                           = 4.33h
```

The historical Configuration label is preserved for audit but is not the Packet M target.

## Superseded calculation

Do not use:

```text
38 remaining -> 38 workstations -> 76 devices -> 152h Configuration
```

Reason: the `38 remaining` value is device-testing / IDT scope.

## Current timing inputs

| Device | Current timing basis |
| --- | ---: |
| Neuron normalized | 1.50h |
| Neuron detailed | 56-88 min |
| Neuron detailed + rename | 61-98 min |
| Cybernet detailed | 118-156 min / 1.97-2.60h |
| Confirmed paired Cybernet+Neuron | 3.47-4.10h |

## Install chronology

The All-Wave install/IDT surface shows recurring installation activity through May, including a `05/26` CCMC installation anchor in the questioned window.

This supports Configuration continuity but not an exact configuration count.

## Scenario table against the 135h historical tracker

| Confirmed paired configs | Configuration low | Configuration high | Share low | Share high |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 3.47h | 4.10h | 2.6% | 3.0% |
| 2 | 6.93h | 8.20h | 5.1% | 6.1% |
| 3 | 10.40h | 12.30h | 7.7% | 9.1% |
| 4 | 13.87h | 16.40h | 10.3% | 12.1% |
| 5 | 17.33h | 20.50h | 12.8% | 15.2% |
| 6 | 20.80h | 24.60h | 15.4% | 18.2% |
| 8 | 27.73h | 32.80h | 20.5% | 24.3% |
| 10 | 34.67h | 41.00h | 25.7% | 30.4% |

No row is the recovered answer until the corresponding configured-device count is proven.

## Packet M conclusion

The evidence now supports a narrower statement than the old tracker:

- direct Configuration remained recurring through May;
- installation chronology reaches May 26;
- device-specific timing makes each confirmed paired configuration materially time-consuming;
- but the `38` testing count cannot support a high Configuration allocation;
- therefore the next management ratio should be **materially lower than 77.61%** unless a larger confirmed configuration count is recovered.

## Generator rule

When the exact count is available:

```python
configuration_hours_range(
    cybernet_configurations=<confirmed>,
    neuron_configurations=<confirmed>,
    source_classification="configuration_list",
)
```

Then reserve explicitly supported non-Configuration lanes and apply the selected historical labor ceiling.
