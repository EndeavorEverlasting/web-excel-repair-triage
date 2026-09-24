# Campaign Doctrine — WORKING DRAFT (Sparse Brief)

> **Status: WORKING / UNKNOWNS — not a launch-ready doctrine.** Created because the current brief supplied no campaign brand, offer, audience, budget, geography, destination, or evidence. All unknowns are explicitly marked; no client scenario was manufactured. This document is subordinate to `AGENTS.md` and `harness/ad-campaign/DOCTRINE.md`. Use it to collect decisions before `PLANNED`.

## Identity and provenance

| Field | Value |
|---|---|
| **Campaign identity** | `WORKING-UNKNOWN-20260909` |
| **Doctrine version** | `0.1.0-draft` |
| **Source list** | Current conversation (no brand/offer/budget/audience evidence supplied); `AGENTS.md`; `harness/CONTEXT.md`; `harness/ad-campaign/DOCTRINE.md`; `harness/ad-campaign/campaign.v1.json`; `harness/ad-campaign/templates/campaign.v1.json`; `docs/ad-campaign/README.md` (no private workbook, testimonial, or platform evidence supplied) |
| **Owner** | `UNKNOWN — operator must assign campaign strategy owner` |
| **Date / timezone** | `2026-09-09 UTC` |
| **Stage** | `BRIEF → doctrine draft` — `BLOCKED` for `PLANNED`; see Open Decisions |

## Known facts (evidence-backed)

- Repository governance `AGENTS.md` is the top authority; campaign doctrine is subordinate. No campaign-specific facts are evidenced yet.
- Domain doctrine exists at `harness/ad-campaign/DOCTRINE.md` (10 rules) with contract `harness/ad-campaign/campaign.v1.json` (profile `ad-campaign`, stages BRIEF→MEASURED). Validated on `2026-09-09`.
- Synthetic fixture `harness/ad-campaign/fixtures/synthetic-campaign.v1.json` documents packet shape but its identities, claims, approvals and launch evidence are **invented test data — must not be reused as real proof**.
- No brand, product/service, offer/terms, audience research, geography/language, landing URL, past results, budget, period, or platform decision has been supplied in this brief. **All such fields are UNKNOWN, not zero or default.**
- No evidence reference (product sheet, price list, terms page, rights receipt) is available to support a publishable claim at this time.

## Hypotheses (not evidence)

| # | Hypothesis | Why it is only a hypothesis | Next check |
|---|---|---|---|
| H1 | A defined audience persona alone proves audience need | Persona description ≠ research; no interview/survey/usage data referenced | Replace with a cited source or label as unvalidated assumption in plan |
| H2 | Repeating an unqualified claim makes it publishable | Repetition does not create support; qualification must be retained | Move any such wording to Claims Ledger with `unsupported` status |
| H3 | A small concept description variation is a meaningful creative test | Synonym swap without distinct angle/hook/CTA does not test a learning | Require three materially different concepts per `P133` planning rule |

No audience, channel, or message hypothesis is claimed as fact in this draft.

## Open decisions (blocking)

1. **Brand / product / offer and terms** — exact name, what is sold, price, inclusions/exclusions, promotion window.
2. **Business goal and success definition** — primary objective, conversion event, measurement source/window, decision rule.
3. **Intended audience and geography/language** — who, where, language(s), targeting basis and data-rights basis.
4. **Landing destination** — URL(s), experience consistency with ad promise/CTA/terms, mobile readiness.
5. **Past results / available evidence** — product sheets, prior performance, testimonials/permissions (if any).
6. **Budget currency, ceiling, period/timezone, channel constraints** — all UNKNOWN; no default spend is set.
7. **Asset usage rights** — image/video/font/copy rights receipts and expiry.
8. **Who may approve creative and spend** — named approver(s) for `publish` and `spend`.
9. **Platform/jurisdiction scope** — which channels if any; specialist review for regulated claims.

Each open decision must be resolved with a source or explicitly recorded as `UNKNOWN — provisional` before `PLANNED` can pass. See `scripts/ad_campaign.py validate` for packet-level blocking.

---

## 1. Customer problem, value proposition, desired action, success definition

**Customer problem:** `UNKNOWN — no brief evidence`. Do not infer a problem from the repository domain (spreadsheet intelligence) or from a persona name. Record the problem only when a source (interview notes, support tickets, search data with method) is supplied.

**Supported value proposition:** `UNKNOWN — no evidence-backed proposition available`. No claim is supported at this draft stage; see Claims Ledger `CLAIMS_LEDGER_WORKING.md`. An unsupported proposition must not appear in publishable copy.

**Desired action (CTA destination):** `UNKNOWN — destination URL and CTA not supplied`. CTA, offer terms, and landing message must stay consistent when eventually defined.

**Campaign success definition:** `UNKNOWN — operator must define`. Must name one primary metric with numerator, denominator, source, period, and decision rule (per DOCTRINE rule 8). Example shape (not a commitment): `metric=CPA, numerator=spend, denominator=attributed conversions, source=platform reporting, window=30 days, decision=predefined statistical rule` — remains a placeholder until operator supplies objective and attribution context. Distinguish rates from counts, attributed outcomes from causal lift/profit, and delivery vs engagement vs conversion diagnostics.

**Audience evidence vs hypothesis:** Audience facts require a retained source and date. All persona-derived needs remain hypotheses (H1) until validated.

## 2. Voice, wording, hierarchy, offer constraints, forbidden claims

**Voice:** `UNKNOWN — no brand guide supplied`. Preserve the user's terminology where accurate when it becomes available. Until then, default to plain, verifiable language and avoid invented brand tone.

**Brand preferences vs mandatory constraints:**
- *Preference (hypothesis until approved):* tone adjectives, stylistic choices.
- *Mandatory (if later supplied, must be enforced):* legal qualifiers, claim limitations, terms presentation, trademark usage. Mark each rule's class when added.

**Acceptable wording examples (generic, evidence-dependent):**
- `Explore [Offer] — [qualified benefit] where supported` — allowed only when the bracketed benefit maps to a `supported` claim key with retained qualification.
- `[Product] includes [verifiable feature]` — allowed only with source and limitation retained.

**Unacceptable wording examples (forbidden in publishable copy):**
- `Best / #1 / guaranteed results / limited-time scarcity` without dated, qualified evidence.
- `Customer Johnson says "…"` — invented testimonial; never manufacture quotes or reviews.
- `Before/after showing profit/lift` without experiment evidence showing causal lift.
- Any claim that drops its qualification/limitation on reuse.

**Message hierarchy (to be populated):** `UNKNOWN`. When defined, order is: 1) primary supported promise (linked to claim key) 2) proof/qualifier 3) offer terms 4) CTA + destination. No hierarchy is assumed from sparse brief.

**Offer constraints:** `UNKNOWN — no offer supplied`. When supplied, record exact price, currency, term, eligibility, and expiry with source/date. Constraints travel with every asset; silent CTA/destination drift is blocked.

**Forbidden claims:** All claims without `supported` status and retained qualification are forbidden in published assets. Includes invented testimonials, scarcity, unqualified superlatives, unproven performance, and any price/guarantee not in the terms source. Unsupported rows stay in the ledger as `unsupported — excluded from publishable copy` and are not promoted by repetition.

## 3. Claims ledger

Canonical artifact: `docs/ad-campaign/CLAIMS_LEDGER_WORKING.md` + packet `doctrine.claims` array per `campaign.v1.json`.

Each claim row holds: `claim key | exact proposed wording | evidence reference + date | qualification/limitation | allowed context | evidence status (supported/unsupported) | business approver`.

Gate rule: only `supported` claims with evidence reference, retained qualifier, and named approver may appear in assets. Assets reference `claim_ids`; the validator blocks unknown or unsupported linkage. See ledger for the current (empty) state and insertion template.

## 4. Budget, schedule, channel, rights, approval authority

| Item | Value at this draft |
|---|---|
| **Budget currency** | `UNKNOWN` — no default currency is set |
| **Total ceiling** | `UNKNOWN` — no default spend; provisional planning uses percentages without spend authorization |
| **Period / timezone** | `UNKNOWN — start/end/timezone not supplied` |
| **Channel constraints** | `UNKNOWN` — no channel selected; no format/targeting/spend rule is assumed |
| **Audience / data rights** | `UNKNOWN — no audience definition or consent/rights basis supplied; no upload is authorized` |
| **Asset usage rights** | `UNKNOWN — no asset rights receipts supplied; rights check remains BLOCKED` |
| **Who may approve creative** | `UNKNOWN — assign owner` |
| **Who may approve spend/publish** | `UNKNOWN — explicit `publish` and `spend` authority required; preparation ≠ permission` |
| **Reserve** | `UNKNOWN` — allocation + reserve ≤ ceiling must be proven with exact arithmetic when defined |

`UNKNOWN` amounts stay unknown; planning stays provisional and never implies spend/publish permission.

## 5. Platform or jurisdiction requirements

Only two references have been checked on `2026-09-09` for general doctrine: [Google Ads misrepresentation policy](https://support.google.com/adspolicy/answer/6020955?hl=en-GB) (supported-claims boundary) and [Google Ads experiment monitoring](https://support.google.com/google-ads/answer/6318747?hl=en) (why performance needs experiment evidence). These are **references, not assumed platforms for this campaign**.

No channel has been selected for this brief, so no channel-specific format, dimension, duration, targeting, or policy rule is asserted. When a channel is selected, verify its current primary guidance at campaign start and record `source + date` in the doctrine; unresolved specialist review (legal/policy/format) stays as `BLOCKED — specialist review required` without claiming platform or legal approval.

---

## Close and next stage

**Material rules status:** Evidenced (governance, contract shape, reference fixtures, 10 doctrine rules) **or** explicitly unresolved (all campaign-specific facts above marked `UNKNOWN`). No fact has been inferred from a persona description, and no claim has been promoted to fact by repetition.

**Next stage capability:** `P132 Ad Campaign Harness Builder` / `P133 Ad Campaign Planner` can proceed only after the Open Decisions are filled or explicitly accepted as provisional. The harness will bind the next packet to `campaign_id=WORKING-UNKNOWN-20260909`, `revision=1`, `brief/doctrine/plan/assets` snapshot, and dependency on this doctrine version `0.1.0-draft`.

**Next executable action:** Operator supplies brand/offer/terms, objective/conversion definition, audience/geography/destination, evidence source for at least one claim, and currency/period or explicitly confirms `UNKNOWN — provisional`. No spend, publish, audience upload, account change, or message is authorized by this draft.

## Proof ceiling

Documented decision quality, stage binding, and evidence status traceability — not audience validation, platform approval, or campaign performance. Live proof requires observed platform state with campaign/ad identity, timestamp with timezone offset, and retained evidence, per `DOCTRINE.md` rule 6.
