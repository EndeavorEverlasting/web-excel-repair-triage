# Local Hook and Artifact Hygiene

## Purpose

This repository keeps local Git hooks opt-in. The hooks add path-only safety rails
that stop generated evidence, logs, saves, crash dumps, credential material, and
machine-local tool installs from entering commits while leaving ordinary code,
documentation, and sanitized fixtures commit-friendly.

## Install or verify

From the repository root:

```powershell
python scripts/install_local_hooks.py
python scripts/install_local_hooks.py --check
```

The installer writes only the repository-local `core.hooksPath=.githooks`
configuration. It never changes global Git configuration. When a different local
hooks path already exists, installation fails closed and preserves that setting
unless the operator explicitly reruns with `--replace`.

## Pre-commit behavior

The pre-commit hook first runs:

```text
python scripts/validate_staged_artifacts.py
```

The validator inspects staged **paths only**. It does not open or print staged
file contents. A rejected path is reported as:

```text
[harness] refusing staged generated/runtime artifact: <path>
Move live/generated evidence back to ignored local output, or commit a sanitized fixture under an approved fixture/docs path.
```

After the path gate passes, the hook validates the isolated staged tree and runs
patch hygiene. It does not launch the product, contact the network, or invoke a
browser, GUI, workbook runtime, or deployment path.

## Paths blocked by default

- live or generated material under `Outputs/`, `outputs/`, `billing_runs/`,
  `Candidates/`, `Repaired/`, `ArtifactIntake/`, `References/`, and related
  protected drop zones;
- root runtime locations such as `logs/`, `saves/`, and `crash_dumps/`;
- caches and local tool installations such as `.venv/`, `node_modules/`,
  `.pytest_cache/`, `.mypy_cache/`, and `.ruff_cache/`;
- logs, traces, temporary saves, crash dumps, and backup files;
- environment, credential, token, certificate, private-key, and password-vault
  material.

Only the path and policy reason are reported. Sensitive excerpts are never read
or echoed.

## Approved commit surfaces

- ordinary source code and repository documentation;
- tracked control-plane files and contracts;
- sanitized fixtures under `tests/fixtures/`, `harness/fixtures/`, or
  `docs/fixtures/`;
- `.gitkeep` and `README.md` metadata used to describe protected drop zones.

A fixture path does not permit private keys, credential files, environment files,
or password-vault material.

## Validation

```powershell
python scripts/validate_artifact_hygiene.py
python -m unittest tests.test_gitignore_hygiene tests.test_local_hook_artifact_hygiene -v
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
git diff --check
```

## Failure handling

Do not bypass the hook with `--no-verify` to commit live evidence. Move the file
back to an ignored local output location. When a small artifact is genuinely
needed for regression coverage, sanitize it, place it under an approved fixture
path, document what was removed, and rerun the focused hygiene validator.

## Proof ceiling

These checks prove path policy, local hook configuration, and the tested
repository state. They do not inspect artifact contents, prove sanitization
quality, scan remote history, validate production runtime behavior, or replace
credential-management and secret-scanning systems.
