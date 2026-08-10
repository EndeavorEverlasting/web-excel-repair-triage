---
name: prompt-kit-browser-proof-cleanup
description: Safely classify and remove detached Prompt Kit browser-proof scratch directories without touching canonical repositories, browser profile data, or Favorites.
---

# Prompt Kit Browser-Proof Cleanup

## Trigger

Use when the operator supplies a `prompt-kit-browser-proof-*` path under the OS temp directory or asks what may be removed after Prompt Kit browser proof.

## Required inputs

- current repository checkout;
- optional exact scratch path;
- preview versus explicit deletion intent;
- minimum age requirement when deletion is requested.

## Procedure

1. Read `AGENTS.md`.
2. Read `harness/browser-proof-cleanup/manifest.v1.json` and `WORKFLOW.md`.
3. Run `scripts/Clear-PromptKitBrowserProofScratch.ps1` **without `-Apply` first**.
4. Confirm the candidate is a direct child of the OS temp root, matches the exact browser-proof regex, is not a reparse point, and contains `web/prompt-kit/index.html`.
5. Preserve every rejected candidate.
6. If deletion is explicitly requested, close browser tabs still using the file URL and rerun the exact target with `-Apply`.
7. Read the JSON receipt and report eligible/preserved/deleted/failed counts.
8. Do not claim browser site-data or Favorites cleanup.

## Commands

Preview:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\scripts\Clear-PromptKitBrowserProofScratch.ps1
```

Exact apply:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\scripts\Clear-PromptKitBrowserProofScratch.ps1 -TargetPath "<exact path>" -MinimumAgeMinutes 0 -Apply
```

## Expected output

`Outputs/prompt-kit-browser-proof-cleanup-report.json`

## Proof ceiling

Repository/static/CI proof plus the filesystem result recorded by the operator command. This skill does not prove browser localStorage, Favorites, or browser-profile cleanup.
