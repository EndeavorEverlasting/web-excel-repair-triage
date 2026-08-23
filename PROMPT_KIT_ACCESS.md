# Get the Latest Prompt Kit Website

<!-- PROMPT_KIT_FAST_PATH_START -->
## Choose the easiest path

| Device / need | Do this |
|---|---|
| Browser on any computer | Open **https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/** |
| Phone / tablet / install / QR | Open **https://endeavoreverlasting.github.io/web-excel-repair-triage/** |
| Windows Favorites-preserving local app | Download **https://raw.githubusercontent.com/EndeavorEverlasting/web-excel-repair-triage/main/Open-Latest-PromptKit.cmd** and double-click it |
| No Git client | Download **https://github.com/EndeavorEverlasting/web-excel-repair-triage/archive/refs/heads/main.zip** and open `web/prompt-kit/index.html` after extraction |
| Git user | `git clone --branch main --single-branch https://github.com/EndeavorEverlasting/web-excel-repair-triage.git` |

Normal browser/phone users should prefer the public URL. The Windows CMD path adds a stable local origin and portable Favorites while preserving the same canonical `main` release. ZIP and clone are fallback acquisition paths, not prerequisites for using the web app.
<!-- PROMPT_KIT_FAST_PATH_END -->

The canonical checked-in website is:

```text
web/prompt-kit/index.html
```

The canonical public browser URL is:

```text
https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/
```

The release source is the repository's `main` branch. GitHub Pages and the Windows portable runtime are delivery surfaces generated from that exact release, not competing editable Prompt Kits.

## Phone, tablet, or any browser

After GitHub Pages is enabled for this repository and the `Prompt Kit GitHub Pages` workflow has deployed `main`, open:

```text
https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/
```

No repository clone, ZIP extraction, Git client, Python installation, PowerShell, or local web server is required for normal browser use.

To keep the Prompt Kit one tap away:

- iPhone or iPad Safari: open the public URL, use **Share**, choose **Add to Home Screen**, then choose **Add**.
- Android Chrome: open the public URL, use the browser menu, then choose **Add to Home screen** or **Install app** when that option is offered.

The home-screen shortcut opens the same responsive Prompt Kit used on desktop. It does not create a separate prompt database or bypass the `main` release source.

### One-time repository publishing gate

GitHub Pages must use GitHub Actions as its publishing source:

1. open the repository on GitHub;
2. choose **Settings**;
3. under **Code and automation**, choose **Pages**;
4. under **Build and deployment**, set **Source** to **GitHub Actions**.

After that one-time repository setting is enabled, `.github/workflows/prompt-kit-pages.yml` automatically rebuilds and deploys the canonical Prompt Kit when relevant files land on `main`. Pull requests run the Pages build contract but do not deploy.

The deployment workflow fails closed before publishing if the checked-in release no longer matches `scripts/build_prompt_kit_registry.py`.

## Fastest Windows path — one file, no dialog

Download `Open-Latest-PromptKit.cmd` and double-click it.

The quick launcher now treats the Prompt Kit like a local app while retaining the repository's existing safety rules:

1. if the CMD is already inside the canonical tracked checkout, it reuses that checkout; otherwise it resolves the Windows Desktop and uses exactly `Desktop\dev\web-excel-repair-triage`, independent of the folder where the CMD was downloaded;
2. it reuses the existing safe acquisition functions and canonical `main` origin;
3. an existing destination must be clean, on `main`, and fast-forwardable; a missing canonical destination is cloned;
4. dirty, divergent, wrong-branch, wrong-origin, local-only, or occupied canonical paths are preserved and refused rather than reset, overwritten, or bypassed with `web-excel-repair-triage-latest[-N]` sibling clones;
5. `web\prompt-kit\index.html` must exactly match the canonical builder;
6. `scripts\serve_prompt_kit_portable.py` generates `Outputs\prompt-kit-portable\index.html` from the canonical site plus the tracked portability runtime;
7. `Outputs\prompt-kit-portable\manifest.json` records source/runtime/artifact SHA-256 evidence;
8. the portable artifact is validated before launch;
9. a loopback-only, no-cache server opens the stable origin:

```text
http://127.0.0.1:8765/
```

That stable origin preserves the browser's `promptKit.favoritePromptIds.v1` state across ordinary repository/site upgrades. The served runtime also exposes **Export Favorites** and **Import Favorites** using schema `prompt-kit-favorites/v1`.

Export before clearing browser data, changing browser profiles/devices, or moving between the public GitHub Pages origin and the local loopback origin. Import merges and deduplicates; it does not delete Favorites already saved at the destination. Legacy browser keys are merged with current Favorites, malformed IDs are rejected or sanitized, and well-formed IDs not present in the current release remain portable for future versions.

A copy of `Open-Latest-PromptKit.cmd` may live outside the repository. Its download directory is never treated as an implicit checkout root; normal automatic acquisition still resolves the single Desktop `dev` checkout.

## Canonical Windows workstation layout

Normal Windows source work uses one predictable repository location:

```text
C:\Users\<user>\Desktop\dev\web-excel-repair-triage
```

The launcher resolves the actual Windows Desktop through the operating system and appends `dev\web-excel-repair-triage`. This also handles a redirected Desktop without teaching agents to search unrelated OneDrive backup trees or invent new sibling repository names.

Automatic Prompt Kit acquisition must **not**:

- create `web-excel-repair-triage-latest`, `web-excel-repair-triage-latest-2`, or similar persistent sibling clones;
- derive a repository destination from the folder where a downloaded CMD happens to live;
- leave persistent source checkouts or browser-proof website copies under arbitrary `%TEMP%`, Downloads, or ad-hoc proof directories.

Repository-owned generated local artifacts belong under `Outputs/`. CI may use its own ephemeral runner temp directory because the runner is disposable; that is not a workstation checkout convention.

## Advanced Windows acquisition GUI

Use `Acquire-Latest-PromptKit.cmd` when a technician needs to choose a destination or open the generator selection GUI.

It opens **Get Latest Prompt Kit**, where the operator can choose **Open Prompt Kit website** or **Open generator selection GUI**, then select **Get Latest and Open**.

The advanced GUI defaults to the Windows Desktop `dev` root and the canonical repository folder. It no longer searches backup/OneDrive trees or silently creates `-latest` copies when the canonical path is occupied. An explicitly supplied `-Destination` remains an operator override and should normally remain under the workstation's Desktop `dev` folder:

```text
Acquire-Latest-PromptKit.cmd -Quick -Destination "C:\Users\<user>\Desktop\dev\web-excel-repair-triage"
```

Use `Open-Latest-PromptKit.cmd` for the stable-origin Favorites-preserving app experience. Both paths preserve the same no-reset/no-force/no-silent-discard Git posture.

## Existing checkout

From a clean checkout already on `main`, validate the canonical release:

```powershell
git fetch origin main --prune
git pull --ff-only origin main
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
```

Build and validate the portable runtime manually:

```powershell
python scripts\serve_prompt_kit_portable.py --build-only
python scripts\validate_prompt_kit_portability.py --require-artifact --output Outputs\prompt-kit-portability-validation.json --summary
```

To launch that validated checkout through the supported stable origin:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts\Open-LatestPromptKitPortable.ps1 -Destination (Get-Location).Path
```

If the canonical checkout contains local work, do not reset or clean it merely to run the Prompt Kit, and do not let automation create a second `-latest` repository beside it. Preserve/commit the work first, or deliberately create an isolated Git worktree under the Desktop `dev` workspace when a separate writing lane is actually required.

## Fresh clone

On Windows, make the canonical destination explicit:

```powershell
$Repo = Join-Path ([Environment]::GetFolderPath([Environment+SpecialFolder]::Desktop)) 'dev\web-excel-repair-triage'
git clone --branch main --single-branch https://github.com/EndeavorEverlasting/web-excel-repair-triage.git $Repo
Set-Location -LiteralPath $Repo
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
```

On Windows, run `Open-Latest-PromptKit.cmd` from there for the stable-origin portable experience.

## Download ZIP — no Git commands

On the GitHub repository page:

1. choose **Code**;
2. choose **Download ZIP**;
3. extract the ZIP;
4. open `web/prompt-kit/index.html` for static/direct use.

The ZIP is a snapshot. Direct `file://` origins can change with extraction paths, so ZIP/direct-file use is not the preferred Favorites-preserving upgrade mechanism.

## GitHub Actions preview artifacts

Every Prompt Kit web contract run builds the website from canonical source before checking the checked-in copy.

The workflow exposes:

```text
prompt-kit-current-preview
prompt-kit-portable-runtime
```

`prompt-kit-current-preview` is the canonical builder preview. `prompt-kit-portable-runtime` contains the generated stable-origin artifact, its SHA-256 manifest, and portability validation output. Neither artifact replaces `main` as the source of truth. GitHub-hosted runner temp paths are ephemeral CI evidence and must not be copied into the workstation as another persistent Prompt Kit checkout.

## Rebuild and open locally

Windows canonical builder entry point:

```text
Build-PromptKitWebsite.cmd
```

Developer command:

```powershell
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html
```

Exact parity check without rewriting:

```powershell
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
```

## Where the website comes from

- Prompt registry: `docs/prompts.json` plus registered prompt extensions
- Combined registry builder: `scripts/build_prompt_kit_registry.py`
- HTML renderer: `build_prompt_kit.py`
- Base browser behavior and Favorites storage owner: `docs/prompt-kit.js`
- Guided questionnaire: `docs/prompt-kit-guided-recommendations.js`
- Interaction polish/action rail plus compact browsing controls: `docs/prompt-kit-polish.js`
- Favorites transfer runtime: `docs/prompt-kit-favorites-portability.js`
- Checked-in canonical release: `web/prompt-kit/index.html`
- Portable generated artifact: `Outputs/prompt-kit-portable/index.html`
- Portable receipt: `Outputs/prompt-kit-portable/manifest.json`
- Portable builder/server: `scripts/serve_prompt_kit_portable.py`
- Portable launcher: `scripts/Open-LatestPromptKitPortable.ps1`
- Public deployment workflow: `.github/workflows/prompt-kit-pages.yml`
- Public share path: `https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/`
- Web usage notes: `web/README.md`
- Zero-dialog normal-user Windows launcher: `Open-Latest-PromptKit.cmd`
- Advanced acquisition bootstrap: `Acquire-Latest-PromptKit.cmd`
- Shared safe acquisition implementation: `scripts/Acquire-LatestPromptKit.ps1`

Generated HTML is not the primary editable source. Repair canonical tracked sources, rebuild, validate parity, and preserve the proof boundary between the checked-in site and the gitignored portable runtime.

## Desktop and mobile browsing contract

The desktop and mobile layouts use the same prompts, filters, renderers, and action functions.

- Tap/click the **AI Harness Prompt Kit** title to reset the temporary browsing state while preserving Favorites.
- Use **Hide filters** to collapse the search/category/section/type filter chrome and maximize the screen area available to prompt cards; **Show filters** restores it.
- Press **4** or use the header **Favorites** shortcut to clear transient search/type/category restrictions and show the complete saved Favorites list. Favorites remain persistent; they are not promoted ahead of normal chronological library order unless this explicit Favorites view is selected.
- **Doctrine** remains available in the header and moves to keyboard shortcut **5**.
- Use the glowing **Tutorial · Find My Prompt** control when you do not know which prompt to choose; it reuses the same search/synonym/registry logic.
- Single click or tap on a prompt card copies the prompt; the current polish layer gives green clipboard confirmation.
- Double-click expands on desktop; touch users receive explicit **Open**.
- Favorite / Open / Copy occupy one guarded action rail rather than overlapping absolute coordinates.
- Library, category, type, search, Favorites, and collapsible sections remain the same model on narrow screens.
- Every visible prompt category heading retains **Top** and **Bottom** navigation without clearing active filters.

Physical browser persistence through a real upgrade, file-picker/download behavior, cross-profile/device transfer, phone/tablet ergonomics, clipboard permission behavior, live GitHub Pages publication, and Windows launch remain field-acceptance checks after repository validation passes.
