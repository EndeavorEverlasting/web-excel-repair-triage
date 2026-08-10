# App Harness Validation

## Purpose

`scripts/validate_app_harness.py` is the one-command offline/synthetic harness proof entry point. It aggregates only checks that are safe to execute without launching the application, Prompt Kit, a browser, a game, a target runtime, or a network probe.

## Matrix

A healthy repository prints six rows:

```text
APP HARNESS VALIDATION
[PASS] required files
[PASS] run context
[PASS] artifact registry
[PASS] report renderer
[SKIP] optional MCP symbol smoke: lsp_project_not_loaded
[PASS] hook hygiene
Result: 5 passed / 1 skipped / 0 failed
```

The actual output also prints the resolved branch, commit, JSON path, and proof ceiling.

## Required behavior

- detect the repository root through Git;
- resolve branch and commit without modifying either;
- execute the canonical root harness validator and artifact-hygiene checker only through an explicit offline allowlist;
- parse the machine artifact and validator registries;
- verify registered hooks exist;
- emit `Outputs/app-harness-validation.json` plus the English matrix;
- preserve an existing app-harness receipt and the nested harness-completeness receipt under `Outputs/backups/app-harness-validation/<UTC timestamp>/` before replacement;
- treat an unloaded LSP/MCP project as an explicit optional `SKIP`, never as a fabricated pass;
- return nonzero when any required check fails.

## Canonical registration

- `harness/artifacts.v1.json` registers `app-harness-validation-report` at `Outputs/app-harness-validation.json`, schema `app-harness-validation/v1`.
- `harness/validators.v1.json` registers `app-harness-validation` and includes it in the canonical `harness` and `pre_push` profiles.
- `harness/manifest.v1.json` includes the command in the canonical validation order.
- `scripts/validate_harness.py` fail-closes if the new artifact or validator registration disappears.

## Safety boundary

The validator must not execute launchers, browsers, application/game entry points, network tools, cleanup/reset commands, target mutations, save mutations, account mutations, or secret collection. JSON output and receipt backups are restricted to `Outputs/`.

## Proof ceiling

A green matrix proves only offline/synthetic repository harness readiness for the checked commit. It does **not** prove Prompt Kit layout correctness or repair the currently observed overlap defect. It also does not prove browser geometry, live runtime behavior, network reachability, launcher behavior, target state, saves, accounts, or production acceptance.

## Command

```powershell
python scripts/validate_app_harness.py --output Outputs/app-harness-validation.json
```
