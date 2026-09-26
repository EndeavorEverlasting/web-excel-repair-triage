# PACKET PK-B02C — Routing-decision continuation / Evidence Spine

**packet_id:** `PK-B02C-routing-decision`  
**destination:** TokenCorridor PK-B02C  
**donor_prs:** `#600`

## Donor identity

| Field | Value |
| --- | --- |
| donor_repo | `EndeavorEverlasting/web-excel-repair-triage` |
| donor_branch | `feat/rrb03-routing-decision-r3-20260919` |
| donor_head_sha | `4f5ee2372ed4135238de17c7146b3074a1151757` |
| main_comparison_floor | `0fd4c578610f1c3ae81fadd795ace3bb97d7ebc3` |
| mergeable | CONFLICTING (rebase/reconcile required before Triage merge; prefer TokenCorridor port) |

## Exact unique source paths vs main

- `harness/prompt-topology/EVIDENCE_SPINE_SPRINT_MAP.md`
- `harness/test-floor.v1.json`
- `scripts/evidence_spine_runtime.py`
- `scripts/prompt_routing_decision.py`
- `tests/test_evidence_spine_runtime.py`
- `tests/test_prompt_routing_decision_prompt.py`

## Exact tests / validators / contracts

- `tests/test_prompt_routing_decision_prompt.py`
- `tests/test_evidence_spine_runtime.py`
- Evidence Spine sprint map obligations in `harness/prompt-topology/EVIDENCE_SPINE_SPRINT_MAP.md`
- Deterministic floor registration via `harness/test-floor.v1.json` (collision-sensitive)

## Destination module owner

TokenCorridor PK-B02C routing-decision / Evidence Spine continuation owner.

## Already-integrated behavior to EXCLUDE

- Evidence Spine architecture already on main from prior P95 work — port only the **routing-decision compiler/runtime delta** and associated focused tests/map edits unique to #600
- Do not re-litigate closed Evidence Spine plan history already contained on main

## Forbidden Triage-domain paths

- Excel/OOXML, billing, roster, attendance
- Unrelated Prompt Kit website chrome

## Compatibility obligations

- Routing decisions must consume current registry authority
- Do not invent a second Evidence Spine ledger

## Generation rules

- No generated site ownership unless destination packaging requires registry rebuild after prompt additions (none expected for pure routing script port)

## Validation commands

```bash
python -m unittest tests.test_prompt_routing_decision_prompt tests.test_evidence_spine_runtime -v
git diff --check origin/main...4f5ee2372ed4135238de17c7146b3074a1151757
```

## Parity acceptance gate

Current-registry prompt decisions compile deterministically; Evidence Spine runtime continuation behavior covered by focused tests; test-floor registration present without weakening unrelated floor entries.

## Donor closure gate

Keep #600 open until TokenCorridor Sync C B02C containment; then close as CLOSE_AFTER_TOKENCORRIDOR_CONTAINMENT. Do not independently modernize in Triage.

## Stop conditions

- Resolving conflicts by dropping unique routing tests
- Merging into Triage solely to reduce open-PR count
- Colliding with active `harness/test-floor.v1.json` writers without serialize

## Proof ceiling

Donor focused tests after conflict-reconciled tree + destination containment. Conflicted PR mergeability is not destination proof.
