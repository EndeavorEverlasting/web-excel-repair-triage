# Prompt Kit Generator Operator Guide

## Operator entry points

The repository provides three Windows double-click entry points.

### Get the latest repository, website, and generators

Double-click or download and double-click:

```text
Acquire-Latest-PromptKit.cmd
```

This is the technician acquisition surface. It opens a Windows GUI where the operator chooses:

- the parent destination folder;
- whether to open the Prompt Kit website or the generator selection GUI after validation.

When the repository is absent, it clones canonical `main`. When the repository exists, it verifies canonical origin, clean status, and current branch `main`, then fetches and fast-forwards only. It refuses dirty worktrees, wrong origins, wrong branches, local-only commits, and divergence. It never resets, cleans, force-pushes, or discards local work.

After clone or update, it validates required site and generator files and runs the exact combined-registry website check. It opens the selected surface only after validation succeeds.

The CMD is self-bootstrapping: when run outside the repository, it downloads the current tracked PowerShell GUI from canonical `main` into a temporary cache and launches it. It does not download or store credentials.

### Generator with options

From the repository root, double-click:

```text
Run-PromptKitGenerator.cmd
```

This opens a Tkinter GUI. Generator choices and options come from the tracked manifest at `configs/prompt_kit/generators.v1.json`; operators do not type command-line flags.

Current GUI options:

- generated HTML output path;
- validate the exact generated output after the build;
- open the website after the build.

The GUI is deliberately bounded to `scripts/build_prompt_kit_registry.py`. The manifest cannot launch arbitrary commands.

### Default one-click build

From the repository root, double-click:

```text
Build-PromptKitWebsite.cmd
```

This has no choices. It builds `web/prompt-kit/index.html`, validates that the written file exactly matches the combined registry build, and opens the result.

## Technician prerequisites

- Windows PowerShell 5.1 or newer;
- Git for Windows;
- Python 3 with `py -3` or `python` available on `PATH`;
- network and GitHub repository access for clone or update.

The acquisition GUI reports missing prerequisites, authentication failures, network failures, wrong origins, local modifications, branch mismatch, divergence, missing required files, and generated-site drift without mutating local work destructively.

## Output safety

`Candidates/` and `Active/` are read-only operator-input directories. Both the generator GUI and registry builder reject output paths inside either directory before creating folders or writing files.

Use the checked-in `web/prompt-kit/index.html` destination for the canonical operator site. Use `Outputs/` for previews, comparisons, or alternate generated copies.

## Registry composition

The website builder combines:

1. `docs/prompts.json` — canonical base prompt registry;
2. `registry/prompts/skill-development-prompts.v1.json` — versioned skill-development registry extension;
3. `docs/reference.json` — reference-panel data.

The extension currently adds:

- `P61` — Skill Factoring and Boundary Refactorer;
- `P62` — Skill Evaluation Harness Implementer.

The P61 prompt is backed by `.ai/skills/skill-factoring/SKILL.md`. Technician acquisition is backed by `.ai/skills/technician-prompt-kit-acquisition/SKILL.md`.

## Adding another generator

A generator with operator-selectable options must be registered in `configs/prompt_kit/generators.v1.json` and exposed through the GUI. Do not add another CMD that asks operators to type or choose command-line arguments.

A direct CMD is appropriate only when the action has one safe default behavior and no operator choices. Direct launchers should:

1. resolve the repository from `%~dp0` when repository-local;
2. fail clearly when required tools are unavailable;
3. validate after generation or acquisition;
4. avoid machine-specific paths;
5. never embed credentials or private artifact paths;
6. never reset, clean, or overwrite unknown local work.

## Validation

Run:

```powershell
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
python -m unittest tests.test_skill_prompt_registry -v
python scripts\build_prompt_kit_registry.py --output Outputs\prompt-kit-preview.html
python scripts\build_prompt_kit_registry.py --output Outputs\prompt-kit-preview.html --check
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
```

CI workflows:

```text
Operational harness contracts
Skill prompt registry and generator UX
Prompt Kit web contracts
```

## Proof ceiling

Repository tests prove registry composition, prompt uniqueness, required skill sections, bounded generator routing, protected-path refusal, acquisition command boundaries, dirty/divergent checkout refusal, checked-in-site parity, and deterministic HTML generation. Native Windows mouse behavior, network access, GitHub authentication, and operator usability on a specific technician desktop remain field acceptance checks.
