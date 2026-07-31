# Packet M — May Configuration Recalibration

Status: **current math surface; exact May 26-29 configured-device count remains open**

Canonical implementation base: `main` after PR #125.

## Historical questioned-week artifact

```text
May 26-29 historical tracker total = 135.00h
Historical Configuration label      = 104.78h / 77.61%
Inventory Management                = 20.65h
Deployment                          = 5.24h
Logistics                           = 4.33h
```

The historical Configuration label is preserved for audit. It is **not** the Packet M target.

## Source correction

The All-Wave `38 remaining` figure is device-testing / IDT scope.

Do not use either superseded calculation:

```text
38 × 2h = 76h
38 workstations × 2 devices × 2h = 152h
```

The canonical NTH implementation now requires explicit Configuration-count authority. Testing/IDT and installation-only counts fail closed as Configuration multipliers.

## Current timing model

| Device | Current direct Configuration basis |
| --- | ---: |
| Neuron normalized | **1.50h / 90 min** |
| Neuron detailed | **56-88 min** |
| Neuron detailed + separate rename | **61-98 min** |
| Cybernet detailed | **118-156 min / 1.97-2.60h** |
| Confirmed Cybernet+Neuron pair | **3.47-4.10h** |

Implementation lives in `triage/nth_evidence_bounded_allocation.py` via `ConfirmedConfigurationTiming` and fail-closed `scope_kind="configuration_count"` controls.

## Installation chronology

The All-Wave installation / IDT surface preserves recurring May installation activity, including a **05/26 CCMC installation anchor** inside the questioned May 26-29 window.

This supports the bounded conclusion that Configuration production continued ahead of installation.

It does **not** establish:

- the exact Configuration timestamp;
- the exact configured-device count for May 26-29;
- direct Configuration labor by itself.

## Scenario translation against the historical 135h tracker

Until the exact configured-device count is recovered, use scenario math only:

| Confirmed paired configurations | Direct Configuration range | Share of 135h |
| ---: | ---: | ---: |
| 1 | 3.47-4.10h | 2.6%-3.0% |
| 2 | 6.93-8.20h | 5.1%-6.1% |
| 3 | 10.40-12.30h | 7.7%-9.1% |
| 4 | 13.87-16.40h | 10.3%-12.1% |
| 5 | 17.33-20.50h | 12.8%-15.2% |
| 6 | 20.80-24.60h | 15.4%-18.2% |
| 8 | 27.73-32.80h | 20.5%-24.3% |
| 10 | 34.67-41.00h | 25.7%-30.4% |

No scenario row is a recovered answer until the corresponding configuration count is independently supported.

## Packet M conclusion

The evidence supports a narrower and more durable statement:

> Direct Configuration remained a recurring workstream through May, and installation chronology reaches May 26 inside the questioned period. Device-specific technician timing confirms that each completed configuration carries meaningful direct effort. But the `38` testing count cannot support a large Configuration allocation, so the next management ratio should be materially lower than the historical 77.61% label unless a larger confirmed configuration count is recovered.

## Generator / workbook audit rule

For future NTH generation:

1. select the historical labor authority for the artifact;
2. preserve testing/IDT count separately;
3. preserve install chronology separately;
4. require `scope_kind="configuration_count"` for any count multiplied into Configuration labor;
5. translate confirmed device counts through the device-specific timing model;
6. reserve explicit non-Configuration work;
7. enforce the outer historical labor ceiling;
8. expose source classification and timing basis in the internal audit;
9. keep scenario math labeled as scenario math when the exact count is open.
