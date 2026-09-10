# Ad campaigns

Use [the six-prompt pack](PROMPT_PACK.md) to take a campaign from its brief through planning, creative production, launch review, and results. Start with the first incomplete stage. The prompts recover context already supplied; a Git repository is optional.

| Stage | Output |
|---|---|
| Doctrine Builder | Brand/offer rules, supported claims and decision owners |
| Harness Builder | Campaign workspace, artifact manifest and handoffs |
| Planner | Strategy, budget allocation, creative brief and measurement plan |
| Creative Executor | Actual ad copy and rendered assets or clearly labeled production briefs |
| Launch Reviewer | Repaired creative, readiness checks, exact-scope approval package and observed launch status |
| Results Analyst | Calculations, findings and the next bounded experiment |

In Operant, search **ad campaign**, or assign the **Ad Campaigns** pack to a named profile tab. All six prompts carry the `ad-campaign` profile. The standalone pack is generated from those same canonical source records, without repository-only policy appendices. It is never a separate authoring source.

## Repository-assisted workflow

Create a new campaign packet with a unique output directory. Keep client data in an approved private workspace; never commit completed packets or receipts. The following creates an empty example under ignored `Outputs/`, with no account access or ad spend:

```powershell
python scripts/ad_campaign.py init --output Outputs/ad-campaign-example --campaign example
python scripts/ad_campaign.py validate --input Outputs/ad-campaign-example/campaign.json --target BRIEF
```

Use the prompts to populate that packet. The [complete synthetic packet](../../harness/ad-campaign/fixtures/synthetic-campaign.v1.json) documents every row and evidence-record shape. All of its identities, claims, approval and launch evidence are invented test data; never reuse those entries as real approval or runtime proof. Copy its structure only, replace the campaign facts, and leave review/authorization/launch records empty until real evidence exists. The starter intentionally lacks campaign facts; a later gate reports the missing fields. Choose `PLANNED`, `PRODUCED`, `REVIEWED`, `AUTHORIZED`, `LIVE` or `MEASURED` as the target:

```powershell
python scripts/ad_campaign.py validate --input Outputs/ad-campaign-example/campaign.json --target PLANNED
```

Exit 0 means the requested evidence-packet gate passes, 1 means BLOCKED, and 2 means malformed input/output. The report identifies the highest evidenced stage and missing requirements. A passing packet does not authenticate its evidence or prove advertising effectiveness.

When the plan/assets are final, `python scripts/ad_campaign.py snapshot --input Outputs/ad-campaign-example/campaign.json` prints their current SHA-256 binding. Reviewers record that binding with their check evidence; an authorized approver records it with the exact permitted actions. This command grants no permission. Any change to the campaign identity, revision, brief/account/budget/period, doctrine, plan or assets invalidates old bindings. The reviewed account, destination, currency and budget are within that bound packet.

Only a real platform observation can support a launch record. Pending review stays pending. Permission and prepared assets cannot substitute for observed live evidence. Review and approval timestamps must include timezone offsets.

## Measurement

`python scripts/ad_campaign.py metrics --input results.json` accepts one reporting aggregate with `impressions`, `clicks`, `spend`, `conversions`, and optional `revenue`. Keep its source, period, currency and attribution context in the campaign packet. Never combine incompatible reporting windows, currencies or attribution definitions merely to fit the input.

CTR and click-conversion rate are ratios (0.02 means 2%). CPC, CPM and CPA use the supplied spend currency. ROAS is attributed revenue divided by spend, not profit or causal lift. Missing/zero denominators return `null` with a reason. NaN, infinity, negative amounts, booleans masquerading as numbers, duplicate JSON keys, and invalid counts are rejected. JSON decimal tokens that cannot survive decoding without precision loss are rejected rather than rounded; budget comparisons use exact arithmetic.

## Ownership and verification

[Doctrine](../../harness/ad-campaign/DOCTRINE.md) owns campaign rules; [the domain map](../../harness/ad-campaign/CODEBASE_MAP.md) routes implementation. [The contribution record](CONTRIBUTION.md) records prior-art decisions, scope authorization, and evidence limits.

```powershell
python -m unittest tests.test_ad_campaign tests.test_ad_campaign_prompts -v
python scripts/build_ad_campaign_pack.py --check
python scripts/prompt_registry_ops.py validate
```

These checks prove deterministic campaign packet behavior and registry/discovery parity. They do not claim a live campaign, ad-platform approval, model-evaluation score, or business results.
