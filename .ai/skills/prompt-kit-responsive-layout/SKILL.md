# Prompt Kit Responsive Layout Audit

## Trigger
Use when Prompt Kit controls overlap, clip, escape their header/container, create horizontal page overflow, behave differently across viewport widths, or strict browser no-overlap proof is requested.

## Required inputs
- repository and exact branch/commit when available;
- viewport width/height or screenshot dimensions;
- elements involved in the collision;
- whether the lane may edit product code;
- current browser/runtime evidence if any.

## Outputs
- harness validation receipt;
- focused source/generated-artifact regression proof;
- browser geometry receipt when strict product proof is actually observed;
- exact files, commit/PR evidence, proof ceiling, and next executable gate.

## Procedure
1. Read `AGENTS.md`, the root harness registration, `harness/prompt-kit-layout/manifest.v1.json`, and the responsive-header collision contract.
2. Classify the symptom: brand/search, filter/search, container escape, horizontal overflow, touch-target regression, or another bounded layout defect.
3. In a harness-only lane, update harness evidence/contracts/validators without claiming product repair.
4. In a product lane, repair the canonical authored layout source, rebuild the registered generated site, and run Prompt Kit header/mobile checks.
5. For strict browser proof, measure bounding rectangles at every declared viewport and emit the registered geometry receipt. Any forbidden intersection, escape, overflow, missing viewport, or unusable touch target fails.
6. Record runtime evidence only under `Outputs/`, report the actual proof ceiling, and hand off the next executable gate.

## Guardrails
- Never treat one screenshot, a media-query marker, or an editable implementation-status string as browser geometry proof.
- Never hand-edit `web/prompt-kit/index.html`; use the canonical builder.
- Never shrink controls below usable accessibility/touch dimensions merely to remove collisions.
- Preserve unrelated work and keep browser/live-target mutation outside a static harness lane.

## Validation
- `python scripts/validate_prompt_kit_layout_harness.py --summary`
- `python -m unittest tests.test_prompt_kit_layout_harness -v`
- Strict only with real geometry: `python scripts/validate_prompt_kit_layout_harness.py --require-implementation --geometry-report Outputs/prompt-kit-layout-geometry.json --summary`
- Rebuild/parity and header contracts when product source changes.

## Proof ceiling
Default validation proves tracked responsive-layout contracts, registration, source markers, and generated-artifact regressions only. Observed no-overlap behavior requires a validated browser-geometry receipt covering every declared viewport; production/operator acceptance remains higher proof.
