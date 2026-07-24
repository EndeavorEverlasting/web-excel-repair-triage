# Workflow Specifications

This file defines how agents and operators enter, select, validate, recover, and hand off work in this repository. Product-specific behavior remains in focused modules, schemas, tests, and contract documents.

## 1. Pick up a task

1. Read `AGENTS.md` and any nearest nested instruction file.
2. Read `CODEBASE_MAP.md`, `harness/manifest.v1.json`, and `harness/reports/CURRENT_STATE.md`.
3. Record the Git floor:

   ```bash
   git status --short
   git branch --show-current
   git log --oneline --decorate -5
   ```

4. Inspect open PRs, affected files, registered capabilities/triggers, validators, and recent commits.
5. Declare repository, branch/worktree, lane, mission, owned scope, forbidden scope, dependencies, expected artifacts, validation order, proof ceiling, and mutation authority.
6. Preserve dirty or occupied worktrees; use an isolated branch/worktree instead of reset or cleanup.
7. Choose one primary workflow and capability owner.

## 2. Workflow selection

### A. Technician acquisition or update

**Trigger:** A technician needs the latest `main` Prompt Kit through a mouse-accessible Windows surface.

**Entry point:** `Acquire-Latest-PromptKit.cmd`

**Flow:** clone when absent; otherwise verify canonical origin, clean `main`, no local-only commits or divergence; fetch and fast-forward only; validate required files and exact website parity; open the selected surface after success.

**Failure routing:** preserve state and report the exact tool, authentication, network, origin, cleanliness, branch, divergence, file, or parity failure.

### B. Prompt registry or website change

**Trigger:** Canonical prompts, extensions, policies, reference data, builder behavior, generator options, or checked-in HTML change.

1. Change canonical source, never only generated HTML.
2. Run the prompt-language audit in audit mode before mutation.
3. Add or repair focused fixtures and tests.
4. Regenerate the combined Prompt Kit deterministically.
5. Run strict audit for the owned repaired scope and exact website parity.
6. Run harness and broad repository checks.

### C. Harness infrastructure change

**Trigger:** Maps, workflow specs, artifact/capability/trigger registries, validators, hooks, skills, evals, reports, or acquisition surfaces change.

1. Repair existing canonical components before adding competing files.
2. Update `harness/manifest.v1.json` atomically with path or command changes.
3. Update human indexes when machine-readable ownership changes.
4. Add or repair contract tests and fixtures.
5. Run `scripts/validate_harness.py`, focused tests, and `git diff --check`.
6. Run affected Prompt Kit checks and the broader artifact suite last.

### D. Workbook or artifact engine change

**Trigger:** A `triage/` engine, workbook contract, schema, fixture, or generated artifact behavior changes.

Keep `Candidates/` and `Active/` read-only, use sanitized fixtures, write runtime outputs only to approved locations, run focused engine tests and hygiene, and treat Excel for Web/operator acceptance as separate runtime proof.

### E. PR-floor cleanup and integration

**Trigger:** Work is stacked, divergent, superseded, or blocked across branches/PRs.

Inspect commit/file deltas, preserve unique useful work before closure, integrate in dependency order, resolve findings/checks, and never force-push or delete unique work without separate authority.

### F. Prompt-language audit or repair

**Triggers:** `prompt-language-change` or `lazy-next-action-report`.

**Capability:** `prompt-language-audit`

**Audit flow:**

1. Run `scripts/evaluate_prompt_language.py` across every raw and effective prompt.
2. Require equal canonical, effective, and disposition counts.
3. Fail on duplicate IDs, coverage gaps, empty required language, missing effective policy, or other error findings.
4. Record warning findings as canonical-source repair debt with stable rule IDs.
5. Write the report to `Outputs/prompt-language-audit.json` or CI artifact storage.

**Repair flow:**

1. Reproduce each owned finding with a fixture.
2. Repair canonical registries, policy, builder, or focused tests—not generated HTML alone.
3. Run strict audit.
4. Regenerate `web/prompt-kit/index.html` and prove exact parity.
5. Commit source, tests, and deterministic output together.

### G. Skill-evaluation build

**Trigger:** `skill-quality-unproven`.

**Capability:** `skill-evaluation`; Prompt Kit owner: P62.

1. Define the eval contract and baseline before changing behavior.
2. Add positive, negative, near-miss, boundary, malformed-input, forbidden-condition, unit, integration, and historical-regression cases.
3. Reproduce weaknesses before repair when practical.
4. Use TDD and profile-guided feedback for the smallest valid repair.
5. Measure latency, calls, context, retries, cost, and tokens when available.
6. Accept efficiency changes only with correctness/safety/routing gates green.
7. Emit machine-readable results and a finding-to-repair ledger.

## 3. Validate before committing

Use the strongest practical checks in this order:

1. Focused unit/fixture tests.
2. Contract validators and static compilation.
3. Exhaustive prompt-language audit when prompt or skill surfaces are involved.
4. Exact generated-output checks.
5. Repository hygiene.
6. Broader tests and honest runtime checks.

Baseline harness sequence:

```powershell
python -m py_compile scripts\validate_harness.py scripts\evaluate_prompt_language.py tests\test_harness_contract.py tests\test_prompt_language_audit.py
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_prompt_language_audit -v
python scripts\evaluate_prompt_language.py --output Outputs\prompt-language-audit.json --summary
python -m unittest tests.test_skill_prompt_registry -v
python tests\test_prompt_kit_header_contract.py
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
python -m triage.gitignore_hygiene
git diff --check
```

Never claim skipped checks passed. Name the exact command and reason.

## 4. Handle failures

### Focused test, validator, or eval failure

Read and reproduce the first actionable failure. Repair implementation or contract drift; do not weaken expectations merely to turn CI green. Add a regression fixture and rerun the focused gate before broad checks.

### Dirty worktree or branch collision

Do not reset, clean, or discard files. Identify the owner, isolate the lane, and preserve coherent work with a commit or explicit handoff.

### Generated-output drift

Regenerate from canonical source, commit source and deterministic output together, and keep CI read-only after any bounded repair transaction.

### Prompt-language coverage failure

Stop if any canonical prompt lacks an effective partner, any effective prompt lacks a canonical source, IDs duplicate, or disposition count differs. Repair registry/builder ownership before interpreting language findings.

### Network, authentication, provider, or runtime failure

Preserve local state, report exact command/error, never embed secrets, and do not substitute static proof for the blocked external surface.

## 5. Commit and PR contract

```bash
git diff --check
git status --short
git diff --stat
git diff
git add <owned tracked files>
git commit -m "<useful message>"
git push -u origin <branch>
```

Open or update a focused PR, state stack dependencies, and resolve review findings and required checks before merge.

## 6. Handoff contract

A handoff must state repository, branch/worktree, sprint, lane, owned/forbidden scope, trigger/capability used, files changed, artifacts, validation commands/results, commit SHA, push/PR state, blockers, skipped checks, proof achieved/ceiling, final Git status, and one exact actionable next command. Interrupted work must include the last coherent commit and uncommitted file list.
