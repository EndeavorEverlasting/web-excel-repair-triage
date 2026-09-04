# Delivery Sign-Off Harness — Workflows

## Select this workflow

Use for serial-first delivery, transfer, receipt, or acceptance sign-offs generated from a validated FUN specification and, when needed, active-roster context. Equipment-only stock receipts are supported; serial groups are required only when serialized assets are included.

Do not use it to infer unsupported equipment quantities, pair unrelated assets, convert device counts into labor, or route an unresolved evidence-pack task into local generation. Evidence-pack-only work returns to `EndeavorEverlasting/FUN` until a validated `delivery-signoff-spec/v1` exists.

## Execution preflight

Before document construction or tracked-file modification, declare:

- repository and branch or isolated worktree;
- lane and mission;
- owned scope and forbidden scope;
- expected artifacts;
- validation commands and order;
- proof ceiling;
- mutation authority plus push, PR, merge, and release authority;
- one-writer boundary for the branch and canonical sign-off identity.

Preserve dirty or separately owned work. Generated outputs must use a new root under `Outputs/delivery-signoff/`; the input specification and protected operator inputs may not be stored there.

## Generate

1. Read `AGENTS.md`, this harness registry, layout config, capability, trigger, and skill.
2. Confirm the input declares `delivery-signoff-spec/v1` and records the supported proof ceiling.
3. Resolve roster context through the existing per-date precedence implementation only when needed; do not build a second active-roster reader.
4. Reject unresolved required fields, non-positive quantities, quantity/identifier mismatches, duplicate serials or asset groups, collapsed equipment rows, cable rows missing model and color/variant, and lossy path collisions.
5. Run:

```bash
python scripts/generate_delivery_signoff.py <spec.json> --output-root Outputs/delivery-signoff/<new-run-root>
```

6. The generator constructs the complete replacement in a unique temporary package while the last valid canonical package remains available.
7. A same-identity lock prevents concurrent writers. After rendering and validation pass, an existing canonical package is moved under `Outputs/backups/delivery-signoff/` and the replacement is atomically published. Failed regeneration preserves the prior package.
8. Orientation and serial-column count are chosen from identifier length, serial density, and equipment density. Small serialized receipts remain portrait; dense or long identifiers reflow to landscape without dropping below the typography floor.
9. Serial numbers remain primary; MACs stay paired with their serials. Temporary hostnames are not rendered into the primary verification drawbox.
10. Every separately counted line remains distinct. Cable types require explicit model and color/variant.
11. One page is preferred, the two-page maximum is enforced, body/serial text stays at or above 8.5 points, and headings stay at or above 11 points.
12. LibreOffice renders the DOCX, `pdftoppm` rasterizes every page, and `pdftotext` verifies complete serialized identifiers survived rendering.
13. The manifest binds contained file hashes, page proof, equipment rows, and serial counts to the normalized input specification.

## Validate before commit

```bash
python scripts/validate_delivery_signoff_harness.py
python scripts/validate_delivery_signoff_harness.py --manifest <canonical-package>/delivery-signoff-artifact-manifest.json
python -m pytest -q tests/test_delivery_signoff_generator.py tests/test_delivery_signoff_harness_validator.py tests/test_delivery_signoff_trigger.py
git diff --check
```

## Handle failures

- Input evidence gap: route to FUN with the exact unresolved field.
- Invalid quantity, duplicate identity, serial mismatch, or equipment mismatch: stop generation.
- Equipment-only sign-off: set `serialized_assets` to an empty list; do not invent serials.
- Existing same-ID package: preserve it until replacement validation passes, then back it up before atomic publication.
- Existing lock: stop; do not delete another writer's lock or package.
- More than two pages: reflow columns and use page area more efficiently; never shrink below 8.5 pt.
- Signature stranded or dead space excessive: rebalance tables and field-notes area.
- Render dependency missing: install LibreOffice/soffice and Poppler utilities; do not emit an unproven manifest.
- Draw support uncertain: keep the DOCX unprotected and record `draw_ready_static`, not operator acceptance.
- Stale site/recipient/range/footer or rendered identifier truncation: reject and preserve the last valid package.
- Package path escape, input-spec mismatch, or hash mismatch: fail closed and preserve the validation log.

## Handoff

Return the DOCX, preview PDF, page PNGs internally, artifact manifest, validator log, hashes, page count, backup/replacement result, draw-support proof level, unresolved gates, branch/commit/PR state, final Git status or explicit local-Git limitation, and one exact command that consumes the canonical manifest and opens the generated DOCX.
