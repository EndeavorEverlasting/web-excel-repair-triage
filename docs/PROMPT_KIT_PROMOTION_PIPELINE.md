# Prompt Kit production promotion pipeline

## Authority

`.github/workflows/prompt-kit-pages.yml` is the single GitHub Pages promotion authority for Prompt Kit. It validates and packages pull-request candidates, but it deploys only a push to the repository default branch. CI/CD does not author or opportunistically rewrite Prompt Kit source.

Canonical source generation remains owned by `scripts/build_prompt_kit_registry.py`. Generated `web/prompt-kit/index.html` must already match that builder before a candidate can pass promotion validation.

## Promotion graph

```text
PR / main push
  -> checkout exact candidate SHA
  -> verify current main is an ancestor of a PR candidate
  -> harness E2E
  -> explicit-feedback contract + production feedback regression
  -> promotion fail-closed regression
  -> generated Prompt Kit parity
  -> application browser E2E
  -> release identity
  -> Pages contract
  -> canonical package + SHA-256 manifest + promotion receipt
  -> main-push-only Pages deploy
  -> deployed-byte comparison with the tracked canonical artifact
```

## Proof levels

**Harness E2E** proves repository contracts and proof machinery together through `scripts/validate_harness.py` and `tests.test_harness_contract`.

**Application E2E** is separate. `scripts/run_prompt_kit_browser_e2e.sh` serves the real `web/prompt-kit/index.html` entrypoint and loads it in headless Chrome/Chromium. If a browser executable is unavailable, the required job fails with `APPLICATION_E2E_BLOCKED`; it is not downgraded to a synthetic PASS.

Focused Node/Python tests exercise feedback persistence, replacement semantics, cursor behavior, strict imported-event validation, out-of-order vote handling, and promotion fail-closed paths. Those tests complement rather than replace the browser E2E gate.

## Candidate and artifact identity

Pull-request validation checks out `${{ github.event.pull_request.head.sha }}` directly and proves that `origin/main` is an ancestor of that head. A moved default branch invalidates that proof and blocks the candidate until it is reconciled and revalidated.

`package` regenerates the Pages bundle with the canonical builder and compares the generated Prompt Kit byte-for-byte with the tracked canonical artifact. It emits a SHA-256 manifest and `prompt-kit-promotion-receipt/v1`. The receipt rejects an unauthorized target and rejects a requested candidate SHA that differs from `git rev-parse HEAD`.

## Write authority and recursion boundaries

Validation and scheduled feedback processing use `contents: read`. Only the Pages deploy job receives `pages: write` and `id-token: write`, and only on a push to `main`. Pull requests and manual dispatches can validate/package but cannot deploy. No durable promotion workflow has repository-content write permission.

The feedback maintenance hook is read-only. It consumes explicitly ingested `prompt-feedback-export/v1` batches and may emit `REVIEW_CANDIDATE`; it has no prompt-registry or source mutation authority.

## Feedback persistence boundary

The static GitHub Pages client keeps append-only feedback history in browser `localStorage`. It does not embed a repository credential or make a repository-write network request. If browser storage cannot accept the complete append-only history, the write fails closed with `FEEDBACK_STORAGE_FULL` rather than silently deleting older events.

Cross-device or server-side automatic feedback ingestion requires a separately authorized backend identity. Until such an owner exists, the supported trust boundary is explicit browser export followed by repository-side ingestion.

## Post-promotion proof

After Pages deployment, `post-deploy` downloads the public `/prompt-kit/` artifact with bounded retries and compares it byte-for-byte against the canonical `web/prompt-kit/index.html` from the deployed candidate. A successful deploy API call without this containment check is not considered full promotion proof.
