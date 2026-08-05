# Skill: Generate a Serial-First Ink-Ready Delivery Sign-Off

## Trigger

Use when the requested output is a delivery, transfer, receipt, or acceptance sign-off that must preserve distinct stock rows, prioritize serialized identifiers when present, fit in the fewest legible pages, and remain usable with Word Draw or pen input.

## Required inputs

- validated `delivery-signoff-spec/v1` from FUN or an operator-approved protected-data-safe fixture;
- output directory;
- optional serialized asset groups;
- optional protected active-roster log for date/person/project context;
- optional reference template for branding and general visual hierarchy.

## Procedure

1. Read `AGENTS.md`, the harness registry, workflow, artifact registry, capability, trigger, and layout config.
2. Validate the input before rendering. Stop on missing required fields, non-positive quantities, duplicate serials, quantity/identifier mismatch, duplicate equipment rows, or incomplete cable identity.
3. Reuse the repository's existing active-roster reader when roster context is required. Preserve approved override, worked project, assignment, then default precedence.
4. Run `python scripts/generate_delivery_signoff.py <spec.json> --output-root Outputs/delivery-signoff`.
5. The generator creates a clean document tree; it never patches copied site-specific text in place.
6. Populate every distinct equipment line exactly once. Keep separate cable colors/models and scanner/adapter types. Equipment-only receipts are valid and must not invent serials.
7. When serial groups exist, place serials in the dominant verification drawbox, keep Neuron serial/MAC pairs together, and omit temporary hostnames from the primary drawbox.
8. Choose orientation and serial-column count from content density. Fill available page area ergonomically; the field annotation box expands when stock rows are sparse.
9. Prefer one page; permit two when required. Never use a third page merely because tables were not rebalanced. Never shrink body or serial text below 8.5 pt.
10. Provide mark/initial cells, a large annotation/exceptions box, and a receiver signature block. Keep the DOCX editable and unprotected; do not flatten content to images.
11. Render through LibreOffice to PDF, rasterize every page through `pdftoppm`, and inspect every page for clipping, truncation, split rows, dead space, and stranded acceptance blocks.
12. Emit a manifest with contained relative paths and SHA-256 values for the input, DOCX, PDF, and every page image.
13. Run `python scripts/validate_delivery_signoff_harness.py --manifest <manifest.json>`.
14. Record static draw readiness separately from an actual Word pen smoke test.

## Expected outputs

- editable unprotected DOCX;
- rendered PDF and page-preview PNGs;
- artifact manifest with hashes, page/font metrics, strict serial/equipment counts, draw surfaces, stale-content scan, and proof ceiling;
- validation log;
- operator handoff with canonical artifact path and exact regeneration/validation command.

## Known traps

- requiring fake serials for an equipment-only receipt;
- serials omitted while temporary hostnames are shown;
- two cable types collapsed into one row;
- assumed accessory quantities copied from device count;
- empty preview objects or missing page hashes accepted as proof;
- absolute or escaping manifest paths;
- large unused page space beside overflowing serial tables;
- acceptance block isolated on a third page;
- tiny text used to claim a one-page result;
- copied JTM, SSUH, OPR, recipient, or footer text surviving in a different site's artifact;
- claiming Word Draw was tested merely because the DOCX is unprotected.
