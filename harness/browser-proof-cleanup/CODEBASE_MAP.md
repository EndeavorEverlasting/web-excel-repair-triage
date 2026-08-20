# Prompt Kit Browser-Proof Scratch — Codebase Map

## Purpose

This harness governs detached Prompt Kit browser-proof scratch directories such as `%LOCALAPPDATA%\Temp\prompt-kit-browser-proof-<hex>\web\prompt-kit\index.html`. These directories are disposable browser-proof copies. They are not the canonical repository checkout, the GitHub Pages site, or the portable loopback runtime.

## Relevant repository structure

- `AGENTS.md` — repository governance authority.
- `web/prompt-kit/index.html` — canonical checked-in Prompt Kit website.
- `scripts/Acquire-LatestPromptKit.ps1` — canonical Windows acquisition/update route.
- `scripts/Open-LatestPromptKitPortable.ps1` and `scripts/serve_prompt_kit_portable.py` — stable loopback runtime.
- `harness/browser-proof-cleanup/` — this scratch-lifecycle harness.
- `scripts/Clear-PromptKitBrowserProofScratch.ps1` — preview/apply cleanup entry point.
- `scripts/validate_prompt_kit_browser_proof_cleanup.py` — completeness and safety validator.
- `tests/test_prompt_kit_browser_proof_cleanup_harness.py` — regression contract.
- `Outputs/prompt-kit-browser-proof-cleanup-report.json` — default cleanup receipt.

## Eligibility contract

A directory is eligible only when all gates pass:

1. it is a direct child of the operating system temp directory;
2. its leaf matches `^prompt-kit-browser-proof-[0-9a-fA-F]{16,64}$`;
3. it is not a reparse point/symlink;
4. it contains `web/prompt-kit/index.html`;
5. it meets the configured minimum age;
6. the operator explicitly supplies `-Apply`.

Anything else is preserved and reported.

## Never cleared by this harness

- `Desktop\dev\web-excel-repair-triage` or any other Git checkout;
- canonical `web/prompt-kit/index.html`;
- GitHub Pages;
- `http://127.0.0.1:8765/` portable runtime state;
- browser profiles, cookies, cache, history, IndexedDB, or localStorage;
- Prompt Kit Favorites;
- `Outputs/` evidence from other workflows.

## Commands

Preview all matching scratch directories:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\scripts\Clear-PromptKitBrowserProofScratch.ps1
```

Preview one exact path by adding `-TargetPath "<path>"`.

Delete one exact eligible path only after preview:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\scripts\Clear-PromptKitBrowserProofScratch.ps1 -TargetPath "<exact path>" -MinimumAgeMinutes 0 -Apply
```

## Build / test / deploy

There is no product build or deployment in this harness. Validate with:

```text
python scripts/validate_prompt_kit_browser_proof_cleanup.py --summary
python -m unittest tests.test_prompt_kit_browser_proof_cleanup_harness -v
git diff --check
```

CI is `.github/workflows/prompt-kit-browser-proof-cleanup.yml`. Native Windows/P-Top cleanup is a separate operator-runtime gate.
