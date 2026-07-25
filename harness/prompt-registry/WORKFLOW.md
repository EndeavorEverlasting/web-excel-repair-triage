# Prompt Registry Harness Workflow

## 1. Pick up a passage task

1. Read `AGENTS.md`, the domain manifest, canary contract, execution-profile schema, capability registry, trigger registry, and operator report.
2. Record repository and Git state without discarding existing work.
3. Declare whether the lane is:
   - **audit-only** — inventory, profiling, routing, and canary-gap reporting;
   - **harness repair** — domain contracts, skills, validator, tests, hook, CI, and reports;
   - **prompt product repair** — canonical prompt sources and generated output, which is outside this harness sprint.
4. Select `prompt-registry-passage` as the primary capability for a full registry pass.
5. Use the profile-assigned execution capability only when moving from audit into an authorized prompt run.

## 2. Run a full passage

```powershell
python scripts\audit_prompt_registry_harness.py `
  --output Outputs\prompt-registry-harness-audit.json `
  --summary
```

The report must contain one profile per effective prompt, no embedded full prompt text, deterministic capability/skill ownership, the ordered passage list, and visible canary coverage.

For one prompt:

```powershell
python scripts\audit_prompt_registry_harness.py --prompt P07 --summary
```

## 3. Canary gate

Non-strict mode records missing canaries without failing the harness. After a separately authorized prompt-registry product sprint inserts the contract into canonical/effective prompts, run:

```powershell
python scripts\audit_prompt_registry_harness.py `
  --strict-canary `
  --output Outputs\prompt-registry-canary-strict.json `
  --summary
```

The strict gate passes only when every effective prompt contains the canary instruction marker and both `OBJECTIVE:` and `REPOS:` labels.

## 4. Validate before committing

1. Compile auditor and tests.
2. Run domain tests.
3. Generate the non-strict audit report.
4. Run the root harness validator/contracts.
5. Run exact Prompt Kit builder parity to prove the harness did not mutate product output.
6. Run artifact hygiene and `git diff --check`.
7. Run broader suites last.

## 5. Handle failures

- **Coverage mismatch:** stop and repair registry loading/profile generation before interpreting findings.
- **Unknown capability/skill:** repair domain registries atomically; do not ask the model to guess.
- **Full prompt leaked into a profile:** fail closed and remove the field.
- **Canary missing in non-strict mode:** report downstream product debt.
- **Canary missing in strict mode:** fail with the prompt IDs; do not weaken the contract.
- **Provider/model stops emitting the canary:** leave the chat and preserve the last trustworthy state; static harness proof is not a substitute.
- **Dirty or conflicting worktree:** isolate the lane; no reset, clean, or force.

## 6. Handoff

Report repository, branch, domain capability, prompt count/profile count, canary coverage, capability distribution, artifact path, validation results, commit SHA, PR state, proof ceiling, product gaps, and one exact executable next command.
