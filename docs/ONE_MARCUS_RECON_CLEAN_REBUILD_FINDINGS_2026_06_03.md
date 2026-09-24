# One Marcus Recon Clean Rebuild Findings - 2026-06-03

## Summary

A prior inventory recon workbook render failed in Excel for Web severely enough that the browser would not attempt repair. Treat that as a failed artifact, not a near miss.

The successful direction is a clean rebuild from source data rather than mutation of the damaged workbook package.

## Applied Web Excel rules

- Repaired or Web-refused artifacts are failed artifacts.
- Package-level preflight is mandatory before claiming Web Excel safety.
- Avoid native pivot-cache dependency for this inventory lane.
- Avoid stale calculation chains, external workbook links, duplicate table names, unsupported namespace tokens, R1C1 conditional-format leakage, and cached error literals.
- Keep worksheet names stable. Put dates in filenames, visible titles, manifests, and reports.

## Stable worksheet contract

```text
Part Numbers
1M Recon Pivot Module
```

## Clean rebuild posture

The clean rebuild uses:

- Technician edit zone: `Part Numbers!A:R`
- Helper and guardrail zone: `Part Numbers!S:AG`
- Supported row window: row 2 through row 500
- Executive rollup key list: `1M Recon Pivot Module!A13:A190`
- Formula-driven leadership view instead of native pivot-cache refresh
- Conditional formatting for duplicate keys, missing rollup keys, and quantity review

## Current clean render counts

```text
Included inventory lines: 74
Distinct normalized part keys: 65
Total represented quantity: 1515
Duplicate part-key lines flagged: 16
Duplicate normalized keys: 7
Missing executive rollup lines at render: 0
Future source capacity through row 500: 422
Web Excel package preflight: PASS
```

## Package preflight passed

The generated workbook passed these local package gates:

```text
ZIP opens cleanly
All XML parts parse
No stale content-type overrides
No broken relationships
No calcChain.xml
No xl/externalLinks parts
No duplicate table names
No unsupported formula namespace tokens
No cached formula error literals
No inlineStr
No ns0 namespace leakage
No R1C1 conditional-format leakage
```

## Repo implementation target

Implement this as a deterministic clean-render lane, not a fragile workbook patch lane:

1. Parse the private source workbook.
2. Extract `Part Numbers` or the latest dated Part Numbers candidate.
3. Normalize part keys.
4. Preserve technician source columns A:R.
5. Generate helper formulas S:AG through a bounded row window.
6. Generate the executive rollup from normalized keys.
7. Emit duplicate-key review queue.
8. Emit manifest and package preflight report.
9. Reject outputs if Excel for Web repairs or refuses repair.
