# Prompt Kit Browser-Proof Scratch — P-Top Acceptance

## Evidence source

This report records sanitized operator-observed evidence from a native Windows/P-Top run on 2026-08-10. The raw local JSON receipt remains operator-local under the repository `Outputs/` tree and is not committed.

## Observed execution

- repository source: `origin/main` containing merge `fb03bb06a622933e95de606d3472324e0a0ce78c`;
- runner: `scripts/Clear-PromptKitBrowserProofScratch.ps1`;
- mode: `apply`;
- target class: one direct child of the Windows system Temp root matching `prompt-kit-browser-proof-<hex>`;
- required marker: `web/prompt-kit/index.html` present;
- candidates: 1;
- eligible: 1;
- deleted: 1;
- preserved: 0;
- failed: 0;
- postcondition: target path absent after cleanup (`TARGET_EXISTS=False`);
- durable local receipt: written to the operator checkout under `Outputs/prompt-kit-browser-proof-cleanup-report.json`.

## Privacy and retention

This tracked report intentionally omits the Windows username, absolute user-profile path, exact scratch identifier, and raw machine-local receipt. The operator-local receipt remains the detailed filesystem evidence.

## Exclusions preserved

The observed run did not clear or prove browser cookies/cache/history, browser profile data, browser `localStorage`, Prompt Kit Favorites, GitHub Pages state, canonical repository checkouts, or unrelated `Outputs/` evidence.

## Acceptance result

**PASS — native Windows/P-Top explicit-apply cleanup was observed for one eligible operator-owned Prompt Kit browser-proof scratch directory, and deletion was independently confirmed by the postcondition check.**

## Proof ceiling

This closes the native Windows/P-Top filesystem cleanup runtime gate for the browser-proof scratch runner. It does not raise the proof level for browser profile data, `localStorage`, Favorites, or any Prompt Kit product behavior outside filesystem scratch cleanup.
