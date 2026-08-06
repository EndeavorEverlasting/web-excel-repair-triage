# Get the Latest Prompt Kit Website

## Source of truth

The canonical tracked website is:

```text
web/prompt-kit/index.html
```

The canonical public URL is:

```text
https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/
```

The release source is `main`. GitHub Pages, the Windows portable runtime, and CI previews are delivery surfaces generated from that release—not competing editable sites.

## Recommended Windows path: portable Favorites across upgrades

Download or retain `Open-Latest-PromptKit.cmd`, then double-click it.

The launcher:

1. resolves the deterministic local checkout path;
2. reuses the repository's safe clone/fast-forward acquisition implementation;
3. refuses dirty, divergent, wrong-origin, wrong-branch, or local-only work instead of resetting it;
4. validates exact `web\prompt-kit\index.html` parity;
5. generates `Outputs\prompt-kit-portable\index.html` from the canonical site plus the tracked Favorites portability runtime;
6. writes `Outputs\prompt-kit-portable\manifest.json` with source/runtime/artifact SHA-256 hashes;
7. validates that generated artifact;
8. serves it on loopback only with caching disabled;
9. opens the stable origin:

```text
http://127.0.0.1:8765/
```

The stable origin preserves the browser's existing `promptKit.favoritePromptIds.v1` storage when a later Prompt Kit version is installed. Ordinary same-browser upgrades therefore keep Favorites automatically.

The served site also exposes **Export Favorites** and **Import Favorites** using schema `prompt-kit-favorites/v1`. Export before clearing browser data, changing browser profiles, changing devices, or moving between the local and public origins. Import merges and deduplicates without deleting Favorites already saved at the destination.

## Advanced Windows acquisition GUI

Use `Acquire-Latest-PromptKit.cmd` when a technician needs to choose a destination or open the generator selection GUI. It provides **Open Prompt Kit website**, **Open generator selection GUI**, and **Get Latest and Open** while preserving the same fast-forward-only Git safety.

Advanced zero-dialog acquisition remains available with an explicit destination:

```text
Acquire-Latest-PromptKit.cmd -Quick -Destination "C:\path\to\web-excel-repair-triage"
```

That advanced path opens the canonical tracked file directly. Use `Open-Latest-PromptKit.cmd` for persistent Favorites and the portable runtime receipt.

## Existing checkout

To validate the tracked release:

```powershell
git fetch origin main --prune
git pull --ff-only origin main
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
```

To generate and validate the portable runtime manually:

```powershell
python scripts\serve_prompt_kit_portable.py --build-only
python scripts\validate_prompt_kit_portability.py --require-artifact --output Outputs\prompt-kit-portability-validation.json --summary
```

To open through the supported Windows route:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts\Open-LatestPromptKitPortable.ps1 -Destination (Get-Location).Path
```

Do not reset or clean a checkout containing local work merely to run the launcher. Preserve it or use a separate safe destination.

## Phone, tablet, or public browser

Open:

```text
https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/
```

The public origin has separate browser storage from `http://127.0.0.1:8765/`. Transfer Favorites with Export/Import when moving between them.

To keep the Prompt Kit one tap away:

- iPhone or iPad Safari: **Share** → **Add to Home Screen**.
- Android Chrome: browser menu → **Add to Home screen** or **Install app** when offered.

GitHub Pages must use GitHub Actions as the publishing source. `.github/workflows/prompt-kit-pages.yml` rebuilds and validates the canonical site before publishing `main`.

## ZIP and direct-file use

A downloaded repository ZIP contains `web/prompt-kit/index.html`, but direct `file://` origins may differ when the extracted path changes. That path is suitable for static inspection, not the preferred Favorites-preserving upgrade mechanism.

Do not search for arbitrary `index.html` files. In particular, do not treat `.venv\Lib\site-packages\...\index.html` or an unrelated `Outputs\...\index.html` as the Prompt Kit. The registered portable artifact is specifically resolved through `Outputs\prompt-kit-portable\manifest.json`.

## GitHub Actions artifacts

The Prompt Kit web workflow generates:

- `prompt-kit-current-preview` — canonical builder preview;
- `prompt-kit-portable-runtime` — portable site, hash manifest, and portability validation result.

These artifacts prove the workflow's generated output on one commit. They do not replace `main` or establish browser acceptance.

## Implementation ownership

- Prompt registries: `docs/prompts.json` plus registered extensions
- Canonical builder: `scripts/build_prompt_kit_registry.py`
- HTML renderer: `build_prompt_kit.py`
- Base browser behavior: `docs/prompt-kit.js`
- Favorites portability runtime: `docs/prompt-kit-favorites-portability.js`
- Portable generator/server: `scripts/serve_prompt_kit_portable.py`
- Portable PowerShell launcher: `scripts/Open-LatestPromptKitPortable.ps1`
- Windows entry point: `Open-Latest-PromptKit.cmd`
- Machine contract: `harness/contracts/prompt-kit-portability.v1.json`
- Human contract: `docs/PROMPT_KIT_PORTABILITY.md`
- Canonical tracked release: `web/prompt-kit/index.html`
- Portable generated site: `Outputs/prompt-kit-portable/index.html`
- Portable receipt: `Outputs/prompt-kit-portable/manifest.json`

Generated HTML is never the primary editable source. Repair tracked sources, run the registered builders and validators, and preserve exact proof boundaries.

## Proof boundary

Repository and CI validation can prove source wiring, exact canonical parity, stable-origin generation, receipt hashes, loopback/no-cache guardrails, and focused transfer logic. They cannot prove the user's browser retained Favorites through a real upgrade, completed download/import dialogs, restored another browser profile/device, or passed native Windows/mobile acceptance. Those require observed field proof.
