# Delivery Sign-Off Artifact Registry

## Canonical outputs

| Artifact | Canonical path pattern | Required proof |
| --- | --- | --- |
| Editable sign-off | `Outputs/delivery-signoff/<run-root>/<site>/<signoff-id>/<SITE>_Delivery_Sign_Off_<id>_SERIAL_FIRST_INK_READY.docx` | SHA-256, unprotected/editable state, serial reconciliation when applicable, complete equipment rows |
| Rendered preview | `Outputs/delivery-signoff/<run-root>/<site>/<signoff-id>/preview/<artifact>.pdf` | SHA-256, exact page count, complete rendered serial tokens |
| Page previews | `Outputs/delivery-signoff/<run-root>/<site>/<signoff-id>/preview/page-<n>.png` | per-page SHA-256 and page-count reconciliation |
| Artifact manifest | `Outputs/delivery-signoff/<run-root>/<site>/<signoff-id>/delivery-signoff-artifact-manifest.json` | contained relative paths, input/output hashes, input-spec reconciliation, layout and draw-surface checks |
| Validation log | `Outputs/delivery-signoff/<run-root>/<site>/<signoff-id>/delivery-signoff-validation.txt` | focused generator/validator result and proof ceiling |
| Replacement backup | `Outputs/backups/delivery-signoff/<site>/<signoff-id>/<timestamp-id>/` | complete prior canonical package preserved before atomic replacement |

## Naming, containment, and replacement rules

- use site code and sign-off ID while checking the original identities before any lossy-slug replacement;
- use `SERIAL_FIRST_INK_READY` to describe the contract, not `FINAL` or numbered versions as the sole identity;
- resolve the canonical artifact through the manifest, never by guessing the newest file;
- every manifest path is relative to and contained by the manifest package;
- absolute paths, `..` escapes, malformed hashes, input-spec mismatches, and safe-slug collisions fail closed;
- acquire one same-identity writer lock, generate in a temporary package, validate fully, back up an existing package, then atomically publish;
- failed regeneration must preserve the last valid package.

## Layout acceptance rules

1. Serial numbers are the primary asset identifiers when serialized assets exist.
2. Neuron serial + MAC pairs remain together.
3. Temporary hostnames are omitted from the main verification drawbox by default.
4. Equipment-only receipts are valid and must not invent serial identifiers.
5. Each serialized group matches exactly one equipment row and the quantities agree.
6. Every separately counted equipment type appears on its own line; different cable colors/models cannot be merged.
7. One page is preferred. Two pages are allowed when necessary.
8. Body/serial text may not fall below 8.5 pt; headings may not fall below 11 pt.
9. The DOCX remains editable and unprotected, with mark cells, an annotation box, and a receiver signature region.
10. Render proof rejects clipping, truncated identifiers, split rows, stranded acceptance blocks, and stale content.

## Proof vocabulary

- `package_valid`: DOCX package opens and required parts exist.
- `layout_valid`: rendered pages satisfy page/font/overflow rules.
- `draw_ready_static`: document is editable, unprotected, and contains required writable regions.
- `draw_smoke_tested`: operator successfully inked and saved in Word.
- `operator_accepted`: receiving operator approved the real artifact.

Do not claim a higher level than recorded evidence supports.
