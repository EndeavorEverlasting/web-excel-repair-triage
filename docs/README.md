# Operator Documentation Index

Use this page to choose the shortest current-repository guide for the job. These documents describe tracked behavior on `main`; planned behavior is labeled explicitly.

## Start here

| Audience | Goal | Guide |
|---|---|---|
| Any user | Get or refresh the latest validated Prompt Kit website | [Get the latest Prompt Kit website](GET_LATEST_PROMPT_KIT_WEBSITE.md) |
| Technician | Use the mouse to clone or safely update the repo and open the Prompt Kit | [Technician acquisition tutorial](TECHNICIAN_PROMPT_KIT_ACQUISITION_TUTORIAL.md) |
| Prompt author or operator | Build the site, select generator options, and understand output paths | [Generator tutorial](PROMPT_KIT_GENERATOR_TUTORIAL.md) |
| Developer or administrator | Verify prerequisites, contracts, Git state, CI, and field-proof boundaries | [Administrator verification runbook](PROMPT_KIT_ADMIN_VERIFICATION.md) |
| Any operator | Use the compact command and safety reference | [Prompt Kit operator guide](PROMPT_KIT_GENERATOR_OPERATOR_GUIDE.md) |

## Canonical website

The only canonical Prompt Kit website is:

```text
web\prompt-kit\index.html
```

Do not confuse it with third-party `.venv\...\index.html` files or generated `Outputs\...\index.html` reports. The [latest website quick reference](GET_LATEST_PROMPT_KIT_WEBSITE.md) gives the exact user instruction and safe update behavior.

## Current Windows entry points

| File | Behavior |
|---|---|
| `Open-Latest-PromptKit.cmd` | Normal-user zero-dialog launcher. Resolves Desktop/OneDrive development roots, preserves unsafe existing checkouts, clones or safely fast-forwards canonical `main`, validates exact site parity, and opens the website. |
| `Acquire-Latest-PromptKit.cmd` | Advanced mouse-accessible acquisition GUI. Uses the same safe acquisition implementation but lets a technician choose a destination and website versus generator surface. |
| `Run-PromptKitGenerator.cmd` | Opens the generator-selection GUI for registered generators and their tracked options. |
| `Build-PromptKitWebsite.cmd` | Rebuilds the canonical site with safe defaults, validates exact output, and opens the result. |

The zero-dialog and GUI launchers share `scripts\Acquire-LatestPromptKit.ps1`; do not fork their Git safety rules into separate implementations.

## Browser and mobile behavior

The Prompt Kit remains one static HTML application. Responsive layout changes presentation, not prompt/filter semantics.

- The main title is the stable reset-to-home control.
- Mobile exposes explicit touch-sized **Open** and **Copy** actions.
- Library, category, and type filters remain the same controls and can scroll horizontally on narrow screens.
- Cards become one column, while prompt detail and the reference panel use the mobile viewport.
- Existing Top/Bottom category anchors remain available.

## Platform boundaries

- **Windows technician workstation:** the quick launcher, acquisition GUI, and generator GUI are intended to run here.
- **Browser:** the Prompt Kit is a local static HTML file; no web server is required for normal use.
- **Linux or CI:** run validators and builders, but do not claim Windows GUI, process-launch, or physical mobile proof.
- **Administrator box:** verify Git, Python, policy, network access, and CI; do not automate credentials.
- **Remote target machine:** this workflow does not deploy to or modify a remote target machine.
- **Target machine:** no remote-target mutation is part of Prompt Kit acquisition.

## Safety summary

The acquisition workflow never runs `git reset`, `git clean`, force-push, branch deletion, or credential automation. The advanced GUI refuses unexpected origins, dirty worktrees, non-`main` branches, local-only commits, and divergence. Quick mode preserves those candidates and may select or create a separate safe canonical checkout instead. Generator outputs may not be written under `Candidates/` or `Active/`.

Use fast-forward-only updates. Do not run `git reset` to solve acquisition failures. Do not use `git reset` or `git clean` to make an unsafe candidate look clean. The tooling does not store credentials. Recovery and rollback mean preserving the existing checkout and using another safe destination, not destroying local work.

## Proof vocabulary

- **Documentation proof:** the documented files, links, controls, commands, and messages match tracked source.
- **Static/CI proof:** validators and safe command checks passed in CI.
- **Windows field proof:** a human successfully used the CMD and GUI on the intended Windows machine.
- **Operator acceptance:** the technician confirms the resulting site or generator workflow is usable for the real assignment.

Documentation and CI do not prove Windows GUI behavior and do not substitute for Windows field proof, physical mobile field acceptance, or operator acceptance. The responsive contract does not replace a technician's Windows mouse test.
