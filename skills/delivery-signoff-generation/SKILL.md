# Skill: Generate a Serial-First Ink-Ready Delivery Sign-Off

## Trigger

Use when the requested output is a delivery, transfer, receipt, or acceptance sign-off that must preserve distinct stock rows, prioritize serialized identifiers when present, fit in the fewest legible pages, and remain usable with Word Draw or pen input. Typed trigger deny rules run first; evidence-pack-only requests route to FUN until a validated specification exists.

## Required inputs

- validated `delivery-signoff-spec/v1` from FUN or an operator-approved protected-data-safe fixture;
- a newly created output root beneath `Outputs/delivery-signoff/`;
- optional serialized asset groups whose count exactly matches the corresponding equipment row;
- optional protected active-roster log for date/person/project context;
- optional reference template for branding and general visual hierarchy.

Reject an output path that equals, contains, or is contained by the validated specification, source evidence, or protected operator inputs. All generated documents, sidecars, previews, manifests, logs, and backups remain under `Outputs/`.

## Pre-mutation declaration

Before changing tracked files or generating a canonical package, state the repository/worktree, branch, lane, mission, owned scope, forbidden scope, expected artifacts, validation order, mutation authority, one-writer boundary, proof ceiling, and deterministic next proof gate.

## Procedure

1. Read `AGENTS.md`, the harness registry, workflow, artifact registry, capability, typed trigger, and layout config.
2. Validate the input before rendering. Stop on missing required fields, non-positive quantities, duplicate serials or serialized asset types, quantity/identifier mismatch, duplicate equipment rows, incomplete cable identity, or unsafe output paths.
3. Reuse the repository's existing active-roster reader when roster context is required. Preserve approved override, worked project, assignment, then default precedence.
4. Run `python scripts/generate_delivery_signoff.py <spec.json> --output-root Outputs/delivery-signoff/<new-run-root>`.
5. The generator acquires one same-identity writer lock and builds in a unique temporary directory. It never deletes the last valid package before replacement proof exists.
6. Populate every distinct equipment line exactly once. Keep separate cable colors/models and scanner/adapter types. Equipment-only receipts are valid and must not invent serials.
7. When serial groups exist, match each group to exactly one equipment row, require equal quantities, place serials in the dominant verification drawbox, keep Neuron serial/MAC pairs together, and omit temporary hostnames from the primary drawbox.
8. Choose portrait or landscape and two or three serial columns from content density and identifier length. Body/serial text may not fall below 8.5 points; headings may not fall below 11 points.
9. Provide mark/initial cells, a large annotation/exceptions box, and a receiver signature block. Keep the DOCX editable and unprotected; do not flatten content to images.
10. Render through LibreOffice to PDF, rasterize every page through `pdftoppm`, and extract PDF text through `pdftotext` to prove complete serialized identifiers survived rendering.
11. Inspect every page for clipping, truncation, split rows, dead space, and stranded acceptance blocks.
12. Emit a manifest with contained relative paths and SHA-256 values for the normalized input, DOCX, PDF, and every page image; reconcile manifest equipment and serial claims back to the input specification.
13. On successful replacement, move the prior package to `Outputs/backups/delivery-signoff/` and atomically publish the validated replacement. On any failure, retain the prior package.
14. Run `python scripts/validate_delivery_signoff_harness.py --manifest <canonical-package>/delivery-signoff-artifact-manifest.json`.
15. Record static draw readiness separately from an actual Word pen smoke test.

## Expected outputs

- editable unprotected DOCX;
- rendered PDF and page-preview PNGs;
- artifact manifest with hashes, page/font metrics, strict serial/equipment counts, draw surfaces, stale-content scan, and proof ceiling;
- validation log;
- timestamped backup when a canonical package was replaced;
- operator handoff with exact branch/commit/PR state and an executable artifact-consumption command.

## Known traps

- requiring fake serials for an equipment-only receipt;
- serials omitted while temporary hostnames are shown;
- substring-based serial reconciliation that confuses `1`, `11`, and `111`;
- repeated asset groups overwriting manifest counts;
- equipment quantity and serial count drifting apart;
- safe-slug collisions overwriting a different site/sign-off identity;
- deleting the prior package before rendering succeeds;
- concurrent generators interleaving the same canonical package;
- arbitrary output directories or generated content beside protected inputs;
- two cable types collapsed into one row;
- assumed accessory quantities copied from device count;
- empty preview objects or missing page hashes accepted as proof;
- absolute or escaping manifest paths;
- headings below the 11-point contract;
- large unused page space beside overflowing serial tables;
- acceptance block isolated on a third page;
- claiming Word Draw was tested merely because the DOCX is unprotected.
