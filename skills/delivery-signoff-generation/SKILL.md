# Skill: Generate a Serial-First Ink-Ready Delivery Sign-Off

## Trigger

Use when the requested output is a delivery, transfer, receipt, or acceptance sign-off that must prioritize serial identifiers, fit in the fewest legible pages, and remain usable with Word Draw or pen input.

## Required inputs

- validated `delivery-signoff-spec/v1` from FUN;
- output directory;
- optional protected active-roster log for date/person/project context;
- optional reference template for branding and general visual hierarchy.

## Procedure

1. Read `AGENTS.md`, the harness registry, workflow, artifact registry, capability, trigger, and layout config.
2. Validate the input spec before rendering. Stop on missing required fields, duplicate serials, or quantity/identifier mismatch.
3. Reuse the repository's existing active-roster reader when roster context is required. Preserve approved override, worked project, assignment, then default precedence.
4. Create a clean document tree; do not patch copied site-specific text in place.
5. Populate project details and every distinct equipment line exactly once. Keep separate cable colors/models and separate scanner/adapter types.
6. Place serials in the dominant verification drawbox. Keep Neuron serial/MAC pairs together. Omit temporary hostnames from the primary drawbox unless the spec explicitly requires a secondary reference.
7. Choose orientation and column count from serial density. Fill available page area ergonomically.
8. Prefer one page; permit two when required. Never use a third page merely because tables were not rebalanced. Never shrink body or serial text below 8.5 pt.
9. Provide mark cells beside assets, a large annotation/exceptions box, and a receiver signature block. Keep the DOCX editable and unprotected; do not flatten content to images.
10. Render every page to PDF or preview images and inspect clipping, truncation, split rows, dead space, and stranded acceptance blocks.
11. Emit the artifact manifest and run `python scripts/validate_delivery_signoff_harness.py --manifest <manifest.json>`.
12. Record static draw readiness separately from an actual Word pen smoke test.

## Expected outputs

- editable unprotected DOCX;
- PDF or page-preview images;
- artifact manifest with hashes, page/font metrics, serial/equipment counts, draw surfaces, stale-content scan, and proof ceiling;
- validation log;
- operator handoff with canonical artifact path and exact retrieval/validation command.

## Known traps

- serials omitted while temporary hostnames are shown;
- two cable types collapsed into one row;
- assumed accessory quantities copied from device count;
- large unused page space beside overflowing serial tables;
- acceptance block isolated on a third page;
- tiny text used to claim a one-page result;
- copied JTM, SSUH, OPR, recipient, or footer text surviving in a different site's artifact;
- claiming Word Draw was tested merely because the DOCX is unprotected.
