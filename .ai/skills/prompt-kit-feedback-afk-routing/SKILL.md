# Prompt Kit Feedback AFK Routing

## Trigger
Use this skill when accepted Prompt Kit explicit feedback or an accepted privacy-bounded Operant friction receipt must be converted into one bounded AFK work request, or when the private feedback bridge/router boundary is being repaired. Do not select it for raw usage telemetry, generic repository implementation, CI repair, or promotion when those owners are already known.

## Required inputs
- `AGENTS.md` and `harness/CONTEXT.md`.
- `harness/contracts/prompt-kit-feedback-afk-routing.v1.json`.
- The accepted explicit feedback signal, privacy-bounded Operant friction receipt, or sanitized provider receipt with stable signal identity.
- Current Prompt Kit/Operant behavior, feedback/runtime, and P99 telemetry-owner evidence.
- Current branch/PR/provider evidence when the signal refers to a repository candidate.

## Outputs
- One classified signal disposition.
- A deduplicated machine-readable work request for `ACTIONABLE_REPAIR` signals.
- A bounded worker invocation when a configured capable worker exists.
- Validation and proof-ceiling evidence without claiming telemetry-derivation or promotion authority.

## Procedure
1. Verify the repository/root and refresh provider truth before branch-sensitive work.
2. Validate the signal against the feedback-AFK routing contract and reject sensitive or malformed provider payloads.
3. Keep raw likes and ordinary `prompt_usage` observations `INFORMATION_ONLY`. Explicit written feedback and current dislike votes are `ACTIONABLE_REPAIR`. An `operant_friction` receipt may become `ACTIONABLE_REPAIR` only when P99-owned derivation has already reduced ordinary use to the contract's coarse fields and the evidence kind reaches its minimum occurrence floor: one deterministic runtime failure or at least three repeated local-pattern occurrences.
4. For friction receipts, preserve only coarse signal identity, optional prompt ID, surface ID, friction class, evidence kind, occurrence count, timestamp/sequence, and pseudonymous source hash when supplied. Never route search text, typed content, session/navigation history, user identity, page URLs/referrers, clipboard content, prompt bodies, or raw usage history.
5. Deduplicate the stable signal identity before dispatch.
6. Bind actionable work to P115 as coordinator, then route the mutation to the smallest capable existing owner such as P07 or P32. Include exact evidence, owned surface, acceptance condition, forbidden scope, and validation entry point.
7. Execute at most one configured worker invocation for the signal. Local workers and remote SCM/CI adapters consume the same sanitized signal/work-request semantics; GitHub Actions is one worked adapter, not the semantic owner. Do not create a polling loop, a second scheduler, or provider-specific authority in the router.
8. Route any green candidate to the existing P105 / `pr-floor-integration` promotion authority. Never merge from this skill or its router.
9. Record the disposition, work-request artifact, validation, and remaining runtime/provider proof ceiling.

## Guardrails
- P99 owns telemetry/usage semantics and friction derivation; P115 consumes accepted signals and coordinates follow-through. Do not make P115 a telemetry collector.
- Browser code never owns GitHub credentials or merge authority.
- Raw written feedback remains private to the local work request; provider wakeups carry only allow-listed sanitized receipt fields.
- Raw ordinary usage is not itself an AFK work request. Aggregate locally first and route only a coarse accepted friction receipt that crosses the contract threshold.
- The bridge transports and sanitizes; it does not schedule workers or merge PRs.
- The router classifies, deduplicates, and dispatches one bounded work item; it does not scan provider queues or poll indefinitely.
- Local and remote adapters share one provider-neutral contract. Do not hardcode GitHub-specific semantics into the router merely because GitHub Actions is the first worked adapter.
- P99 remains the explicit feedback/telemetry semantic owner; P115 remains the AFK coordination semantic owner; P105 / `pr-floor-integration` remains promotion authority.
- Preserve one writer per shared registry, workflow, generated artifact, branch, and PR.

## Validation
Run:

```text
python scripts/validate_prompt_kit_feedback_afk_routing.py --summary
python -m unittest tests.test_prompt_kit_feedback_afk_routing tests.test_prompt_kit_feedback_production tests.test_prompt_kit_portability -v
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
git diff --check
```

When browser collection/sync behavior changes, add observed browser proof before claiming ordinary public usage reaches the private bridge. This skill's friction-receipt admission contract alone does not authorize silent public telemetry collection.

## Proof ceiling
Static contract, routing, dedupe, privacy-boundary, and source-boundary tests prove repository behavior on the tested commit. They do not prove HTTPS Pages-to-loopback browser policy, local firewall behavior, friction derivation by a particular production UI, GitHub authentication, another SCM/CI adapter, worker quality, provider review behavior, or merge/deployment success. Promotion proof belongs to P105 / `pr-floor-integration`.
