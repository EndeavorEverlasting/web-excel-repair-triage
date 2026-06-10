# Artifact profiles

Committed JSON profiles drive stop-ship checks and approved-reference comparison.
Private blessed workbooks live under `References/approved/` (gitignored).

`one_marcus_recon.json` sets `require_sheet_preservation` — baseline compare must not
delete sheets vs the emulator. Other engines may adopt the same flag when integrated
multi-tab sources need relink-not-regenerate protection. See
[`docs/OPERATOR_SOURCE_IMMUTABILITY.md`](../../docs/OPERATOR_SOURCE_IMMUTABILITY.md).

## Approved delta file

When a semantic change is intentional, provide a sidecar JSON:

```json
{
  "allow_candidate_semantic_sha256": "<candidate semantic_sha256>",
  "reason": "April totals corrected after roster override",
  "approved_utc": "2026-06-02",
  "scope": "April_2026_Client_totals_only"
}
```

Required fields: `reason`, `approved_utc`, and either `allow_candidate_semantic_sha256` or `semantic_sha256_allowlist`. Compare passes on semantic mismatch only when the candidate hash matches and audit fields are present.

Record manual Excel for Web proof:

```powershell
python -m triage.record_excel_for_web_manual `
  --out-dir Outputs/proof_pr35_admin_billing `
  --workbook "Outputs/.../April_2026_Billing_Summary_Client.xlsx" `
  --status PROVEN `
  --checked-by "initials" `
  --preflight-json "Outputs/.../April_2026_Billing_Summary_Client_preflight.json"
```
