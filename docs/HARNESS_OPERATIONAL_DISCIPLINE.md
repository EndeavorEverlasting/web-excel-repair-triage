# Portable Operational Harness Discipline

## Authority

`configs/harness/operational_discipline_v1.json` is the portable machine-readable policy. `triage.harness_operational_discipline` validates the policy and concrete run contexts. `triage.harness_troubleshooting_contract` validates the canonical P54 live-evidence prompt and its generator contract.

## Required run context

Always name repository, branch or worktree, PR or sprint, lane, owned scope, forbidden scope, expected artifacts, and validation order when the user supplied one.

## Executable loop

`request -> evidence review -> bounded decision -> repo/Git/GitHub mutation -> artifacts -> validation -> report -> next decision`

Evidence precedes confidence. Completion requires the strongest applicable check, artifact, commit, branch, push, PR, merge, release, deployment, or runtime proof.

## Evidence-grounded troubleshooting

P54 is the canonical troubleshooting surface. It reconstructs the latest trustworthy state from validated local runtime evidence, current repository contents, tests and validators, CI and generated artifacts, Git and PR history, operational doctrine, then conversation context. Material claims are labeled `CONFIRMED`, `STALE OR UNVERIFIED`, `HYPOTHESIS`, `MISSING EVIDENCE`, or `BLOCKED`.

Troubleshooting identifies the first confirmed divergence, ranks hypotheses, and selects the smallest discriminating check before repair. Repository-specific filenames, commands, paths, and validators are derived from current repository contracts at execution time; they are not frozen into the workbook prompt. When repair is requested, mutation and proof are required. Diagnosis-only work stops before mutation.

The canonical source is `configs/prompt_kit/v39_p54_troubleshooting_prompt.json`. The supported V39 launcher calls `triage.prompt_kit_v39_live_context_generator`, which merges P54 into the standard-AI prompt source and fails closed on contract drift.

## Connected GitHub fallback

When the execution container cannot network-clone the repository, use the connected GitHub branch as the mutation surface. Reconstruct only relevant generator, validator, and test files locally. Record the reduced local proof ceiling, but still require commit, branch, push or PR mutation evidence.

## Artifact contract

Generate the actual artifact, inspect it, run artifact-family validators, record its path and hash when practical, and state field gates. In Prompt Library workbooks, B:O of every prompt row targets the associated prompt tab and exact copy range; A/P remain sparse navigation. Sparse cadence is the largest evenly dividing member of 10, 5, and 2.

## Sequential routing

- P03: unknown repository intake and first action
- P06: repository and PR cleanup
- P07: general implementation
- P14: broken PR
- P15: merge or release
- P20: selected Opportunity_Discovery row
- P12: closeout

Task-specific prompt rules override generic closeout. Rewritten prompts, plan-only responses, handoff-only responses, and acknowledgment-only completion cannot substitute for requested repository work.

## Complete repo-local harness

`HARNESS.md` and `configs/harness/harness_manifest_v1.json` are the discovery spine. The harness includes repo agent rules, a codebase map, workflow specifications, a run-context schema, an artifact registry, fail-closed validators, an opt-in repo-local pre-commit hook, scoped skills, read-only code-intelligence queries, English operator reports, and final-handoff compression. `python -m triage.harness_operational_discipline --repo-root . --json` fails when a registered surface is missing.

## Prompt placeholder and color doctrine

Prompt placeholders are bare underscore-delimited `xyz_...` tokens. ASCII and smart quotes immediately surrounding a placeholder are forbidden because they disrupt double-click replacement. Prompt Library B:O row fills derive from the semantic Color label. Every associated prompt tab uses the same RGB fill where Excel supports RGB tab colors. The machine-readable authority is `configs/harness/prompt_library_visual_policy_v1.json`; `triage.prompt_kit_visual_contract` and generated-workbook validation fail drift.
