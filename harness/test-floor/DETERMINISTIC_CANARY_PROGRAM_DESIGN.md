# Deterministic Test-Floor Canary Program Design

Status: DESIGN / executable-prototype contract
Owner: deterministic test-floor harness
Base evidence floor: `main@6c56e6286658474180c6a06368b205264d0fa9e9`

## User outcomes and invariants

The deterministic negative canary must prove that the repository test floor detects the **declared generated-site drift**, not merely that some test somewhere inside the broad `test-floor-self-tests` step fails.

Required invariants:

1. A clean, unmodified checkout passes the selected canary witness and the canonical deterministic floor immediately before mutation.
2. The declared mutation is applied atomically to exactly one owned target and is observable by the witness.
3. The same witness fails after the mutation for evidence containing the declared marker/signature.
4. The full deterministic floor fails at the contract-declared earliest gate using a receipt created by the current invocation, never a pre-existing receipt.
5. An unrelated failure at the same broad gate is insufficient proof.
6. The mutation target is restored atomically and byte-identically even when ordinary execution fails.
7. The ordinary clean deterministic floor still passes after restoration.
8. Proof artifacts remain bounded, non-secret, deterministic, fresh-by-construction, and reviewable.

The P123 field-proof correction is a predecessor evidence transition, not part of this canary runtime: provider readback now proves that a Gemini-produced source-specific Drive artifact exists and that its Drive title / first H1 can be repaired through the connected Drive interface. The canary program must not absorb Google Drive behavior.

## Governance vs harness vs program design vs implementation

- **Governance:** exact-head freshness, no evidence promotion, one canonical owner, generated-output protection, merge only after green exact-head proof.
- **Harness:** `harness/test-floor.v1.json`, `.github/workflows/deterministic-test-floor.yml`, `scripts/run_deterministic_test_floor.py`, CI artifacts and validators.
- **Program design:** a contract-driven canary orchestrator that owns mutation lifecycle, witness execution, floor execution, restoration, and proof evaluation.
- **Implementation:** the thin canary runner, its contract, focused tests, and workflow delegation. Broad changes to the deterministic floor runner are explicitly unnecessary unless prototype evidence proves otherwise.

## Existing behavior and defect

The previous workflow appended `<!-- deterministic-test-floor-negative-canary -->` to `web/prompt-kit/index.html`, ran the complete deterministic floor, and accepted the result when `status == FAIL` and `failed_step == test-floor-self-tests`.

That proved fail-closed behavior at a broad step, but not failure specificity. Any unrelated failing self-test could satisfy the same condition. The prior inline mutation also wrote directly to the target and the proof path could inherit an old nested floor receipt.

The current deterministic-floor report already exposes bounded `stdout_tail` / `stderr_tail` for each step, so the design reuses that evidence rather than forking the floor runner.

## Domain vocabulary

- **Canary contract:** versioned declaration of target, mutation, witness, expected full-floor gate, and required proof signatures.
- **Canary target:** repository file mutated only for the duration of the probe.
- **Mutation marker:** deterministic content proving which mutation was injected.
- **Witness:** narrow repository-owned test command that passes clean and must fail under the declared mutation.
- **Witness result:** command result with return code plus bounded stdout/stderr.
- **Floor receipt:** `deterministic-test-floor-report/v1` produced by the existing canonical runner for the current invocation.
- **Failure fingerprint:** contract-evaluated tuple of expected failed gate plus mutation-specific evidence from the witness/floor output.
- **Atomic replacement:** same-directory temp-file write, flush, and `os.replace` used for mutation/restoration so the target is never partially rewritten.
- **Fresh receipt boundary:** pre-existing nested floor proof is removed before the floor process starts; absence of a newly written receipt is a proof failure.
- **Restoration proof:** before/after content digest equality for the canary target.
- **Canary receipt:** durable runtime report describing each transition and the final proof decision.

## Alternatives compared

### A. Broad failed-step check (previous behavior)

Interface: `failed_step == expected`.

Pros: tiny and cheap.
Cons: cannot distinguish the declared mutation from an unrelated self-test failure; rejected.

### B. Full-floor output string matching only

Interface: require the mutation marker in the failed full-floor step output.

Pros: small change; reuses existing receipt.
Cons: couples proof to bounded tail truncation and pytest rendering; a noisy failure can push the marker out of the retained tail. Better than A, but not sufficiently causal by itself.

### C. Clean-floor baseline + differential witness + mutated full-floor gate + restoration (selected)

Interface:

`clean witness PASS -> fresh clean full-floor PASS -> atomic declared mutation -> mutated witness FAIL with marker -> fresh mutated full-floor receipt FAIL at expected gate -> atomic restore digest == original -> workflow clean floor PASS`

Pros: proves the exact checkout/environment is green immediately before mutation, the declared mutation causes a specific narrow detector to fail, the full harness transitions from PASS to the expected FAIL after that mutation, stale evidence cannot be reused, and the repository is restored. An unrelated pre-existing self-test or collection failure cannot certify a canary because it fails the clean full-floor baseline before mutation.
Cons: each canary pays for one additional clean deterministic-floor invocation. Accepted because causal proof is the purpose of the canary.

### D. Teach the generic floor runner canary-specific semantics

Pros: single executable.
Cons: pollutes a generic deterministic runner with one mutation class and creates split responsibility. Rejected unless later evidence shows multiple canary families need shared structured classification.

## Module and interface map

### `harness/contracts/deterministic-test-floor-canary.v1.json`

Responsibility: canonical declaration of the one supported generated-site canary.
Owned data: schema version, canary id, target, mutation marker, witness argv, expected failed step, required witness signature, proof ceiling.
Side effects: none.
Failure contract: malformed/missing fields fail closed before mutation.
Test seam: load/validate with focused tests.

### `scripts/run_deterministic_test_floor_canary.py`

Responsibility: orchestrate one canary lifecycle and emit one receipt.
Owned transient state: original target bytes, original digest, mutation-applied state, command results, and freshness of the nested floor receipt.
Public interface:

`python scripts/run_deterministic_test_floor_canary.py --contract <path> --report <path> --floor-report <path> --baseline-floor-report <path>`

Hidden complexity: subprocess normalization, atomic mutation/restoration, nested-receipt freshness, bounded output capture, evidence evaluation.
Dependencies: canary contract; existing `scripts/run_deterministic_test_floor.py` as the canonical full-floor port.
Side effects: temporary atomic replacement of the declared target; report writes. Restoration is mandatory in `finally` and itself uses atomic replacement.
Failure contract: nonzero for contract error, failed proof, failed restoration, stale/missing current-run floor evidence, or unexpected command outcome. A failed canary probe is never converted to PASS.
Observability: receipt records transition states, return codes, digests, and bounded tails.
Test seam: pure proof-evaluation function plus small filesystem primitives for atomic replacement and fresh-receipt preparation.

### `harness/contracts/prompt-semantic-weakening-canary.v1.json`

Responsibility: declare the second materially different canary: a temporary canonical P07 text weakening that must be rejected by Prompt Semantic Coverage.
Owned data: P07 target path, one bounded text replacement, semantic-validator witness, expected deterministic-floor failure gate, and proof ceiling.
Safety boundary: the weakened prompt is never committed; the orchestrator restores the canonical file byte-identically in `finally`.

### Existing `scripts/run_deterministic_test_floor.py`

Responsibility remains unchanged: own the real deterministic floor and its report.
The canary runner calls it as a port; it is not duplicated or reimplemented.

### `.github/workflows/deterministic-test-floor.yml`

Responsibility: CI composition only.
It delegates negative-canary behavior to the repository-owned canary runner, then executes the existing private-input and clean-floor gates.

## State model

`READY_CLEAN -> CLEAN_WITNESS_PROVEN -> CLEAN_FLOOR_PROVEN -> MUTATED -> MUTATED_WITNESS_PROVEN -> FLOOR_PROCESS_OBSERVED -> RESTORED -> PROVEN`

`FLOOR_PROCESS_OBSERVED` intentionally does not claim the floor failure is valid; proof evaluation must still establish the current receipt, expected gate, witness signature, and restoration digest before promotion to `PROVEN`.

Terminal failures:

- `CONTRACT_INVALID`
- `CLEAN_WITNESS_FAILED`
- `CLEAN_FLOOR_BASELINE_PROCESS_FAILED`
- `CLEAN_FLOOR_BASELINE_RECEIPT_NOT_PASS`
- `MUTATED_WITNESS_UNEXPECTEDLY_PASSED`
- `WRONG_FAILURE_SIGNATURE`
- `FULL_FLOOR_UNEXPECTEDLY_PASSED`
- `FULL_FLOOR_RECEIPT_NOT_FAIL`
- `WRONG_FULL_FLOOR_GATE`
- `RESTORE_MISMATCH`

Illegal transition: `PROVEN` without current-run floor evidence and byte-identical restoration.

## Dependency direction and ownership

Workflow -> canary orchestrator -> canary contract
Workflow -> clean deterministic floor
Canary orchestrator -> narrow witness subprocess
Canary orchestrator -> existing deterministic-floor CLI -> floor manifest / validators / tests
Canary orchestrator -> atomic target filesystem replacement
Canary orchestrator -> nested receipt freshness boundary

The workflow does not interpret canary semantics. The generic deterministic-floor runner does not own canary mutation semantics. The canary orchestrator is the only mutation/state owner.

## Representative success call stack

CI pull-request event
-> `.github/workflows/deterministic-test-floor.yml`
-> `run_deterministic_test_floor_canary.py`
-> load/validate canary contract
-> read target + digest
-> run clean witness (must PASS)
-> remove any pre-existing clean-floor baseline receipt
-> invoke canonical `run_deterministic_test_floor.py` on the clean checkout (must PASS with a current receipt)
-> atomically replace target with declared mutation
-> run same witness (must FAIL with declared marker/signature)
-> remove any pre-existing nested floor report
-> invoke canonical `run_deterministic_test_floor.py`
-> require a newly written floor receipt and classify it (`FAIL`, expected gate)
-> atomically restore exact original bytes in `finally`
-> compare digest
-> emit canary receipt `PASS`
-> workflow runs clean deterministic floor
-> user value: CI proves the declared regression class is detected while the unmodified repository is green.

## Representative failure call stacks

### Same broad gate, wrong cause

Synthetic/unrelated self-test or collection failure exists before mutation
-> clean witness may still PASS
-> clean canonical deterministic floor runs before mutation
-> baseline process or receipt is not PASS
-> `CLEAN_FLOOR_BASELINE_PROCESS_FAILED` and/or `CLEAN_FLOOR_BASELINE_RECEIPT_NOT_PASS`
-> mutation is never applied
-> receipt FAIL
-> workflow FAIL

### Stale floor receipt

Pre-existing floor receipt says expected gate failed
-> canary orchestrator removes it before current floor invocation
-> current floor process exits without writing a receipt
-> evaluator receives no current floor receipt
-> `FULL_FLOOR_RECEIPT_NOT_FAIL`
-> receipt FAIL

### Mutation not detectable

Clean witness PASS
-> atomic mutation applied
-> witness still PASS
-> `MUTATED_WITNESS_UNEXPECTEDLY_PASSED`
-> atomic restore in `finally`
-> receipt FAIL

### Restoration failure

Any probe state
-> atomic restoration or digest verification fails
-> `RESTORE_MISMATCH`
-> receipt FAIL even if all detection assertions otherwise passed.

## Prototype acceptance gates

1. Contract loader rejects malformed declarations before write.
2. Pure proof evaluator accepts one representative correct evidence tuple.
3. Clean full-floor baseline accepts only a current PASS receipt and rejects an unrelated same-gate failure before mutation.
4. Pure proof evaluator rejects an unrelated report with the same broad failed step.
5. Thin integration path proves clean witness PASS and mutated witness FAIL for the real generated-site marker.
6. Mutation/restoration uses same-directory atomic replacement with no temp residue.
7. Pre-existing clean/mutated nested floor receipts are removed before invocation and missing current-run receipts cannot prove either gate.
8. Workflow uses the repository-owned runner instead of embedded Python proof logic.
9. Exact-head deterministic-floor workflow passes after the canary restores the checkout.
10. Second-pass review confirms no duplicate runner semantics and no hand-edited generated output.

## Proof ceiling

The prototype can prove same-checkout differential behavior (clean full-floor PASS before mutation, declared mutated-floor FAIL afterward), deterministic CI failure specificity for the declared mutation, current-run floor-receipt freshness, and byte-identical restoration in a clean repository checkout. It does not prove arbitrary mutation classes, survival of an uncatchable process kill after a complete atomic replacement, production runtime behavior, or every future test framework output format.

## Phase map

### Phase 0 — P123 provider truth correction

Persist observed provider evidence that the existing Gemini-created Drive artifact is reachable and that source-specific Drive title/H1 identity is corrected in place. Do not promote unobserved full-source/tail analysis quality.

### Phase 1 — Canary executable seam

Create the versioned canary contract, orchestrator, focused tests, atomic mutation/restoration, fresh-receipt boundary, and workflow delegation described here.

### Phase 2 — Exact-head integration proof

Run targeted tests, deterministic test-floor CI, review the receipt, falsify with the same-gate/wrong-cause and stale-receipt cases, then integrate the exact green head into `main`.

### Phase 3 — Canonical P07 semantic-weakening canary

The second materially different canary deliberately replaces one mainline-convergence sentence in canonical P07 with a weaker branch-only completion sentence. The direct witness is `scripts/validate_prompt_semantic_coverage.py`, which must reject the temporary body drift with PSC009 and identify P07. Before mutation, the exact checkout/environment must pass a fresh canonical deterministic-floor baseline; only then may the mutated full floor fail closed at its earliest registered gate. Restoration must return `docs/prompts.json` to the exact pre-probe digest.

This phase extends the existing orchestrator with one bounded `replace_text` primitive and focused fail-closed tests. It does not add a mutation plugin framework, change accepted prompt profiles, or persist weakened prompt text.

## Deferred work

Two canaries justify the shared append/replace mutation seam but still do not justify a registry or generalized mutation-plugin framework. Add a broader registry only when another materially different canary demonstrates repeated orchestration/registration pressure that the two explicit contracts cannot cleanly absorb.
