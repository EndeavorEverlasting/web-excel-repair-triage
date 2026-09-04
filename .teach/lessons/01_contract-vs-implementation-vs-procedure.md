# Lesson 01 — Contract vs implementation vs procedure

Status: VERIFIED

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

Therefore, changing the implementation is not the same as changing the capability or skill. If the exporter were internally refactored or rewritten in another language while preserving the same observable contract, the runtime implementation changes while the higher-level operation may remain valid unchanged. Implementation-specific skill, test, CI, or registry references need repair only when they become stale.

Conversely, if the operation changes — for example, the producer becomes responsible for establishing evidence truth rather than only artifact validation — that is not a harmless implementation refactor. It collides with the current ownership contract and would require contract/capability, tests, procedure, and possibly prompt/routing changes.

## Learner checkpoint attempt 1

### A — mechanism-preserving rewrite

The learner correctly identified that the implementation layer must change when the Python implementation is replaced by Rust. The learner also recognized that implementation-specific validation or harness references may need adjustment. Remaining precision point was that the harness does **not** need to change merely because the implementation language changes. Only surfaces that name Python-specific files, commands, or assumptions need updating.

### B — contradictory skill prose

The learner initially predicted that the agent might continue until later self-evaluation or harness review. Remediation established that `build_fun_nth_export` rejects `artifact_type=fixture` with any publication posture other than `sanitized_fixture`; the CLI catches the resulting `FunNthExportError`, prints `FAIL`, and returns exit code 2. Runtime enforcement and later agent reporting are separate layers.

## Learner checkpoint attempt 2 — VERIFIED

### A — stale instruction vs stable contract

The learner correctly identified the skill as stale when it retained a Python-specific invocation after an implementation-preserving Rust rewrite, while keeping the capability unchanged. Minor terminology correction: the rewrite preserves the **observable capability contract**, not the implementation; the implementation is what changed.

### B — runtime enforcement vs agent narrative

The learner correctly separated the CLI/runtime layer that prevents the invalid export from the agentic layer that could falsely report success. This demonstrates the required distinction between deterministic execution truth and an agent's later narrative claim.

## Verified conclusion

The learner can now distinguish a capability/contract from its replaceable implementation mechanism, identify when a skill becomes stale because it embeds an implementation-specific instruction, and separate deterministic runtime enforcement from agent reporting. This atomic invariant is verified; broader Prompt Kit ontology remains in progress.
