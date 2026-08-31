# Jon Zhou NTH Drive Sync Receipt — 2026-08-30

## Scope

This receipt records the bounded repository ↔ Google Drive synchronization decision for the Jon Zhou NTH reconciliation send set. Git remains repository history. Google Drive remains the collaboration/delivery workspace. No whole-repository mirroring, private workbook copying, or Drive-as-source-control behavior is authorized by this receipt.

Binding repository authorities:

- `harness/specs/billing-artifact-safety.md`
- `docs/NTH_QUALITATIVE_ADMIN_PROFILE.md`
- `configs/artifact_profiles/nth_qualitative_admin.v1.json`
- `scripts/build_nth_qualitative_admin.py`

Drive workspace reused: `Neuron Track Hours (NTH) — 2026` → `00_CURRENT`.

## Send-set decision

| Artifact | Repository / producer identity | Drive location | Authority | Action | Status / evidence |
| --- | --- | --- | --- | --- | --- |
| Jon Zhou reconciliation email/status draft | Recipient-facing reconciliation wording bounded by current NTH controls | `00_CURRENT/Published_Admin_Share/2026-08-30-jon-zhou-nth-reconciliation-status-draft.md` | DRIVE-AUTHORITATIVE delivery draft; repository contracts bound evidence language | UPDATE DRIVE | Updated in place. June remains `603.25h / 73 shifts`. August-through-2026-08-21 is expressed as `22 completed attendance records with NTH involvement` plus gross `184h / 23 completed records`; one 8h Projects Team record is outside NTH and one separate completed day is multi-project. The stale whole-shift NTH subtotal is not presented as a billing total. |
| May–July claim-safe executive packet | Existing claim-safe leadership projection; bounded by NTH evidence-language rules | `00_CURRENT/Published_Admin_Share/ADMIN_SHARE_NTH_EXECUTIVE_PACKET_May-July_2026_CLAIM_SAFE_CURRENT_2026-08-14.xlsx` | DERIVED / PUBLISH-ONLY | NO CHANGE; SELECT FOR SEND | June control is `603.25h`. Operational themes are descriptive; exact workstream-hour splits are explicitly not presented without task-level attribution. Raw punch/internal evidence mechanics are excluded from the outward projection. |
| Site/device overview | Deployment/site projection; physical scope is not labor evidence | `00_CURRENT/Client_Share/Neuron Deployment — Site and Device Overview.xlsm` | DERIVED / PUBLISH-ONLY | NO CHANGE; HOLD UNLESS NEEDED | Client wording retained. Device/site counts state they describe deployment scope and do not create/allocate labor hours. Not part of the default Jon send set unless physical deployment scope is specifically useful. |
| Standalone June NTH summary | Historical admin-management workbook family | `00_CURRENT/Published_Admin_Share/Neuron Track Hours — June 2026 Summary.xlsm` | DERIVED / PUBLISH-ONLY | SKIP FOR THIS SEND | A newer claim-safe executive packet provides the same June control with a clearer recipient-facing posture. Do not send both. |
| Detailed August MTD workbook | August management workbook candidate | `00_CURRENT/Published_Admin_Share/Neuron Track Hours — August 2026 Month-to-Date.xlsm` | PRIVATE / DO-NOT-SYNC TO RECIPIENT in current form | SKIP / WITHHOLD | Current candidate contains private allocation/reconciliation mechanics and technical troubleshooting detail that are unnecessary for recipient-facing reconciliation and conflict with the current qualitative-admin outward posture. |
| Private August workstream math / internal allocation evidence | Internal evidence and management allocation controls | internal Drive evidence locations / canonical roster allocation ledger | PRIVATE / DO-NOT-SYNC | SKIP | Retained only as internal evidence. It may support bounded interpretation but must not be copied into the recipient package merely because it exists. |

## Reconciliation finding

A second-pass check against the current allocation-aware roster found that one completed August attendance day is explicitly multi-project. Therefore the older whole-shift subtotal must not be represented as an exact August NTH billing total. The recipient draft now reports the directly supportable record counts and gross attendance boundary instead of promoting private allocation arithmetic into an outward claim.

The current qualitative-admin profile remains the controlling outward pattern: direct paid attendance is quantitative; workstream interpretation is qualitative unless direct task/time evidence supports a split. Technical-scope controls may bound claims but do not create labor hours by themselves.

The through-2026-08-21 August control is intentionally period-bounded. Later roster activity is a newer source floor and is not silently projected backward into this MTD send.

## Recipient package

Default send set:

1. the updated Jon Zhou reconciliation draft / resulting email;
2. `ADMIN_SHARE_NTH_EXECUTIVE_PACKET_May-July_2026_CLAIM_SAFE_CURRENT_2026-08-14.xlsx`.

Hold unless specifically useful:

- `Neuron Deployment — Site and Device Overview.xlsm` for physical deployment scope.

Do **not** attach the current detailed August MTD workbook or the standalone June summary in this send.

## Proof ceiling

This receipt proves repository/Drive identity resolution, audience-boundary review, per-artifact authority classification, Drive draft update/readback, static workbook-content review on the accessible files, and reconciliation against the current allocation-aware roster. It does not prove email delivery, Jon's acceptance, Excel-for-Web rendering on Jon's device, or a newly regenerated August qualitative-admin workbook. The canonical August producer could not be executed in the current container because GitHub could not be resolved from that runtime; no substitute generator was invented.
