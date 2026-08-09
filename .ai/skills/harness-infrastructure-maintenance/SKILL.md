# Skill: Maintain the Operational Harness

## Trigger

Use this skill when repository maps, workflow specifications, artifact or validator registries, hooks, scoped skills, completeness checks, operator reports, focused Prompt Kit contracts, or operator-command delivery are missing, stale, disconnected, or failing. Route through trigger `harness-infrastructure-change` and capability `harness-infrastructure-maintenance`.

Also use this skill when a Prompt Kit usability defect must first be converted into an enforceable harness contract without crossing into product implementation. Examples include a non-chronological default prompt order, sparse long-list navigation, filter-state regressions, or mobile accessibility requirements that are currently only described informally.

A failed NEXT COMMAND is a harness trigger when it assumes the wrong local path, runs Git after a failed directory gate, embeds Markdown hyperlink syntax inside a pasteable command, closes the terminal with top-level `exit`, fails to pin unmerged remote work, or asks the operator to guess the canonical artifact.

Do not use this skill for governance-contract changes in `AGENTS.md`, product implementation, secret handling, destructive cleanup, or production deployment.

## Required inputs

- `AGENTS.md` and the closest nested instructions;
- current Git branch, worktree, recent commits, open PRs, and required checks when local Git state is available;
- explicit notice when the execution environment cannot clone or inspect the operator's local checkout;
- `CODEBASE_MAP.md`, `WORKFLOW.md`, `ARTIFACT_REGISTRY.md`, `SKILLS.md`, `CAPABILITIES.md`, and `TRIGGERS.md`;
- `harness/manifest.v1.json`, workflow/artifact/validator/capability/trigger registries, domain contracts, and reports;
- `harness/contracts/prompt-kit-order-navigation.v1.json` and `harness/reports/PROMPT_KIT_ORDER_NAVIGATION.md` when ordering, long-list navigation, or filter-persistent navigation is implicated;
- `harness/contracts/operator-command-envelope.v1.json`, its fixtures, and the tracked remote-proof PowerShell template when the failure is operator-command delivery;
- `scripts/validate_harness.py`, focused harness validators, contract tests, hooks, and harness CI;
- the exact missing component, drift, failure output, stale claim, failed operator transcript, or product-gap evidence being registered.

## Outputs

- bounded tracked repairs to canonical harness component files;
- synchronized human and machine-readable ownership;
- a passing `harness-completeness-report/v1` runtime report;
- focused regression tests for the repaired harness defect or newly registered acceptance contract;
- an operator-readable report that distinguishes harness state from product implementation state;
- a validated copy-safe operator command template when handoff delivery is implicated;
- commit SHA, push or PR evidence, proof ceiling, and one actionable next command.

## Procedure

1. Declare repository, isolated branch or worktree, sprint, lane, mission, owned and forbidden scope, expected artifacts, validation order, proof ceiling, and mutation authority.
2. Record `git status --short`, `git branch --show-current`, and `git log --oneline --decorate -5` when the repository is locally available. When it is not, use the connected GitHub branch as the mutation surface and state that local Git status is unavailable instead of inventing a path.
3. Read the governance contract and canonical harness spine before changing files.
4. Inspect `harness/manifest.v1.json` and the workflow, artifact, validator, capability, trigger, and focused domain-contract registries. Reuse existing IDs, schemas, paths, commands, and report patterns.
5. Repair the canonical harness owner rather than adding a competing map, registry, validator, hook, report, or command-delivery surface.
6. When the user reports a product behavior gap but the lane forbids product code, encode the desired behavior as a focused contract with an observable baseline, a non-destructive harness gate, a strict product gate, mutation fixtures, and an operator report. Do not claim the behavior is fixed merely because the harness now detects it.
7. For Prompt Kit chronological ordering or long-list navigation, require `navigation_interval = 5`, default/filtered numeric sequence order, Top and Bottom controls throughout the visible result stream, filter-persistent regeneration, mobile touch targets, and stable prompt identity. Run `scripts/validate_prompt_kit_order_navigation.py` plus its contract tests. Reserve `--require-implementation` for the product lane that is authorized to change Prompt Kit behavior sources.
8. Update human indexes, machine registries, validator logic, tests, hooks/CI path filters, and operator state together when ownership or commands change.
9. If the defect is a NEXT COMMAND or operator proof command, run `scripts/validate_operator_command_envelope.py` and its fixtures. Never emit a remembered `C:\Users\<name>\...` path as repository evidence. Never place Markdown hyperlink syntax inside PowerShell command data. Never use top-level `exit` in an interactive pasteable command. If the exact local root is not proven in the current shell, use `harness/templates/Invoke-RemoteHarnessProof.ps1`, which works from an environment-derived isolated checkout.
10. Make pre-commit validation inspect the staged index, not unrelated unstaged work. Keep pre-push validation exhaustive and non-destructive.
11. Run focused compilation, the owning focused domain validator/tests, `scripts/validate_harness.py --report Outputs/harness-completeness-report.json`, harness contract tests, connected validators, broader affected tests, and `git diff --check`.
12. Commit coherent owned files with the required sprint message when one was specified, push normally, and update the existing focused PR rather than creating a duplicate owner.
13. Hand off with exact files, artifacts, commands/results, commit, push/PR state, blockers, skipped checks, proof achieved, final Git state, and a next command that advances the next unproven owner without assuming the operator's local path.

## Guardrails

- Never edit `AGENTS.md` in a harness-infrastructure lane.
- Never mutate product implementation merely to satisfy a harness contract.
- Never write generated output into `Candidates/` or `Active/`.
- Never weaken validators, fixtures, schemas, strict product gates, or proof language to make a check pass.
- Never convert a known product implementation gap into a harness success claim; report `needs-product-repair` and name the owning product lane.
- Never reset, clean, force-push, delete unique work, embed credentials, or disclose private workbook data.
- Keep one writer per branch or worktree and preserve unrelated work.
- A remembered machine path is not a verified repository root. Use current-shell evidence or the environment-derived isolated proof template.
- A raw URL may be transformed by chat rendering; do not depend on a raw auto-linkable URL token surviving inside copy/paste PowerShell when a repository slug or split string is available.
- Top-level `exit` is forbidden in pasteable interactive PowerShell because it can close the terminal and destroy visible evidence. Use terminating errors inside a script/scriptblock instead.
- Treat skills as procedures, registries as ownership, validators as proof, templates as transport, and reports as evidence; do not collapse them into one prose file.

## Validation

Focused Prompt Kit order/navigation harness gate:

```bash
python -m py_compile scripts/validate_prompt_kit_order_navigation.py tests/test_prompt_kit_order_navigation_contract.py
python scripts/validate_prompt_kit_order_navigation.py --output Outputs/prompt-kit-order-navigation-audit.json --summary
python -m unittest tests.test_prompt_kit_order_navigation_contract -v
```

Strict product acceptance gate, only in an authorized product lane:

```bash
python scripts/validate_prompt_kit_order_navigation.py --require-implementation --output Outputs/prompt-kit-order-navigation-audit.json --summary
```

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
python scripts/evaluate_prompt_language.py --output Outputs/prompt-language-audit.json --summary
python -m unittest tests.test_skill_prompt_registry -v
python tests/test_prompt_kit_header_contract.py
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
python -m triage.gitignore_hygiene
git diff --check
```

Do not claim skipped checks passed. Record the exact command, failure, dependency, and remaining owner.

## Proof ceiling

A green focused harness contract, harness validator, focused tests, hooks, and CI prove only the tracked repository surfaces, source evidence, command shapes, fixtures, and commands exercised on the tested commit. A non-strict Prompt Kit order/navigation pass may intentionally report `needs-product-repair`; it proves the gap is registered and reproducible, not that the website behavior is fixed. Browser scrolling ergonomics, mobile touch behavior, focus behavior, native Windows execution, product runtime behavior, Excel for Web acceptance, provider obedience, credentials, network reachability, protected target access, technician acceptance, deployment, and production success require separate proof.
