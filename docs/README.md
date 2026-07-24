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
| `Acquire-Latest-PromptKit.cmd` | Opens the mouse-accessible acquisition GUI. Clones `main` when absent or fast-forwards a clean canonical `main` checkout when present, validates the site and generators, then opens the selected surface. |
| `Run-PromptKitGenerator.cmd` | Opens the generator-selection GUI for registered generators and their tracked options. |
| `Build-PromptKitWebsite.cmd` | Rebuilds the canonical site with safe defaults, validates exact output, and opens the result. |

## Platform boundaries

- **Windows technician workstation:** the acquisition and generator GUIs are intended to run here.
- **Browser:** the Prompt Kit is a local static HTML file; no web server is required for normal use.
- **Linux or CI:** run validators and builders, but do not claim Windows GUI or mouse proof.
- **Administrator box:** verify Git, Python, policy, network access, and CI; do not automate credentials.
- **Target machine:** this workflow does not deploy to or modify a remote target machine.

## Safety summary

The acquisition workflow never runs `git reset`, `git clean`, force-push, branch deletion, or credential automation. It refuses unexpected origins, dirty worktrees, non-`main` branches, local-only commits, and divergence. Generator outputs may not be written under `Candidates/` or `Active/`.

## Proof vocabulary

- **Documentation proof:** the documented files, links, controls, commands, and messages match tracked source.
- **Static/CI proof:** validators and safe command checks passed in CI.
- **Windows field proof:** a human successfully used the CMD and GUI on the intended Windows machine.
- **Operator acceptance:** the technician confirms the resulting site or generator workflow is usable for the real assignment.

Documentation and CI do not substitute for Windows field proof or operator acceptance.