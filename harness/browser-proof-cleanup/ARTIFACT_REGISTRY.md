# Prompt Kit Browser-Proof Scratch — Artifact Registry

## `prompt-kit-browser-proof-cleanup-report`

**Path:** `Outputs/prompt-kit-browser-proof-cleanup-report.json`

**Producer:** `scripts/Clear-PromptKitBrowserProofScratch.ps1`

**Purpose:** Durable receipt describing scratch candidates, safety classification, preview/apply mode, and deletion outcomes.

**Naming:** The default report path is stable so the newest operator run is easy to find. Historical retention is operator-owned; this harness does not create timestamped repository clutter automatically.

**Required fields:** schema version, generated UTC timestamp, mode, system temp root, minimum age, optional target path, candidate records, eligible/preserved/deleted/failed counts, and proof ceiling.

## Ephemeral scratch inputs

`%TEMP%\prompt-kit-browser-proof-<hex>\`

These directories are cleanup inputs, not durable repository artifacts. They are never canonical Prompt Kit output and must not be committed.

## Canonical surfaces outside this cleanup registry

- `web/prompt-kit/index.html`
- `Outputs/prompt-kit-portable/index.html`
- GitHub Pages deployment

The cleanup runner must not mutate those surfaces.
