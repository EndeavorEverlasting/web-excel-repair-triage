# Get the Latest Prompt Kit Website

Use this page when somebody asks how to obtain or refresh the current Prompt Kit website.

## Instruction to send to users

> Download or double-click `Acquire-Latest-PromptKit.cmd`. In the **Get Latest Prompt Kit** window, confirm the destination, select **Open Prompt Kit website**, and click **Get Latest and Open**. Wait for `Repository and Prompt Kit validation passed.` The tool will open the current validated website automatically.

Download the tracked launcher from [`Acquire-Latest-PromptKit.cmd`](../Acquire-Latest-PromptKit.cmd). For screenshots, first-time setup, and failure recovery, use the [technician acquisition tutorial](TECHNICIAN_PROMPT_KIT_ACQUISITION_TUTORIAL.md).

## Canonical website

There is exactly one canonical Prompt Kit website in the repository:

```text
web\prompt-kit\index.html
```

Other files named `index.html` are not the Prompt Kit. In particular, do not distribute or open these as the Prompt Kit:

- `.venv\Lib\site-packages\...\index.html` — third-party Python package files;
- `Outputs\...\index.html` — generated reports, dashboards, or proof artifacts;
- copied files outside the canonical checkout unless their source commit and validation are known.

The acquisition launcher validates the canonical file before opening it, so users do not need to search the repository for `index.html`.

## What the launcher does

### First use

When the destination repository does not exist, the launcher:

1. clones the canonical repository and branch `main`;
2. verifies the required Prompt Kit and generator files;
3. checks that `web\prompt-kit\index.html` exactly matches the tracked prompt registries and builder;
4. opens the website only after validation passes.

### Later use

When the repository already exists, the launcher:

1. verifies that the checkout uses the canonical origin;
2. refuses dirty worktrees, the wrong branch, local-only commits, or divergence;
3. fetches `origin/main` and fast-forwards only;
4. validates the canonical website;
5. opens `web\prompt-kit\index.html`.

It does not reset, clean, overwrite, rebase, force-push, delete branches, or discard work.

## Success messages

A successful update ends with:

```text
Repository and Prompt Kit validation passed.
Opening Prompt Kit website.
```

The final dialog says:

```text
The latest validated Prompt Kit is ready.
```

## When the launcher refuses to update

Treat a refusal as a safety result. Do not bypass it with reset or cleanup commands.

- **Dirty or untracked files:** preserve or commit the work first.
- **Not on `main`:** ask the branch owner to finish and return the checkout safely.
- **Local commits or divergence:** escalate to a developer so the commits are preserved.
- **Unexpected origin:** confirm that the selected checkout is the canonical repository.
- **Exact-output mismatch:** do not distribute the website as current; report the failure.

## Proof boundary

A successful launcher run proves that the local checkout was safely acquired or updated and that the canonical website matches the tracked builder output. CI documentation checks alone do not prove that the Windows GUI, browser opening, network access, or authentication worked on a particular workstation.