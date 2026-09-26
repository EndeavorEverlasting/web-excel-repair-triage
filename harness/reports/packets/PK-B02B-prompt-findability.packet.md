# PACKET PK-B02B — Prompt findability / wayfinding

**packet_id:** `PK-B02B-prompt-findability`  
**destination:** TokenCorridor PK-B02B  
**donor_prs:** `#630` → `#636` (preserve #630 design intent when extracting #636 implementation)

## Donor identity

| Field | Value |
| --- | --- |
| donor_repo | `EndeavorEverlasting/web-excel-repair-triage` |
| main_comparison_floor | `0fd4c578610f1c3ae81fadd795ace3bb97d7ebc3` |
| #630 head | `087d49f870d0fbc4a8cb120484ab852a76f22c82` (`plan/prompt-findability-agent-readability-20260922`) |
| #636 head | `590de22304ecbcf79d148b7774beafdda9a02fef` (`feat/prompt-findability-f0-a1-20260922`) |

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
- Operant intake skill body already on main except the #636 wayfinding route deltas

## Forbidden Triage-domain paths

- Excel/billing/roster product code
- Unrelated Prompt Kit UX favorites/gameplay PRs

## Compatibility obligations

- Preserve progressive disclosure: do not preload full harness
- Donor prior-art route remains intake→P79, not automatic authoring

## Generation rules

- No Prompt Kit HTML generation required for this packet unless destination rebuilds a site that embeds CONTEXT excerpts

## Validation commands

```bash
python -m unittest tests.test_context_architecture -v
git diff --check origin/main...590de22304ecbcf79d148b7774beafdda9a02fef
```

## Parity acceptance gate

F0 wayfinding baseline + A1 donor prior-art route cases pass; CONTEXT architecture tests encode expected primary owners; #630 sprint-map intent remains the design authority for gaps not yet implemented.

## Donor closure gate

Close #630/#636 only after TokenCorridor Sync C B02B containment proof.

## Stop conditions

- Porting #636 without #630 intent document
- Forking duplicate findability semantics in Triage after packet emission

## Proof ceiling

Donor focused tests + destination parity. Not full Prompt Kit browser tutorial certification unless destination requires it.
