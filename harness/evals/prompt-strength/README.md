# Prompt Strength Evaluation

This directory owns the prompt-strength recovery evaluation surfaces introduced by `harness/contracts/prompt-strength.v1.json`.

Current durable artifacts:
- `adversarial-regression-matrix.v1.json` — negative/positive semantic expectations across compiler identity, compute profiles, parallel dispatch, proof continuity, evidence-state integrity, integration, upstream intake, and closeout.

Canonical validation:

```bash
python scripts/validate_prompt_strength.py --summary
python -m unittest tests.test_prompt_strength_contract -v
```

The matrix is design/static evidence. Executable fixture conversion and downstream behavioral evaluation are successor phases in `harness/evals/PROMPT_STRENGTH_RECOVERY_SPRINT_PLAN.md`; repository/static PASS does not prove downstream model obedience.
