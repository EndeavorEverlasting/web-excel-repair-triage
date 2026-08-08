# Skill: Maintain the Operational Harness

## Trigger

Use this skill when repository maps, workflow specifications, artifact or validator registries, hooks, scoped skills, completeness checks, operator reports, operator-command delivery, or integration behavior are missing, stale, disconnected, or failing. Route through trigger `harness-infrastructure-change` and capability `harness-infrastructure-maintenance`.

A failed NEXT COMMAND is a harness trigger when it assumes the wrong local path, runs Git after a failed directory gate, embeds Markdown hyperlink syntax inside a pasteable command, closes the terminal with top-level `exit`, fails to pin unmerged remote work, asks the operator to guess the canonical artifact, or leaves an exact validated green PR unmerged without naming a required blocker.

Do not use this skill for governance-contract changes in `AGENTS.md`, product implementation, secret handling, destructive cleanup, or production deployment.

## Required inputs

- `AGENTS.md` and the closest nested instructions;
- current Git branch, worktree, recent commits, open PRs, required checks, review state, dependencies, and mergeability when local or connected Git state is available;
- explicit notice when the execution environment cannot clone or inspect the operator's local checkout;
- `CODEBASE_MAP.md`, `WORKFLOW.md`, `ARTIFACT_REGISTRY.md`, `SKILLS.md`, `CAPABILITIES.md`, and `TRIGGERS.md`;
- `harness/manifest.v1.json`, workflow/artifact/validator/capability/trigger registries, domain contracts, and reports;
- `registry/prompts/actionable-next-step-policy.v1.json` when harness work affects Prompt Kit completion behavior;
- `harness/contracts/operator-command-envelope.v1.json`, its fixtures, and the tracked remote-proof PowerShell template when the failure is operator-command delivery;
- `scripts/validate_harness.py`, `tests/test_harness_contract.py`, hooks, and harness CI;
- the exact missing component, drift, failure output, stale claim, failed operator transcript, or stranded green branch being repaired.

## Outputs

- tracked repairs to canonical harness component files within declared owned scope;
- synchronized human and machine-readable ownership;
- a passing `harness-completeness-report/v1` runtime report;
- focused regression tests for the repaired defect;
- a validated copy-safe operator command template when handoff delivery is implicated;
- updated human-readable operator state;
- commit SHA and push evidence;
- merge SHA when the exact validated PR head is green and authorized, or the exact required merge blocker;
- one actionable next command only when safe unproven work actually remains.

## Procedure

1. Declare repository, isolated branch or worktree, sprint, lane, mission, owned and forbidden scope, expected artifacts, validation order, proof ceiling, mutation authority, and merge authority.
2. Record `git status --short`, `git branch --show-current`, and `git log --oneline --decorate -5` when the repository is locally available. When it is not, use the connected GitHub branch as the mutation surface and state that local Git status is unavailable instead of inventing a path.
3. Read the governance contract and canonical harness spine before changing files.
4. Inspect `harness/manifest.v1.json` and the workflow, artifact, validator, capability, trigger, and focused domain-contract registries. Reuse existing IDs, schemas, paths, commands, and report patterns.
5. Repair the canonical owner rather than adding a competing map, registry, validator, hook, report, or command-delivery surface.
6. Update human indexes, machine registries, validator logic, tests, hooks, CI path filters, and operator state atomically when ownership or commands change.
7. If the defect is a NEXT COMMAND or operator proof command, run `scripts/validate_operator_command_envelope.py` and its fixtures. Never emit a remembered `C:\Users\<name>\...` path as repository evidence. Never place Markdown hyperlink syntax inside PowerShell command data. Never use top-level `exit` in an interactive pasteable command. If the exact local root is not proven in the current shell, use `harness/templates/Invoke-RemoteHarnessProof.ps1`, which works from an environment-derived isolated checkout.
8. Make pre-commit validation inspect the staged index, not unrelated unstaged work. Keep pre-push validation exhaustive and non-destructive.
9. Run focused compilation, the operator-command validator when applicable, `scripts/validate_harness.py --report Outputs/harness-completeness-report.json`, harness contract tests, connected validators, broader affected tests, and `git diff --check`.
10. Commit coherent owned files with the required sprint message when one was specified, push normally, and update the existing focused PR rather than creating a duplicate owner.
11. Inspect the exact current PR head after validation. If the validated head is still current, required checks and owning validators are green, declared dependencies and blocking reviews are satisfied, no merge conflict or protection gate remains, and merge authority exists, merge it in the same run using a repository-accepted merge method. Bounded owned scope limits mutation; it is not a reason to strand green owned work on a branch.
12. For stacked green PRs, merge in dependency order, refresh downstream evidence after the base changes, and continue integrating while the required gates stay green.
13. If merge cannot proceed, report the exact required check, validator, dependency, review, conflict, protection rule, approval, authorization, or moved-head blocker. Do not substitute a generic handoff for an available merge.
14. After merge, verify the target branch contains the intended change, report the merge SHA and final PR state, preserve or close superseded work safely, and only then identify the next unproven executable action.

## Guardrails

- Never edit `AGENTS.md` in a harness-infrastructure lane.
- Never mutate product implementation merely to satisfy a harness contract.
- Never write generated output into `Candidates/` or `Active/`.
- Never weaken validators, fixtures, schemas, required checks, or proof language to make a check pass.
- Never reset, clean, force-push, delete unique work, embed credentials, or disclose private workbook data.
- Never merge a head that moved after validation or carries unresolved required checks, owning validators, dependencies, blocking reviews, conflicts, protection rules, approvals, unrelated work, or forbidden-scope changes.
- Keep one writer per branch or worktree and preserve unrelated work.
- A remembered machine path is not a verified repository root. Use current-shell evidence or the environment-derived isolated proof template.
- A raw URL may be transformed by chat rendering; do not depend on a raw auto-linkable URL token surviving inside copy/paste PowerShell when a repository slug or split string is available.
- Top-level `exit` is forbidden in pasteable interactive PowerShell because it can close the terminal and destroy visible failure evidence. Use terminating errors inside a script/scriptblock instead.
- Treat skills as procedures, registries as ownership, validators as proof, templates as transport, and reports as evidence; do not collapse them into one prose file.

## Validation

Focused operator-command gate:

```bash
python -m py_compile scripts/validate_operator_command_envelope.py tests/test_operator_command_envelope.py
python scripts/validate_operator_command_envelope.py --summary
python -m unittest tests.test_operator_command_envelope -v
```

Root harness profile:

```bash
python -m py_compile scripts/validate_harness.py tests/test_harness_contract.py
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_prompt_kit_interactions_contract -v
python scripts/validate_prompt_kit_interactions.py --output Outputs/prompt-kit-interaction-audit.json --summary
python scripts/validate_prompt_kit_discovery.py --summary
python -m unittest tests.test_prompt_kit_discovery -v
python -m unittest tests.test_prompt_language_audit -v
python -m unittest tests.test_green_branch_integration_policy -v
python scripts/evaluate_prompt_language.py --output Outputs/prompt-language-audit.json --summary
python -m unittest tests.test_skill_prompt_registry -v
python tests/test_prompt_kit_header_contract.py
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
python -m triage.gitignore_hygiene
git diff --check
```

Do not claim skipped checks passed. Record the exact command, failure, dependency, and remaining owner.

## Proof ceiling

A green operator-command envelope, harness validator, focused tests, hooks, and CI prove only the tracked repository surfaces and commands exercised on the tested commit. Provider-reported merge state can additionally prove that a specific PR was integrated into its target branch. These checks do not prove the operator's local repository path, native Windows execution, product runtime behavior, Excel for Web acceptance, browser event ordering, clipboard access, provider obedience, credentials, network reachability, protected target access, technician acceptance, deployment, or production success.