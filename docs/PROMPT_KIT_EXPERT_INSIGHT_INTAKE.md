# Prompt Kit expert insight intake

## Purpose

This seam turns expert knowledge captured in a Google Sheet into **review-only Prompt Kit contribution candidates**. It is intentionally not a prompt-writing bot.

The current knowledge workspace is a native Google Sheet named `Expert Insight Ledger — Prompt Kit Sources`. Its raw rows are **Drive-authoritative**. Git remains authoritative for Prompt Kit implementation, prompt registry history, tests, CI, and integration.

Do not track the Google Sheet file ID, service-account JSON, OAuth tokens, private Drive URLs, or raw private Sheet exports in this public repository.

## Authority and flow

```text
Google Sheet (Drive-authoritative raw knowledge)
  -> read-only Insights tab fetch
  -> exact CSV schema validation
  -> review-only candidate report
  -> human/canonical-owner review
  -> prompt_registry_ops.py or an existing owner is deliberately strengthened
  -> normal Prompt Kit validation / PR / integration
```

The candidate report always declares:

- `raw_source_authority: DRIVE-AUTHORITATIVE`
- `repo_candidate_authority: REVIEW-ONLY`
- `mutation_authority: false`

The CI job must never call registry writers, edit `registry/prompts/**`, rebuild a prompt merely because a row exists, or promote an `ASSESS` row directly.

## Sheet contract

The `Insights` tab must expose these columns in this exact order:

1. Insight ID
2. Source ID
3. Captured Date
4. Timestamp
5. Domain
6. Topic
7. Atomic Insight
8. Why It Matters
9. Prompt Kit Relevance
10. Candidate Action
11. Candidate Owner
12. Target Surface
13. Sprint Track
14. Priority
15. Status
16. Acceptance / Proof Idea
17. Validation Lenses
18. Tags
19. CI Eligible
20. Notes

One row is one atomic insight. Stable IDs are mandatory. Video timestamps are literal provenance text, not spreadsheet durations.

## Publication gate

Rows may be captured freely with `Status=CAPTURED` and `Candidate Owner=UNKNOWN`. Those rows are summarized only by safe routing metadata in CI; their full insight text is not copied into the review-candidate payload.

A row becomes publishable to the repository review lane only when all of these are true:

- `Status=READY_FOR_REPO`
- `Candidate Action` is `ADD` or `STRENGTHEN`
- `Candidate Owner` is proven and is not `UNKNOWN`
- `Acceptance / Proof Idea` is nonblank
- `Validation Lenses` is nonblank
- `CI Eligible` is `YES` or `PARTIAL`

This is a publication/review gate, not merge authority.

## Local / fixture validation

```bash
python -m py_compile \
  scripts/prompt_kit_expert_insight_intake.py \
  scripts/fetch_google_sheet_tab.py \
  tests/test_prompt_kit_expert_insight_intake.py
python -m unittest tests.test_prompt_kit_expert_insight_intake -v
python scripts/prompt_kit_expert_insight_intake.py \
  --input fixtures/prompt-kit-expert-insights/sample.csv \
  --output Outputs/prompt-kit-expert-insight-intake.json \
  --source-ref synthetic-fixture
git diff --check
```

The committed fixture is synthetic. Real Sheet exports are not tracked.

## CI modes

`.github/workflows/prompt-kit-expert-insight-intake.yml` has two modes.

### Fixture mode

Pull requests and pushes to `main` that change this seam run the synthetic fixture, tests, fail-closed assertions, and upload the review-only report. This proves the transformation contract without requiring private Google access.

### Live mode

A manual `workflow_dispatch` with `mode=live` reads the private `Insights` tab using a read-only Google service account, then runs the same normalizer and uploads only the review-only report.

Live mode requires two repository secrets that are intentionally absent from tracked state:

- `PROMPT_KIT_EXPERT_INSIGHTS_SHEET_ID`
- `PROMPT_KIT_EXPERT_INSIGHTS_GOOGLE_CREDENTIALS`

The credential must be a Google service-account JSON object. Grant that service-account email **Viewer** access to the one source Sheet; do not broaden public sharing. The workflow requests only the `spreadsheets.readonly` scope.

Until those secrets and Viewer permission exist, fixture CI is the proof ceiling and live Sheet ingestion is **BLOCKED by an explicit credential/access gate**. Do not downgrade that gate to a claimed live sync.

## Relationship to P111 and the prompt registry helper

P111 (`Repository + Google Drive Artifact Synchronizer`) remains the generic repo↔Drive mapping/sync owner. This seam specializes only the Prompt Kit expert-insight intake semantics.

`scripts/prompt_registry_ops.py` remains the low-friction canonical contribution helper for genuinely approved prompt additions. A candidate generated here is input evidence for canonical-owner review; it is never permission to allocate a new P-number automatically.
