# LANE 09 — P67 Observed External-Agent Effectiveness

**Repo:** EndeavorEverlasting/web-excel-repair-triage  
**Wave:** E  
**Hard dependency:** Lane 08 publication complete; treatment identity frozen for this evaluation generation  
**Canonical owner:** P67 Repository Eval Framework Builder + `skill-evaluation`  
**Primary plan:** `harness/evals/COMPUTE_AUTHORITY_EVALUATION_SPRINT_PLAN.md`

## Mission

Close the final evidence gap without inventing a second eval system: execute the existing real external-agent pilot against the integrated/published treatment identity.

## Read first

- `harness/evals/COMPUTE_AUTHORITY_EVALUATION_SPRINT_PLAN.md`
- `harness/evals/compute-authority/README.md`
- `harness/evals/compute-authority/manifest.json`
- `harness/evals/compute-authority/runtime/adapter-contract.v1.json`
- frozen condition identities
- current main/release identity

## Owned scope

P67 compute-authority runtime evidence/aggregate outputs and only the plan/registry surfaces explicitly authorized by the canonical P67 phase map.

## Forbidden scope

- changing treatment prompt wording during the frozen study
- editing Prompt Kit behavior to improve results
- provider credentials/secrets/raw transcripts in tracked files
- starting Sprint 3 before a valid observed pilot
- claiming universal model/provider behavior

## Tasks

1. Refresh current main and record the exact integrated/published treatment identity/hash.
2. Materialize/validate fixtures and conditions.
3. Select an actually available external-agent adapter config satisfying the canonical adapter contract.
4. Run the 16-run balanced pilot.
5. Classify invalid/incomplete runs instead of scoring them silently.
6. Verify same-provider/agent/model identities per pair, zero hidden-gold leakage, zero forbidden-mutation escape.
7. Produce pilot aggregate and fixture-validity disposition.
8. If no adapter/credentials/quota exist, preserve `UNPROVEN_RUNTIME` and state the exact runtime gate; do not manufacture a repository task to fake progress.
9. Only if the pilot gate is valid may the existing Sprint-3 plan advance.

## Validation order

```bash
python harness/evals/compute-authority/scripts/materialize_fixtures.py
python harness/evals/compute-authority/scripts/validate_fixtures.py --summary
python harness/evals/compute-authority/scripts/conditions.py --summary
python -m unittest tests.test_compute_authority_eval_harness tests.test_compute_authority_runtime_harness -v
python harness/evals/compute-authority/scripts/pilot.py --plan-only --pilot-id closeout-plan-only --summary
```

Observed execution:

```bash
python harness/evals/compute-authority/scripts/pilot.py --adapter-config <adapter.json> --pilot-id <provider-model-pilot> --summary
```

## Safety

Keep credentials outside the repository; only allowlisted environment names may reach the subprocess. Do not persist raw prompt/response/clipboard/transcript/query/identity fields.

## Commit / integration contract

Runtime outputs remain under ignored `runs/`, `aggregate/`, and/or `Outputs/` per canonical plan. Tracked plan/eval updates occur only after valid runtime evidence and through P67 ownership.

## Proof level / ceiling

Target: OBSERVED for the exact tested agent/model/provider population and study conditions.  
Ceiling: no universal generalization beyond that population.

## Exact final response

Report adapter identity as safely exposable, treatment/control identities, valid/invalid run counts, leakage/mutation checks, aggregate disposition, exact proof ceiling, and whether Sprint 3 is dependency-ready.

## NEXT COMMAND

```bash
python harness/evals/compute-authority/scripts/pilot.py --plan-only --pilot-id closeout-plan-only --summary
```
