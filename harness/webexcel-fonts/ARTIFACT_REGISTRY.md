# WebExcel Font Harness — Artifact Registry

## Tracked harness artifacts

| Artifact | Path | Generation or maintenance | Validation |
|---|---|---|---|
| Font policy | `configs/webexcel_fonts_v1.json` | edited canonical JSON | completeness validator and focused tests |
| Font validator | `scripts/validate_webexcel_fonts.py` | edited Python | compile, unit tests, CI workflow |
| Completeness validator | `scripts/validate_webexcel_font_harness.py` | edited Python | self-test and CI workflow |
| Codebase map | `harness/webexcel-fonts/CODEBASE_MAP.md` | edited Markdown | completeness validator |
| Workflow specs | `harness/webexcel-fonts/WORKFLOWS.md` | edited Markdown | completeness validator |
| Artifact registry | `harness/webexcel-fonts/ARTIFACT_REGISTRY.md` | edited Markdown | completeness validator |
| Machine registry | `harness/webexcel-fonts/registry.json` | edited JSON | completeness validator and tests |
| Scoped skill | `.ai/skills/webexcel-font-compatibility/SKILL.md` | edited Markdown | section and path validation |
| Operator state report | `reports/harness/webexcel-font-compatibility-state.md` | edited Markdown | completeness validator |
| CI workflow | `.github/workflows/webexcel-font-harness.yml` | edited YAML | GitHub Actions |

## Runtime artifacts

| Artifact | Default path | Naming and contents | Tracking policy |
|---|---|---|---|
| WebExcel font validation report | `Outputs/webexcel-font-validation.json` | `webexcel-font-validation-result/v1`; policy ID, artifact identity, observed fonts, rule IDs, locations, disposition | Gitignored runtime proof or CI artifact |
| WebExcel font harness report | `Outputs/webexcel-font-harness.json` | `webexcel-font-harness-result/v1`; component count, policy identity, canonical report path, proof ceiling | Gitignored runtime proof or CI artifact |
| Validated share-ready workbook | operator-approved `Outputs/` or delivery path | existing artifact naming contract; never renamed by this validator | Track only when the owning artifact contract permits it |

## Generation commands

```powershell
python scripts\validate_webexcel_font_harness.py --output Outputs\webexcel-font-harness.json --summary
python scripts\validate_webexcel_fonts.py --scan-source --output Outputs\webexcel-font-validation.json --summary
python scripts\validate_webexcel_fonts.py --workbook "<share-ready.xlsx>" --require-workbook --output Outputs\webexcel-font-validation.json --summary
```

## Naming conventions

- Policy and registry JSON use stable versioned schema IDs.
- Runtime reports use stable filenames because hooks, CI, and handoffs resolve them from `registry.json`.
- Workbooks retain the owning artifact family's canonical name; this harness records filename, size, and SHA-256 rather than inventing a competing name.
- Reports never include workbook cell contents. Font names, rule IDs, OOXML package paths, and artifact identities are sufficient.

## Delivery gate

A WebExcel-facing workbook is font-ready only when:

1. the font harness completeness report is `PASS` on the producing commit;
2. source scan is `PASS` for the producer/configuration surface;
3. the exact workbook-byte report is `PASS`;
4. the first/default explicit font is Aptos;
5. every explicit font is in the approved Aptos family;
6. no OOXML part contains Carlito;
7. the operator opens the same saved bytes in Excel for Web for visual proof.

## Proof boundary

The harness proves repository wiring, static source-token safety, OOXML font declarations, artifact identity, and tested fail-closed behavior. It does not prove browser font availability, layout fidelity, print fidelity, macro safety, workbook math, private-data safety, or admin acceptance.
