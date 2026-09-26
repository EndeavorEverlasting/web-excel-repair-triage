# PACKET PK-B02A — Upstream capability watch (+ freshness recovery)

**packet_id:** `PK-B02A-upstream-capability-watch`
**destination:** TokenCorridor PK-B02A
**donor_prs:** `#619` → `#631` (**intent chain only** — not git-stacked)

## Chain anatomy (critical)

| Check | Evidence |
| --- | --- |
| `#619` ancestor of `#631`? | **NO** — `git merge-base --is-ancestor ab35d72f… fb730893…` fails |
| Path-set overlap (three-dot unique vs floor)? | **DISJOINT** — zero shared unique file paths |
| What `#631` tip carries for `#619` overlap paths | **main** blobs for workflow/intake/validate — **not** `#619` content |
| Design link | `#631` sprint map cites U1 proof on `#619` head `ab35d72f…` and adds Freshness Recovery F0–F6 |

**Transplant rule:** port `#619` code/contracts/tests as Slice A, then merge `#631` freshness/recovery **sections** into the sprint map as Slice B. Do **not** cherry-pick `#631` expecting it to contain capability-watch runtime. Do **not** replace whole intake/validate/workflow files with tip blobs — apply additive `capability_watch` hunks only.

## Donor identity

| Field | Value |
| --- | --- |
| donor_repo | `EndeavorEverlasting/web-excel-repair-triage` |
| main_comparison_floor | `0fd4c578610f1c3ae81fadd795ace3bb97d7ebc3` |
| #619 head | `ab35d72f7149e79fcd15cabd5f65ec8081a3470c` (`feat/upstream-capability-watch-contract-floor-20260920`) |
| #631 head | `fb730893b9e73bd06729f4ab8dffed5852ae47c0` (`plan/upstream-source-freshness-recovery-20260922`) |
| #619 mergeable | MERGEABLE |
| #631 mergeable | MERGEABLE |

## Exact unique source paths vs main

### From #619 (contract/runtime floor)

- `.github/workflows/operant-external-resource-refresh.yml`
- `harness/contracts/operant-external-resource-intake.v1.json`
- `registry/resources/upstream-capability-impact-edges.v1.json`
- `scripts/upstream_capability_watch.py`
- `scripts/validate_operant_external_resources.py`
- `tests/test_upstream_capability_watch.py`

### From #631 (successor plan extension only vs main)

- `docs/plans/UPSTREAM_CAPABILITY_WATCH_SPRINT_MAP.md`

## Exact tests / validators / contracts

- `tests/test_upstream_capability_watch.py`
- capability-watch checks inside `scripts/validate_operant_external_resources.py`
- contract: `harness/contracts/operant-external-resource-intake.v1.json`
- impact edges: `registry/resources/upstream-capability-impact-edges.v1.json`
- workflow wiring: `.github/workflows/operant-external-resource-refresh.yml`

## Destination module owner

TokenCorridor PK-B02A upstream capability-watch / source-floor freshness owner (canonical convergence plan).

## Already-integrated behavior to EXCLUDE

- Current main Operant intake/discovery without the watch kernel (`capability_watch` key absent on floor)
- Tip blobs of intake/validate/workflow that merely mirror main — transplant **additive** capability_watch / edges / watch modules only
- Any later main refresh of donor pins unrelated to watch state machine
- Claiming U2+ runtime proven from `#631` docs alone (map marks those unproven)

## Forbidden Triage-domain paths

- Excel/OOXML, billing, roster, attendance engines
- Prompt Kit website marketing content unrelated to watch

## Compatibility obligations

- Keep `operant-external-resource-intake` as the only donor registry
- Do not auto-author prompts from donor drift
- Preserve observed-vs-processed identity separation
- Do not race findability A1 (`#636`) into capability-watch contract/validator/workflow surfaces

## Generation rules

- No generated Prompt Kit site ownership in this packet
- If intake contract changes require projection refresh, use `scripts/sync_operant_external_resources.py` only

## Validation commands

```bash
python -m unittest tests.test_upstream_capability_watch tests.test_operant_external_resources tests.test_external_prior_art_gate -v
python scripts/validate_operant_external_resources.py --summary
git diff --check origin/main...ab35d72f7149e79fcd15cabd5f65ec8081a3470c
git diff 0fd4c578610f1c3ae81fadd795ace3bb97d7ebc3...fb730893b9e73bd06729f4ab8dffed5852ae47c0 -- docs/plans/UPSTREAM_CAPABILITY_WATCH_SPRINT_MAP.md
```

## Parity acceptance gate

UNSEEN→CURRENT baseline; last_observed vs last_processed distinct until durable routing; transition dedupe; routing failure preserves processed identity; missing impact edge retains source event; promotion cannot jump changed→integrated; `#631` F0–F6 freshness/recovery sections present with `#619` U1 head pin; `#631` not treated as substitute for `#619` runtime.

## Donor closure gate

Close #619/#631 only after TokenCorridor Sync C reports B02A containment with ancestry+content proof for **both** slices.

## Stop conditions

- Treating `#619→#631` as a git-stacked branch and cherry-picking `#631` alone
- Flattening `#619`+`#631` into undocumented cherry-picks
- Replacing whole intake/validate/workflow tip blobs instead of additive capability_watch hunks
- Creating a second donor registry
- Merging into Triage merely to tidy open PRs
- Inventing non-empty production impact edges without owner review

## Proof ceiling

Donor branch unit/validator proof + destination containment receipt. Scheduled live donor drift remains a separate Operant refresh concern.
