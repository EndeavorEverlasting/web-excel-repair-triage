# Workflow Specifications

This file defines how agents and operators enter, select, validate, recover, commit, and hand off work in this repository. Machine-readable workflow ownership lives in `harness/workflows.v1.json`. Focused domain-contract ownership, including operator command delivery and Prompt Kit cross-device access, is registered in `harness/manifest.v1.json`. Product behavior remains in focused modules, schemas, registries, tests, and contracts.

## 1. Pick up a task

1. Read `AGENTS.md` and any nearest nested instructions.
2. Read `CODEBASE_MAP.md`, `harness/manifest.v1.json`, `harness/workflows.v1.json`, `harness/validators.v1.json`, and `harness/reports/CURRENT_STATE.md`.
3. Record the Git floor:

   ```bash
   git status --short
   git branch --show-current
   git log --oneline --decorate -5
   ```

4. Inspect open PRs, recent commits, affected files, registered triggers/capabilities, validators, canonical artifacts, and known gaps.
5. Declare repository, branch/worktree, sprint, lane, mission, owned scope, forbidden scope, dependencies, expected artifacts, validation order, proof ceiling, and mutation authority.
6. Preserve dirty or separately owned work. Use an isolated branch/worktree instead of reset, clean, force, or overwrite.
7. Select one workflow ID from `harness/workflows.v1.json`, one primary capability owner, and the validator profile or focused domain gate that proves the requested change.

## 2. Workflow selection

### A. Technician acquisition or update

**Workflow ID:** `technician-acquisition`  
**Trigger:** A user or technician needs to open, install, share, download, clone, update, or locally edit the current `main` Prompt Kit.  
**Capability:** `technician-prompt-kit-acquisition`  
**Skill:** `.ai/skills/technician-prompt-kit-acquisition/SKILL.md`  
**Focused contract:** `harness/contracts/prompt-kit-cross-device-access.v1.json`

Route by **intent first**, then by device. Do not default every acquisition question into a Git checkout.

1. **Normal browser use / sharing** — open `https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/`. No repository clone, ZIP extraction, Git client, Python, PowerShell, Termux, or local server is required.
2. **Phone/tablet install** — open `https://endeavoreverlasting.github.io/web-excel-repair-triage/` in the system browser and use the install/Add to Home Screen surface. If the GitHub mobile app uses its in-app browser, move to the system browser first.
3. **Windows stable local app / portable Favorites** — use `Open-Latest-PromptKit.cmd`. The repository-owned launcher owns safe clone-or-fast-forward, parity validation, portable runtime generation, and stable loopback serving.
4. **Edit, commit, push, inspect source, or run repository tooling locally** — use a real Git checkout. Clone exactly:

   ```bash
   git clone --branch main --single-branch https://github.com/EndeavorEverlasting/web-excel-repair-triage.git
   ```

   Update an existing clean canonical checkout only with:

   ```bash
   git pull --ff-only origin main
   ```

   On Android, use Termux from F-Droid, then `pkg update`, `pkg install git`, and the same clone command. This route is for source work, not ordinary Prompt Kit use.
5. **Explicit source snapshot without Git** — use the repository `main.zip` and state clearly that it is a point-in-time snapshot, not a synchronized checkout.

For a Windows editable/acquisition checkout, verify canonical origin, clean `main`, no local-only commits or divergence, fetch, and fast-forward only. On failure, preserve the checkout and report the exact access-mode, Git, authentication, network, origin, branch, divergence, required-file, parity, browser, or device gate. Do not automate credentials or use destructive Git commands.

Focused validation:

```bash
python -m py_compile scripts/validate_prompt_kit_cross_device_access.py tests/test_prompt_kit_cross_device_access.py
python scripts/validate_prompt_kit_cross_device_access.py --summary
python -m unittest tests.test_prompt_kit_cross_device_access -v
```

Static success does not prove a specific browser menu, PWA installation, Termux/F-Droid availability, Git authentication, Favorites persistence, clipboard behavior, or push access.

### B. Prompt registry or website change

**Workflow ID:** `prompt-kit-change`  
**Trigger:** Canonical prompts, extensions, policies, reference data, builder behavior, generator options, checked-in HTML, or Prompt Kit interaction/discovery contracts change.

1. Change canonical source, never only generated HTML.
2. Read the relevant contract before implementation.
3. Keep harness-only work to contracts, registries, validators, fixtures, hooks, CI, reports, and documentation.
4. In an authorized product lane, repair the canonical behavior source and regenerate deterministic output.
5. Run interaction/discovery validators, prompt-language audit when language changes, registry tests, header checks, exact site parity, and broader affected tests.
6. Keep browser, clipboard, focus, provider, and visual proof separate from static checks.

### C. Harness infrastructure change

**Workflow ID:** `harness-infrastructure`  
**Trigger:** Maps, workflow specifications, artifact/validator/capability/trigger registries, validators, hooks, skills, reports, acquisition surfaces, command-delivery contracts, or versioned contracts are missing, stale, disconnected, or failing.  
**Capability:** `harness-infrastructure-maintenance`  
**Skill:** `.ai/skills/harness-infrastructure-maintenance/SKILL.md`

1. Preserve occupied or dirty work and create an isolated harness branch/worktree.
2. Inspect all canonical harness files before inventing new names or contracts.
3. Repair the canonical owner. Do not create a competing map, registry, validator, hook, report, or command-delivery surface.
4. Update `harness/manifest.v1.json`, human indexes, workflow/artifact/validator registries, capabilities/triggers, tests, hooks, CI path filters, and operator state atomically when ownership or commands change.
5. Keep `AGENTS.md`, product implementation, secrets, and destructive cleanup out of scope.
6. Make pre-commit inspect the staged index through an isolated staged tree. Keep pre-push exhaustive and non-destructive.
7. When the failure involves Prompt Kit acquisition/access routing, read `harness/contracts/prompt-kit-cross-device-access.v1.json`, preserve the single `technician-prompt-kit-acquisition` owner, and run its focused validator/tests before the root profile.
8. When the failure involves a NEXT COMMAND, handoff snippet, or operator proof command, read `harness/contracts/operator-command-envelope.v1.json`, use `harness/templates/Invoke-RemoteHarnessProof.ps1` for unmerged harness proof, and run:

   ```bash
   python -m py_compile scripts/validate_operator_command_envelope.py tests/test_operator_command_envelope.py
   python scripts/validate_operator_command_envelope.py --summary
   python -m unittest tests.test_operator_command_envelope -v
   ```

   The operator command must not assume a remembered `C:\Users\<name>\...` path, must not contain Markdown hyperlink syntax as command data, and must not use top-level `exit` in an interactive PowerShell envelope. When the exact local repo root has not been proven in the current shell, use the environment-derived isolated checkout template rather than guessing.
9. Run the root harness checks:

   ```bash
   python -m py_compile scripts/validate_harness.py tests/test_harness_contract.py
   python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
   python -m unittest tests.test_harness_contract -v
   ```

10. Run the remaining `harness` validator profile from `harness/validators.v1.json`, followed by affected broader tests and `git diff --check`.
11. Commit coherent owned files, push normally, and open or update the existing focused PR.
12. Hand off the component list, report path, validator results, commit SHA, push/PR evidence, blockers, skipped checks, proof ceiling, and an executable next command.

### D. Workbook or artifact engine change

**Workflow ID:** `artifact-engine-change`  
**Trigger:** A `triage/` engine, workbook contract, schema, sanitized fixture, or generated artifact behavior changes.

Keep `Candidates/` and `Active/` read-only. Use sanitized fixtures. Write runtime outputs only to registered paths. Run focused engine tests, artifact hygiene, broader tests, and exact artifact validation. Treat Excel for Web and operator acceptance as separate runtime proof.

### E. PR-floor cleanup and integration

**Workflow ID:** `pr-floor-integration`  
**Trigger:** Work is stacked, divergent, superseded, conflicted, or blocked across branches/PRs.

Inspect base/head SHAs, unique commits, file deltas, required checks, review findings, and dependencies. Preserve unique work before closure. Integrate in dependency order. Never force-push, delete unique work, destructively clean, or merge with unresolved required gates.

### F. Prompt-language audit or repair

**Workflow ID:** `prompt-language-audit`  
**Triggers:** `prompt-language-change` or `lazy-next-action-report`  
**Capability:** `prompt-language-audit`

Audit every canonical and effective prompt. Require equal canonical, effective, and disposition counts. Fail duplicate identity, coverage gaps, empty required language, missing effective policy, and error findings. Repair canonical registries, policies, builders, and focused tests—not generated HTML alone. Strict mode is the completion gate for bounded language repair.

### G. Skill-evaluation build

**Workflow ID:** `skill-evaluation`  
**Trigger:** `skill-quality-unproven`  
**Capability:** `skill-evaluation`; Prompt Kit owner P62.

Define the eval contract and baseline, add positive/negative/near-miss/boundary/malformed/regression cases, reproduce weaknesses, implement the smallest valid repair, and measure performance, calls, context, retries, cost, and tokens when available. Accept efficiency changes only after correctness, safety, and routing gates remain green.

## 3. Validate before committing

Use the strongest practical checks in dependency order:

1. Focused unit/fixture tests.
2. Static compilation.
3. Focused domain-contract validators such as cross-device access or operator command envelope.
4. Root contract validators.
5. Exhaustive audits when prompt/skill surfaces are involved.
6. Deterministic generated-output parity.
7. Artifact and Git hygiene.
8. Broader tests and honest runtime checks.

For a cross-device Prompt Kit acquisition/access change, run:

```bash
python -m py_compile scripts/validate_prompt_kit_cross_device_access.py tests/test_prompt_kit_cross_device_access.py
python scripts/validate_prompt_kit_cross_device_access.py --summary
python -m unittest tests.test_prompt_kit_cross_device_access -v
```

For a harness command-delivery change, run the focused gate before the root profile:

```bash
python scripts/validate_operator_command_envelope.py --summary
python -m unittest tests.test_operator_command_envelope -v
```

The canonical root harness profile is stored in `harness/validators.v1.json` and mirrored exactly in `harness/manifest.v1.json`. Execute it in order:

```bash
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

Do not claim a skipped check passed. Report the exact command, dependency, failure, and remaining proof owner.

## 4. Handle failures

### Harness completeness or contract failure

Read the first actionable failure and identify the canonical owner: human map, machine registry, validator, skill, hook, workflow, test, report, or focused domain contract. Repair that owner and add a regression test. Do not weaken expected component IDs, command profiles, protected paths, or proof ceilings merely to obtain green output.

### Prompt Kit cross-device access failure

Treat unnecessary cloning for normal use, asking a mobile GitHub-app user to hunt for `index.html`, giving editable-checkout commands before establishing edit/commit/push intent, or replacing a safe launcher with manual destructive Git steps as harness defects.

1. Read `harness/contracts/prompt-kit-cross-device-access.v1.json`.
2. Classify user intent: use/install/share versus edit/commit/push/local tooling.
3. Select the lowest-friction registered mode that satisfies that intent.
4. Preserve existing checkout work. Never repair routing by resetting, cleaning, force-pushing, or discarding local work.
5. Run `scripts/validate_prompt_kit_cross_device_access.py` plus focused tests.
6. Keep device/browser/Termux/network/authentication acceptance outside static proof.

### Operator command / NEXT COMMAND failure

Treat a failed `Set-Location`, a command that runs Git outside a repo after the location gate failed, a Markdown-wrapped URL, or a vanished terminal caused by `exit` as a harness defect. Do not simply issue another guessed path.

1. Preserve the failed transcript as evidence.
2. Run `scripts/validate_operator_command_envelope.py` and the mutation fixtures.
3. If the current shell has not already proven the exact canonical repo root, use the isolated proof template under `LOCALAPPDATA`/`TEMP`; do not derive a user name from memory or another machine.
4. For remote work, fetch without force and verify the exact expected branch head before checkout.
5. Resolve the result artifact by ID through `harness/artifacts.v1.json` and print or open it only after validation succeeds.
6. Use terminating errors inside the proof script; never use top-level interactive `exit` as failure propagation.

### Staged-index hook failure

Inspect the staged tree rather than assuming ordinary working-tree state. Preserve unrelated unstaged changes. Repair only owned staged files, restage them, and rerun the hook.

### Generated-output drift

Repair canonical sources and regenerate deterministically. Commit source and generated output together only when the product workflow owns both. Harness-only work must not patch generated product output.

### Dirty worktree or branch collision

Do not reset, clean, or discard files. Identify the writer, create an isolated worktree/branch, and preserve coherent unique work.

### Network, authentication, provider, GUI, device, or protected-runtime failure

Preserve local state, report the exact blocked command or gate, never embed secrets, and do not substitute static proof for the blocked runtime.

## 5. Commit and PR contract

Before commit:

```bash
git diff --check
git status --short
git diff --stat
git diff
```

Stage only owned files, allow the staged-index pre-commit hook to validate the exact commit, then commit with a useful message and push normally:

```bash
git add <owned-files>
git commit -m "<useful message>"
git push -u origin <branch>
```

Open or update a focused PR. State dependencies, owned/forbidden scope, artifacts, validation, proof ceiling, blockers, and the exact head SHA. Resolve valid review findings and required checks before merge.

## 6. Handoff contract

A handoff must state:

- repository, branch/worktree, sprint, lane, mission, owned and forbidden scope;
- workflow ID, trigger ID, capability, and skill;
- every file created or modified;
- canonical and runtime artifacts with paths and, for Prompt Kit access, the selected delivery mode;
- validation commands actually run and results;
- skipped checks and exact reasons;
- commit SHA, push state, PR URL/state, and required-check state;
- blockers, risks, proof achieved, and proof ceiling;
- final Git status or explicit statement that local Git status was unavailable;
- one executable next command that fetches the exact remote commit non-destructively, runs the owning validator/build/launcher, resolves the canonical artifact through tracked registry evidence, prints or opens it, and propagates failure without closing the operator terminal.

Before delivering an unmerged harness NEXT COMMAND, validate the shape against `harness/contracts/operator-command-envelope.v1.json`. Prefer the tracked `harness/templates/Invoke-RemoteHarnessProof.ps1` instead of reconstructing a machine-specific path-heavy snippet. A remembered path, a raw Markdown hyperlink embedded as a string, or a top-level `exit` invalidates the handoff.
