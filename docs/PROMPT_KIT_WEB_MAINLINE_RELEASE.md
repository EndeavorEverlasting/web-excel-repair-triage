# Prompt Kit Website Mainline Release

## Mission

Publish the technician-facing Prompt Kit website from the repository default branch so operators clone or pull `main`, then open `web/prompt-kit/index.html`.

## Preservation source

- Source PR: #94
- Source product commit: `6b357af052ebdf29a60fc5c06762fa06990f68da`
- Source validated head: `791ff280e1ed9ee13bb6542ab3f2965252e93628`
- Mainline preservation commit: `95f04d20234d4ab5c7d283425897bdb03014feed`

## Included website surface

- `build_prompt_kit.py`
- `docs/prompt-kit.js`
- `docs/prompts.json`
- `docs/reference.json`
- `web/prompt-kit/index.html`
- `web/README.md`
- `tests/test_prompt_kit_header_contract.py`
- `.github/workflows/prompt-kit-web.yml`

## Repository-floor cleanup included

- remove the generated `docs/AI_Harness_Prompt_Kit_v39.xlsx` binary from tracked source;
- retire the foreign Cybernet target package, configs, fixtures, tests, contract, and CI registration;
- preserve the validated One Marcus XML namespace repair from PR #57 without importing the V21 generator stack.

## Explicit exclusions

This release does not import Neuron, billing, workbook-generator, private-artifact, generated-workbook, or unrelated application changes from stacked feature branches.

## Operator contract

From a clean clone of `main`:

```powershell
start web\prompt-kit\index.html
```

The website header must expose All, Standard, GNHF, and Doctrine in that order with keyboard shortcuts 1, 2, 3, and 4.

## Deferred hardening

Repository issue #99 owns the reference-variable schema mismatch. Additional inherited client-rendering and builder hardening discovered during mainline review must remain isolated from the technician release and be addressed in a focused follow-up without reopening the retired application lanes.
