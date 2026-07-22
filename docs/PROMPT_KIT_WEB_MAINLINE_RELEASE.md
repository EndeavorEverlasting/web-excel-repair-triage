# Prompt Kit Website Mainline Release

## Mission

Publish the technician-facing Prompt Kit website from the repository default branch so operators clone or pull `main`, then open `web/prompt-kit/index.html`.

## Preservation source

- Source PR: #94
- Source product commit: `6b357af052ebdf29a60fc5c06762fa06990f68da`
- Source validated head: `791ff280e1ed9ee13bb6542ab3f2965252e93628`
- Mainline preservation commit: `95f04d20234d4ab5c7d283425897bdb03014feed`

## Included surface

- `build_prompt_kit.py`
- `docs/prompt-kit.js`
- `docs/prompts.json`
- `web/prompt-kit/index.html`
- `web/README.md`
- `tests/test_prompt_kit_header_contract.py`
- `.github/workflows/prompt-kit-web.yml`

## Explicit exclusions

This release does not carry Cybernet, Neuron, billing, One Marcus, workbook-generator, private-artifact, or generated-workbook changes from stacked feature branches.

## Operator contract

From a clean clone of `main`:

```powershell
start web\prompt-kit\index.html
```

The website header must expose All, Standard, GNHF, and Doctrine in that order with keyboard shortcuts 1, 2, 3, and 4.
