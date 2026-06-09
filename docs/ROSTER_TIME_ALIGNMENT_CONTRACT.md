# Roster Time Alignment Contract

## Purpose

When Paylocity shows real worked hours and the roster has standard placeholder hours, the fastest practical correction is to edit the roster time cells so the roster-derived payable hours match Paylocity.

This is the preferred field workflow when the user wants the roster itself to line up with payroll evidence before generating artifacts.

## Practical rule

Do not flag tiny deltas like `.02` or `.05` hours as meaningful problems.

Use a payroll delta tolerance of:

```text
0.10 hours
```

That is 6 minutes. Anything inside that band is rounding noise unless the operator explicitly wants exact-second reconciliation.

## Time math

The repo lunch rule still applies.

For OT days:

```text
roster gross span = Paylocity paid hours + 1.00 lunch hour
```

Then:

```text
roster payable hours = roster gross span - 1.00 lunch hour
```

## April 28 and April 29 example

Keep the existing 9:00 AM start time and change only the out-time.

| Date | Paylocity paid hours | Lunch | Required gross span | Suggested out-time from 9:00 AM | Notes |
| --- | ---: | ---: | ---: | --- | --- |
| 2026-04-28 | 13.98 | 1.00 | 14.98 | 11:58:48 PM | Use 11:59 PM if minute precision only |
| 2026-04-29 | 16.95 | 1.00 | 17.95 | 2:57:00 AM next day | Overnight out-time |

If the roster only accepts minute precision, these edits are close enough:

| Date | In | Out | Expected payable result |
| --- | --- | --- | ---: |
| 2026-04-28 | 9:00 AM | 11:59 PM | about 13.98 hours |
| 2026-04-29 | 9:00 AM | 2:57 AM | 16.95 hours |

## Pipeline expectation

The artifact pipeline should:

1. Parse roster punch cells.
2. Apply lunch rules.
3. Compare roster payable hours to Paylocity paid hours.
4. Treat daily deltas within `0.10` hours as rounding noise.
5. Flag only material differences beyond tolerance.
6. Preserve the daily detail in audit tabs, but do not let rounding noise pollute the executive dashboard.

## When not to edit time cells

Use a correction/override table only when:

- the visible punch span must remain 9:00 AM to 6:00 PM for operational readability;
- the correction is not a true punch-span correction;
- a date contains mixed projects that require project-scoped payable targets;
- editing the punch cell would misrepresent the operational record.

## Acceptance criteria

A corrected roster row passes when:

- roster payable hours and Paylocity paid hours differ by no more than `0.10` hours;
- the row remains tied to the correct project context;
- the daily audit shows the original comparison and the corrected comparison;
- executive dashboards do not present corrected/rounding-noise dates as offsets.
