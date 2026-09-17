# P123 Full-Source / Tail Coverage Proof Plan

- **Status:** Sprint 1 IMPLEMENTATION — deterministic coverage scorer TRACKED → VALIDATED on feature head; field `OBSERVED` remains UNPROVEN
- **Canonical owner:** P123 (prompt/export behavior) + P67 (eval scoring)
- **Repository:** `EndeavorEverlasting/web-excel-repair-triage`
- **Evidence floor at plan creation:** `main@c0090aa285fe0580ff19c26c1e1de0d7e95506bc`
- **Plan owner path:** `harness/evals/P123_SOURCE_COVERAGE_PROOF_PLAN.md`
- **Related observed receipt:** `harness/evals/observations/prompt-outcome/2026-09-16-p123-gemini-drive-title.json` (document identity only)

## 1. Mission

Close the remaining P123 product gap named after PR #525: prove **beginning-to-end source coverage / tail accounting** as a distinct contract from Gemini→Drive **document identity**.

Document identity is already `OBSERVED` for source `7UyhyhxdFsQ`. Coverage quality is still `UNPROVEN`. This plan must not silently promote identity evidence into coverage evidence.

## 2. Fresh floor and owners

Current `main@c0090aa2` already contains:

- P123 prompt contract language for `FULL-SOURCE COVERAGE / TAIL-CHECK CONTRACT`, `COVERAGE_LEDGER`, `LAST_INSPECTED_POSITION`, `UNACCOUNTED_SPANS`, and `FULL_SOURCE_COVERAGE`
- historical quality regression fixture `tests/fixtures/p123_source_document_quality/drive_7UyhyhxdFsQ_20260910.v1.json` (last timestamped finding 97s / 128s extent; no explicit end-coverage receipt)
- prompt-outcome field receipt proving Drive title/H1 identity without promoting tail coverage
- deterministic test-floor canary specificity (PR #525)
- synthetic P123 source-fidelity behavior eval (`p123-source-proof-boundary`) for a different source/failure family

Reuse these owners. Do not invent a second P123 identity, second outcome-receipt vocabulary, or second canary runtime.

### Active collision owners

| Surface | Current owner | Disposition |
| --- | --- | --- |
| `harness/evals/repository-ai-evals.v1.json` | P67; also mutated by open PR #450 | **Defer shared-registry suite registration** until #450 is reconciled or this lane owns a conflict-free additive merge. Sprint 1 wires proof through focused unittest + deterministic test-floor registration. |
| `tests/test_repository_ai_eval_framework.py` | P67 / PR #450 | Read-only for Sprint 1. |
| Gemini / Google Drive live export | provider field proof | Required for field `OBSERVED`; **not** available as local mutation authority in this sprint. |
| Upstream semantic extraction prototype | open PR #526 | Independent; do not edit. |
| Compute Mode browser proof | open PR #524 | Independent green merge candidate; do not absorb. |

## 3. Program phases

### Phase A — Deterministic coverage harness (this sprint)

**Owned**

- durable plan (this file)
- versioned contract `harness/contracts/p123-source-coverage-proof.v1.json`
- scorer `scripts/evaluate_p123_source_coverage.py`
- gold fixture derived from the known `7UyhyhxdFsQ` partial-coverage structure
- synthetic COMPLETE candidate labeled as non-field evidence
- focused tests + deterministic test-floor self-test registration
- P66 / TRQ ledger index

**Forbidden**

- claiming field `OBSERVED` / `COMPLETE` from synthetic fixtures
- mutating the existing document-identity receipt into a coverage claim
- live Gemini regeneration or Drive rewrite in this lane without provider authority
- rewriting P123 prompt copy unless a scorer defect proves the contract text is insufficient
- editing PR #450 / #524 / #526 owned surfaces

**Acceptance**

- baseline partial receipt FAILS with declared failure classes
- synthetic complete candidate PASSES only when extent, last-inspected, unaccounted spans, end receipt, and ledger accounting agree
- COMPLETE overclaim, missing end receipt, fabricated tail facts, and extent mismatch fail closed
- proof ceiling text forbids promoting synthetic PASS to provider observation

### Phase B — Shared eval-registry wiring (successor)

Register `p123-source-coverage` in `harness/evals/repository-ai-evals.v1.json` as a blocking synthetic suite after the PR #450 collision is cleared. Keep the same scorer and fixtures.

### Phase C — Provider field proof (successor / operator+provider)

Regenerate or re-inspect the Gemini→Drive artifact for `7UyhyhxdFsQ` (or an explicitly declared successor source), extract a bounded coverage receipt, score it with the Phase A harness, and only then write a prompt-outcome receipt that may promote coverage to `OBSERVED`.

**Completion gate for Phase C:** scorer PASS on provider-derived receipt + bounded field receipt linking to the existing identity receipt + no invented tail content.

## 4. Failure classes (contract-owned)

- `SOURCE_EXTENT_MISMATCH`
- `MISSING_END_COVERAGE_RECEIPT`
- `UNACCOUNTED_TAIL_UNRECEIPTED`
- `COMPLETE_WITHOUT_FULL_ACCOUNTING`
- `FABRICATED_UNREPRESENTED_TAIL_FACTS`
- `COVERAGE_LEDGER_INCOMPLETE`

## 5. Proof ceiling

Phase A proves deterministic scoring of structured coverage receipts against the P123 coverage contract. It does **not** prove that the current live Drive export for `7UyhyhxdFsQ` has complete beginning-to-end coverage. That remains a Phase C provider observation.

## 6. Validation commands

```bash
python -m unittest tests.test_p123_source_coverage_eval_prompt -v
python scripts/evaluate_p123_source_coverage.py --summary
python -m unittest tests.test_p123_source_document_quality_prompt -v
```

Broader gate after implementation: focused suite green, then exact-head CI / deterministic floor as available.

## 7. Ledger index

TRQ-015 owns continuity for this plan. Update TRQ status as proof advances; do not replace this plan with a terse ledger row.
