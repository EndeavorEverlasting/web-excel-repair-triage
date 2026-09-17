# Prompt retrospective evaluation

## Purpose

This lane turns recent prompt-use evidence into a **review-only prompt matrix** that can expose Prompt Kit gaps without confusing manual originality, reuse, productivity, or current library coverage.

It exists because those are different questions:

1. **Use-case relevance** — how precisely did the prompt fit the problem that triggered it?
2. **Productivity** — how much durable, attributable project movement came out of that use?
3. **Prompt Kit gap** — how much of that capability is missing from the current canonical Prompt Kit?
4. **Authorship origin** — on the manual ↔ canonical-reuse spectrum, where did the prompt originate?

Every score carries its **own confidence and evidence references**. There is deliberately no composite priority formula yet.

Canonical contract: `harness/contracts/prompt-retrospective-evaluation.v1.json`.
Current review-only register: `harness/evals/prompt-retrospective/recent-candidates.v1.json`.
Validator: `python scripts/validate_prompt_retrospective_evaluations.py --summary`.

## Authorship is temporal

Authorship must be compared with the Prompt Kit revision that existed **when the prompt was written or invoked**.

A prompt can be manually authored on Monday, promoted into the Prompt Kit on Tuesday, and be canonical reuse on Wednesday. Looking only at Wednesday's library must not rewrite Monday's provenance.

The authorship scale is:

| Score | Label | Meaning |
|---:|---|---|
| 1 | `CANONICAL_REUSE` | Essentially the registered Prompt Kit prompt; only placeholders/runtime context changed. |
| 2 | `REUSE_DOMINANT` | Canonical structure dominates; manual changes are limited. |
| 3 | `HYBRID` | Canonical structure/doctrine and manual reasoning both materially shape the prompt. |
| 4 | `MANUAL_DOMINANT` | Primarily hand-authored; borrowed Prompt Kit/repository doctrine is subordinate. |
| 5 | `MANUAL_ORIGINAL` | Core structure is manual and no material contemporaneous Prompt Kit match is found. |

`MANUAL_ORIGINAL` is intentionally expensive to prove: it requires a contemporaneous Prompt Kit reference and evidence that no material match existed. A current-only search cannot earn that claim.

## Confidence sits beside every score

`HIGH`, `MEDIUM`, `LOW`, and `NONE` describe evidence quality for the individual rating, not how good the prompt was.

A useful prompt can have `productivity=5/HIGH` while authorship remains `UNRESOLVED/NONE`. Conversely, an exact canonical reuse can have `authorship=1/HIGH` and still be extraordinarily productive.

Scores without evidence are rejected by the validator.

## Four rubrics

### Use-case relevance

- **1** — poor fit or materially mismatched.
- **2** — partial fit requiring substantial operator translation/correction.
- **3** — useful but broad or incomplete for the situation.
- **4** — tightly matched with only minor generic overhead.
- **5** — exact problem, constraints, ownership, and execution behavior encoded.

### Productivity

- **1** — little durable movement.
- **2** — durable plan/design/artifact, but no validated implementation.
- **3** — implementation or artifact produced and locally/deterministically validated, not integrated.
- **4** — meaningful reviewed/validated PR or integrated bounded implementation.
- **5** — high-value integrated implementation with strong validation or observed proof.

Productivity is **attribution-sensitive**. A merge that merely happened near the prompt is not evidence that the prompt caused the result.

### Prompt Kit gap

- **1** — current canonical owner already covers the capability; `NO_KIT_CHANGE`.
- **2** — existing owner needs only minor strengthening.
- **3** — material strengthening or an explicit seam is needed.
- **4** — substantial coverage/ownership gap.
- **5** — distinct missing capability after completed P79/prior-art/topology review; only then may `CREATE_NEW_REVIEW` be recorded.

Gap 5 is not permission to allocate a P-number. The normal Prompt Kit admission gate remains authoritative.

### Authorship origin

Use the temporal scale above. Manual authorship is not a quality score and must not automatically increase gap or productivity.

## Evidence workflow

```text
prompt-event evidence
  + contemporaneous Prompt Kit revision (for historical authorship)
  + current Prompt Kit/topology evidence (for current gap)
  + attributable repository/PR/validator/runtime outcome evidence (for productivity)
  -> retrospective register
  -> deterministic validator
  -> human/P79 review
  -> NO_KIT_CHANGE | STRENGTHEN_EXISTING | POSSIBLE_DUPLICATE | CREATE_NEW_REVIEW
  -> normal Prompt Kit contribution path if admitted
```

When an evaluated use is already a registered Prompt Kit invocation, `prompt-outcome-receipt/v1` can be linked as evidence rather than inventing a second outcome authority. The retrospective register only adds cross-cutting scoring and historical provenance analysis.

## Recovered examples: 2026-09-17

The first register intentionally preserves uncertainty instead of copying the earlier conversational guesses into repository truth.

| Candidate | Current coverage | Gap | Historical authorship | Next evidence needed |
|---|---|---|---|---|
| `INSTALL GOVERNANCE DOCTRINE NOW` | Current registry maps the anchor to **P00 Governance Doctrine Installer**. | `1 / HIGH` | `UNRESOLVED / NONE` | Prompt-event date/text fingerprint plus the Prompt Kit revision that existed at that event. |
| Cross-repository authority factoring | Candidate mechanism retained for review. | Unscored | `UNRESOLVED / NONE` | Exact prompt-event evidence, attributable outcome evidence, and full current P79/topology comparison. |

This distinction is intentional: **covered now** is not the same claim as **reused then**.

## Admission and mutation boundaries

This subsystem is review-only. It must not:

- allocate prompt IDs;
- edit canonical prompt bodies;
- promote a candidate because its manual-authorship score is high;
- infer historical authorship from current library state;
- calculate a composite priority score before a weighting policy is approved;
- persist raw private chat transcripts merely to support the matrix.

The Prompt Kit topology/P79 strengthen-before-add gate remains the owner of `STRENGTHEN`, duplicate detection, and new-prompt admission. This retrospective layer supplies evidence to that gate; it does not replace it.

## Validation

Focused checks:

```bash
python scripts/validate_prompt_retrospective_evaluations.py --summary
python -m unittest tests.test_prompt_retrospective_evaluation_prompt -v
```

The focused tests prove, among other things:

- hybrid authorship is a first-class valid state;
- current P00 coverage does not retroactively prove historical reuse;
- `MANUAL_ORIGINAL` cannot be claimed without contemporaneous no-match evidence;
- a scored rating requires evidence;
- Prompt Kit gap 5 cannot bypass prior-art/topology review;
- no composite priority policy exists yet.

## Proof ceiling

Repository validation can prove the rubric, consistency rules, and review-only candidate state. It cannot prove historical authorship or prompt effectiveness until the corresponding event, contemporaneous-library, and outcome evidence is attached.
