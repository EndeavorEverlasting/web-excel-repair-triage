# Get the Latest Prompt Kit Website

Use this page when somebody asks how to obtain or refresh the current Prompt Kit website.

## Instruction to send to most Windows users

> Download or double-click `Open-Latest-PromptKit.cmd`. It finds or creates a safe Prompt Kit checkout, syncs canonical `main`, validates the exact tracked site, generates a hash-receipted portable copy, and opens `http://127.0.0.1:8765/` without asking the user to choose a path.

That stable loopback origin is intentional. The browser keeps `promptKit.favoritePromptIds.v1` at the same origin when a newer repository/site version is installed, so ordinary upgrades retain Favorites automatically. Browser caching is disabled so a new run serves the newly generated version rather than an old cached page.

The portable website also provides **Export Favorites** and **Import Favorites**. Use them before clearing browser data, switching browser profiles, moving devices, or abandoning an older origin. The backup schema is `prompt-kit-favorites/v1`.

The quick launcher resolves the actual Windows Desktop and bounded OneDrive development roots, including an existing `OG Laptop Backup\Desktop\dev` layout. It verifies repository identity by Git origin. Unsafe dirty, divergent, wrong-branch, or wrong-origin work is preserved rather than overwritten.

## Advanced technician GUI

`Acquire-Latest-PromptKit.cmd` remains tracked and supported. In the **Get Latest Prompt Kit** window, confirm the **Destination folder**, select **Open Prompt Kit website**, and click **Get Latest and Open**. Wait for `Repository and Prompt Kit validation passed.` The advanced tool opens the current validated tracked website automatically.

Download the advanced launcher from [`../Acquire-Latest-PromptKit.cmd`](../Acquire-Latest-PromptKit.cmd). For screenshots, first-time setup, and failure recovery, use the [technician acquisition tutorial](TECHNICIAN_PROMPT_KIT_ACQUISITION_TUTORIAL.md).

## Canonical tracked site and portable runtime artifact

There is exactly one canonical tracked Prompt Kit website in the repository:

```text
web\prompt-kit\index.html
```

The standard quick launcher reads that exact file and the tracked portability runtime, then generates:

```text
Outputs\prompt-kit-portable\index.html
Outputs\prompt-kit-portable\manifest.json
```

The manifest records the source, runtime, and generated-artifact SHA-256 hashes plus the loopback/cache/protected-input guardrails. The generated `Outputs` copy is a runtime delivery artifact, not a second editable source of truth.

Other files named `index.html` are not automatically the Prompt Kit. In particular:

- `.venv\Lib\site-packages\...\index.html` — third-party Python package files;
- `Outputs\...\index.html` — generated reports or runtime artifacts unless resolved through the registered portability manifest;
- copied files outside the canonical checkout unless their source commit and validation are known.

Users do not need to search the repository for `index.html`; the supported launchers resolve and validate the correct surface.

## What the quick launcher does

### First use

When the deterministic destination is absent, the launcher:

1. resolves the Windows destination without a person-specific path;
2. clones canonical `main` through the shared safe acquisition implementation;
3. verifies required Prompt Kit, portability, and generator files;
4. checks that `web\prompt-kit\index.html` exactly matches the tracked registries and builder;
5. generates the portable artifact and receipt under `Outputs\prompt-kit-portable`;
6. validates exact source/runtime composition and hashes;
7. starts a loopback-only no-cache server at `http://127.0.0.1:8765/`;
8. opens the stable origin only after validation passes.

### Later use

When the destination already exists, the launcher:

1. verifies canonical origin, clean worktree, `main`, and no local-only commits or divergence;
2. fetches `origin/main` and fast-forwards only;
3. validates canonical site parity;
4. regenerates and validates the portable artifact;
5. starts or reuses the healthy stable-origin server;
6. opens the upgraded site with the same browser-storage origin.

It does not reset, clean, overwrite, rebase, force-push, delete branches, or discard work.

The advanced GUI retains its single-destination behavior: if the selected checkout is unsafe, it reports that condition instead of overwriting it.

## Success evidence

The portable path prints:

```text
PROMPT_KIT_PORTABLE_ARTIFACT=<resolved Outputs path>
PROMPT_KIT_PORTABLE_MANIFEST=<resolved manifest path>
PROMPT_KIT_PORTABLE_URL=http://127.0.0.1:8765/
```

The advanced acquisition path continues to report:

```text
Repository and Prompt Kit validation passed.
Opening Prompt Kit website.
```

## When acquisition refuses or preserves a checkout

Treat the safety result as evidence. Do not bypass it with reset or cleanup commands.

- **Dirty or untracked files:** preserve or commit the work first.
- **Not on `main`:** preserve the branch; use another safe checkout.
- **Local commits or divergence:** preserve them and use another safe checkout or escalate.
- **Unexpected origin:** do not treat that directory as this repository.
- **Exact-output mismatch:** do not distribute the site as current; repair canonical source or regeneration drift.
- **Port 8765 already used by another process:** stop or reconfigure that process, or run the tracked PowerShell launcher with a different explicit port; the server never binds externally.

## Mobile and cross-device use

The public GitHub Pages URL remains useful for phone/tablet access:

```text
https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/
```

Favorites are origin-specific. Export from the old origin and import into the public/mobile origin when transferring the collection. The same JSON backup may be used when moving browser profiles or devices.

## Validation

```powershell
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
python scripts\serve_prompt_kit_portable.py --build-only
python scripts\validate_prompt_kit_portability.py --require-artifact --output Outputs\prompt-kit-portability-validation.json --summary
python -m unittest tests.test_prompt_kit_portability -v
```

## Proof boundary

Static repository checks prove the policy, source, generator, exact runtime composition, receipt hashes, and launcher wiring. They do not prove an actual browser retained Favorites across a live upgrade, completed a download/file-picker flow, restored another profile/device, or accepted the touch layout. Those remain Windows/browser/mobile field-acceptance gates.
