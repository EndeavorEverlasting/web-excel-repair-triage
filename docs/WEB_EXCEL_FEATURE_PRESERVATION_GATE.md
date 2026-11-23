# Workbook feature preservation gate

An Excel-for-Web-compatible package can still suffer functional regression during
a library export. The existing single-package scanner checks OOXML stop-ship
conditions. This additional **pairwise** guard protects visible workbook
affordances that otherwise disappear without a cell-value difference.

## Run before releasing any regenerated/repaired workbook

```bash
python -m triage.web_excel_feature_preservation last_accepted.xlsx candidate.xlsx
python -m triage.semantic_preservation last_accepted.xlsx candidate.xlsx
python -m pytest -q tests/test_web_excel_feature_preservation.py
```

Compatibility first uses the existing package-level API:

```bash
python -c "from triage.web_excel_compatibility_rules import assert_web_excel_compatible; assert_web_excel_compatible('candidate.xlsx')"
```

The pairwise feature guard checks worksheet names/order, auto-filter ranges,
frozen pane definitions, data-validation ranges/formulas, and attached image
content/anchors. Output is JSON with SHA-256 receipts and named feature failures;
it does **not** emit private cell values.

A passing local guard is not proof of live Excel-for-Web compatibility. The
final gate remains opening the candidate in Excel for Web and checking for
repair banners, with provider-backed readback if available.

### Important regression reproduced on 2026-11-23

A round-trip of an uploaded, Excel-repaired tracker with a generic workbook
serializer silently **removed the AutoFilter on each of two worksheets**.
The source's frozen panes, validation rules, and guidance image survived in
that particular test. The pairwise guard rejected the round-trip, whereas
single-package structural checks alone did not establish feature preservation.

The private workbook and its cell contents were never committed to this
repository. Synthetic tests exercise the same failure mode.

### Boundaries

- The known-good original/unrepaired workbook is preferred as the baseline.
- Never overwrite the SharePoint/OneDrive original just because a local
  regeneration passes.
- Preserve the image, top-of-sheet entry buffer, filters, and dropdowns.
- Compare cell payloads with the existing `semantic_preservation` owner.
- Inspect the operator's screenshot and actual provider open/readback before
  declaring a repaired file production-safe.
