# Lesson 01 — Contract vs implementation vs procedure

Status: ACTIVE — awaiting learner checkpoints.

## Atomic invariant

A repository may expose one operation through several layers. The layers are not redundant when they answer different change questions:

- **Contract/capability layer:** what operation, inputs, outputs, routing, and proof boundary must remain true for consumers.
- **Implementation layer:** code/scripts that actually compute, validate, persist, or transform the operation's runtime result.
- **Skill layer:** reusable agent procedure and judgment for selecting, sequencing, and safely using deterministic owners.
- **Prompt layer:** task-facing invocation/orchestration instructions for a particular mission or context; it may implement a capability, invoke a skill, or coordinate several owners.

## FUN NTH trace

The selected skill says to verify a pinned FUN contract, build only artifact-validation assertions, run `scripts/export_fun_nth_artifact_manifest.py`, preserve manifest/receipt, then pass the result to FUN's resolver/validator. The skill therefore does not itself calculate SHA-256, validate the lock schema, enforce publication posture, or construct the manifest bytes.

The CLI parses runtime arguments and delegates to `triage.fun_nth_artifact_export.build_fun_nth_export` / `write_export_result`.

The deterministic module owns concrete invariants such as allowed artifact/publication types, exact contract-lock identities, packet/profile validation, SHA-256 calculation, manifest/receipt schemas, and fail-closed behavior. Tests independently assert those invariants.

Therefore, changing the implementation is not the same as changing the capability or skill. If the exporter were internally refactored from one Python function to several helper modules while preserving the same CLI, schemas, outputs, failure behavior, and proof ceiling, the runtime implementation changes while the higher-level operation and reusable skill may remain valid unchanged.

Conversely, if the operation changes — for example, the producer becomes responsible for establishing evidence truth rather than only artifact validation — that is not a harmless implementation refactor. It collides with the current ownership contract and would require contract/capability, tests, procedure, and possibly prompt/routing changes.

## Learner checkpoints

A. **CONCEPTUAL TRADE-OFF / MECHANISM** — Suppose `triage/fun_nth_artifact_export.py` is rewritten in Rust behind the same CLI contract: identical inputs, manifest/receipt schemas, failure conditions, FUN ownership boundary, and proof ceiling. Which layers *must* change, which layers *might* change only for accuracy, and which should remain untouched? Explain why.

B. **CODE DIAGNOSTIC / EDGE CASE** — Suppose a developer changes only `.ai/skills/fun-nth-artifact-export/SKILL.md` so it says a `fixture` may use `protected_runtime`, but leaves `triage/fun_nth_artifact_export.py` and its tests unchanged. Predict what happens when an agent follows the edited skill and runs the exporter with `artifact_type=fixture` and `publication_posture=protected_runtime`. What does that failure tell you about which layer owns the invariant?
