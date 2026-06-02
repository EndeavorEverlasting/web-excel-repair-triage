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
