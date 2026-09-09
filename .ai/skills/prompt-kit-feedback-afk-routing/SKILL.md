# Prompt Kit Feedback AFK Routing

## Trigger
Use this skill when accepted Prompt Kit explicit feedback must be converted into one bounded AFK work request, or when the private feedback bridge/router boundary is being repaired. Do not select it for generic repository implementation, CI repair, or promotion when those owners are already known.

## Required inputs
- `AGENTS.md` and `harness/CONTEXT.md`.
- `harness/contracts/prompt-kit-feedback-afk-routing.v1.json`.
- The accepted feedback signal or sanitized provider receipt with stable signal identity.
- Current Prompt Kit feedback/runtime owners and focused tests.
- Current branch/PR/provider evidence when the signal refers to a repository candidate.

## Outputs
- One classified signal disposition.
- A deduplicated machine-readable work request for ACTIONABLE_REPAIR signals.
- A bounded worker invocation when a configured capable worker exists.
- Validation and proof-ceiling evidence without claiming promotion authority.

## Procedure
1. Verify the repository/root and refresh provider truth before branch-sensitive work.
2. Validate the signal against the feedback-AFK routing contract and reject sensitive or malformed provider payloads.
3. Classify explicit written feedback and current dislike votes as `ACTIONABLE_REPAIR`; classify likes and usage metadata as `INFORMATION_ONLY` unless stronger repository evidence independently creates work.
4. Deduplicate the stable signal identity before dispatch.
5. Bind actionable work to P115 as coordinator, then route the mutation to the smallest capable existing owner such as P07 or P32. Include exact evidence, owned surface, acceptance condition, forbidden scope, and validation entry point.
6. Execute at most one configured worker invocation for the signal. Do not create a polling loop or a second scheduler.
7. Route any green candidate to the existing P105 / `pr-floor-integration` promotion authority. Never merge from this skill or its router.
8. Record the disposition, work-request artifact, validation, and remaining runtime/provider proof ceiling.

## Guardrails
- Browser code never owns GitHub credentials or merge authority.
- Raw written feedback remains private to the local work request; provider wakeups carry only the allow-listed sanitized receipt fields.
- The bridge transports and sanitizes; it does not schedule workers or merge PRs.
- The router classifies, deduplicates, and dispatches one bounded work item; it does not scan provider queues or poll indefinitely.
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

When browser sync behavior changes, add observed browser proof before claiming the loopback runtime works from the public Pages origin.

## Proof ceiling
Static contract, routing, dedupe, and source-boundary tests prove repository behavior on the tested commit. They do not prove HTTPS Pages-to-loopback browser policy, local firewall behavior, GitHub authentication, worker quality, provider review behavior, or merge/deployment success. Promotion proof belongs to P105 / `pr-floor-integration`.
