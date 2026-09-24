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

### Anchor equality is not authorship proof

Retrospective recovery often finds only a title, first sentence, or distinctive anchor. That is useful evidence of **coverage**, but it is weaker than full prompt provenance.

The authorship comparison therefore distinguishes:

- `EXACT` — full-prompt equality after allowed placeholder/runtime normalization;
- `MATERIAL` — enough of the substantive structure is shared to support reuse-dominant classification;
- `DOCTRINE_ONLY` — shared principles but not a substantially shared prompt;
- `ANCHOR_ONLY` — title/first-line/distinctive phrase matches, but the full prompt has not been proven equal;
- `NONE` — no material contemporaneous owner/template found;
- `UNKNOWN` — evidence is insufficient to compare.

`ANCHOR_ONLY` can prove that a Prompt Kit owner already covered the use case, but it **cannot** by itself prove `CANONICAL_REUSE` or `REUSE_DOMINANT` authorship.

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

The current register deliberately preserves uncertainty instead of copying conversational guesses into repository truth.

| Candidate use | Relevance | Productivity | Current Prompt Kit gap | Historical authorship | What the evidence says |
|---|---:|---:|---:|---|---|
| `INSTALL GOVERNANCE DOCTRINE NOW` | Unscored | Unscored | `1 / HIGH` | `UNRESOLVED / NONE` | P00 owns this capability now, but the recovered evidence does not yet bind the exact historical prompt event or full prompt text. |
| `ANALYZE THE REPOSITORY, BUILD THE EVIDENCE PACK, THEN EXECUTE THE FIRST SAFE SPRINT...` | `5 / HIGH` | `4 / HIGH` | `1 / HIGH` | `UNRESOLVED / NONE` | The Sep-14 Prompt Kit already contained P03 with the same first-line anchor, and the use led into merged TRQ-007 PR #480. Full-prompt equality is still unproven. |
| `FACTOR THE REUSABLE INSIGHT INTO THE CORRECT REPOSITORIES. DO NOT DUPLICATE AUTHORITY.` | `5 / HIGH` | `5 / HIGH` | `1 / HIGH` | `UNRESOLVED / NONE` | P16 existed before the Sep-16 use, and the prompt led into merged H&H PR #6 with focused tests and live document readback. Full-prompt equality is still unproven. |

These examples are intentionally useful even though none currently proves manual originality:

- P03 and P16 demonstrate that **Prompt Kit reuse can be extremely productive**.
- Their low gap scores mean they are not strong candidates for a new Prompt Kit identity merely because they worked well.
- Their unresolved authorship proves why a matching anchor must not be promoted into a claim about how the whole prompt was authored.
- The high-value search zone for Prompt Kit expansion is therefore not simply “the most productive prompt.” It is **high relevance + high productivity + demonstrated current gap**, with authorship retained as a separate provenance dimension rather than a value multiplier.

## Admission and mutation boundaries

This subsystem is review-only. It must not:

- allocate prompt IDs;
- edit canonical prompt bodies;
- promote a candidate because its manual-authorship score is high;
- infer historical authorship from current library state;
- infer full-prompt reuse from an anchor-only match;
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
- an anchor-only match cannot prove canonical reuse;
- a scored rating requires evidence;
- Prompt Kit gap 5 cannot bypass prior-art/topology review;
- no composite priority policy exists yet.

## Regression safety is a separate layer

The retrospective matrix evaluates **prompt uses**; it is not the complete defect detector. A recurring defect may instead be discovered by a local validator or required check, hosted CI, code review, runtime observation, operator feedback, or commit history.

Those failures belong to the regression-safety loop in `docs/PROMPT_REGRESSION_SAFETY.md` and `harness/contracts/prompt-regression-safety.v1.json`. That loop can strengthen shared operational Prompt Kit behavior even when no single matrix row captures the defect. Trailing whitespace is the first registered example: repeated cross-repository incidents are treated as a patch-hygiene system defect rather than another one-off cleanup.

The two systems therefore feed each other without collapsing into one metric: retrospective evaluation discovers useful prompt-use gaps; regression safety turns recurring defect evidence from **any supported intake surface** into a negative fixture, positive control, canonical-owner strengthening, local required-check proof, and a retained regression.

## Proof ceiling

Repository validation can prove the rubric, consistency rules, and review-only candidate state. It cannot prove historical authorship or prompt effectiveness beyond the attached event, contemporaneous-library, and outcome evidence. It also does not authorize Prompt Kit mutation or new prompt identity creation.
