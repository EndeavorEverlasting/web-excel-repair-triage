# V39 P50 — GitHub CLI Repository Bootstrapper

## Purpose

P50 is a standard AI prompt for safely spinning up a new GitHub repository through local Git and GitHub CLI tools.

It is not a Goodnight, Have Fun (GNHF) command. It belongs at the end of the contiguous P37–P50 advanced standard-AI section.

## Supported modes

### New remote and local clone

The prompt may produce or execute a reviewed command shaped as:

```powershell
gh repo create "OWNER/REPOSITORY" --private --description "DESCRIPTION" --clone
```

The visibility flag must be explicit. Optional `--add-readme`, `--license`, `--gitignore`, `--template`, `--disable-issues`, and `--disable-wiki` flags are added only when the operator selected them and their values were validated.

### Publish an existing local repository

The prompt may use a reviewed command shaped as:

```powershell
gh repo create "OWNER/REPOSITORY" --private --description "DESCRIPTION" --source "VERIFIED_ROOT" --remote origin --push
```

This mode is permitted only when:

- the operator explicitly selected the existing local repository;
- its root, branch, history, status, and remotes were inspected;
- the history is approved for publication;
- secret, private, generated, or unrelated artifacts are not included;
- push authority was explicitly granted.

`--push` is omitted when publishing commits has not been authorized.

## Directory gate

A repository that does not exist locally has no Git root yet. P50 therefore verifies one of two boundaries before creation:

- the exact parent directory in clone-new mode;
- the exact existing Git root in publish-existing mode.

The first executable command enters that path. Unknown existing child directories are never deleted or overwritten automatically.

## Authentication boundary

P50 uses:

```powershell
gh auth status --active --hostname github.com
```

It never authorizes `--show-token`, prints token-bearing environment variables, requests credentials in chat, or automates `gh auth login`.

Authentication, owner, organization permission, network, or policy failures are reported as blockers.

## Collision gate

Before creation, P50 uses `gh repo view OWNER/REPOSITORY` and distinguishes:

- an existing repository;
- confirmed not-found;
- authentication failure;
- permission failure;
- network failure.

An existing repository is a stop condition unless the operator changes the task to inspecting or cloning it.

## Verification

After creation, P50 requires:

```powershell
gh repo view "OWNER/REPOSITORY" --json nameWithOwner,url,visibility,defaultBranchRef
git rev-parse --show-toplevel
git remote get-url origin
git branch --show-current
git log --oneline --decorate -5
git status --short
```

Creation, clone, push, visibility, and remote claims require direct CLI evidence.

## V39 generation

The operator launcher now invokes:

```powershell
python -m triage.prompt_kit_v39_composed_generator
```

This generator combines:

- `configs/prompt_kit/v39_local_first_prompts.json` for P45–P49;
- `configs/prompt_kit/v39_github_repo_creation_prompt.json` for P50.

The two prompt sources remain separately factored, but one direct package-preserving generation pass adds all six tabs to V38.

## Validation

The repository validates that:

- P50 is a standard AI prompt;
- P50 is contiguous with P37–P49;
- P50 contains directory, authentication, collision, creation-mode, and verification contracts;
- P50 contains both `--clone` and `--source` pathways;
- token display and GNHF markers are forbidden;
- the generated workbook contains P00–P50 in exact order;
- Prompt Library rows, formulas, backlinks, app metadata, and the calculation chain remain valid;
- identical source and prompt inputs produce byte-identical workbook output.

## Proof ceiling

Repository tests prove the prompt and workbook contracts. V39 generation does not itself create a GitHub repository. A P50 runtime must separately prove CLI authentication, repository creation, remote state, local checkout, commit/push state, and visibility.
