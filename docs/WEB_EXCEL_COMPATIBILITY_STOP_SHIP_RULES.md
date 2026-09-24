# Web Excel Compatibility — STOP-SHIP Rules (NW PRJ Dashboard)

## Failed artifact rule

```text
If Excel for Web repairs the workbook, the artifact is failed.
Do not bless it.
Do not continue from it without labeling it as a repaired source.
Rebuild clean if possible.
```

If Excel for Web refuses to attempt repair, treat the artifact as a package-shape failure until proven otherwise.

A workbook can be a valid ZIP and still be Web Excel-invalid.

## Filename STOP-SHIP

Reject outputs or inputs when the basename contains:

- `repaired_`
- `Deprecated_repaired_`
- `web_repaired_` (legacy local pattern)

## Package STOP-SHIP tokens

Scan all XML parts (see `configs/web_excel_stop_ship_tokens.json`):

| Token / pattern | Why |
| --- | --- |
| `_xlfn.` | Unsupported function namespace |
| `_xludf.` | User-defined function leakage |
| `_xlpm.` | Lambda / PM namespace |
| `AGGREGATE(` | Known Web hazard |
| `#REF!` | Broken references (especially CF) |
| `#VALUE!` | Eval errors in stored XML |
| `#NAME?` | Unknown names |

## Structural STOP-SHIP

| Check | Failure |
| --- | --- |
| XML parse | Any `.xml` part fails `ElementTree` parse |
| Relationship targets | `.rels` Target does not resolve in package |
| Relationship escapes package | Internal `.rels` Target resolves outside package root |
| Absolute internal relationship target | Unexpected absolute package target where the known-good lane uses relative targets |
| Content types | Missing `[Content_Types].xml`, bad XML default, or missing workbook-main override |
| Chart part topology | Chart part lives under an unexpected drawing subpath instead of the accepted chart path |
| Chart relationship integrity | Drawing relationship points to a chart part that is absent or misplaced |
| Duplicate table names | Two `table` parts share `displayName` or `name` |
| Stale calc chain | `xl/calcChain.xml` survives programmatic edits |
| External workbook links | `xl/externalLinks/` exists in a delivery artifact |
| Serializer namespace pollution | XML contains `ns0:` or `xmlns:ns0` leakage |
| R1C1 CF leakage | `RC\d` in `<f>` inside conditional formatting |
| Missing `CF_Dictionary` | NW PRJ dashboard profile detected, sheet absent |
| Column A override | Done row still matches queue-amber CF only |

## Package-shape drift rule

Known-good workbook structure is a compatibility fixture.

For one-tab or value-only repairs, unexpected changes to these areas are review-gate failures:

- `[Content_Types].xml`
- `_rels/.rels`
- `xl/_rels/workbook.xml.rels`
- worksheet relationship parts outside the target sheet
- chart parts and chart relationship parts
- drawing parts and drawing relationship parts
- table parts and table relationship parts
- `xl/styles.xml`
- shared string strategy
- workbook calculation metadata

Do not hide structural churn behind a screenshot.

## Excel Web repair symptoms

- File opens as repaired
- Filename becomes `Deprecated_repaired_...`
- Excel Web refuses to repair
- Excel Web will not attempt repair
- Tables disappear
- Charts disappear or detach from source ranges
- CF behaves but workbook structure is poisoned

**Likely causes:** duplicate tables, broken worksheet relationships, table relationship mismatch, inherited cruft, unsupported formulas/names, bad CF references, bad content-type defaults/overrides, bad drawing/chart topology, stale calc chain, or package-shape drift from full regeneration.

## Minimum acceptance ladder

A workbook candidate must pass these checks before delivery:

1. ZIP package opens.
2. XML and `.rels` parts parse.
3. Required package parts exist.
4. Content types are sane.
5. Relationship targets resolve inside the package.
6. Stop-ship formula/name/error tokens are absent.
7. `calcChain.xml` is absent after programmatic edits.
8. Tables/charts/drawings remain in the known-good topology.
9. Target sheets render correctly.
10. Non-target sheets remain stable.
11. Excel Web opens without repair.

## Integration

- Core battery: `triage/gate_checks.py`
- NW PRJ profile: `triage/nw_prj_dashboard_validator.py`
- Billing wrapper pattern: `triage/billing_bridge_validator.py`
- Package insight notes: `docs/insights/web-excel-compatibility-artifact-lessons-2026-07-01.md`
- Structure contract: `docs/XLSX_STRUCTURE_PRESERVATION_CONTRACT.md`
- Contract doc: `docs/billing_bridge/WEB_EXCEL_VALIDATION.md`
