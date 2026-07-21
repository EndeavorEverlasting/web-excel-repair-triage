# Bidirectional Website / Spreadsheet Generator Contract

## Authority

`configs/harness/bidirectional_web_spreadsheet_v1.json` is the machine-readable direction, sequencing, safety, and action-commitment contract. `configs/harness/web_spreadsheet_ir_v1.schema.json` defines the shared semantic intermediate representation. `triage.harness_bidirectional_conversion_contract` validates both and performs bounded local input analysis.

## Current repository evidence

The repository already generates self-contained review websites through `triage.sidecar_html.portal`. Those pages embed a structured `PORTAL` JSON object assembled from manifests, CSV, JSON, and adapter-defined sections. The repository also has mature package-preserving spreadsheet generation, Web Excel compatibility, formula, hyperlink, protection, and artifact-validation rules.

There is no repository-owned website-to-workbook inverse converter today. The existing sidecar portal is therefore evidence for a new inverse path, not proof that bidirectional conversion already exists.

## Required architecture

Both directions pass through `web-spreadsheet-ir-v1`:

```text
website snapshot/export -> input analysis -> shared IR -> workbook projection
workbook/package        -> input analysis -> shared IR -> website projection
```

The IR separates semantic content from presentation hints. Direction-specific generators may project the same semantics into worksheets, ranges, styles, tabs, portal sections, navigation, or links without inventing separate data models.

## Implementation order

1. **Input analyzer and contract enforcement.** Classify local HTML, workbooks, and workbook bundles; fingerprint the source; identify structured payloads, extraction strategy, mapping profile, blockers, direction, and proof ceiling.
2. **Website to spreadsheet — sidecar portal profile.** Read embedded `PORTAL` JSON first, convert sections into the shared IR, then project through existing workbook contracts and validators.
3. **Website to spreadsheet — generic HTML profiles.** Use semantic tables and labels only through an operator-approved mapping profile. Do not silently infer arbitrary page meaning.
4. **Spreadsheet to website.** Use a package-preserving workbook reader and registered sheet/range semantics, normalize into the same IR, then render through `triage.sidecar_html.portal` and registered adapters.
5. **Round-trip proof.** Compare semantic IR hashes in both directions. Static structure does not prove browser, Excel for Web, visual, formula, or operator fidelity.

Website to spreadsheet is first because the current portal already exposes structured JSON and the workbook target is more deeply codified. This is a lower-risk first implementation than attempting to infer a general website from an arbitrary workbook.

## Extraction precedence

For website inputs:

1. embedded `PORTAL` JSON;
2. linked local manifest, JSON, or CSV sidecars;
3. semantic DOM tables and labels;
4. an explicit operator-approved mapping profile.

Screenshot reconstruction, OCR, pixel matching, remote JavaScript execution, cookie use, and credential use are not primary extraction paths. Network fetching requires separate explicit scope; the current analyzer accepts local snapshots only.

## Action commitment

Input analysis is complete only when `conversion_analysis.json` exists. Conversion is complete only when the requested workbook or website exists and has a source fingerprint, conversion manifest, IR semantic hash, direction-specific validation, Git or artifact evidence when applicable, and an explicit field-acceptance ceiling.

A plan, rewritten prompt, acknowledgment, or handoff is not a converted artifact. Task-specific execution rules override generic closeout behavior.

## Commands

Validate the installed contract:

```powershell
python -m triage.harness_bidirectional_conversion_contract --repo-root . --json
```

Analyze a local website snapshot:

```powershell
python -m triage.harness_bidirectional_conversion_contract --analyze-input .\Outputs\run\index.html --out .\Outputs\run\conversion_analysis.json --json
```

Analyze a workbook:

```powershell
python -m triage.harness_bidirectional_conversion_contract --analyze-input .\Outputs\artifact.xlsx --out .\Outputs\conversion_analysis.json --json
```

These commands classify and plan the bounded pipeline. They do not claim that conversion has occurred.

## Field gates

- Generic website mapping approval.
- Excel for Web open, formulas, links, protection, and operator acceptance for workbook outputs.
- Browser rendering, navigation, accessibility, and operator acceptance for website outputs.
- Bidirectional semantic hash comparison before any round-trip fidelity claim.
