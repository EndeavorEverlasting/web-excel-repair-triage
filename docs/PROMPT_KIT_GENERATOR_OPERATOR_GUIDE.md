# Prompt Kit Generator Operator Guide

## Operator entry points

The repository provides two Windows double-click entry points from the repository root.

### Generator with options

Double-click:

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

Double-click:

```text
Build-PromptKitWebsite.cmd
```

This has no choices. It builds `web/prompt-kit/index.html`, validates that the written file exactly matches the combined registry build, and opens the result.

## Registry composition

The website builder combines:

1. `docs/prompts.json` — canonical base prompt registry;
2. `registry/prompts/skill-development-prompts.v1.json` — versioned skill-development registry extension;
3. `docs/reference.json` — reference-panel data.

The extension currently adds:

- `P61` — Skill Factoring and Boundary Refactorer;
- `P62` — Skill Evaluation Harness Implementer.

The P61 prompt is backed by the reusable repository skill at `.ai/skills/skill-factoring/SKILL.md`.

## Adding another generator

A generator with operator-selectable options must be registered in `configs/prompt_kit/generators.v1.json` and exposed through the GUI. Do not add another CMD that asks operators to type or choose command-line arguments.

A direct CMD is appropriate only when the action has one safe default behavior and no operator choices. Direct launchers should:

1. resolve the repository from `%~dp0`;
2. use `py -3` when available and fall back to `python`;
3. fail clearly when Python is unavailable;
4. validate after generation;
5. avoid machine-specific paths;
6. never embed credentials or private artifact paths.

## Validation

Run:

```powershell
python -m unittest tests.test_skill_prompt_registry -v
python scripts\build_prompt_kit_registry.py --output Outputs\prompt-kit-preview.html
python scripts\build_prompt_kit_registry.py --output Outputs\prompt-kit-preview.html --check
```

CI workflow:

```text
Skill prompt registry and generator UX
```

The workflow compiles the builder, GUI, and tests; validates registry uniqueness and skill contracts; builds a combined website; and proves P61 and P62 are present.

## Proof ceiling

Repository tests prove registry composition, prompt uniqueness, required skill sections, bounded GUI routing, launcher structure, and deterministic HTML generation. Native double-click appearance and operator usability on a specific Windows desktop remain a field acceptance check.
