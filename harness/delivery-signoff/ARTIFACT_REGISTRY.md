# Delivery Sign-Off Artifact Registry

## Canonical outputs

| Artifact | Canonical path pattern | Required proof |
| --- | --- | --- |
| Editable sign-off | `Outputs/delivery-signoff/<site>/<date>/<SITE>_<Hospital>_Delivery_Sign_Off_<date>_SERIAL_FIRST_INK_READY.docx` | SHA-256, unprotected/editable state, serialized asset counts, equipment rows |
| Rendered preview | `Outputs/delivery-signoff/<site>/<date>/preview/` | exact page count and unclipped page images or PDF |
| Artifact manifest | `Outputs/delivery-signoff/<site>/<date>/delivery-signoff-artifact-manifest.json` | input spec identity, output hashes, layout and draw-surface checks |
| Validation log | `Outputs/delivery-signoff/<site>/<date>/delivery-signoff-validation.txt` | focused validator result and proof ceiling |
| Operator report | `reports/harness/delivery-signoff-state.md` | working/broken/missing state and next action |

## Naming rules

- use site code and hospital name;
- use ISO date in paths and filenames;
- use `SERIAL_FIRST_INK_READY` to describe the contract, not `FINAL` or numbered versions as the sole identity;
- resolve the canonical artifact through the manifest, never by guessing the newest file.

## Layout acceptance rules

1. Serial numbers are the primary asset identifiers.
2. Neuron serial + MAC pairs remain together.
3. Temporary hostnames are secondary and omitted from the main verification drawbox by default.
4. Every separately counted equipment type appears on its own line; different cable colors/models cannot be merged.
5. One page is preferred. Two pages are allowed when necessary for serial volume and usable signature/draw space.
6. Body text may not fall below 8.5 pt.
7. The page must be filled ergonomically; large empty regions beside overflowing serial tables are a failure.
8. The DOCX remains editable and unprotected, with mark cells, an annotation box, and a receiver signature region.
9. Render inspection must reject clipping, truncated identifiers, split rows, stranded acceptance blocks, and stale content from another site.

## Proof vocabulary

- `package_valid`: DOCX package opens and required parts exist.
- `layout_valid`: rendered pages satisfy page/font/overflow rules.
- `draw_ready_static`: document is editable, unprotected, and contains required writable regions.
- `draw_smoke_tested`: operator successfully inked and saved in Word.
- `operator_accepted`: receiving operator approved the real artifact.

Do not claim a higher level than the recorded evidence supports.
