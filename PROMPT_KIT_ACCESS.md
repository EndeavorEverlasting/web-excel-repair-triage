# Get the Latest Prompt Kit Website

The canonical website is:

```text
web/prompt-kit/index.html
```

The release source is the repository's `main` branch. Do not treat an old feature branch, copied HTML file, or downloaded preview from an older run as the latest release.

## Fastest Windows path — one file, one button

Download `Acquire-Latest-PromptKit.cmd` from the repository and double-click it.

The launcher:

1. downloads its companion acquisition GUI from canonical `main` when the local script is absent;
2. clones `EndeavorEverlasting/web-excel-repair-triage` when the destination does not exist;
3. safely fast-forwards a clean local `main` checkout when it already exists;
4. refuses dirty, divergent, wrong-origin, or non-`main` checkouts instead of overwriting work;
5. validates the exact checked-in Prompt Kit;
6. opens `web/prompt-kit/index.html`.

This is the recommended technician path.

## Existing checkout

From a clean checkout already on `main`:

```powershell
git fetch origin main --prune
git pull --ff-only origin main
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
start web\prompt-kit\index.html
```

If the checkout contains local work, do not reset or clean it. Use `Acquire-Latest-PromptKit.cmd` with a separate destination, or create a separate worktree.

## Fresh clone

```powershell
git clone --branch main --single-branch https://github.com/EndeavorEverlasting/web-excel-repair-triage.git
cd web-excel-repair-triage
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
start web\prompt-kit\index.html
```

## Download ZIP — no Git commands

On the GitHub repository page:

1. choose **Code**;
2. choose **Download ZIP**;
3. extract the ZIP;
4. open `web/prompt-kit/index.html`.

The ZIP is a snapshot. Download it again when you need a newer release.

## GitHub Actions preview artifact

Every Prompt Kit web contract run builds the website from canonical source before checking the checked-in copy.

Open the latest successful **Prompt Kit web contracts** run for `main`, download the artifact named:

```text
prompt-kit-current-preview
```

Extract it and open `index.html`.

This is useful for inspecting the builder output without cloning, but `main:web/prompt-kit/index.html` remains the checked-in release surface.

## Rebuild and open locally

Windows double-click entry point:

```text
Build-PromptKitWebsite.cmd
```

Developer command:

```powershell
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html
start web\prompt-kit\index.html
```

Exact parity check without rewriting:

```powershell
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
```

## Where the website comes from

- Prompt registry: `docs/prompts.json` plus registered prompt extensions
- Combined registry builder: `scripts/build_prompt_kit_registry.py`
- HTML renderer: `build_prompt_kit.py`
- Browser behavior: `docs/prompt-kit.js`
- Checked-in release: `web/prompt-kit/index.html`
- Web usage notes: `web/README.md`
- Safe clone/update GUI: `scripts/Acquire-LatestPromptKit.ps1`
- One-click acquisition bootstrap: `Acquire-Latest-PromptKit.cmd`

Generated HTML is not the source of truth. Repair canonical sources, rebuild, validate parity, then commit the generated website.

## Current browsing contract

The released site must keep these behaviors together:

- single-click prompt card = copy;
- double-click prompt card = expand;
- click outside or press Escape = close detail without losing active filters;
- every visible prompt category heading has **Top** on the left and **Bottom** on the right;
- **All Categories** shows each category exactly once;
- choosing one category shows only that category and its matching prompts;
- **All Types** or one type may be selected independently;
- prompts inside every visible category remain in numeric prompt sequence even when IDs have gaps.
