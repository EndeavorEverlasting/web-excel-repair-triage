# Prompt Kit Compute-Authority Evaluation

Paired Control/Treatment harness for measuring whether the strengthened Prompt Kit compute-authority contract produces **more useful compute**, not merely longer runs.

Canonical program plan: `harness/evals/COMPUTE_AUTHORITY_EVALUATION_SPRINT_PLAN.md`.

## Current proof state

- **IMPLEMENTED / WIRED / Phase-A VALIDATED** in this directory for fixture reachability, prompt freeze, graders, and aggregate scaffolding.
- **External-agent effectiveness:** empirically under evaluation (no OBSERVED EFFECTIVE claim yet).

## Quick start

```bash
python harness/evals/compute-authority/scripts/materialize_fixtures.py
python harness/evals/compute-authority/scripts/validate_fixtures.py --summary
python -m unittest tests.test_compute_authority_eval_harness -v
```

## Layout

See `manifest.json`. Hidden ground truth lives in each case's `evaluator.manifest.yaml` (and TC05 `evaluator/` oracles) and must never be copied into agent workspaces (`reset_fixture.py` enforces this).

## Pilot / main runs

Agent runs are out of band. For each run, create `harness/evals/compute-authority/runs/<run-id>/` with the evidence bundle from the evaluation plan, then:

```bash
python harness/evals/compute-authority/scripts/grade_run.py --run-dir harness/evals/compute-authority/runs/<run-id> --summary
python harness/evals/compute-authority/scripts/aggregate.py --summary
```

Blinded human scoring uses `templates/blinded-scoring.md`.
