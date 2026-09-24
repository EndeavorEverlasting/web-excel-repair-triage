# Live Thread-Convergence → P02 Continuity Contract

This directory owns the durable machine-checkable seam between a live conversation thread-convergence controller and P02 (`Previous Chat → Active Sprint Executor`). It does not replace either prompt. It makes the handoff resumable and testable.

## Ownership boundary

- **Live controller:** detects material divergence, selects one focused thread, checkpoints every suspended thread, drives the focused target to COMPLETE, BLOCKED, HANDOFF-READY, or SUPERSEDED, then either restores work in the current conversation or emits this checkpoint for P02.
- **P02:** ingests a validated checkpoint when the current conversation is being retired or a clean execution surface is required. P02 refreshes mutable repository/provider/runtime evidence and resumes from the first unproven gate. It does not replay completed work merely to rebuild context.

## Trigger boundary

Emit a checkpoint for P02 when conversation closeout is explicit, the context surface has become execution-degrading, the remaining thread belongs on a different execution surface, or the active thread is coherently blocked/hand-off ready. Do not route to P02 for a brief side question, a normal dependency, or a suspended thread that can be safely restored in the current conversation.

## Contract

Canonical schema: `harness/conversation-continuity/checkpoint.schema.v1.json`

Canonical validator: `scripts/validate_conversation_handoff_checkpoint.py`

Stable invocation:

```bash
python scripts/validate_conversation_handoff_checkpoint.py path/to/checkpoint.json
```

Validate the repository-owned schema contract itself with:

```bash
python scripts/validate_conversation_handoff_checkpoint.py --schema-only
```

Each surviving thread carries target/disposition/priority, current execution state, last meaningful action, first unproven gate, settled/provisional decisions, exact evidence anchors, changed surfaces, completed validations, classified remaining work, exact next action, route, and return trigger. BLOCKED threads additionally carry the exact blocker and unblocking/resumption contract. Repository-backed threads carry exact branch/head and first unproven repository gate state.

## P02 ingestion algorithm

1. Validate the checkpoint before treating it as a durable execution ledger.
2. Preserve valid settled decisions and historical proof; do not reconstruct them from scratch.
3. Refresh every mutable evidence anchor before treating it as current truth.
4. Reconcile moved state narrowly: state moved, unsupported prior claim, invalidated decision, or work collision.
5. Resume from `first_unproven_gate` and `next_action`; rerun only proof invalidated by moved inputs/head/dependencies.
6. Search older conversation/history only for genuine gaps, contradictions, or omitted targets.
7. Route every surviving thread to resumed execution, durable handoff, exact blocker, user-only gate, archive, superseded, or complete.

## Anti-rework invariant

The checkpoint is a starting execution ledger, not a prose summary. A new agent must not re-plan everything when the carried decisions/proof remain valid. Mutable state is refreshed; durable proof is preserved; execution restarts at the first unproven gate.

## Proof ceiling

Schema/validator PASS proves structural and cross-field resumability requirements. It does **not** prove that evidence values are factually current. P02 still owns current-truth refresh before mutation.
