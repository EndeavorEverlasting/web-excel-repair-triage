# Sidecar HTML review portal

Each artifact-engine run folder can include a self-contained **`index.html`** that renders manifest KPIs, preflight results, review-queue CSVs, and JSON sidecars in a dark ops dashboard (DeployAxis-inspired tokens; aligned with `billing_context/html_dashboard.py`).

## When it is created

Portals are written automatically at the end of:

- `triage.admin_billing_summary.cli`
- `triage.nw_prj_neuron_track_hours.bonita_cli`
- `triage.nw_prj_neuron_track_hours.cli`
- `triage.one_marcus_recon` export
- `triage.cybernet_targets.cli`

The manifest JSON gains `html_portal` (and `outputs.html_portal` where applicable).

## Rebuild without regenerating workbooks

```powershell
python -m triage.sidecar_html Outputs\admin_billing_summary_2026_06_02
```

Reads the newest `*manifest*.json` in that folder and rewrites `index.html`.

## Usage

Open `index.html` in a browser. Tabs: **Overview**, **Review queue**, **Preflight**, **Data**. Tables support search and category filters. JSON/CSV files remain on disk for scripts and diff tools.

When runs pass `--reference` to admin billing or Bonita CLIs, the **Preflight** tab also shows **Approved reference compare** KPIs (`raw_sha_match`, `semantic_compare`, etc.) and links to `*_artifact_compare.json`. See [ARTIFACT_FINGERPRINT_AND_COMPARE.md](ARTIFACT_FINGERPRINT_AND_COMPARE.md).

## Bidirectional conversion boundary

The current implementation is one-way: registered manifests, CSV, and JSON are rendered into a self-contained website. It does not currently reconstruct a workbook from HTML.

Generated portals embed a structured `const PORTAL = ...` JSON payload. The bidirectional conversion doctrine treats that payload as the first and most reliable website-to-spreadsheet source, ahead of DOM inference and far ahead of screenshot reconstruction or OCR.

Use `python -m triage.harness_bidirectional_conversion_contract --analyze-input <local-index.html> --out <approved-output>/conversion_analysis.json --json` before designing or running a converter. Both website-to-spreadsheet and spreadsheet-to-website must normalize through `configs/harness/web_spreadsheet_ir_v1.schema.json`.

See [HARNESS_BIDIRECTIONAL_WEB_SPREADSHEET.md](HARNESS_BIDIRECTIONAL_WEB_SPREADSHEET.md). Input analysis is not conversion; an actual workbook or website plus direction-specific validation is required before claiming success.
