# NW PRJ v6.8 Dashboard Checkpoint Artifacts

This folder preserves the working v6.8 checkpoint so the next PC can pull the repo and recover the exact dashboard/admin/roster artifacts without hunting through chat downloads.

## Why this exists

The v6.8 sprint established the current Web Excel-safe dashboard baseline:

- resolution-ledger routing
- lighter tab colors
- color-coded CF dictionary and visual system
- notes/context preservation
- manual admin scratch/control copy as the first target
- roster log as confirmation evidence
- hidden backend columns for analysis while keeping tech-facing tabs fast

## Payload scope

This checkpoint commit includes **generator-critical xlsx only** (3 files):

- `NW_PRJ_Tech_Roster_Dashboard_v6_8_RESOLUTION_LEDGER_WEBSAFE.xlsx`
- `NW PRJ Tech hours 5-27-2026 - Khadejah and Alejandro Updates - Manually Updated 5x.xlsx`
- `INTERNAL_May_Billing_Active_Roster_Log_2026-05-28-update so that partial hours are flagged before submission.xlsx`

Optional items (v6.7 dashboard source, PNG screenshots) are listed under `not_included` in `manifest.json`.

Carryover notes are committed as UTF-8 text: `NW_PRJ_Dashboard_v6_8_Repo_Carryover_Notes.md`.

## Restore the payloads

From the repo root after pulling branch `artifacts/nw-prj-v6-8-checkpoint-2026-05-28`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/artifacts/decode_nw_prj_v6_8_checkpoint.py
```

When prompted, enter the checkpoint password (stored externally — never in the repo).

Non-interactive decode:

```powershell
$env:NW_PRJ_CHECKPOINT_PASSWORD = "your-secret"
python scripts/artifacts/decode_nw_prj_v6_8_checkpoint.py
```

Files extract to:

```text
RecoveredArtifacts/NW_PRJ_v6_8_checkpoint_artifacts_2026-05-28/
```

Verify against `payload_checksums.sha256` and per-file SHA-256 entries in `manifest.json`.

## Re-package (maintainers only)

If you have raw workbooks in `Workbook Payload Artifacts/` (gitignored):

```powershell
python scripts/artifacts/package_nw_prj_v6_8_checkpoint.py
```

Then update `manifest.json` `archive_sha256` from script output and commit the new archive + checksums.

## Important doctrine captured by this checkpoint

- `Addressed` is not the same as `Resolved`.
- `ROSTER CONFIRMED` means the roster supports the proposed value; it does not prove the admin scratch copy is already fixed.
- `Gray/Skip` rows are dismissed/reference, not active targets.
- Column A review status must override queue coloring.
- A file renamed `Deprecated_repaired_...` by Excel Web is failed output.
- `Resolved_Queue` is values-routed in v6.8; dynamic linked routing belongs to v7.x.

## Contents

See `manifest.json` for file roles, SHA-256 checksums, and storage method.
