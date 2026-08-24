# Observed Behavior Proof Contract

Runtime behavior is UNKNOWN until the required event sequence has actually occurred in an evidence-producing runtime.

## Claim law

- Source inspection, a diff, a static validator, a build, a unit test, a mock, or a synthetic model may prove only its own layer. None may be promoted to browser/runtime observation.
- A behavior claim may be `PASS` only when every observation required by that claim is present in a receipt, has `occurred: true`, and has `passed: true`.
- Evidence tiers are ordered. Browser observation cannot satisfy a target-runtime or production requirement; stronger tiers may satisfy weaker requirements.
- Missing artifacts, stale subjects, skipped events, or weaker evidence yield `UNKNOWN`/`UNPROVEN`, never an inferred pass.
- Every receipt pins the exact commit, artifact path/hash, environment, scenario, claims, and observations.
- If the commit, generated artifact, relevant dependency, or scenario changes, the prior receipt is stale for the changed claim.
- CI/browser proof is representative runtime proof, not operator workstation or production proof. Raise the proof ceiling only when that stronger target was actually observed.

## UI interaction minimum

A UI claim must observe the user-visible sequence that matters, including side effects and focus/keyboard state when they are part of the bug. For clipboard/navigation behavior, prove the exact clipboard payload, the intended target visibility/scroll result, and the absence of the destructive or contradictory focus/modal outcome.

## Completion guard

Agents and reports must not say `works`, `fixed`, `passes`, `successful`, or equivalent for a runtime claim unless a current receipt supports that claim at the required evidence class. Otherwise report the claim as `UNKNOWN` or `UNPROVEN` and name the missing observation.
