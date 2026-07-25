# Workflow Specifications

This file defines how agents enter, select, validate, recover, and hand off work. Focused domain behavior remains in versioned contracts and domain workflows.

## 1. Pick up a task

1. Read `AGENTS.md`, `CODEBASE_MAP.md`, `harness/manifest.v1.json`, and `harness/reports/CURRENT_STATE.md`.
2. Record `git status --short`, `git branch --show-current`, and `git log --oneline --decorate -5`.
3. Inspect open PRs, affected files, capabilities, triggers, validators, artifacts, and recent commits.
4. Declare repository, branch/worktree, lane, objective, owned scope, forbidden scope, dependencies, expected artifacts, validation order, and proof ceiling.
5. Preserve dirty or occupied worktrees; isolate rather than reset or clean.
6. Choose one primary workflow and capability owner.

## 2. Workflow selection

### A. Technician acquisition or update

Use `Acquire-Latest-PromptKit.cmd`. Clone when absent; otherwise verify canonical origin, clean `main`, no local-only divergence, fetch, and fast-forward only. Validate required files and exact website parity before opening.

### B. Prompt registry or website change

Change canonical sources, not generated HTML. Run prompt-language and relevant domain audits first. Prompt-card product behavior follows `harness/contracts/prompt-kit-interactions.v1.json`; harness-only work may not masquerade as product implementation.

### C. Harness infrastructure change

Repair existing canonical components before adding competing files. Update manifest, registries, indexes, skills, tests, hooks, reports, and CI atomically. Run focused domain tests, root harness validation, exact Prompt Kit parity, hygiene, and `git diff --check`.

### D. Workbook or artifact engine change

Keep `Candidates/` and `Active/` read-only, use sanitized fixtures, write to approved output locations, and separate static proof from Excel/operator acceptance.

### E. PR-floor cleanup and integration

Preserve unique useful work before closure. Integrate in dependency order without force. Verify exact head and owning validators after integration.

### F. Prompt-language audit or repair

Run `scripts/evaluate_prompt_language.py` across every raw and effective prompt. Require complete pairing and one disposition per prompt. Repair canonical registries or policy, regenerate deterministic output, and use strict mode only as the repair completion gate.

### G. Skill-evaluation build

Use P62 when skill correctness, routing, regression safety, performance, cost, or token use lacks proof. Add versioned cases, reproduce weaknesses, make the smallest valid repair, and measure efficiency without weakening correctness or safety.

### H. Prompt passage and efficiency evaluation

Use `harness/prompt-registry/WORKFLOW.md`.

1. Generate compact profiles with `audit_prompt_registry_harness.py`.
2. Run `evaluate_prompt_efficiency.py` code checks before judge tokens.
3. Emit ordered one-case judge packets.
4. For LLM-on-LLM evaluation, provide candidate-response JSONL.
5. Validate judge result schema, dimensions, scores, verdicts, coverage, and uniqueness.
6. Strict efficiency passes only with zero code warnings, complete judge coverage, and passing rubric floors.
7. Do not shorten prompts by deleting structure weak models require.

## 3. Validate before committing

Run focused tests and contracts before broad checks:

```powershell
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_prompt_registry_harness -v
python -m unittest tests.test_prompt_efficiency_eval -v
python scripts\audit_prompt_registry_harness.py --output Outputs\prompt-registry-harness-audit.json --summary
python scripts\evaluate_prompt_efficiency.py --output Outputs\prompt-efficiency-eval.json --emit-judge-packets Outputs\prompt-efficiency-judge-packets.json --summary
python -m unittest tests.test_prompt_kit_interactions_contract -v
python scripts\validate_prompt_kit_interactions.py --output Outputs\prompt-kit-interaction-audit.json --summary
python -m unittest tests.test_prompt_language_audit -v
python scripts\evaluate_prompt_language.py --output Outputs\prompt-language-audit.json --summary
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
python -m triage.gitignore_hygiene
git diff --check
```

Never claim skipped checks passed.

## 4. Handle failures

- Repair the first actionable contract or test failure; do not weaken expectations just to turn green.
- Coverage mismatch blocks interpretation of prompt findings.
- Missing or malformed judge evidence blocks strict LLM-eval claims.
- Prompt-efficiency warnings remain product repair debt; do not lower thresholds without evidence.
- A shorter prompt that loses weak-model structure is a regression.
- Preserve dirty work and exact external failures; never embed secrets.
- Keep static, judge, human, user, browser, live, and production proof separate.

## 5. Commit and PR contract

Run `git diff --check`, inspect status/stat/diff, add only owned files, commit coherently, push normally, and open or update a focused PR with dependency and proof state.

## 6. Handoff contract

State repository, branch/worktree, sprint, lane, owned/forbidden scope, trigger/capability, target kind, files, artifacts, validation, commit SHA, push/PR state, code and judge findings, skipped checks, proof ceiling, final Git status, and one exact executable next command.
