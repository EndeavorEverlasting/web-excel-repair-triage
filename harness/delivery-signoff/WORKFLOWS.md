# Delivery Sign-Off Harness — Workflows

## Select this workflow

Use for serial-first delivery, transfer, receipt, or acceptance sign-offs generated from a validated FUN specification and, when needed, active-roster context. Equipment-only stock receipts are supported; serial groups are required only when serialized assets are included.

Do not use it to infer unsupported equipment quantities, pair unrelated assets, or convert device counts into labor.

## Generate

1. Read `AGENTS.md`, this harness registry, layout config, capability, trigger, and skill.
2. Confirm the input declares `delivery-signoff-spec/v1` and records the supported proof ceiling.
3. Resolve roster context through the existing per-date precedence implementation only when needed; do not build a second roster reader.
4. Reject unresolved required fields, non-positive quantities, quantity/identifier mismatches, duplicate serials, collapsed equipment rows, or cable rows missing model and color/variant.
5. Run:

```bash
python scripts/generate_delivery_signoff.py <spec.json> --output-root Outputs/delivery-signoff
```

6. The generator constructs a clean editable DOCX, chooses portrait or landscape from content density, renders it through LibreOffice, rasterizes every PDF page with `pdftoppm`, reconciles serialized identifiers against the DOCX XML, scans stale-content tokens, and writes a contained manifest plus validation log.
7. Serial numbers remain primary; MACs stay paired with their serials. Temporary hostnames are not rendered into the primary verification drawbox.
8. Every separately counted line remains distinct. Cable types require explicit model and color/variant.
9. One page is preferred, two pages are the maximum, and text never drops below 8.5 points.
10. The field-notes area expands for low-density equipment receipts so the page remains useful rather than mostly blank.

## Validate before commit

```bash
python scripts/validate_delivery_signoff_harness.py
python scripts/validate_delivery_signoff_harness.py --manifest <artifact-manifest.json>
python -m pytest -q tests/test_delivery_signoff_generator.py tests/test_delivery_signoff_harness_validator.py
git diff --check
```

The manifest must prove: contained relative input/DOCX/preview paths, SHA-256 values, a non-empty page-hash list matching page count, minimum font, editable/unprotected state, required ink surfaces, strict serial counts when expected, complete equipment rows, and absence of stale site text.

## Handle failures

- Input evidence gap: return to FUN with the exact unresolved field.
- Invalid quantity, serial mismatch, or duplicate: stop generation.
- Equipment-only sign-off: set `serialized_assets` to an empty list; do not invent serials.
- More than two pages: reflow columns and use page area more efficiently; never shrink below 8.5 pt.
- Signature stranded or dead space excessive: rebalance the tables and field-notes area.
- Render dependency missing: install LibreOffice/soffice and `pdftoppm`; do not emit an unproven manifest.
- Draw support uncertain: keep the DOCX unprotected and record `draw_ready_static`, not operator acceptance.
- Stale site/recipient/range/footer: reject the artifact and regenerate from a clean document tree.
- Package path escape or hash mismatch: fail closed and preserve the validation log.

## Handoff

Return the DOCX, preview PDF, page PNGs internally, artifact manifest, validator log, hashes, page count, draw-support proof level, unresolved gates, branch/commit/PR state, and one exact command that regenerates and validates the canonical artifact.
