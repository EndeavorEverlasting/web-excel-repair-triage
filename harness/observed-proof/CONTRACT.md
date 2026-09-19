# Observed Behavior Proof Contract

Runtime behavior is UNKNOWN until the required event sequence has actually occurred in an evidence-producing runtime.

## Claim law

- Source inspection, a diff, a static validator, a build, a unit test, a mock, or a synthetic model may prove only its own layer. None may be promoted to browser/runtime observation.
- A behavior claim may be `PASS` only when every observation required by that claim is present in a receipt, has `occurred: true`, and has `passed: true`.
- Evidence tiers are ordered. Browser observation cannot satisfy a target-runtime or production requirement; stronger tiers may satisfy weaker requirements.
- Missing artifacts, stale subjects, skipped events, or weaker evidence yield `UNKNOWN`/`UNPROVEN`, never an inferred pass.
- Every receipt pins the exact commit, artifact path/hash, clean-worktree evidence, generated-parity evidence, environment, scenario, claims, and observations.
- Exact-head browser proof rejects tracked modifications, checks the canonical generated Prompt Kit (`python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check`), and records that evidence before Chromium launches. Recording `git rev-parse HEAD` alone is not exact-head proof.
- If the commit, generated artifact, relevant dependency, or scenario changes, the prior receipt is stale for the changed claim.
- CI/browser proof is representative runtime proof, not operator workstation or production proof. Raise the proof ceiling only when that stronger target was actually observed.

## Proof-state promotion boundary

The observed-proof harness owns a **promotion boundary**, not a generic completion label. A stronger repository, deployment, or acceptance state must never be inferred from a weaker class:

| Evidence/state | What it can prove | What it cannot prove by itself |
| --- | --- | --- |
| source / build / synthetic | repository implementation, buildability, deterministic modeled behavior | any live interaction occurred |
| integrated / installed / deployed | the exact artifact reached the named repository, host, or deployment surface | the requested behavior executed successfully there |
| browser_runtime_observed | the required interaction occurred in the representative browser runtime named by the receipt | intended desktop/provider/production behavior |
| target_runtime_observed | the required interaction occurred in the intended runtime/host named by the receipt | production behavior on a different target, or operator acceptance |
| production_observed | the required interaction occurred on the named production target | human/operator acceptance unless that acceptance is separately observed and recorded |
| operator acceptance | the responsible human accepted the observed result for the stated use case | broader runtime correctness beyond the accepted scenario |

Non-equivalences are binding:

- `VALIDATED`, `INTEGRATED`, `INSTALLED`, and `DEPLOYED` are not aliases for `OBSERVED`.
- A hook/config/package being present on a workstation or deployment target does not prove that the host loaded it, invoked it, or produced the required behavior.
- Synthetic/replay traces may validate protocol semantics but may not satisfy an observed-runtime claim.
- Browser observation may not be promoted to target-runtime observation unless the browser is itself the declared target runtime.
- Target-runtime observation may not be promoted to production observation for a different environment.
- Runtime observation and operator acceptance are separate contracts; neither silently implies the other.

A target-runtime `PASS` therefore requires an actual interaction in the named target runtime, current subject/artifact identity, and the claim's required observed events. If the runtime is inaccessible, the correct state is `UNKNOWN`/`UNPROVEN` with the exact access or execution gate—not `PASS`, `DEPLOYED`, or an inferred observation.

## UI interaction minimum

A UI claim must observe the user-visible sequence that matters, including side effects and focus/keyboard state when they are part of the bug. For clipboard/navigation behavior, prove the exact clipboard payload, the intended target visibility/scroll result, and the absence of the destructive or contradictory focus/modal outcome.

## Completion guard

Agents and reports must not say `works`, `fixed`, `passes`, `successful`, or equivalent for a runtime claim unless a current receipt supports that claim at the required evidence class. Otherwise report the claim as `UNKNOWN` or `UNPROVEN` and name the missing observation.
