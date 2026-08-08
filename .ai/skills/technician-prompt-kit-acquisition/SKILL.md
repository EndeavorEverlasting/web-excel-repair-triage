# Technician Prompt Kit Acquisition

## Trigger

Use this skill when a technician needs to obtain the repository for the first time, update an existing checkout, or open the latest Prompt Kit website or generator GUI without typing Git commands.

Do not use it to repair arbitrary Git history, recover local commits, switch feature branches, or authenticate providers.

## Required inputs

- Canonical repository URL: `https://github.com/EndeavorEverlasting/web-excel-repair-triage.git`.
- Default branch: `main`.
- A technician-selected destination folder.
- Git for Windows, Windows PowerShell, and Python 3.
- Network and repository access when cloning or fetching.

## Outputs

- A clean local checkout on `main`, cloned or fast-forwarded without destructive operations.
- A validated `web/prompt-kit/index.html` and generator manifest.
- The selected Prompt Kit website or generator GUI opened only after validation.
- Clear operator-visible errors for missing tools, authentication, network, dirty worktrees, divergence, wrong origins, or missing files.

## Procedure

1. Launch `Acquire-Latest-PromptKit.cmd` by double-click.
2. Choose the parent destination with the GUI when the default is not appropriate.
3. Choose whether to open the website or generator GUI after validation.
4. When the destination does not exist, clone `main` from the canonical repository.
5. When the repository exists:
   - verify the canonical origin;
   - require a clean worktree;
   - require the current branch to be `main`;
   - fetch `origin/main`;
   - reject local-only commits or divergence;
   - fast-forward with `git merge --ff-only` only.
6. Verify the required website, launcher, builder, and generator-manifest files.
7. Run the exact combined-registry website check.
8. Open the selected surface only after every check passes.

## Guardrails

- Never run `git reset`, `git clean`, force-push, branch deletion, stash deletion, or credential automation.
- Never overwrite a destination that exists but is not the canonical repository.
- Never update a dirty worktree or a branch other than `main`.
- Never treat static validation as proof of Windows visual usability.
- Never embed user-specific paths or credentials.
- Destination and post-validation choices belong in the GUI, not command-line questions.

## Validation

- `python scripts/validate_harness.py`
- `python -m unittest tests.test_harness_contract -v`
- `python -m unittest tests.test_skill_prompt_registry -v`
- `python tests/test_prompt_kit_header_contract.py`
- Native Windows field check: download or double-click `Acquire-Latest-PromptKit.cmd`, choose a temporary destination, clone, validate, and open the selected surface.

## Proof ceiling

Repository and CI checks prove tracked launcher structure, bounded Git operations, required-file validation, manifest integrity, and absence of destructive command patterns. They do not prove a specific technician's network, credentials, Windows policy, GUI rendering, or local Git installation.
