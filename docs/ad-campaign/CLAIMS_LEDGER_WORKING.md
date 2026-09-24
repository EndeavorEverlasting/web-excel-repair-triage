# Claims Ledger — WORKING DRAFT (Sparse Brief)

> **Status: WORKING / NO SUPPORTED CLAIMS.** No brand, offer, or evidence was supplied in the current brief. This ledger contains no publishable claim and demonstrates the required columns and gating. All rows are `unsupported — excluded from publishable copy` until a source, qualifier, and business approver are supplied. This artifact is `revision 0.1.0-draft` for `campaign WORKING-UNKNOWN-20260909`.

## Identity and provenance

| Field | Value |
|---|---|
| **Campaign identity** | `WORKING-UNKNOWN-20260909` |
| **Ledger version** | `0.1.0-draft` (matches `CAMPAIGN_DOCTRINE_WORKING.md` `0.1.0-draft`) |
| **Source list** | Current conversation (no claim evidence supplied); `harness/ad-campaign/DOCTRINE.md`; `harness/ad-campaign/campaign.v1.json` contract; `harness/ad-campaign/templates/campaign.v1.json` packet shape |
| **Owner** | `UNKNOWN — operator must assign claims owner / business approver` |
| **Date** | `2026-09-09 UTC` |
| **Packet binding** | When placed into `campaign.json`, `doctrine.claims[]` SHA participates in `scripts/ad_campaign.py snapshot`; review/authorization bind the snapshot SHA (see README snapshot section) |

## Known facts

- No evidence reference (product sheet, terms page, price list, study, rights receipt) has been supplied.
- No claim is supported; therefore **no claim is eligible for publishable copy** at this draft.
- Repeating a claim does not make it supported.

## Hypotheses

- `H-CLAIM-1`: An unqualified benefit statement may be publishable without limitation — **hypothesis, false until a retained qualifier and evidence are recorded**.

## Open decisions

1. Supply or explicitly waive each contemplated benefit/off er statement with source + date.
2. Name the qualification/limitation that must travel with each claim (e.g., eligibility, geography, time window).
3. Designate allowed context (placement/channel) per claim.
4. Assign a named business approver per claim.

---

## Ledger

| Claim key | Exact proposed wording | Evidence reference + date | Qualification / limitation | Allowed context | Evidence status | Business approver |
|---|---|---|---|---|---|---|
| `CLAIM-PLACEHOLDER-01` | `[Offer] does [benefit] — exact wording to be supplied` | `UNKNOWN — no source supplied` | `UNKNOWN — limitation must be retained (e.g., eligibility, geography, period)` | `UNKNOWN — no channel selected` | `unsupported — EXCLUDED from publishable copy. Do not use in assets.` | `UNKNOWN — no approver assigned` |

> Template for a future supported row (do not publish until filled):
> `CLAIM-02 | "Includes 24/7 email support for paid plans in EN region through 2026-12-31" | "Pricing & Support sheet v2.1, 2026-08-20, §Support" | "Paid plans only; EN region; excludes phone support" | "Search + website destination" | "supported" | "Jane Doe, Product, 2026-09-09"`

### Insertion rules

- Duplicate `claim key` values are rejected by `scripts/ad_campaign.py validate`.
- `supported` requires `evidence` text + qualifier retained. Missing evidence → `unsupported`.
- Assets may reference only `supported` claim keys via `assets[].claim_ids`; unknown or `unsupported` linkage is a `BLOCKED` gate.
- Include attribution to source with date; stale or un-sourced claims are re-verified before reuse.
- Keep the ledger as the single source of truth; do not duplicate wording without the key.

### Allowed-context and qualification semantics

- **Allowed context** is the placement/channel where the claim may appear (e.g., "Search text ad + landing page FAQ"). Until a channel is selected, leave `UNKNOWN — blocked`.
- **Qualification** stays with the wording in every asset and landing variant. Stripping a qualifier is a repair, not an edit, and reopens `claims` review.
- Changing a claim's wording, evidence, qualifier, or allowed context invalidates prior `REVIEWED`/`AUTHORIZED` bindings; regenerate the snapshot and rerun checks.

---

## Close and next stage

**Material rules:** All claim rows are explicitly `unsupported` and blocked from copy; the gate behavior is evidenced. No claim has been turned into fact by repetition.

**Next executable action:** Operator either (a) supplies a claim with exact wording + evidence reference + date + qualifier + allowed context + approver, marking it `supported`, or (b) confirms that no claim is ready and leaves the ledger empty/unsupported for provisional planning. Publishable assets remain `BLOCKED` until at least one supported claim exists.

**Proof ceiling:** Ledger integrity and linkage checks only (`scripts/ad_campaign.py validate` for `supported` linkage, budget arithmetic, snapshot binding). Evidence truth, legal sufficiency, and platform acceptance require external observation and named business approval.
