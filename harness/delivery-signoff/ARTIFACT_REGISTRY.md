# Delivery Sign-Off Artifact Registry

## Canonical outputs

| Artifact | Canonical path pattern | Required proof |
| --- | --- | --- |
| Editable sign-off | `Outputs/delivery-signoff/<site>/<signoff-id>/<SITE>_Delivery_Sign_Off_<id>_SERIAL_FIRST_INK_READY.docx` | SHA-256, unprotected/editable state, serial reconciliation when applicable, complete equipment rows |
| Rendered preview | `Outputs/delivery-signoff/<site>/<signoff-id>/preview/<artifact>.pdf` | SHA-256, exact page count, and one contained SHA-256 page-image entry per page |
| Page previews | `Outputs/delivery-signoff/<site>/<signoff-id>/preview/page-<n>.png` | per-page SHA-256 and page-count reconciliation |
| Artifact manifest | `Outputs/delivery-signoff/<site>/<signoff-id>/delivery-signoff-artifact-manifest.json` | contained relative paths, input/output hashes, layout and draw-surface checks |
| Validation log | `Outputs/delivery-signoff/<site>/<signoff-id>/delivery-signoff-validation.txt` | focused generator/validator result and proof ceiling |
| Operator report | `reports/harness/delivery-signoff-state.md` | working/broken/missing state and next action |

## Naming and containment rules

- use site code and sign-off ID;
- use `SERIAL_FIRST_INK_READY` to describe the contract, not `FINAL` or numbered versions as the sole identity;
- resolve the canonical artifact through the manifest, never by guessing the newest file;
- every manifest path is relative to and contained by the manifest package;
- absolute paths, `..` escapes, missing files, malformed hashes, and mismatched hashes fail closed.

## Layout acceptance rules

1. Serial numbers are the primary asset identifiers when serialized assets exist.
2. Neuron serial + MAC pairs remain together.
3. Temporary hostnames are secondary and omitted from the main verification drawbox by default.
4. Equipment-only receipts are valid and must not invent serial identifiers.
5. Every separately counted equipment type appears on its own line; different cable colors/models cannot be merged.
6. One page is preferred. Two pages are allowed when necessary for serial volume and usable signature/draw space.
7. Body text may not fall below 8.5 pt.
8. The page must be filled ergonomically; large empty regions beside overflowing serial tables are a failure.
9. The DOCX remains editable and unprotected, with mark cells, an annotation box, and a receiver signature region.
10. Render inspection must reject clipping, truncated identifiers, split rows, stranded acceptance blocks, and stale content from another site.

## Manifest count rules

- `serialized_assets_expected` is boolean.
- `serial_counts` may be empty only when `serialized_assets_expected` is false.
- Every `declared`, `rendered`, and `duplicates` value is a non-negative integer.
- Declared and rendered counts must match; duplicates must equal zero.
- `equipment_rows` is non-empty. Each row has a non-empty equipment type, string model/variant fields, and a positive integer quantity.

## Proof vocabulary

- `package_valid`: DOCX package opens and required parts exist.
- `layout_valid`: rendered pages satisfy page/font/overflow rules.
- `draw_ready_static`: document is editable, unprotected, and contains required writable regions.
- `draw_smoke_tested`: operator successfully inked and saved in Word.
- `operator_accepted`: receiving operator approved the real artifact.

Do not claim a higher level than the recorded evidence supports.
