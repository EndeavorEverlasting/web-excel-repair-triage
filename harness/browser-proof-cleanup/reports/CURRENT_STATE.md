# Prompt Kit Browser-Proof Scratch — Current State

## Working

- Detached `prompt-kit-browser-proof-<hex>` directories have an explicit lifecycle contract.
- Preview mode is the default; apply requires an explicit switch.
- Exact-target cleanup is supported.
- The runner refuses paths outside the OS temp root.
- The runner refuses unexpected leaf names, missing Prompt Kit markers, and reparse points.
- Cleanup emits a JSON receipt under `Outputs/`.
- CI validates the harness and exercises a test-owned scratch fixture.

## Intentionally outside this harness

- clearing browser cookies/cache/history;
- clearing browser `localStorage`;
- resetting Prompt Kit Favorites;
- deleting canonical repository checkouts;
- deleting `Outputs/` evidence;
- changing Prompt Kit website/product behavior.

## Missing / unproven

Native P-Top/Windows execution against an operator-owned scratch directory remains unproven until preview and apply are run on that workstation.

## Operator interpretation

A URL like `file:///C:/Users/<user>/AppData/Local/Temp/prompt-kit-browser-proof-<hex>/web/prompt-kit/index.html` is a detached browser-proof copy when its filesystem path passes this harness classification. It is disposable scratch; it is not the public Pages site or canonical checkout.
