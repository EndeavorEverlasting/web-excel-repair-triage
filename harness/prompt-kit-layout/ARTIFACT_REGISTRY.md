# Responsive layout artifact registry

This harness produces evidence, not a replacement Prompt Kit website.

| Artifact | Path | Generator | Naming |
|---|---|---|---|
| Harness validation report | `Outputs/prompt-kit-layout-harness.json` | `python scripts/validate_prompt_kit_layout_harness.py --output Outputs/prompt-kit-layout-harness.json` | stable latest receipt |
| Browser geometry report | `Outputs/prompt-kit-layout-geometry.json` | future product/runtime browser probe | stable latest receipt |
| Operator state | `harness/prompt-kit-layout/reports/CURRENT_STATE.md` | tracked human report | fixed tracked path |

Generated evidence belongs under `Outputs/` and remains untracked unless repository policy explicitly registers a sanitized proof artifact. Screenshot evidence supplied by an operator is evidence input, not a canonical generated artifact.

## Browser geometry receipt schema

Strict product proof consumes `Outputs/prompt-kit-layout-geometry.json`; a status string alone is never sufficient. The receipt must identify `contract_id`, `browser_engine`, and one `viewports` row for every declared viewport. Each row records the exact `id`, `width`, and `height`, `brand_search_intersections: 0`, `filter_search_intersections: 0`, `header_escape: false`, `horizontal_overflow_pixels: 0`, `responsive_reflow: true`, and `touch_targets_usable: true`.

The default harness gate does not fabricate this receipt. `--require-implementation` fails until a browser/geometry lane has produced and validated it.
