# Artifact fingerprint and approved-reference comparison

Generated submission workbooks are compared to **manually blessed** references under `References/approved/` (gitignored). Profiles live in `configs/artifact_profiles/`.

**PR #35 private proof checklist:** [`PR35_CHECKPOINT_AND_PROOF_GUIDE.md`](PR35_CHECKPOINT_AND_PROOF_GUIDE.md)

## Three layers

| Layer | Field | Fails build by default? |
|-------|--------|-------------------------|
| Raw file | `raw_sha256` | No (warning only) |
| Canonical package | `canonical_package_sha256` | No (warning; profile may opt in) |
| Visible semantic workbook | `semantic_sha256` | Yes, unless approved delta |
| All-sheet semantic workbook | `all_sheets_semantic_sha256` | No (diagnostic / explicit-use only) |

Raw SHA proves byte identity. Canonical package SHA removes volatile OOXML noise. The default semantic SHA now covers only **visible** worksheets so hidden/reference scratch tabs do not poison user-visible artifact comparison. `all_sheets_semantic_sha256` is still exposed for explicit investigations when you intentionally want hidden sheets to count.

Visible semantic SHA proves visible sheet names, cell values, formulas, number formats, tables, chart count, frozen panes, and autofilter refs — without filesystem path noise. Use the all-sheet semantic hash only when hidden-sheet drift is itself the thing you want to compare.

## CLI

```powershell
python -m triage.artifact_compare `
  --reference "References/approved/April_2026_Billing_Summary_Client_APPROVED.xlsx" `
  --candidate "Outputs/admin_billing_summary_2026_06_02/April_2026_Billing_Summary_Client.xlsx" `
  --profile admin_billing_summary `
  --expect-neuron-tab "Apr 26" `
  --out "Outputs/admin_billing_summary_2026_06_02/April_Client_compare.json"
```

Exit code `1` when `compare_pass` is false.

## Engine integration

**Admin billing** (Client variant only when `--reference` is set):

```powershell
python -m triage.admin_billing_summary.cli `
  --roster-log ... `
  --reference-client References/approved/...Client.xlsx `
  --reference-internal References/approved/...Internal.xlsx `
  --websafe
```

`--reference` remains an alias for `--reference-client` (**single-month runs only**). For April and May together use `--reference-client-april` and `--reference-client-may` (and internal `-april`/`-may` if comparing Internal). Internal compare is `NOT_RUN` when no internal reference is supplied (manifest records reason).

**Bonita**:

```powershell
python -m triage.nw_prj_neuron_track_hours.bonita_cli `
  --roster-log ... --reference References/approved/...xlsx --websafe
```

Sidecar HTML portals show compare KPIs on the **Preflight** tab when `*_artifact_compare.json` exists.

## Approved delta

See [`configs/artifact_profiles/README.md`](../configs/artifact_profiles/README.md).

## Release candidate

Manifests expose `release_candidate` and `release_blockers`. Delivery Client workbooks require `excel_for_web_manual_check: PROVEN` (via [`triage.record_excel_for_web_manual`](../triage/record_excel_for_web_manual.py)) before `release_candidate` is true.

## internal_admin_log profile

Reserved for a future standalone internal admin log exporter. Today use **admin billing Internal variant** workbooks; do not treat `internal_admin_log.json` as wired to a generator.

## Related modules

- `triage/artifact_fingerprint.py` — hashing
- `triage/artifact_profiles.py` — profile stop-ship
- `triage/artifact_compare.py` — compare + CLI
- `triage/webexcel_semantic_gate.py` — sharedStrings / sentinel gate (still runs at preflight)
- `triage/nw_prj_artifact_compare.py` — **different**: dashboard row reconciliation

## Validation flow

```text
Generate workbook
  → Package preflight (engine)
  → Semantic integrity gate
  → Artifact fingerprint
  → Compare to approved reference (optional)
  → Compare JSON + HTML portal
  → Manual Excel for Web check (NOT_PROVEN)
```
