# PACKET PK-B01A — Operator state presentation (Sync A)

**packet_id:** `PK-B01A-operator-state-presentation`  
**destination:** TokenCorridor M2 / `plans/active/M2-PROMPT-KIT-MIGRATION-STATE-PRESENTATION.*` → PK-B01A  
**donor_prs:** `#651`  
**status:** PRE-MERGE floor packet — refresh integrated SHAs immediately after #651 merges

## Donor identity

| Field | Value |
| --- | --- |
| donor_repo | `EndeavorEverlasting/web-excel-repair-triage` |
| donor_branch | `feat/operator-state-presentation-20260926` |
| donor_head_sha (pre-merge repair) | `c638fbc7ce426d05f0a3bcd988cd9be1b20b0b07` |
| prior_head_observed | `fc9da406bffa73c030660d49d3fd7c63c07a244e` |
| operant_projection_refresh_on_branch | `362f920c` |
| main_comparison_floor | `0fd4c578610f1c3ae81fadd795ace3bb97d7ebc3` (#650 merged) |
| integrated_main_sha | `PENDING_SYNC_A` |
| merge_sha | `PENDING_SYNC_A` |

## Exact unique source paths

- `registry/prompts/actionable-next-step-policy.v1.json` (`state_presentation` + `state_presentation_marker`)
- `scripts/build_prompt_kit_registry.py` (appendix upgrade includes state presentation)
- `harness/specs/operator-delivery.md`
- `tests/test_operational_closeout_contract.py`
- Generated only via builder: `web/prompt-kit/index.html`
- Collateral on branch (not B01A semantics; keep parity): `web/prompt-kit/resources.v1.json`, `registry/resources/operant-external-resource-gaps.v1.json`

## Exact tests / validators / contracts

- `tests/test_operational_closeout_contract.py`
- `python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check`
- `python scripts/validate_operant_external_resources.py --summary` (collateral if resources touched)
- Product-boundary: `registry/prompts/product-boundaries.v1.json` (do not invent second product)

## Destination module owner

TokenCorridor Prompt Kit / AFKAF shared operator-state presentation under M2 PK-B01A (canonical plan owns module path).

## Already-integrated behavior to EXCLUDE

- #650 mutation non-weakening lifecycle already on main@0fd4c578 — do not re-port
- Pre-#651 closeout/actionability contracts already on main — port only the **state presentation** delta + appendix upgrade rule

## Forbidden Triage-domain paths

- `registry/prompts/management-operations-prompts.v1.json`
- billing/roster/Excel/OOXML engines
- attendance/time evidence packs

## Compatibility obligations

- Typed state text remains machine authority; icons are presentation only
- Combined Prompt Kit site remains Triage compatibility surface until M5
- Do not claim M4 cutover from this packet

## Generation rules

- Mutate policy/builder sources only
- Regenerate site with `python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html`
- Never hand-edit generated HTML
- Operant resources only via `python scripts/sync_operant_external_resources.py`

## Validation commands

```bash
python -m unittest tests.test_operational_closeout_contract -v
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
git diff --check
```

## Parity acceptance gate

Destination renders the same typed-state matrix contract (`Item | State | Meaning | Exact next transition`), inherits presentation exactly once on operational prompts, and upgrades legacy appendices missing `OPERATOR STATE PRESENTATION CONTRACT`.

## Donor closure gate

Close/supersede #651 only after TokenCorridor proves B01A containment **and** Triage Sync B authorizes donor downgrade. Until then keep Triage as donor authority for this capability.

## Stop conditions

- Required CI/review blocker on #651
- Destination module owner missing in TokenCorridor plan
- Attempt to hand-edit generated site

## Proof ceiling

Repository/CI proof on Triage head + destination unit/parity proof. Not live operator UX certification.

## Proof already run on donor head `c638fbc7`

- focused state-presentation tests PASS
- Prompt Kit `--check` PASS
- Operant validator summary `status=valid` (59 resources)
