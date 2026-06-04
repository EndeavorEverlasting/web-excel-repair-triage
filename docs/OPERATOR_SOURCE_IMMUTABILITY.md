# Operator source immutability (repo-wide doctrine)

Canonical rules for every artifact engine in this repository. Supersedes
lane-specific notes; the One Marcus incident doc remains the concrete case study.

Related:

- [`ONE_MARCUS_SOURCE_OVERWRITE_INCIDENT_2026_06_04.md`](ONE_MARCUS_SOURCE_OVERWRITE_INCIDENT_2026_06_04.md)
- [`triage/output_policy.py`](../triage/output_policy.py)
- [`AGENTS.md`](../AGENTS.md) (agent contract pointer)

## Emulator folders (read-only)

Engines **read** from these roots and **never write** into them:

| Root | Role |
|------|------|
| `Candidates/` | Triage inputs and operator copies |
| `Active/` | Golden standards (analysis only) |
| `ArtifactIntake/` | Dated intake batches (raw evidence) |
| `References/` | Approved/blessed references |
| `Repaired/` | Excel-repaired variants |
| `Workbook Payload Artifacts/` | Payload snapshots |
| `RecoveredArtifacts/` | Recovery dumps |

`Deprecated/` remains a **work area** (mutation allowed by design). It is not
treated as an emulator root for this policy.

## Writable output roots

All engine artifacts go under:

- `Outputs/<engine>/<YYYY-MM-DD>_<run_slug>/` — default run layout
- `artifacts/<engine>/...` — compare-only tools (e.g. roster log compare)

Optional subfolders per run:

```text
delivery/     submission-facing .xlsx
internal/     internal/QA variants
sidecars/     manifests, preflight JSON, review queues
compare/      artifact_compare results
forensics/    incident_compare, zip diffs
index.html    HTML portal when emitted
```

`Outputs/backups/backup_<timestamp>/` — only via explicit overwrite approval
([`triage/repo_apply.py`](../triage/repo_apply.py)).

## Rules

1. **Emulator = backup/reference.** Engines read; they do not mutate integrated
   multi-tab operator workbooks in place.
2. **No `--output == --input`.** No writes under readonly roots (enforced by
   `assert_output_path_allowed` / `assert_not_overwriting_emulator`).
3. **Reserialization gate.** Generators that `save()` via openpyxl must not target
   integrated multi-tab emulators without a sheet-preservation gate (One Marcus:
   use **relink**, not **generate**, on READY workbooks).
4. **Delivery requires baseline compare.** Compare against declared baseline
   (emulator or `References/approved/`); fail closed when sheets are deleted or
   profile gates fail.
5. **Overwrite outside Outputs** requires timestamped backup via `repo_apply`.

## Manifest provenance

Each engine run should record in its manifest (or sidecar):

| Field | Meaning |
|-------|---------|
| `source_emulator_path` | Primary read-only input path |
| `source_raw_sha256` | SHA-256 of that file at run start |
| `run_id` | `<YYYY-MM-DD>_<slug>` folder name |
| `output_layout_version` | `1` — standard run folder layout |

## ArtifactIntake

Raw folders under `ArtifactIntake/<date>/` are emulator evidence. Only
`outputs/admin-ready/` and `outputs/internal-review/` receive **manual** promotion
after validation — engines do not auto-write into intake raw trees.

See [`ArtifactIntake/2026-06-02/README.md`](../ArtifactIntake/2026-06-02/README.md).

## Deferred (known gaps)

- Visual XML graft for One Marcus (relink preserves sheets; Visual column graft is
  a follow-up lane).
- Automatic backup on every engine run (only on explicit overwrite via `repo_apply`).
- Auto-promotion into `ArtifactIntake/.../outputs/admin-ready/` (operator-controlled).
- `Deprecated/` mutation policy unchanged.
