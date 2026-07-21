# Harness Workflow Selection

Use the machine-readable registry at `configs/harness/workflows_v1.json`.

- P03: unknown intake.
- P06: cleanup.
- P07: implementation.
- P14: broken PRs.
- P15: merge or release.
- P20: selected opportunity rows.
- P12: closeout.
- P56: actual artifact generation, including the `bidirectional-web-spreadsheet-conversion` specialization.
- P57: harness installation.

For website/spreadsheet work, run `triage.harness_bidirectional_conversion_contract` first and produce `conversion_analysis.json`. Website-to-spreadsheet is implementation priority 1 because repository sidecar portals expose structured `PORTAL` JSON and workbook contracts are mature. Spreadsheet-to-website is priority 2 and must reuse the same semantic IR plus the registered sidecar renderer.

An input analysis, plan, rewritten prompt, acknowledgment, or handoff is not a converted artifact. Task-specific execution rules override generic closeout behavior.
