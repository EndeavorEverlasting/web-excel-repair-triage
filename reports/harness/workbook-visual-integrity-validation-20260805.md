# Workbook Visual Integrity Validation — 2026-08-05

## Scope

Harness infrastructure only. No `AGENTS.md`, generator product code, workbook math, private workbook bytes, secrets, or destructive cleanup changed.

## Focused local validation

- Python compile: PASS
- Harness completeness: PASS — 22 required tracked surfaces, 3 profiles, 8 canonical semantic roles
- Profile audit: PASS — 3/3 profiles, 0 contract violations
- Focused unit suite: PASS — 12 tests

## Regression coverage

The synthesized fixtures prove detection of:

- semantic workstream color mismatch (`WVI003`);
- one wrong row inside a same-key group (`WVI004`);
- inclusive range bleed into the next row (`WVI005`);
- paired summary/visual range mismatch (`WVI006`);
- value and formula changes during a style-only pass (`WVI007`);
- private cell text omission from reports.

## Protected-runtime observation

The current May administrative workbook was scanned read-only outside the repository. The validator reproduced the reported range-boundary defect at the first row of the May 27 block and classified the broader legacy color drift without committing workbook bytes or cell text.

The current July administrative workbook was also scanned read-only. Its legacy muted palette does not satisfy the new shared semantic palette, which is recorded as product-generator migration debt rather than repaired in this harness-only sprint.

## Proof ceiling

Focused local static and synthesized OOXML proof only. Exact-head CI, product-generator adoption, FUN receipt consumption, Excel for Web rendering, and operator acceptance remain separate gates.
