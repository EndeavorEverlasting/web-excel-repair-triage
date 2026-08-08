# Prompt Kit Generator Tutorial

## Audience and result

This tutorial is for technicians, prompt authors, and developers who already have a current clean checkout and need to build or open the Prompt Kit without memorizing command-line options.

For first-time acquisition or safe update, use [Technician Tutorial: Get the Latest Prompt Kit](TECHNICIAN_PROMPT_KIT_ACQUISITION_TUTORIAL.md) before this guide.

## Choose the correct entry point

| Goal | Entry point | Choices shown |
|---|---|---|
| Get or update the repository, then open a current surface | `Acquire-Latest-PromptKit.cmd` | Destination and what to open after validation |
| Select a registered generator and its options | `Run-PromptKitGenerator.cmd` | Generator, output path, validation, and open-after-build choices |
| Rebuild the canonical website with safe defaults | `Build-PromptKitWebsite.cmd` | None |
| Open the already checked-in website | `web\prompt-kit\index.html` | None |

## Generator GUI prerequisites

On Windows:

- current repository checkout on the intended branch;
- Python 3 available as `py -3` or `python`;
- Tkinter included with the Python installation;
- write access to the chosen output location.

No server is required to open the generated static HTML site.

## Use `Run-PromptKitGenerator.cmd`

1. Open the repository folder in File Explorer.
2. Double-click `Run-PromptKitGenerator.cmd`.
3. Select the registered generator.
4. Review its tracked description and options.
5. Choose the output HTML path.
6. Keep **Validate exact generated output** enabled for normal use.
7. Keep **Open website after build** enabled when you want immediate browser review.
8. Start the build.

Generator choices and options come from:

```text
configs\prompt_kit\generators.v1.json
```

The GUI is bounded to the registered Prompt Kit builder. It does not accept an arbitrary command to execute.

## Current generator options

For **Prompt Kit Website**:

| Option | Safe default | Meaning |
|---|---|---|
| Output HTML | `web\prompt-kit\index.html` | Rebuild the checked-in canonical operator site. |
| Validate exact generated output | Enabled | Re-runs the builder in check mode and fails on drift. |
| Open website after build | Enabled | Opens the generated HTML with the Windows default browser after success. |

## Use `Build-PromptKitWebsite.cmd`

This is the direct one-click path when there are no choices to make.

1. Open the repository folder.
2. Double-click `Build-PromptKitWebsite.cmd`.
3. The launcher builds `web\prompt-kit\index.html`.
4. It checks that the result exactly matches the combined registry build.
5. It opens the site only after success.

Use this path for the canonical site. Use the GUI when you need an alternate output path or want to change open/validation options.

## Safe output locations

### Canonical operator site

```text
web\prompt-kit\index.html
```

### Preview or comparison copy

Use a path under `Outputs/`, for example:

```text
Outputs\prompt-kit-preview.html
```

### Never use these locations

```text
Candidates\
Active\
```

Those directories are read-only operator inputs. The builder and GUI reject output destinations under either path before writing.

## What the builder combines

The generated site contains:

1. `docs/prompts.json` — canonical base prompt registry;
2. `registry/prompts/skill-development-prompts.v1.json` — tracked skill-development extension;
3. `docs/reference.json` — reference panel data;
4. the tracked Prompt Kit HTML, CSS, and JavaScript shell.

The builder rejects duplicate prompt IDs, duplicate sequences, malformed records, protected output paths, and checked-in output drift.

## Browser use

The Prompt Kit is a static local HTML application.

- Double-click the generated `.html` file or allow the launcher to open it.
- No local web server is required for ordinary use.
- Browser security policy may affect clipboard behavior; use the visible copy controls and confirm the paste result.
- Opening the HTML proves only that the browser rendered it. It does not prove every prompt or generated artifact has been operator-accepted.

## Command-line verification for developers and administrators

These commands are optional for technicians and useful for validation or troubleshooting.

From the repository root:

```powershell
python scripts\build_prompt_kit_registry.py --output Outputs\prompt-kit-preview.html
python scripts\build_prompt_kit_registry.py --output Outputs\prompt-kit-preview.html --check
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
python -m unittest tests.test_skill_prompt_registry -v
python tests\test_prompt_kit_header_contract.py
```

When `py -3` is the approved Python entry point, replace `python` with `py -3`.

## Expected successful output

The exact builder text may evolve, but a successful run has these properties:

- process exit code is zero;
- the selected output exists;
- check mode reports no mismatch;
- the selected browser opens only after success;
- `P61` and `P62` remain present in the combined site;
- no files were written under `Candidates/` or `Active/`.

## Troubleshooting

### CMD window closes immediately

Open PowerShell in the repository root and run the same CMD so the error remains visible:

```powershell
Set-Location -LiteralPath '<repository-root>'
.\Run-PromptKitGenerator.cmd
```

Use the real local repository path; do not copy another operator's user-specific path.

### Python is missing

Install the approved Python 3 package and confirm one of these works:

```powershell
py -3 --version
python --version
```

### Tkinter GUI does not open

Verify Tkinter is available:

```powershell
python -c "import tkinter; print('tkinter available')"
```

A Python installation without Tkinter can still run the command-line builder, but it cannot prove the generator GUI.

### Protected output path rejected

Choose `web\prompt-kit\index.html` for the canonical site or an alternate path under `Outputs/`. Do not bypass the refusal.

### Exact-output validation failed

The generated file and tracked registry sources do not agree. Preserve the message and run:

```powershell
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
```

Do not distribute the site as current until the mismatch is repaired and reviewed.

### Browser opens an older-looking site

Confirm the file path in the browser points to the intended checkout. Close duplicate tabs, run `Acquire-Latest-PromptKit.cmd`, and select **Open Prompt Kit website** after the safe update passes.

## Rollback and recovery

- An alternate preview under `Outputs/` may be removed after review if it contains no needed evidence.
- Do not delete or rewrite `docs/prompts.json`, registry extensions, or `web\prompt-kit\index.html` to resolve a failed build.
- Do not use `git reset` or `git clean` as an operator recovery step.
- If the canonical site changed unexpectedly after a legitimate fast-forward, record the commit and escalate for repository review.

## Proof checklist

Record:

- generator selected;
- output path;
- validation enabled or disabled;
- process result;
- output existence;
- browser opened: yes or no;
- operator spot-check of prompt search/copy controls;
- Windows field acceptance: pass or fail.

CI and static tests prove generator contracts. They do not prove the GUI appearance, mouse workflow, or clipboard behavior on a particular Windows workstation.
