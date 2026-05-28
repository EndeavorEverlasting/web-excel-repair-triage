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

## Restore the files

From the repo root after pulling:

```bash
python scripts/artifacts/decode_nw_prj_v6_8_checkpoint.py
```

The script decodes:

```text
artifacts/nw_prj_dashboard_v6_8/NW_PRJ_v6_8_checkpoint_artifacts_2026-05-28.zip.b64
```

into:

```text
RecoveredArtifacts/NW_PRJ_v6_8_checkpoint_artifacts_2026-05-28/
```

Then verify the checksum shown in `manifest.json`.

## Important doctrine captured by this checkpoint

- `Addressed` is not the same as `Resolved`.
- `ROSTER CONFIRMED` means the roster supports the proposed value; it does not prove the admin scratch copy is already fixed.
- `Gray/Skip` rows are dismissed/reference, not active targets.
- Column A review status must override queue coloring.
- A file renamed `Deprecated_repaired_...` by Excel Web is failed output.
- `Resolved_Queue` is values-routed in v6.8; dynamic linked routing belongs to v7.x.

## Contents

See `manifest.json` for file roles and SHA-256 checksums.
