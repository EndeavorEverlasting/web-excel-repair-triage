# Prompt Kit Operator Guide

This is the compact reference for the current Windows acquisition and generator workflow. Use the detailed tutorials when training a new technician or certifying a workstation.

## Detailed tutorials

- [Technician acquisition tutorial](TECHNICIAN_PROMPT_KIT_ACQUISITION_TUTORIAL.md)
- [Generator tutorial](PROMPT_KIT_GENERATOR_TUTORIAL.md)
- [Administrator verification runbook](PROMPT_KIT_ADMIN_VERIFICATION.md)
- [Operator documentation index](README.md)

## Current entry points

### Get or update everything, then open it

Double-click or download and double-click:

```text
Acquire-Latest-PromptKit.cmd
```

The Windows GUI lets the operator choose:

- destination folder;
- **Open Prompt Kit website**; or
- **Open generator selection GUI**.

When the repository is absent, it clones canonical `main`. When the repository exists, it verifies canonical origin, a clean status, and branch `main`, then fetches and fast-forwards only. It refuses dirty worktrees, wrong origins, wrong branches, local-only commits, and divergence. It never resets, cleans, force-pushes, rewrites the origin, deletes branches, or discards local work.

After clone or update, it verifies required site and generator files and runs exact combined-registry output validation. It opens the selected surface only after validation succeeds.

The standalone CMD downloads the tracked PowerShell GUI from canonical `main` into `%TEMP%\WebExcelPromptKit` when the companion script is not beside it. It does not download or store credentials.

### Open the generator-selection GUI

From a current repository root, double-click:

```text
Run-PromptKitGenerator.cmd
```

Generator choices and options come from `configs/prompt_kit/generators.v1.json`. Operators do not type free-form commands.

Current Prompt Kit Website options:

- output HTML path;
- validate exact generated output after build;
- open website after build.

### Rebuild the canonical site with safe defaults

From a current repository root, double-click:

```text
Build-PromptKitWebsite.cmd
```

This launcher has no choices. It builds `web\prompt-kit\index.html`, validates exact output, and opens it after success.

### Open the checked-in site without rebuilding

Open:

```text
web\prompt-kit\index.html
```

The Prompt Kit is static HTML. A local web server is not required for normal use.

## Technician prerequisites

- Windows PowerShell 5.1 or newer;
- Git for Windows;
- Python 3 available as `py -3` or `python`;
- Tkinter for the generator-selection GUI;
- browser or Git access to the canonical GitHub repository;
- repository permission when authentication is required.

The launchers never automate GitHub or provider authentication.

## Safe defaults

| Surface | Safe default |
|---|---|
| Acquisition destination | `%USERPROFILE%\Desktop\dev\web-excel-repair-triage` |
| Acquisition branch | `main` |
| Acquisition update method | `git fetch` followed by `git merge --ff-only` |
| Acquisition open choice | Prompt Kit website |
| Generator output | `web\prompt-kit\index.html` |
| Alternate preview output | A file under `Outputs\` |
| Validation | Enabled |
| Open after build | Enabled |

## Protected paths

Never write generator output under:

```text
Candidates\
Active\
```

Those are read-only operator-input locations. The generator GUI and builder reject them before creating folders or writing files.

## Registry composition

The website builder combines:

1. `docs/prompts.json` — canonical base registry;
2. `registry/prompts/skill-development-prompts.v1.json` — tracked skill-development extension;
3. `docs/reference.json` — reference-panel data;
4. the tracked website shell and scripts.

The current extension includes:

- `P61` — Skill Factoring and Boundary Refactorer;
- `P62` — Skill Evaluation Harness Implementer.

Related repository skills:

- `.ai/skills/skill-factoring/SKILL.md`;
- `.ai/skills/technician-prompt-kit-acquisition/SKILL.md`.

## Common failures

| Message or condition | Meaning | Safe response |
|---|---|---|
| Git or Python not found | Required local prerequisite is unavailable | Install through the approved software process; reopen the launcher. |
| Destination exists but is not a Git repository | The selected folder cannot be safely cloned over | Choose another destination or preserve/move the unrelated folder. |
| Unexpected origin | The selected checkout is not canonical | Stop; inspect with a developer. Do not rewrite the origin automatically. |
| Local modifications or untracked files | Work exists in the checkout | Preserve or commit it. Do not reset or clean. |
| Branch is not `main` | Another lane owns the checkout | Ask the branch owner to finish and return safely to `main`. |
| Local `main` has commits absent from `origin/main` | Reset would lose work | Stop and escalate; preserve the commits. |
| Required file missing | Checkout is incomplete or repository floor is broken | Report a repository defect; do not distribute the site. |
| Exact-output validation failed | The site does not match current tracked registries | Repair through a normal developer branch and PR. |

See the [technician tutorial](TECHNICIAN_PROMPT_KIT_ACQUISITION_TUTORIAL.md) for exact messages and step-by-step recovery.

## Verification commands

From the repository root:

```powershell
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_operator_documentation -v
python -m unittest tests.test_skill_prompt_registry -v
python tests\test_prompt_kit_header_contract.py
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
python -m triage.gitignore_hygiene
git diff --check
```

CI workflows:

```text
Operator documentation contracts
Operational harness contracts
Skill prompt registry and generator UX
Prompt Kit web contracts
Artifact engine tests
```

## Rollback and escalation

- Closing the GUI before **Get Latest and Open** makes no repository change.
- A refused checkout is a safety success; resolve the named condition instead of bypassing it.
- Delete a failed fresh-clone folder only after confirming it contains no operator-created work.
- Do not use `git reset`, `git clean`, force checkout, force-push, or branch deletion as technician recovery steps.
- For an unexpected fast-forward result, record the commit and escalate to a developer-owned recovery lane.

## Proof ceiling

Documentation and CI prove tracked controls, messages, links, command boundaries, registry composition, protected-path refusal, and exact-output contracts. They do not prove Windows GUI rendering, mouse behavior, clipboard behavior, network access, authentication, or operator usability on a specific technician workstation. Record those through a real Windows field acceptance run.
