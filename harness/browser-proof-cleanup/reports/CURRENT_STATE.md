# Prompt Kit Browser-Proof Scratch — Current State

## Working

- Detached `prompt-kit-browser-proof-<hex>` directories have an explicit lifecycle contract.
- The cleanup capability is registered in the canonical root harness manifest, capability/trigger/workflow/artifact/validator registries, and human indexes so a fresh agent can discover it from the normal harness entry points.
- Preview mode is the default; apply requires an explicit switch.
- Exact-target cleanup is supported.
- The runner refuses paths outside the OS temp root.
- The runner refuses unexpected leaf names, missing Prompt Kit markers, and reparse points.
- Cleanup emits a stable JSON receipt under `Outputs/` and preserves the prior receipt under `Outputs/backups/prompt-kit-browser-proof-cleanup/` before replacement.
- CI validates the focused harness, root-harness registration, receipt retention, and preview/apply behavior against a test-owned scratch fixture.
- Native Windows/P-Top acceptance is recorded in `reports/P_TOP_ACCEPTANCE_20260810.md`: one operator-owned candidate passed classification, explicit apply deleted exactly one directory, zero failures were reported, and the postcondition confirmed the target no longer existed.

## Intentionally outside this harness

- clearing browser cookies/cache/history;
- clearing browser `localStorage`;
- resetting Prompt Kit Favorites;
- deleting canonical repository checkouts;
- deleting `Outputs/` evidence;
- changing Prompt Kit website/product behavior.

## Missing / unproven

No remaining filesystem-cleanup runtime gate is open for the observed P-Top acceptance case. Browser profile data, browser `localStorage`, Prompt Kit Favorites, other machines, and unrelated scratch families remain outside this proof rather than implicitly proven.

## Operator interpretation

A URL like `file:///C:/Users/<user>/AppData/Local/Temp/prompt-kit-browser-proof-<hex>/web/prompt-kit/index.html` is a detached browser-proof copy when its filesystem path passes this harness classification. It is disposable scratch; it is not the public Pages site, canonical checkout, browser profile, or Favorites store.
