# Delivery Sign-Off Harness — Workflows

## Select this workflow

Use for serial-first delivery, transfer, receipt, or acceptance sign-offs generated from a validated FUN specification and, when needed, active-roster context.

Do not use it to infer unsupported equipment quantities, pair unrelated assets, or convert device counts into labor.

## Pick up a task

1. Read `AGENTS.md`, this harness registry, layout config, capability, trigger, and skill.
2. Confirm the input declares `delivery-signoff-spec/v1` and records provenance and proof ceiling.
3. Resolve roster context through the existing per-date precedence implementation; do not build a second roster reader in the harness.
4. Reject unresolved required fields, quantity/identifier mismatches, duplicate serials, or collapsed equipment rows.
5. Build the document from the validated spec. Use serial numbers as the primary asset text; MACs may accompany Neuron serials; temporary hostnames are secondary and omitted from the main drawbox unless explicitly requested.
6. Preserve every separately counted line item, including distinct cable colors/models.
7. Apply the layout contract: space-filling landscape or portrait chosen by content, one-page target, two-page maximum, minimum 8.5-point body text, mark cells, field annotation box, and receiver signature.
8. Keep the DOCX editable and unprotected so Word Draw/pen input remains available. Do not flatten the document into page images.
9. Render a PDF or page-preview images and inspect every page for clipping, dead space, stranded signatures, or serial splits.
10. Emit an artifact manifest and run the validator.

## Validate before commit

```bash
python scripts/validate_delivery_signoff_harness.py
python scripts/validate_delivery_signoff_harness.py --manifest <artifact-manifest.json>
python -m pytest -q
git diff --check
```

The manifest must prove: input spec identity, DOCX and preview paths, SHA-256 values, page count, minimum font, editable/unprotected state, required ink surfaces, serial counts, equipment rows, and absence of stale site text.

## Handle failures

- Input evidence gap: return to FUN with the exact unresolved field.
- Serial count mismatch or duplicate: stop generation.
- More than two pages: reflow columns and use page area more efficiently; never shrink below 8.5 pt.
- Signature stranded on a third page: rebalance the serial tables and acceptance area.
- Draw support uncertain: keep the DOCX unprotected and record `draw_smoke_test: pending_operator` rather than claiming field proof.
- Stale site/recipient/range/footer: reject the artifact and regenerate from a clean document tree.
- Package or render failure: preserve logs and do not publish the artifact as accepted.

## Handoff

Return the DOCX, preview/PDF, artifact manifest, validator log, hashes, page count, draw-support proof level, unresolved gates, branch/commit/PR state, and one exact command that retrieves and validates the canonical artifact.
