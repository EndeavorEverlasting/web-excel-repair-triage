# Cybernet Target Sprint Contract — Web Excel Safe

## Purpose

Formalize the June 2026 Wave 3 Cybernet sprint automation so generation is repeatable, auditable, and safe for Excel for Web. This contract governs how All-Wave upstream workbooks, the live sprint dashboard, optional deployment tracker enrichment, and sprint scope config combine into a clean sprint target workbook.

## Carryover thesis

```text
Treat All-Wave as upstream source, not output shape.
Treat the sprint dashboard as the active control surface.
Never blindly pull Wave 1 or Wave 2 rows into active scope.
Resolve AMB before trusting counts.
Replace SSUH placeholders with real SSH locations when available.
Carry forward manual checklist status; never overwrite with blanks.
Never trust Excel Web compatibility until preflight passes.
```

## Input hierarchy (authority order)

1. **Sprint scope config** (`configs/cybernet_sprint_scope_2026_06.json`) — active tabs, excluded waves, site aliases, milestones.
2. **Existing sprint dashboard** — manual status and checklist columns are evidence; carry unless source contradicts site/location.
3. **All-Wave workbook** — upstream truth for locations, wave, device type, PC names, ambulatory hardware rows.
4. **Deployment tracker (optional)** — enriches hostname/serial when matchable; never overwrites carried manual status.

## Sprint scope (June 2026)

| Sprint tab | Count | Meaning |
| --- | ---: | --- |
| HH | 24 | Wave 3 Huntington/Hospital target set |
| JTM | 23 | Wave 3 JTM target set |
| AMB | 6 | Consolidated ambulatory targets (operational view) |
| SSUH | 40 | SSUH/SSH imaging/configuration pipeline |
| **Total** | **93** | Current working sprint surface |

Wave 1 (220) and Wave 2 (246) rows remain in All-Wave for lookup only unless explicitly promoted.

## Source workbooks

Default inputs (under `Candidates/configuration targets/`):

- `ALL WAVE ANESTHESIA MACHINES for Tim 6-1-2026.xlsx`
- `Targets_Wave3_Live_Dashboard_WebExcelSafe_2026-05-26.xlsx`
- `Active Deployment Tracker 2026-05-06 6-1-2026.xlsx` (optional)

### Reader anchors

| Sheet | Header row | Data start |
| --- | ---: | ---: |
| Neuron Cybernet | 6 | 7 |
| ANE Ambulatory Locations | 2 | 3 |
| Deployments | 1 | 2 |

## Site alias map

| Source label | Sprint scope |
| --- | --- |
| SSH | SSUH |
| SSUH | SSUH |
| South Shore | SSUH |
| Wave 3 AMB | AMB |

## AMB reconciliation doctrine

AMB is not a clean row copy. Three layers must reconcile:

| Layer | Source | Typical count |
| --- | --- | ---: |
| 1 | Neuron Cybernet, Site = Wave 3 AMB | 11 |
| 2 | ANE Ambulatory Locations, Wave 2 Cybernet qty > 0 | 9 |
| 3 | Sprint dashboard AMB tab (consolidated) | 6 |

Automation MUST emit `AMB_Reconciliation` and a CSV explaining 6 vs 9 vs 11. Unresolved rows are flagged in `Action Needed`; the engine must not silently pick one count.

## SSUH placeholder rule

Sprint dashboard SSUH rows may use generic `Imaging Pipeline` locations and `WBS-001..040` hostnames. Automation replaces these with All-Wave Wave 3 `SSH` locations when available. Sprint hostnames and checklist values are preserved only on keyed match (`site|normalized_location`).

## HH / JTM asset readiness

HH and JTM are valid target skeletons when location-complete but hostname-empty:

- Target exists = yes
- Location known = yes
- Hostname assigned = no → `Asset Assignment Status = unassigned`, `Readiness Gate = blocked`

## Carry-forward columns

Never overwrite from All-Wave:

- `Status`, `Imaged`, `Labeled`, `Boxed`, `Ready for Delivery`, `Completed Date`

## Required output sheets

| Sheet | Purpose |
| --- | --- |
| Start Here | Operator instructions |
| Dashboard | Counts, readiness, deadlines |
| HH | Active HH targets |
| JTM | Active JTM targets |
| AMB_Grouped | Consolidated ambulatory targets |
| AMB_Raw_Source | Raw AMB source rows |
| AMB_Reconciliation | Explains 6 vs 9 vs 11 |
| SSUH | Site/location-specific SSUH rows |
| Kit_Requirements | Cybernet, Neuron, arms, DIMs, breakaways |
| Shortages | Required minus on-hand (v1 flags gaps) |
| Carryover_Log | Prior dashboard status retained |
| Definitions_Current | Field definitions |
| Dropdown_Values | Valid dropdowns |
| 00_CF_Dictionary | Color and status rules |
| Repo_Automation_Notes | Generator version, inputs, timestamps |

## Output naming

```text
Cybernet_Targets_Sprint_{as_of}_WEBSAFE.xlsx
```

Repaired filenames (`repaired_`, `Deprecated_repaired_`, etc.) are **stop-ship**. Do not bless them.

## Milestones (operational deadlines)

| Workstream | Due |
| --- | --- |
| Ambulatory Cybernets | 2026-06-04 |
| Prototype/full Cybernet kits | 2026-06-08 |
| SSUH configurations | 2026-06-11 |
| SSUH delivery | 2026-06-12 |

## CLI

```powershell
python -m triage.cybernet_targets.cli `
  --all-wave "Candidates/configuration targets/ALL WAVE ANESTHESIA MACHINES for Tim 6-1-2026.xlsx" `
  --existing-dashboard "Candidates/configuration targets/Targets_Wave3_Live_Dashboard_WebExcelSafe_2026-05-26.xlsx" `
  --deployment-tracker "Candidates/configuration targets/Active Deployment Tracker 2026-05-06 6-1-2026.xlsx" `
  --scope configs/cybernet_sprint_scope_2026_06.json `
  --out-dir Outputs `
  --as-of 2026-06-01 `
  --websafe
```

## Known gaps (v1)

- Shortage math requires inventory join; v1 `Shortages` sheet flags required kit fields with on-hand TBD.
- AMB grouping key may not resolve all 11 Wave 3 rows to 6 sprint rows without manual review.
- Deployment tracker fuzzy location match may need human review (`Review Status = needs_review`).
- Sprint workbook tab set is operator-controlled; deleted tabs fail schema validation by design.

## Web Excel stop-ship

Generated workbooks must pass `gate_checks.run_all()` and `run_preflight()` when `--websafe` is set. Post-save `fix_inlinestr()` is mandatory for openpyxl output.
