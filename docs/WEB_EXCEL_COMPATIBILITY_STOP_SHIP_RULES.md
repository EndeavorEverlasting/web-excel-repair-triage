# Web Excel Compatibility — STOP-SHIP Rules (NW PRJ Dashboard)

## Failed artifact rule

```text
If Excel for Web repairs the workbook, the artifact is failed.
Do not bless it.
Do not continue from it without labeling it as a repaired source.
Rebuild clean if possible.
```

If Excel for Web refuses to attempt repair, treat the artifact as a package-shape failure until proven otherwise.

If desktop Excel refuses to open the workbook, the artifact is also failed even when ZIP, XML parsing, validators, screenshots, or a non-Office rendering engine report success.

A workbook can be a valid ZIP and well-formed XML while still being invalid to Office.

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
| Markup-compatibility prefix values | `mc:Ignorable`, `mc:MustUnderstand`, `mc:Choice/@Requires`, or other MC QName lists reference a prefix that is not declared in that XML part |
| Relationship targets | `.rels` Target does not resolve in package; same-workbook `#Sheet!Cell` fragments are validated as fragments rather than package parts |
| Relationship escapes package | Internal `.rels` Target resolves outside package root |
| Absolute internal relationship target | Unexpected absolute package target where the known-good lane uses relative targets |
| Content types | Missing `[Content_Types].xml`, bad XML default, or missing workbook-main override |
| Chart part topology | Chart part lives under an unexpected drawing subpath instead of the accepted chart path |
| Chart relationship integrity | Drawing relationship points to a chart part that is absent or misplaced |
| Duplicate table names | Two `table` parts share `displayName` or `name` |
| Stale calc chain | A `calcChain.xml` entry references a worksheet `sheetId` that is absent or does not resolve to an actual formula cell |
| External workbook links | `xl/externalLinks/` exists in a delivery artifact |
| Serializer namespace pollution | XML contains `ns0:` leakage, or a serializer renames namespace declarations while leaving literal MC prefix lists unchanged |
| R1C1 CF leakage | `RC\d` in `<f>` inside conditional formatting |
| Missing `CF_Dictionary` | NW PRJ dashboard profile detected, sheet absent |
| Column A override | Done row still matches queue-amber CF only |

A calculation chain is workbook-profile evidence, not an automatic failure. Remove it when the generator contract requires removal. Preserve and synchronize it when the accepted structural fixture uses one.

### Why ordinary XML parsing is insufficient

Markup-compatibility attributes contain prefixes as text values. For example:

```xml
<workbook xmlns:mc="..." mc:Ignorable="x15 xr">
  <mc:AlternateContent>
    <mc:Choice Requires="x15">
```

A serializer can rewrite `xmlns:x15` to `xmlns:ns2` while leaving `Ignorable="x15"` and `Requires="x15"` unchanged. The document remains well-formed XML because those values are strings, but Office cannot resolve the referenced prefixes. This is a STOP-SHIP failure.

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
- namespace declarations and markup-compatibility prefix values

Do not hide structural churn behind a screenshot.

Do not round-trip a Microsoft-authored package through a generic XML serializer unless namespace-prefix preservation is proven. Prefer bounded byte-level or namespace-aware edits against the accepted package fixture.

## Excel Web repair symptoms

- File opens as repaired
- Filename becomes `Deprecated_repaired_...`
- Excel Web refuses to repair
- Excel Web will not attempt repair
- Desktop Excel refuses to open the workbook
- Tables disappear
- Charts disappear or detach from source ranges
- CF behaves but workbook structure is poisoned

**Likely causes:** duplicate tables, broken worksheet relationships, table relationship mismatch, inherited cruft, unsupported formulas/names, bad CF references, bad content-type defaults/overrides, bad drawing/chart topology, stale calculation metadata, undeclared markup-compatibility prefixes, or package-shape drift from full regeneration.

## Minimum acceptance ladder

A workbook candidate must pass these checks before delivery:

1. ZIP package opens.
2. XML and `.rels` parts parse.
3. Markup-compatibility prefix values resolve to declared prefixes.
4. Required package parts exist.
5. Content types are sane.
6. Relationship targets resolve inside the package or are valid same-workbook fragments.
7. Stop-ship formula/name/error tokens are absent.
8. Calculation metadata matches the selected workbook profile and every retained chain entry resolves through worksheet `sheetId` to an actual formula cell.
9. Tables/charts/drawings remain in the known-good topology.
10. Target sheets render correctly.
11. Non-target sheets remain stable.
12. Desktop Excel opens without repair or refusal.
13. Excel for Web opens without repair.

Static package and rendering checks are necessary but do not prove Office-host acceptance. When desktop or Web Excel is unavailable, the proof ceiling must remain below delivery acceptance.

## Integration

- Core battery: `triage/gate_checks.py`
- Prompt-kit and generated-workbook package gate: `triage/web_excel_compatibility_rules.py`
- NW PRJ profile: `triage/nw_prj_dashboard_validator.py`
- Billing wrapper pattern: `triage/billing_bridge_validator.py`
- Package insight notes: `docs/insights/web-excel-compatibility-artifact-lessons-2026-07-01.md`
- Prompt Kit V24 failure record: `docs/AI_PROMPT_KIT_V24_OFFICE_OPEN_FAILURE.md`
- Structure contract: `docs/XLSX_STRUCTURE_PRESERVATION_CONTRACT.md`
- Contract doc: `docs/billing_bridge/WEB_EXCEL_VALIDATION.md`
