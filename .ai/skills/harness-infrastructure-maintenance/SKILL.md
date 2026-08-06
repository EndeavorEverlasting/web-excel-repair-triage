# Skill: Maintain the Operational Harness

## Trigger

Use this skill when repository maps, workflow specifications, artifact or validator registries, hooks, scoped skills, completeness checks, operator reports, or operator command envelopes are missing, stale, disconnected, or failing. Route through trigger `harness-infrastructure-change` and capability `harness-infrastructure-maintenance`.

Do not use this skill for governance-contract changes in `AGENTS.md`, product implementation, secret handling, destructive cleanup, or production deployment.

## Required inputs

- `AGENTS.md` and the closest nested instructions;
- current Git branch, worktree, recent commits, open PRs, and required checks;
- `CODEBASE_MAP.md`, `WORKFLOW.md`, `ARTIFACT_REGISTRY.md`, `SKILLS.md`, `CAPABILITIES.md`, and `TRIGGERS.md`;
- `harness/manifest.v1.json`, workflow/artifact/validator/capability/trigger registries, domain contracts, and reports;
- `scripts/validate_harness.py`, `scripts/Invoke-HarnessProfile.ps1`, `tests/test_harness_contract.py`, `tests/test_powershell_command_envelope.py`, hooks, and harness CI;
- the exact missing component, drift, failure output, stale claim, closed-terminal incident, or missing-log defect being repaired.

## Outputs

- bounded tracked repairs to canonical harness component files;
- synchronized human and machine-readable ownership;
- a passing `harness-completeness-report/v1` runtime report;
- focused regression tests for the repaired defect;
- durable operator evidence under the command envelope run root when PowerShell executes;
- updated human-readable operator state;
- commit SHA, push or PR evidence, proof ceiling, and one actionable next command.

## Procedure

1. Declare repository, isolated branch or worktree, sprint, lane, mission, owned and forbidden scope, expected artifacts, validation order, proof ceiling, and mutation authority.
2. Record `git status --short`, `git branch --show-current`, and `git log --oneline --decorate -5`. Preserve dirty or separately owned work through an isolated branch/worktree.
3. Read the governance contract and canonical harness spine before changing files.
4. Inspect `harness/manifest.v1.json` and the workflow, artifact, validator, capability, and trigger registries. Reuse existing IDs, schemas, paths, commands, and report patterns.
5. Repair the canonical owner rather than adding a competing map, registry, validator, hook, or report.
6. Update human indexes, machine registries, validator logic, tests, hooks, CI path filters, and operator state atomically when ownership or commands change.
7. Make pre-commit validation inspect the staged index, not unrelated unstaged work. Keep pre-push exhaustive and non-destructive.
8. Keep repository hooks local and opt-in. Install them through `python scripts/install_local_hooks.py`; never change global Git hook configuration.
9. Run the staged path-only artifact gate before staged-tree validation. Reject live/generated evidence and machine-local junk without opening or printing file contents; allow normal code/docs and sanitized fixtures.
10. For operator-facing PowerShell, use `scripts/Invoke-HarnessProfile.ps1`. Never place a standalone `exit`, `[Environment]::Exit()`, `Stop-Process`, or process-kill call in a pasteable runner. Execute validators as child processes, persist `summary.json`, `run.log`, and per-step stdout/stderr before propagating failure, and return control to the caller by throwing only after evidence finalization.
11. Do not install dependencies, close terminals, or mutate the workstation inside a validation command. Classify a missing dependency from durable logs and leave the operator at the original prompt.
12. Run focused compilation, `scripts/validate_harness.py --report Outputs/harness-completeness-report.json`, harness and PowerShell command-envelope contract tests, connected validators, broader affected tests, and `git diff --check`.
13. Commit coherent owned files with a useful message, push normally, and open or update a focused PR.
14. Hand off with exact files, artifacts, commands/results, durable evidence paths, commit, push/PR state, blockers, skipped checks, proof achieved, final Git state, and a next command that retrieves and exercises the unmerged work safely.

## Guardrails

- Never edit `AGENTS.md` in a harness-infrastructure lane.
- Never mutate product implementation merely to satisfy a harness contract.
- Never write generated output into `Candidates/` or `Active/`.
- Never weaken validators, fixtures, schemas, or proof language to make a check pass.
- Never reset, clean, force-push, delete unique work, embed credentials, or disclose private workbook data.
- Never call standalone `exit`, `[Environment]::Exit()`, `Stop-Process`, or process killing from an operator-facing PowerShell runner.
- Never rely on terminal scrollback as the only evidence. Persist a run summary and separate stdout/stderr for every child command before propagating failure.
- Never surprise-install Node.js, Python, Git, package managers, or another dependency from a validation runner.
- Keep hooks repository-local and opt-in; do not write `--global` Git configuration.
- Hook diagnostics may print paths and policy reasons but never staged file contents or sensitive excerpts.
- Hooks must not start launchers, GUIs, browsers, workbook runtimes, deployments, or network activity.
- Keep one writer per branch or worktree and preserve unrelated work.
- Treat skills as procedures, registries as ownership, validators as proof, and reports as evidence; do not collapse them into one prose file.

## Validation

```bash
python -m py_compile scripts/validate_harness.py scripts/validate_staged_artifacts.py scripts/install_local_hooks.py tests/test_harness_contract.py tests/test_local_hook_artifact_hygiene.py tests/test_powershell_command_envelope.py
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
python -m unittest tests.test_harness_contract tests.test_powershell_command_envelope -v
python -m unittest tests.test_prompt_kit_interactions_contract -v
python scripts/validate_prompt_kit_interactions.py --output Outputs/prompt-kit-interaction-audit.json --summary
python scripts/validate_prompt_kit_discovery.py --summary
python -m unittest tests.test_prompt_kit_discovery -v
python -m unittest tests.test_prompt_language_audit -v
python scripts/evaluate_prompt_language.py --output Outputs/prompt-language-audit.json --summary
python -m unittest tests.test_skill_prompt_registry -v
python tests/test_prompt_kit_header_contract.py
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
python scripts/validate_artifact_hygiene.py
git diff --check
```

Native Windows command-envelope proof:

```powershell
& .\scripts\Invoke-HarnessProfile.ps1 -Profile harness -ExpectedHead '<exact-commit-sha>'
```

Do not claim skipped checks passed. Record the exact command, failure, dependency, durable summary/log paths, and remaining owner.

## Proof ceiling

A green harness validator, focused tests, hooks, and CI prove only the tracked repository surfaces and commands exercised on the tested commit. A native PowerShell run additionally proves that the exercised command envelope retained logs and returned control on that workstation. These checks do not prove product runtime behavior, Excel for Web acceptance, native Windows GUI behavior outside the runner, browser event ordering, clipboard access, provider obedience, credentials, network reachability, protected target access, technician acceptance, deployment, or production success.
