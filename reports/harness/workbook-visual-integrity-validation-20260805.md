# Workbook Visual Integrity Validation — 2026-08-05

## Scope

Harness infrastructure only. No `AGENTS.md`, generator product code, workbook math, private workbook bytes, secrets, or destructive cleanup changed.

## Focused validation

- Python compile: PASS
- Harness completeness: PASS — 22 required tracked surfaces, 3 profiles, 8 canonical semantic roles
- Profile audit: PASS — 3/3 profiles, 0 contract violations
- Focused unit suite: PASS — 12 tests
- Patch hygiene: PASS

## Regression coverage

The synthesized fixtures prove detection of:

- semantic workstream color mismatch (`WVI003`);
- one wrong row inside a same-key group (`WVI004`);
- inclusive range bleed into the next row (`WVI005`);
- paired summary/visual range mismatch (`WVI006`);
- value and formula changes during a style-only pass (`WVI007`);
- private cell text omission from reports.

## Exact-head remote validation

Validated implementation head `f723f74308428a2725167a1f279c43b3aa60bfed`:

- `Workbook visual integrity harness` run `31028478798`: **SUCCESS**
- `WebExcel Aptos font harness` run `31028478869`: **SUCCESS**
- `Operational harness contracts` run `31028479037`: **SUCCESS**
- `Prompt Kit web contracts` run `31028478937`: **SUCCESS**
- `Artifact engine tests` run `31028478955`: **SUCCESS**

Published proof artifact:

- name: `workbook-visual-integrity-report`
- artifact ID: `8939626803`
- digest: `sha256:f8cb8578a3b51361bbedce0bb6552cb43bce80b517516ee9357db531d9826d03`
- harness status: PASS
- profile audit status: PASS
- profile violations: 0

This report-only commit records the completed validation evidence. It does not change the validated policy, profiles, validators, tests, hooks, or workflow behavior.

## Protected-runtime observation

The current May administrative workbook was scanned read-only outside the repository. The validator reproduced the reported range-boundary defect at the first row of the May 27 block and classified the broader legacy color drift without committing workbook bytes or cell text.

The current July administrative workbook was also scanned read-only. Its legacy muted palette does not satisfy the new shared semantic palette, which is recorded as product-generator migration debt rather than repaired in this harness-only sprint.

## Remaining gates

- PR #134 must merge before PR #136 can be retargeted to `main`.
- Generator product code must emit the registered profile and exact visual receipt fields in a separately authorized lane.
- FUN must pin and consume the Triage visual receipt contract in its own implementation lane.
- Exact generated May, July, and Math Packet bytes still require protected-runtime validation and Excel for Web operator review.

## Proof ceiling

Tracked harness/profile completeness, synthesized OOXML behavior, exact CI artifact identity, root-harness compatibility, and patch hygiene. Product-generator adoption, FUN receipt consumption, Excel for Web rendering, print fidelity, workbook math, and operator/recipient acceptance remain separate gates.
