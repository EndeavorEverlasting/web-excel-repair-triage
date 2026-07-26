# Get the Latest Prompt Kit Website

Use this page when somebody asks how to obtain or refresh the current Prompt Kit website.

## Instruction to send to most users

> Download or double-click `Open-Latest-PromptKit.cmd`. It finds or creates a safe Prompt Kit checkout, syncs canonical `main`, validates the exact site, and opens `web\prompt-kit\index.html` without asking the user to choose a path.

The quick launcher resolves the actual Windows Desktop and bounded OneDrive development roots, including an existing `OG Laptop Backup\Desktop\dev` layout. It verifies repository identity by Git origin. Unsafe dirty, divergent, wrong-branch, or wrong-origin work is preserved rather than overwritten.

## Advanced technician GUI

`Acquire-Latest-PromptKit.cmd` remains tracked and supported. In the **Get Latest Prompt Kit** window, confirm the **Destination folder**, select **Open Prompt Kit website**, and click **Get Latest and Open**. Wait for `Repository and Prompt Kit validation passed.` The tool opens the current validated website automatically.

Download the advanced launcher from [`../Acquire-Latest-PromptKit.cmd`](../Acquire-Latest-PromptKit.cmd). For screenshots, first-time setup, and failure recovery, use the [technician acquisition tutorial](TECHNICIAN_PROMPT_KIT_ACQUISITION_TUTORIAL.md).

## Canonical website

There is exactly one canonical Prompt Kit website in the repository:

```text
web\prompt-kit\index.html
```

Other files named `index.html` are not the Prompt Kit. In particular, do not distribute or open these as the Prompt Kit:

- `.venv\Lib\site-packages\...\index.html` — third-party Python package files;
- `Outputs\...\index.html` — generated reports, dashboards, or proof artifacts;
- copied files outside the canonical checkout unless their source commit and validation are known.

Users do not need to search the repository for `index.html`; both launchers validate the canonical file before opening it.

## What the quick launcher does

### First use

When no safe canonical checkout exists, the launcher:

1. resolves the Windows Desktop and available OneDrive roots without a person-specific path;
2. creates the selected `dev` directory when it is missing;
3. clones the canonical repository and branch `main`;
4. verifies required Prompt Kit and generator files;
5. checks that `web\prompt-kit\index.html` exactly matches the tracked prompt registries and builder;
6. opens the website only after validation passes.

### Later use

When candidate repositories already exist, the quick launcher:

1. verifies each candidate by canonical origin;
2. preserves dirty worktrees, wrong branches, local-only commits, or divergence and continues to another candidate when possible;
3. fetches `origin/main` and fast-forwards only on a safe candidate;
4. validates the canonical website;
5. opens `web\prompt-kit\index.html`.

It does not reset, clean, overwrite, rebase, force-push, delete branches, or discard work.

The advanced GUI retains the stricter single-destination behavior: if the selected checkout is unsafe, it reports that condition instead of selecting a different location automatically.

## Success messages

A successful shared acquisition run includes:

```text
Repository and Prompt Kit validation passed.
Opening Prompt Kit website.
```

The advanced GUI's final dialog says:

```text
The latest validated Prompt Kit is ready.
```

## When acquisition refuses or preserves a checkout

Treat the safety result as evidence. Do not bypass it with reset or cleanup commands.

- **Dirty or untracked files:** preserve or commit the work first; quick mode may select another safe checkout.
- **Not on `main`:** preserve the branch; quick mode may select another safe checkout.
- **Local commits or divergence:** preserve them and use another safe checkout or escalate to a developer.
- **Unexpected origin:** do not treat that directory as this repository.
- **Exact-output mismatch:** do not distribute the website as current; report the failure.

## Mobile usage

The website uses the same prompt/filter model on desktop and mobile. On a narrow/touch layout:

- tap the **AI Harness Prompt Kit** title to reset search and all filters to the original view;
- tap **Open** on a prompt card to inspect it without double-tap timing;
- **Copy** remains explicit and touch-sized;
- library, category, and type filters remain the same controls and become touch-scrollable where necessary;
- prompt cards use one column;
- prompt detail and the reference panel expand to the mobile viewport;
- category **Top** and **Bottom** anchors remain available.

## Proof boundary

A successful launcher run proves that the selected local checkout was safely acquired or updated and that the canonical website matches the tracked builder output. CI documentation and responsive-source checks do not prove Windows process launch, live OneDrive state, physical phone/tablet ergonomics, clipboard permission, or touch behavior on a particular device. Those remain Windows/mobile field acceptance checks.
