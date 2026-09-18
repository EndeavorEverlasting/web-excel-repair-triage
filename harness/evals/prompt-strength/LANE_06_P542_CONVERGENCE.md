# LANE 06 — Repair Drift and Integrate #542

**Repo:** EndeavorEverlasting/web-excel-repair-triage  
**PR / branch:** #542 / `feat/execution-boundary-enforcement-architecture-20260918`  
**Current observed head:** `c6e330fe6676a974a79cf384dd279edfea4a9ab3`  
**Wave:** B  
**Hard dependencies for mutation/integration:** Lane 04 + Lane 05 integrated; read-only diagnosis may begin earlier  
**Writer:** singular #542 finalization owner

## Mission

Finish the already review-closed #542 candidate, repair the one observed deterministic donor-projection drift, refresh onto the newest main, rerun exact proof, and merge.

## Current evidence

- zero unresolved #542 review threads at `c6e330fe...`;
- Prompt Quality History, validator profile, App, Operational, Pages, Artifact, AI evals, boundary-adjacent web/topology checks were green or still running at last refresh;
- `Operant external resource refresh` failed because:
  `Outputs/operant-external-resources/resources.v1.json` differed from tracked `web/prompt-kit/resources.v1.json`;
- this is a tracked projection drift, not provider degradation.

## Read first

- current #542 checks/reviews
- `.ai/skills/operant-external-resource-intake/SKILL.md`
- `harness/contracts/operant-external-resource-intake.v1.json`
- `scripts/sync_operant_external_resources.py`
- `scripts/validate_operant_external_resources.py`
- `.github/workflows/operant-external-resource-refresh.yml`
- current main after Lane 04/05
- canonical Prompt Kit builder

## Owned scope

Existing #542 diff plus current donor projection files:
- `web/prompt-kit/resources.v1.json`
- `registry/resources/operant-external-resource-gaps.v1.json`
- generated Prompt Kit only through canonical builder when affected.

## Forbidden scope

#537 prompt-strength semantics, #543 source-owner files beyond merged-main reconciliation, unrelated release/versioning files, manual donor JSON edits when canonical sync can produce them.

## Tasks

1. Refresh main/#542. Confirm review threads are still resolved; if new ones exist, disposition them first.
2. Wait for no provider job: run local/current deterministic proof while hosted jobs are pending.
3. Reproduce donor drift without mutating tracked output:

```bash
mkdir -p Outputs/operant-external-resources
python scripts/sync_operant_external_resources.py \
  --output Outputs/operant-external-resources/resources.v1.json \
  --gaps-output Outputs/operant-external-resources/gaps.v1.json
cmp Outputs/operant-external-resources/resources.v1.json web/prompt-kit/resources.v1.json
cmp Outputs/operant-external-resources/gaps.v1.json registry/resources/operant-external-resource-gaps.v1.json
```

4. If drift persists and source identities are valid, update canonical tracked projections through the producer:

```bash
python scripts/sync_operant_external_resources.py
```

5. Validate resource contract/tests and catalog live-proof where network/provider access exists.
6. After Lane 04 and Lane 05 integrate, merge refreshed main into #542 and rerun affected proof under final generated/line-ending policy.
7. Regenerate Prompt Kit through builder if source/projection changes affect it.
8. Run local required checks + exact-candidate hygiene.
9. Push #542 and inspect exact-head provider checks. Diagnose any red check; do not label candidate drift provider-degraded.
10. Merge when exact head is green/authorized. Refresh main and prove containment + current boundary/resource content.

## Validation order

```bash
python scripts/validate_operant_external_resources.py --summary
python -m unittest tests.test_operant_external_resources tests.test_external_prior_art_gate -v
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
python scripts/run_repository_action.py --action required-checks-proof --base-ref origin/main --report Outputs/repository-actions/required-checks-proof.json
git diff --check
git diff --cached --check
```

If external network proof is available:

```bash
python scripts/search_operant_external_catalog.py --live-proof --summary --receipt-output Outputs/operant-external-resources/catalog-search-live-proof.json
```

## Safety

No manual generated HTML. No force push. No raw donor body copying. Preserve metadata-only/copyright boundary. Do not retry an unchanged external provider merely for activity.

## Commit / push / merge contract

Use existing #542 branch. Commit deterministic projection refresh separately when useful. Merge only at exact validated head.

## Proof level / ceiling

Target: VALIDATED + INTEGRATED #542 with current donor projection.  
Ceiling: repository/provider integration; no universal external donor availability or downstream model-effectiveness proof.

## Exact final response

Report #542 refreshed head, donor source/resolved revisions, projection drift before/after, local receipts/tests, provider checks, merge SHA, current-main containment/content proof, and next #537 gate.

## NEXT COMMAND

```bash
git fetch --all --prune --tags && git switch feat/execution-boundary-enforcement-architecture-20260918 && python scripts/sync_operant_external_resources.py --output Outputs/operant-external-resources/resources.v1.json --gaps-output Outputs/operant-external-resources/gaps.v1.json
```
