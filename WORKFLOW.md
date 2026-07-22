# Workflow Specifications

This file defines how agents and operators enter, validate, recover, and hand off work in this repository. Product-specific workflows remain documented in `README.md` and focused contract documents; this file owns repository operating flow.

## 1. Pick up a task

1. Read `AGENTS.md` and the nearest nested instruction file, if any.
2. Read `CODEBASE_MAP.md`, `harness/manifest.v1.json`, and `harness/reports/CURRENT_STATE.md`.
3. Record the compact Git floor:

   ```bash
   git status --short
   git branch --show-current
   git log --oneline --decorate -5
   ```

4. Inspect open PRs, current workflows, affected validators, and recent commits.
5. Declare repository, branch/worktree, lane, mission, owned scope, forbidden scope, expected artifacts, validation order, proof ceiling, and push/PR authority.
6. Preserve a dirty or occupied worktree. Use an isolated branch or worktree instead of resetting unknown work.
7. Choose the smallest workflow below that fully owns the requested result.

## 2. Workflow selection

### A. Technician acquisition or update

**Trigger:** A technician needs the latest website and generators without typing Git commands.

**Entry point:** Double-click `Acquire-Latest-PromptKit.cmd`.

**Flow:**

1. Present destination and post-validation action choices in the Windows GUI.
2. Clone canonical `main` when the destination is absent.
3. For an existing checkout, verify canonical origin, clean status, and current branch `main`.
4. Fetch `origin/main` and reject local-only commits or divergence.
5. Fast-forward with `git merge --ff-only` only.
6. Validate required website, generator, manifest, and builder files.
7. Run exact combined-registry website validation.
8. Open the selected website or generator GUI only after success.

**Failure routing:** Preserve the repository unchanged and report the exact missing tool, authentication/network error, wrong origin, dirty state, wrong branch, divergence, missing file, or stale generated site.

### B. Prompt registry or website change

**Trigger:** Prompts, prompt extensions, reference data, website behavior, generator options, or checked-in HTML change.

**Flow:**

1. Change canonical source data or code, not only generated HTML.
2. Update focused contracts.
3. Build the combined registry site.
4. Verify the checked-in site is exact output.
5. Run Prompt Kit and harness checks before the broad artifact suite.

**Commands:**

```powershell
python -m unittest tests.test_skill_prompt_registry -v
python tests\test_prompt_kit_header_contract.py
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
```

### C. Harness infrastructure change

**Trigger:** Maps, workflow specs, registries, validators, hooks, skills, operator reports, or acquisition surfaces change.

**Flow:**

1. Repair existing canonical harness components before adding competing files.
2. Update `harness/manifest.v1.json` atomically with path or command changes.
3. Add or repair contract tests.
4. Run harness validation and `git diff --check`.
5. Run affected Prompt Kit checks.
6. Run broader artifact tests last.

**Commands:**

```powershell
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
git diff --check
```

### D. Workbook or artifact engine change

**Trigger:** A `triage/` engine, workbook contract, schema, fixture, or generated artifact behavior changes.

**Flow:**

1. Identify the exact engine and focused contract from `README.md`, `docs/`, configs, and tests.
2. Keep `Candidates/` and `Active/` read-only.
3. Use sanitized fixtures for tests; do not commit private workbooks.
4. Generate outputs under `Outputs/` or the path defined by the focused contract.
5. Run focused engine tests and artifact hygiene.
6. Treat real Excel for Web or operator acceptance as a separate runtime proof gate.

### E. PR-floor cleanup and integration

**Trigger:** Work is split across stacked, divergent, superseded, or blocked PRs.

**Flow:**

1. Inspect commit and file deltas.
2. Preserve unique useful work before closing a source PR.
3. Prefer cherry-pick, bounded repair, restore, or clean integration branches.
4. Resolve review findings and required checks.
5. Merge green predecessors in dependency order.
6. Comment where preserved work landed before closing superseded PRs.
7. Do not delete branches or force-push unless separately authorized.

## 3. Validate before committing

Use the strongest practical checks in this order:

1. Focused tests for changed behavior.
2. Contract validators and static compilation.
3. Exact generated-output checks.
4. Repository hygiene.
5. Broader tests and runtime checks when practical.

Baseline harness sequence:

```powershell
python -m py_compile scripts\validate_harness.py tests\test_harness_contract.py
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_skill_prompt_registry -v
python tests\test_prompt_kit_header_contract.py
python -m triage.gitignore_hygiene
git diff --check
```

Never claim skipped checks passed. Name the exact skipped command and reason.

## 4. Handle failures

### Focused test or validator failure

- Read the first actionable failure and reproduce it directly.
- Repair implementation or contract drift; do not weaken expectations merely to turn CI green.
- Add a regression fixture when the failure exposed an untested boundary.
- Re-run the focused gate before broad checks.

### Dirty worktree or branch collision

- Do not reset, clean, or discard files.
- Identify the owner and use an isolated branch/worktree.
- Preserve coherent local changes with a commit or explicit handoff when authorized.

### Generated-output drift

- Regenerate from canonical source using the registered builder.
- Commit source and deterministic generated output together when the repository tracks both.
- Keep workflows read-only after any one-time repair transaction.

### Network, authentication, or provider failure

- Preserve local state.
- Report the exact command and error.
- Do not embed or solicit secrets in tracked files.
- Do not substitute a static pass for live external proof.

### Divergent technician checkout

- Stop before mutation.
- Report local-ahead and remote-ahead counts.
- Do not reset or overwrite. Route recovery to a developer who can preserve local commits.

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

Open or update a PR when appropriate. Resolve review findings and required checks before merge.

## 6. Handoff contract

A handoff must state:

- repository, branch/worktree, sprint, lane, owned and forbidden scope;
- files changed and why;
- validation commands and exact results;
- commit SHA, push state, and PR state;
- blockers, skipped checks, proof achieved, and proof ceiling;
- final Git status;
- one exact next command or `none; cleanup complete`.

For interrupted work, include the last coherent commit and uncommitted file list. Never require the next agent to reconstruct state from narrative alone.
