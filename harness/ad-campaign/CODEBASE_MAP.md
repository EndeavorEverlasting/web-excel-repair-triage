# Ad campaign domain

Owns reusable campaign doctrine, planning, creative production, launch review, and measurement. Start at [the user guide](../../docs/ad-campaign/README.md) or its generated prompt pack. Re-enter at the first incomplete stage.

| Need | Canonical owner | Proof |
|---|---|---|
| Domain decision rules | `harness/ad-campaign/DOCTRINE.md` | Claims, authority, budget and measurement review |
| Packet/stage contract | `harness/ad-campaign/campaign.v1.json` | `scripts/ad_campaign.py validate` |
| Blank campaign workspace | `harness/ad-campaign/templates/campaign.v1.json` | `scripts/ad_campaign.py init` refuses existing outputs |
| Campaign prompts | `registry/prompts/management-operations-prompts.v1.json`, profile `ad-campaign` | Helper, semantic tests and generated parity |
| Standalone copy pack | `scripts/build_ad_campaign_pack.py` | `python scripts/build_ad_campaign_pack.py --check` |
| Stage and numeric failure cases | `tests/test_ad_campaign.py` | `python -m unittest tests.test_ad_campaign -v` |
| Website discovery | Existing search, `AD_CAMPAIGNS` named pack | `tests.test_ad_campaign_prompts` |

Stages: BRIEF → PLANNED → PRODUCED → REVIEWED → AUTHORIZED → LIVE → MEASURED. Earlier stages may be useful drafts while a later requested gate reports BLOCKED. Each gate accumulates all preceding requirements. Material input changes invalidate review, authorization, launch and results bindings. An observed live state is supplied evidence; the CLI never accesses an ad account or spends money.

Proof ceiling: deterministic evidence-packet checks and synthetic tests. Humans or agents must still verify source truth, creative quality, platform requirements, authorization authenticity, and live results. Read only the chosen stage's sources; private campaign packets belong outside Git.
