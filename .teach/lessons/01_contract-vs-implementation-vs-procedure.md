# Lesson 01 — Contract vs implementation vs procedure

Status: ACTIVE — checkpoint A mostly demonstrated; checkpoint B remediation required.

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

## Learner checkpoint attempt 1

### A — mechanism-preserving rewrite

The learner correctly identified that the implementation layer must change when the Python implementation is replaced by Rust. The learner also recognized that implementation-specific validation or harness references may need adjustment. Remaining precision point: the harness does **not** need to change merely because the implementation language changes. Only harness/skill/test surfaces that name Python-specific files, commands, or assumptions need updating. A stable capability/contract and implementation-agnostic prompt should remain untouched.

### B — contradictory skill prose

The learner predicted that the agent might continue until later self-evaluation or harness review. This misses the fail-closed runtime boundary. `build_fun_nth_export` rejects `artifact_type=fixture` with any publication posture other than `sanitized_fixture`; the CLI catches the resulting `FunNthExportError`, prints `FAIL`, and returns exit code 2. The invalid artifact therefore does not become a valid exporter result merely because skill prose said otherwise.

This demonstrates the current remediation target: distinguish **runtime enforcement** from later **harness validation**. Skill prose can misdirect an agent, but it cannot override a deterministic invariant enforced by executable code. If an agent ignores the nonzero exit and fabricates success, that is a separate agent/compliance defect rather than successful execution of the capability.

## Learner checkpoints

A. **CONCEPTUAL TRADE-OFF / MECHANISM** — Suppose the Rust rewrite preserves every observable contract but the skill still contains a validation command `python scripts/export_fun_nth_artifact_manifest.py --help`. Is the *operation* stale, the *skill* stale, the *implementation* stale, or some combination? Explain exactly what needs repair and why the capability contract itself may remain valid.

B. **CODE DIAGNOSTIC / EDGE CASE** — The runtime returns exit code 2 for `fixture + protected_runtime`, but an agent nevertheless writes in its final response, “Export succeeded.” Which layer successfully prevented the invalid artifact, and which separate layer failed? Name the two failures/successes without using the umbrella word “harness.”
