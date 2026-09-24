# Artifact Generation Ledger — NW PRJ Dashboard

Durable memory of generated workbooks and lessons. Append one row per generation run.

## Ledger format

| Date | Version | Descriptor | Inputs | Output | Gate result | Lessons |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-05-XX | v6.5 | ROSTER_CONFIRMED_REDUCED_NOISE | dashboard, roster, admin scratch | `..._WEBSAFE.xlsx` | pass | Reduced active queue; Column A override fixed yellow-done |
| 2026-05-XX | v6.6 | FULL_ARTIFACT_COMPARISON | + optional official admin | `..._WEBSAFE.xlsx` | pass | Three-way compare; archive demotion |

## Template row (copy for next run)

```text
Date:
Generator commit:
Descriptor:
Dashboard input:
Roster input:
Admin scratch input:
Official admin (optional):
Output path:
web_excel_safe:
Failures:
Lessons:
```

## Automation hook

`nw_prj_dashboard_generator.py` appends a JSON line to `Outputs/nw_prj_generation_ledger.jsonl` when `--ledger` is passed (gitignored under `Outputs/**` except curated JSON).

## Reference artifacts (local only, not in repo)

- v6.5: `NW_PRJ_Tech_Roster_Dashboard_v6_5_ROSTER_CONFIRMED_REDUCED_NOISE_WEBSAFE.xlsx`
- v6.6: `NW_PRJ_Tech_Roster_Dashboard_v6_6_FULL_ARTIFACT_COMPARISON_WEBSAFE.xlsx`

Store golden copies outside git; reference paths in ledger rows above.
