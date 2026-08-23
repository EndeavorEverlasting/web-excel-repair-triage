# Prompt Operations Contract

Binding for Prompt Kit prompt addition/repair, language audit, generated Prompt Kit parity, and prompt-panel/chat orchestration.

## Canonical contribution path

- Change the canonical prompt registry source or registered extension; never edit generated HTML as the source of truth.
- Inspect existing IDs/sequences and ownership before adding a record. Sequence identity is append-only within its registry contract; do not renumber established prompts to make room.
- Every prompt needs deterministic identity/use condition, complete copy-safe content where allowed, owned/forbidden scope, expected artifacts, validation/proof ceiling, and focused tests.
- Reuse registered builders, schemas, skills, capabilities, triggers, and validators. Product behavior belongs in code/schemas/registries/contracts, not only in prompt prose.
- Regenerate the canonical website/artifact deterministically and require exact parity before merge.


## Exact prompt-contribution grounding

Exact registry mechanics are a deterministic tool boundary, not model-memory work. `scripts/prompt_registry_ops.py` owns a compact JIT grounding packet containing current registry IDs/paths, next auto-owned identity, draft-field contract, actionability policy identity, builder/output identity, and SHA-256 provenance for only the canonical structural sources that can affect those values. It does **not** load prompt bodies into the grounding packet. The fingerprint also covers every current builder input consumed by the protected site rebuild: display-order policy, reference data, base and supplemental runtime JavaScript, the HTML builder module, the combined registry builder, and its policy/registry inputs.

For an agent or tool that needs exact structure before composing a contribution, use:

```bash
python scripts/prompt_registry_ops.py ground > /tmp/prompt-grounding.json
python scripts/prompt_registry_ops.py check --input <draft.json> --registry <registry_id> --grounding /tmp/prompt-grounding.json
```

The check is read-only and returns one fail-closed gate state: `GROUNDED_PASS`, `UNSOURCED_BLOCK`, `CONTRADICTION_BLOCK`, `SCHEMA_MISMATCH`, or `GROUNDING_FAILURE`. Critical parameters carry resolvable source-key/path/selector attribution. A stale or tampered grounding packet is never treated as PASS.

Ordinary contributors do not need extra ceremony: `add` repeats the gate internally immediately before its protected registry/site write path. Real writes are serialized by a same-checkout process lock held from fresh grounding and identity allocation through registry mutation, rebuild, parity proof, and rollback; a contending helper fails closed instead of racing the ID allocator. Supplying `--grounding` pins the add to a previously emitted packet; if canonical structural inputs moved, the add blocks and must refresh rather than silently allocating from stale memory. Auto-owned `id`, `seq`, and `copySheet` remain forbidden in drafts. Direct registry writes that bypass this helper remain outside the supported mutation contract.

Model critics may help with semantic prompt quality, but they do not override deterministic registry/schema/grounding failures.

## Copy-safe and reference surfaces

Canonical Prompt Kit records live in registered sources such as `docs/prompts.json` and extension registries. Reference metadata belongs in the registered reference surface. Copy-safe content must follow the repository allowlist/registry contract; index-only or reference-only material must not be silently promoted into copyable prompt bodies.

## Prompt-language quality

Run the canonical audit:

```bash
python scripts/evaluate_prompt_language.py --summary
python -m unittest tests.test_prompt_language_quality -v
```

The audit must cover the effective combined registry rather than a sample. Each registered prompt receives an explicit disposition and coverage must be complete. Repair canonical sources, not generated HTML. Empty/placeholder/non-executable next actions, operator reconstruction, ownership ambiguity, proof inflation, and stale generated output are defects.

## Panels, chats, and parallelism

A prompt panel is a transport container; a chat is an execution instance. One panel may map to one independently schedulable chat only when its complete sprint contract is self-contained.

Parallel execution does not weaken ownership or proof. Units that write the same file, schema, registry, generated artifact, branch, PR, deployment target, or mutable runtime must be serialized or assigned one writer. Every parallel group needs explicit dependencies/collision ownership and one convergence unit that validates the combined result.

## Validation boundary

Use the specific registry, Prompt Kit web, discovery, language, ordering, portability, or release-identity validators owned by the changed surface. Static/CI proof never becomes browser/device/production proof without observation.
