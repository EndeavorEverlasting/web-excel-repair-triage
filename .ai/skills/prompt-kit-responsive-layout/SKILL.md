# Prompt Kit Responsive Layout Audit

## Trigger conditions
Use when Prompt Kit controls overlap, clip, escape their header/container, create horizontal page overflow, or behave differently across viewport widths or released versions.

## Required inputs
- repository and exact branch/commit when available;
- viewport width/height or screenshot dimensions;
- elements involved in the collision;
- whether the lane may edit product code;
- current browser/runtime evidence if any.

## Procedure
1. Read `AGENTS.md`, `harness/prompt-kit-layout/manifest.v1.json`, and the responsive-header collision contract.
2. Classify the symptom: brand/search, filter/search, container escape, horizontal overflow, touch-target regression, or another bounded layout defect.
3. In a harness-only lane, update only harness evidence/contracts/validators; never patch generated HTML or product JS/CSS.
4. In a product lane, find the canonical authored layout source, repair reflow before collision, rebuild the generated site through its registered builder, and run existing Prompt Kit header/mobile checks.
5. For browser proof, measure relevant bounding rectangles at every declared viewport. Any forbidden intersection or page overflow fails the gate.
6. Record artifacts under `Outputs/`, report the actual proof ceiling, and hand off the next executable gate.

## Expected outputs
- harness validation receipt;
- browser geometry receipt for product/runtime proof;
- exact files changed and validator results;
- commit/PR evidence;
- one executable next action.

## Common traps
- treating one desktop screenshot as responsive proof;
- asserting that a media query exists instead of measuring geometry;
- fixing generated `web/prompt-kit/index.html` by hand instead of the canonical source/builder;
- shrinking controls until they are inaccessible;
- weakening the collision contract merely to make CI green.