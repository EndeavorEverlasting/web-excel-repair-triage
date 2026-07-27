# Get the Latest Prompt Kit Website

The canonical website is:

```text
web/prompt-kit/index.html
```

The release source is the repository's `main` branch. Do not treat an old feature branch, copied HTML file, or preview from an older run as the latest release.

## Fastest Windows path — one file, no dialog

Download `Open-Latest-PromptKit.cmd` and double-click it.

The quick launcher uses a deterministic destination derived from the launcher's own folder:

1. if the launcher is inside a tracked Prompt Kit checkout, that checkout is used;
2. otherwise a Desktop copy targets `Desktop\dev\web-excel-repair-triage` beside that launcher;
3. the resolved destination is passed explicitly to the shared safe acquisition implementation, so normal quick-open does not depend on broad path discovery;
4. an existing destination is verified by canonical Git origin, clean worktree, `main` branch, and fast-forward-only history;
5. a missing destination is cloned from canonical `main`;
6. dirty, divergent, wrong-branch, or wrong-origin destinations are preserved and refused rather than reset or overwritten;
7. `web\prompt-kit\index.html` is validated against the tracked Prompt Kit builder output;
8. the validated website opens automatically.

A copy of `Open-Latest-PromptKit.cmd` may live outside the repository. When the tracked bootstrap is not beside it, it downloads the current `Acquire-Latest-PromptKit.cmd` from canonical `main`, which in turn downloads the shared PowerShell implementation when necessary.

This is the recommended normal-user path.

## Advanced Windows acquisition GUI

Use `Acquire-Latest-PromptKit.cmd` when a technician needs to choose a destination or open the generator selection GUI.

It opens **Get Latest Prompt Kit**, where the operator can choose **Open Prompt Kit website** or **Open generator selection GUI**, then select **Get Latest and Open**.

The advanced GUI may derive a default development root from the Windows Desktop and available OneDrive locations, including an existing `OG Laptop Backup\Desktop\dev` tree. The path helper is required to accept an initially empty collection, and that condition is covered by CI.

The same bootstrap also supports zero-dialog mode with an explicit destination:

```text
Acquire-Latest-PromptKit.cmd -Quick -Destination "C:\path\to\web-excel-repair-triage"
```

Both entry points preserve the same safety rules: no reset, clean, force-push, branch deletion, or silent discard of local work.

## Existing checkout

From a clean checkout already on `main`:

```powershell
git fetch origin main --prune
git pull --ff-only origin main
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
start web\prompt-kit\index.html
```

If the canonical Desktop checkout contains local work, do not reset or clean it. Preserve that work first, or use the advanced acquisition GUI with a deliberately separate destination.

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

Open the latest successful **Prompt Kit web contracts** run for `main`, download:

```text
prompt-kit-current-preview
```

Extract it and open `index.html`. This is useful for inspecting builder output without cloning, but `main:web/prompt-kit/index.html` remains the checked-in release surface.

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
- Browser behavior and responsive layer: `docs/prompt-kit.js`
- Checked-in release: `web/prompt-kit/index.html`
- Web usage notes: `web/README.md`
- Zero-dialog normal-user launcher: `Open-Latest-PromptKit.cmd`
- Advanced acquisition bootstrap: `Acquire-Latest-PromptKit.cmd`
- Shared safe acquisition implementation: `scripts/Acquire-LatestPromptKit.ps1`

Generated HTML is not the source of truth. Repair canonical sources, rebuild, validate parity, then commit the generated website.

## Desktop and mobile browsing contract

The desktop and mobile layouts use the same prompts, filters, renderers, and action functions.

- Tap/click the **AI Harness Prompt Kit** title to reset to the original All / All Categories / All Types view, clear search, close detail/reference surfaces, and return to the top.
- Single click or tap on a prompt card still copies the prompt.
- Double-click still expands on desktop; touch users also receive an explicit **Open** button so expansion never depends on double-tap timing.
- The explicit **Copy** button remains available and becomes touch-sized on mobile.
- **All Categories** shows each visible category exactly once; a selected category shows only its matching prompts.
- **All Types** or one concrete type may be selected independently.
- Prompts remain in numeric sequence inside each visible category even when IDs have gaps.
- Library, category, and type controls remain the same filters; on narrow screens they become horizontal touch rails rather than a second navigation model.
- Prompt cards become one column on narrow screens.
- Prompt detail and the reference panel use the mobile viewport while retaining the same underlying actions.
- Every visible prompt category heading retains **Top** on the left and **Bottom** on the right without clearing active filters.

Physical phone/tablet ergonomics, clipboard permission behavior, live filesystem state, and Windows browser launch remain field-acceptance checks after repository validation passes.
