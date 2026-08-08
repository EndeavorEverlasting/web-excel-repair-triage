# Prompt Language Audit

## Trigger

Use this skill when canonical prompt records, actionability policy, the Prompt Kit builder, or generated prompt language changes, or when empty, lazy, optional-only, observation-only, PR/status/log-only, ownerless, artifactless, validatorless, or generic next actions are suspected.

Do not use it to edit generated HTML directly or to sample only a convenient subset of prompts.

## Required inputs

- Repository governance and current Git/PR floor.
- `docs/prompts.json` and every registered prompt extension.
- `registry/prompts/actionable-next-step-policy.v1.json`.
- `scripts/build_prompt_kit_registry.py` and the checked-in Prompt Kit website.
- `harness/evals/prompt-language-audit.v1.json` and its fixtures.
- Existing prompt tests, review findings, and known model failure examples.

## Outputs

- A complete prompt inventory.
- Exactly one `pass`, `repair`, `defer`, or `not_applicable` disposition for every prompt.
- Stable rule IDs, severity, exact field, evidence, and proposed repair for each finding.
- A machine-readable `prompt-language-audit-result/v1` report.
- In repair mode, canonical registry/policy/test changes and regenerated exact-parity Prompt Kit output.

## Procedure

1. Record the repository, branch/worktree, lane, scope, validation order, and proof ceiling.
2. Load every canonical base and extension prompt; do not sample.
3. Load the effective prompts produced by the registered builder and pair them by prompt ID.
4. Fail coverage when IDs are duplicated, omitted, added only after rendering, or the disposition count differs from the canonical prompt count.
5. Evaluate canonical metadata and complete copy-safe content for empty, placeholder, optional-only, observation-only, status/PR/log-only, generic, ownerless, artifactless, validatorless, reconstruction-heavy, contradictory, stale, or incomplete language.
6. Evaluate the effective prompt for the tracked actionability contract. A policy marker alone is not sufficient when required behavior is absent.
7. In audit mode, emit findings without mutating source. Error-severity contract failures block the run; warnings identify bounded canonical-source repair work.
8. In strict repair mode, reproduce each valid finding with a fixture, repair the canonical source or policy, regenerate through the registered builder, and require zero warning findings for the owned scope.
9. Never repair only `web/prompt-kit/index.html`; regenerate it from canonical source and prove exact parity.
10. Commit source, tests, policy, and deterministic generated output together when repair is authorized.

## Guardrails

- Never skip a prompt silently.
- Never treat a sampled review as full-registry proof.
- Never weaken a rule or fixture solely to make the audit green.
- Never let shared appended policy hide missing canonical-source intent without recording a repair finding.
- Never write reports into `Candidates/` or `Active/`.
- Never claim provider or runtime compliance from static language checks.

## Validation

```powershell
python -m unittest tests.test_prompt_language_audit -v
python scripts\evaluate_prompt_language.py --output Outputs\prompt-language-audit.json --summary
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
python scripts\validate_harness.py
git diff --check
```

The report must state equal canonical, effective, and disposition counts; complete coverage; zero error findings; P62 presence; and the exact result path.

## Proof ceiling

This skill proves exhaustive static language coverage, canonical/effective registry pairing, rule execution, and deterministic generated-site parity. It does not prove that every model or provider will follow the language, nor does it prove technician or production behavior.
