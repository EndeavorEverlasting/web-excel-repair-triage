# PACKET PK-B02B — Prompt findability / wayfinding

**packet_id:** `PK-B02B-prompt-findability`
**destination:** TokenCorridor PK-B02B
**donor_prs:** `#630` → `#636` (**intent chain only** — not git-stacked)

## Chain anatomy (critical)

| Check | Evidence |
| --- | --- |
| `#630` ancestor of `#636`? | **NO** — `git merge-base --is-ancestor 087d49f8… 590de223…` fails |
| Path-set overlap (three-dot unique vs floor)? | **DISJOINT** — plan path vs implementation paths |
| Scope of `#636` vs `#630` plan | `#636` implements **F0 + A1 only**; B1/C/D remain plan-only |
| Design link | Preserve `#630` sprint-map intent when extracting `#636` implementation |

**Transplant rule:** keep `#630` plan as design authority; port `#636` wayfinding evals/fixtures + CONTEXT/SKILL/test hunks. Do **not** claim plan alone proves F0/A1. Do **not** expand A1 into `#619` capability-watch contract/validator/workflow.

## Donor identity

| Field | Value |
| --- | --- |
| donor_repo | `EndeavorEverlasting/web-excel-repair-triage` |
| main_comparison_floor | `0fd4c578610f1c3ae81fadd795ace3bb97d7ebc3` |
| #630 head | `087d49f870d0fbc4a8cb120484ab852a76f22c82` (`plan/prompt-findability-agent-readability-20260922`) |
| #636 head | `590de22304ecbcf79d148b7774beafdda9a02fef` (`feat/prompt-findability-f0-a1-20260922`) |
| #630 mergeable | MERGEABLE |
| #636 mergeable | MERGEABLE |

## Exact unique source paths vs main

### From #630 (design intent)

- `docs/plans/PROMPT_FINDABILITY_AGENT_READABILITY_SPRINT_MAP.md`

### From #636 (implementation)

- `.ai/skills/operant-external-resource-intake/SKILL.md`
- `harness/CONTEXT.md`
- `harness/evals/fixtures/prompt-wayfinding-route-cases.v1.json`
- `harness/evals/prompt-wayfinding-baseline.v1.json`
- `tests/test_context_architecture.py`

## Exact tests / validators / contracts

- `tests/test_context_architecture.py`
- `harness/evals/prompt-wayfinding-baseline.v1.json`
- fixtures: `harness/evals/fixtures/prompt-wayfinding-route-cases.v1.json`

## Destination module owner

TokenCorridor PK-B02B findability / wayfinding / context routing owner.

## Already-integrated behavior to EXCLUDE

- Generic CONTEXT progressive-disclosure already on main without F0/A1 wayfinding evals
- Operant intake skill body already on main except the `#636` wayfinding/de-dupe hunks — apply hunks only; do not wholesale-replace tip
- `#630` plan path is absent on main — port separately; do not assume `#636` carries it
- Generated result path `Outputs/prompt-wayfinding-baseline.json` if present — output only, not Triage product authority

## Forbidden Triage-domain paths

- Excel/billing/roster product code
- Unrelated Prompt Kit UX favorites/gameplay PRs

## Compatibility obligations

- Preserve progressive disclosure: do not preload full harness
- Donor prior-art route remains intake→P79, not automatic authoring
- A1 must point at contract `sources[]` rather than copying donor lists into the skill body

## Generation rules

- No Prompt Kit HTML generation required for this packet unless destination rebuilds a site that embeds CONTEXT excerpts

## Validation commands

```bash
python -m unittest tests.test_context_architecture.PromptWayfindingBaselineTests -v
python scripts/validate_context_architecture.py --summary
git diff --check origin/main...590de22304ecbcf79d148b7774beafdda9a02fef
```

## Parity acceptance gate

F0 wayfinding baseline + A1 donor prior-art route cases pass; CONTEXT architecture tests encode expected primary owners; `#630` sprint-map intent remains the design authority for B1/C/D gaps not yet implemented.

## Donor closure gate

Close #630/#636 only after TokenCorridor Sync C B02B containment proof for **both** plan and F0/A1 implementation slices.

## Stop conditions

- Treating `#630→#636` as a git-stacked branch
- Porting `#636` without `#630` intent document
- Expanding A1 into `#619` intake contract/validator/workflow
- Claiming B1/C/D done from F0/A1 alone
- Forking duplicate findability semantics in Triage after packet emission

## Proof ceiling

Donor focused tests + destination parity. Not full Prompt Kit browser tutorial certification unless destination requires it.
