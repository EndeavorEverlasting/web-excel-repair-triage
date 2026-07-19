# Repository AI Harness

Prompts are artifacts inside this harness; they are not the harness itself.

## Fresh-agent entry sequence

1. Read `AGENTS.md`.
2. Read `configs/harness/harness_manifest_v1.json`.
3. Read `docs/harness/CODEBASE_MAP.md` and `configs/harness/code_intelligence_v1.json` without mutating anything.
4. Create or load a run context conforming to `configs/harness/run_context.schema.json`.
5. Select the workflow in `configs/harness/workflows_v1.json`; task-specific prompt rules override generic closeout.
6. Inspect existing rules, tests, validators, docs, scripts, manifests, output policy, and branch/PR conventions before inventing.
7. Run `python -m triage.harness_operational_discipline --repo-root . --json` and `python -m triage.harness_troubleshooting_contract --json`.
8. For failures or regressions, use the canonical P54 live-evidence contract: reconstruct current repository and runtime state, find the first confirmed divergence, and derive commands, paths, and validators from current repository contracts.
9. Mutate only the owned scope, generate actual requested artifacts, inspect them, run focused then broad validation, commit, push, and update the intended PR.
10. Generate an English report with `python -m triage.harness_operator_report --repo-root .`.
11. Compress the final handoff with `python -m triage.harness_handoff --context <run-context.json>`.

## Prompt Kit generation

Use `scripts/Generate-AIPromptKitV39.ps1`, which calls `triage.prompt_kit_v39_live_context_generator`. Generation fails when the P54 contract permits frozen repository-specific commands or paths, loses evidence precedence, or drops repair action commitment.

## Known traps

- Do not overwrite `Candidates/` or `Active/`; generated files belong under approved output paths.
- Do not treat package validity as Web Excel or operator acceptance.
- Do not commit private workbook binaries, secrets, huge logs, or disposable runtime evidence.
- Do not let remembered conversation context override newer repository, Git, CI, artifact, log, or validated runtime evidence.
- Prompt placeholders use bare `xyz_under_score_tokens`; surrounding ASCII or smart quotes are forbidden.
- Prompt Library B:O cells point to the associated exact prompt range. A/P are reserved for deterministic sparse navigation.
- Prompt tab colors and Prompt Library B:O row colors derive from the row's semantic Color label and must match as closely as Excel RGB tab colors permit.
