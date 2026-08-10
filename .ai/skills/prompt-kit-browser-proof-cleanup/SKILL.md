---
name: prompt-kit-browser-proof-cleanup
description: Safely classify and remove detached Prompt Kit browser-proof scratch directories without touching canonical repositories, browser profile data, or Favorites.
---

# Prompt Kit Browser-Proof Cleanup

## Trigger

Use when the operator supplies a `prompt-kit-browser-proof-*` path under the OS temp directory or asks to classify/remove detached Prompt Kit browser-proof copies.

## Required inputs

- current repository checkout and governance;
- optional exact scratch path;
- preview versus explicit deletion intent;
- minimum age requirement when deletion is requested.

## Outputs

- classified candidate list;
- retained prior receipt when the stable report already exists;
- `Outputs/prompt-kit-browser-proof-cleanup-report.json`;
- exact eligible/preserved/deleted/failed counts and proof ceiling.

## Procedure

1. Read `AGENTS.md`, `harness/browser-proof-cleanup/manifest.v1.json`, and `harness/browser-proof-cleanup/WORKFLOW.md`.
2. Run `scripts/Clear-PromptKitBrowserProofScratch.ps1` without `-Apply` first.
3. Confirm each candidate is a direct child of the OS temp root, matches the exact browser-proof regex, is not a reparse point, contains `web/prompt-kit/index.html`, and meets minimum age.
4. Preserve every rejected candidate.
5. If deletion is explicitly requested, close browser tabs still using the file URL and rerun only the exact eligible target with `-Apply`.
6. Read the JSON receipt and report eligible/preserved/deleted/failed counts.
7. Do not claim browser site-data or Favorites cleanup.

## Guardrails

- Preview is the default; `-Apply` is explicit.
- Never widen an exact target into wildcard `%TEMP%` cleanup.
- Never delete a canonical checkout, `Outputs/` evidence, a reparse point, an unexpected name, or a directory missing the Prompt Kit marker.
- Never clear browser cookies/cache/history/profile, localStorage, or Prompt Kit Favorites.
- Preserve the previous stable cleanup receipt under `Outputs/backups/` before replacing it.

## Validation

```powershell
python scripts/validate_prompt_kit_browser_proof_cleanup.py --summary
python -m unittest tests.test_prompt_kit_browser_proof_cleanup_harness -v
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\scripts\Clear-PromptKitBrowserProofScratch.ps1
```

Exact apply after a successful preview:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\scripts\Clear-PromptKitBrowserProofScratch.ps1 -TargetPath "<exact path>" -MinimumAgeMinutes 0 -Apply
```

## Proof ceiling

Repository/static/CI proof plus the filesystem result recorded by the operator command. This skill does not prove browser localStorage, Favorites, or browser-profile cleanup.
