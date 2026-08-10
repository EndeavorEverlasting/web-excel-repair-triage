# Responsive layout artifact registry

This harness produces evidence, not a replacement Prompt Kit website.

| Artifact | Path | Generator | Naming |
|---|---|---|---|
| Harness validation report | `Outputs/prompt-kit-layout-harness.json` | `python scripts/validate_prompt_kit_layout_harness.py --output Outputs/prompt-kit-layout-harness.json` | stable latest receipt |
| Browser geometry report | `Outputs/prompt-kit-layout-geometry.json` | future product/runtime browser probe | stable latest receipt |
| Operator state | `harness/prompt-kit-layout/reports/CURRENT_STATE.md` | tracked human report | fixed tracked path |

Generated evidence belongs under `Outputs/` and remains untracked unless repository policy explicitly registers a sanitized proof artifact. Screenshot evidence supplied by an operator is evidence input, not a canonical generated artifact.