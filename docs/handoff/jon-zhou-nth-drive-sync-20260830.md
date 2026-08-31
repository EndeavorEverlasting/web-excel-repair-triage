# Jon Zhou NTH Drive Sync Receipt — 2026-08-31

## Scope

This receipt records the bounded repository ↔ Google Drive synchronization and Drive organization for the Jon Zhou NTH reconciliation send set. Git remains repository history. Google Drive remains the collaboration/delivery workspace. No whole-repository mirroring, Drive-as-source-control behavior, or destructive cleanup is authorized by this receipt.

Binding repository authorities:

- `harness/specs/billing-artifact-safety.md`
- `docs/NTH_QUALITATIVE_ADMIN_PROFILE.md`
- `configs/artifact_profiles/nth_qualitative_admin.v1.json`
- `scripts/build_nth_qualitative_admin.py`

Drive workspace reused: `Neuron Track Hours (NTH) — 2026` → `00_CURRENT` → `Published_Admin_Share`.

## Human-readable Drive layout

`Published_Admin_Share` now contains only three top-level folders:

- `00_SEND_TO_JON_ZHOU__2026-08-31`
- `90_ARCHIVE__NOT_FOR_JON`
- `95_INTERNAL_SYNC_RECEIPTS`

The send folder intentionally contains exactly two files:

1. `01_EMAIL_DRAFT__Jon_Zhou__NTH_Reconciliation__2026-08-31.md`
2. `02_ATTACH__NTH_May-July__CLAIM_SAFE.xlsx`

Historical/competing June, August, and May–July workbook variants were moved into `90_ARCHIVE__NOT_FOR_JON` without deletion. Sync receipts were moved into `95_INTERNAL_SYNC_RECEIPTS`. Stable Drive file identities were reused; no replacement project workspace was created.

## Send-set decision

| Artifact | Drive location | Authority | Action | Status / evidence |
| --- | --- | --- | --- | --- |
| Jon Zhou reconciliation email/status draft | `Published_Admin_Share/00_SEND_TO_JON_ZHOU__2026-08-31/01_EMAIL_DRAFT__Jon_Zhou__NTH_Reconciliation__2026-08-31.md` | DRIVE-AUTHORITATIVE delivery draft; repository contracts bound evidence language | MOVE + RENAME IN PLACE | Selected for send. June remains `603.25h / 73 shifts`. August-through-2026-08-21 is expressed as `22 completed attendance records with NTH involvement` plus gross `184h / 23 completed records`; one 8h Projects Team record is outside NTH and one separate completed day is multi-project. The stale whole-shift NTH subtotal is not presented as a billing total. |
| May–July claim-safe executive packet | `Published_Admin_Share/00_SEND_TO_JON_ZHOU__2026-08-31/02_ATTACH__NTH_May-July__CLAIM_SAFE.xlsx` | DERIVED / PUBLISH-ONLY | MOVE + RENAME IN PLACE | Selected for attachment. June control is `603.25h`. Operational themes remain descriptive; exact workstream-hour splits are not presented without task-level attribution. |
| Site/device overview | `00_CURRENT/Client_Share/Neuron Deployment — Site and Device Overview.xlsm` | DERIVED / PUBLISH-ONLY | NO CHANGE; HOLD UNLESS NEEDED | Not part of the default Jon send set unless physical deployment scope is specifically useful. |
| Historical/competing NTH publications | `Published_Admin_Share/90_ARCHIVE__NOT_FOR_JON/` | DERIVED / HISTORICAL | MOVE IN PLACE | Preserved, not deleted. These files are no longer visually competing with the send set at the top level. |
| Sync receipts | `Published_Admin_Share/95_INTERNAL_SYNC_RECEIPTS/` | INTERNAL / DO-NOT-SEND | MOVE + DISAMBIGUATING RENAME | Current raw receipt and legacy native-Doc receipt are separated from recipient-facing artifacts. |
| Private August workstream math / allocation evidence | internal evidence locations / canonical roster allocation ledger | PRIVATE / DO-NOT-SYNC | SKIP | Retained only as internal evidence and excluded from the recipient package. |

## Reconciliation finding

A second-pass check against the current allocation-aware roster found that one completed August attendance day is explicitly multi-project. Therefore the older whole-shift subtotal must not be represented as an exact August NTH billing total. The recipient draft reports the directly supportable record counts and gross attendance boundary instead of promoting private allocation arithmetic into an outward claim.

The current qualitative-admin profile remains the controlling outward pattern: direct paid attendance is quantitative; workstream interpretation is qualitative unless direct task/time evidence supports a split. Technical-scope controls may bound claims but do not create labor hours by themselves.

## Recipient package

Default send set — no judgment call required:

1. `01_EMAIL_DRAFT__Jon_Zhou__NTH_Reconciliation__2026-08-31.md`
2. `02_ATTACH__NTH_May-July__CLAIM_SAFE.xlsx`

Do not attach anything from `90_ARCHIVE__NOT_FOR_JON` or `95_INTERNAL_SYNC_RECEIPTS`.

## Proof ceiling

This receipt proves Drive organization, stable-identity moves/renames, recipient send-set separation, repository/Drive mapping, audience-boundary review, and reconciliation against the current allocation-aware roster. It does not prove email delivery, Jon's acceptance, Excel-for-Web rendering on Jon's device, or a newly regenerated August qualitative-admin workbook.