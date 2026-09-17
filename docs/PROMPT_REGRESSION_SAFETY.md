# Prompt regression safety

## Why this exists

The Prompt Kit retrospective matrix answers useful questions about a **prompt use**: fit, productivity, current Prompt Kit coverage, and authorship provenance. It cannot see every systemic failure.

A defect such as trailing whitespace may be discovered by `git diff --check`, a local merge gate, hosted CI, review, runtime observation, operator feedback, or commit history. It may recur across many different prompts without belonging to one prompt-use row at all.

Regression safety is therefore a separate operational layer:

```text
incident
  -> repair the immediate instance
  -> classify the defect family
  -> detect recurrence
  -> find the canonical shared owner
  -> write a failing negative fixture + passing positive control
  -> strengthen the shared owner
  -> run repository-owned local required checks
  -> run affected provider parity when applicable
  -> integrate and retain the regression
```

Canonical contract: `harness/contracts/prompt-regression-safety.v1.json`.
Defect-family register: `harness/evals/prompt-regression/defect-families.v1.json`.
Validator: `python scripts/validate_prompt_regression_safety.py --summary`.
Focused regression: `python -m unittest tests.test_prompt_regression_safety_prompt -v`.

## Recurrence changes the unit of repair

One defect occurrence can be an instance. Two independently evidenced occurrences in the same family are treated as a system defect by the v1 contract.

That changes the completion standard. Repeating the same cleanup is no longer enough. A systemic repair must locate the smallest canonical prevention owner—shared policy, generator, validator, hook, required-check profile, schema, or test floor—and strengthen it there.

Prompt-by-prompt wording edits are specifically the wrong repair when every prompt inherits the same missing invariant.

### Ownership map

- **P13 Self-Improving Rules Review** owns the repeated-pain → enforceable prevention workflow.
- **P94 Regression Test & Live Behavior Guard** owns protected-behavior regression design and live verification when appropriate.
- **P100** can contribute transcript-wide judgment failures as one intake source, but transcript mining is not the only intake path.
- **P79** remains the Prompt Kit identity/admission owner; regression recurrence does not justify inventing another P-number.
- `registry/prompts/actionable-next-step-policy.v1.json` is the current shared compilation seam that can strengthen every canonical Prompt Kit prompt once.

## First registered family: trailing whitespace

Trailing whitespace is not hypothetical. The register binds multiple dedicated/follow-up whitespace repairs in both Triage and AgentSwitchboard, including cases where `git diff --check` blocked otherwise unrelated validation.

The retained detectors are:

```bash
git diff --check
git diff --cached --check
git diff --check <base>...<head>
```

Those correspond to three different moments:

1. **working candidate** — catch patch errors while implementing;
2. **staged candidate** — catch them before commit;
3. **exact integration candidate** — prove the base/head delta itself is clean.

Triage already has these primitives in repository-owned hooks, validators, and required-check contracts. The regression-safety layer changes the prompt contract so agents must use those gates early rather than repeatedly discovering whitespace in hosted CI and writing cleanup commits.

## Local-first proof and hostless merge work

The desired architecture is not “replace GitHub Actions with an unrelated local script.” It is **one repository-owned check contract with multiple execution adapters**.

The portable semantics should be:

```text
repository-owned required-check profile
        |                     |
        v                     v
 local executor          hosted executor
        |                     |
        +---- comparable exact-candidate receipts ----+
```

When local Git and the repository-owned local runner are available, the prompt contract requires the local profile first. GitHub Actions, GitLab CI, or another provider can independently rerun the same semantic gate, but the provider should not own the portable command list.

This sprint does **not** silently change the repository's current merge-authority policy. Current promotion tests still encode provider mutation as a requirement, so hostless merge authority remains separate successor work until that promotion contract is deliberately changed and regression-proven. The regression-safety contract prevents prompts from confusing those two statements:

- **local proof can be valid without hosted CI**, when the repository contract defines that local proof;
- **local proof does not automatically grant merge authority**, while the active promotion policy still reserves a provider/external gate.

That distinction is important while the local-action work in Triage and AgentSwitchboard converges.

## Why the retrospective matrix is still useful

The matrix remains valuable for discovering high-value Prompt Kit gaps and judging the result of prompt use. It now feeds a larger system rather than pretending to be the complete defect detector.

Regression-safety intake can come from:

- retrospective prompt-use evaluation;
- local validator or required-check failure;
- hosted CI failure;
- code review;
- runtime/field observation;
- explicit operator feedback;
- repository commit history.

This is how a problem such as trailing whitespace becomes visible even when there is no meaningful “authorship” or “productivity” row for it.

## Regression-safe strengthening standard

A systemic defect is not closed until all applicable gates hold:

1. The immediate incident is repaired.
2. The family has durable evidence and a canonical owner.
3. A negative fixture reproduces the defect or a mutation equivalent.
4. A positive control proves legitimate behavior is not blocked.
5. The shared owner is strengthened rather than copying a fix into every prompt.
6. The focused semantic regression is registered in the deterministic floor when repository convention requires it.
7. Applicable local required checks pass on the candidate.
8. Provider parity runs when it adds required/independent proof.
9. Integration retains both the repair and the regression.

A later recurrence after those gates is evidence that the prevention mechanism itself is incomplete and should be strengthened again; it is not another invitation to repeat cleanup.

## Proof boundary

This mechanism can prove repository-owned classification, global prompt inheritance, retained regression semantics, and connection to local required-check surfaces. It cannot by itself prove that downstream models always obey the instruction, nor does it grant hostless merge authority while the repository's active promotion contract still requires a provider mutation.
