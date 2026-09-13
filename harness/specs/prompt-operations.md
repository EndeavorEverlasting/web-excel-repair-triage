# Prompt Operations Contract

Binding for Prompt Kit prompt addition/repair, language audit, generated Prompt Kit parity, and prompt-panel/chat orchestration. For vocabulary and navigation, use `GLOSSARY.md`; it is not a second behavior specification.

## Canonical contribution path

- Change the canonical prompt registry source or registered extension; never edit generated HTML as the source of truth.
- Inspect existing IDs/sequences and ownership before adding a record. Sequence identity is append-only within its registry contract; do not renumber established prompts to make room.
- Every prompt needs deterministic identity/use condition, complete copy-safe content where allowed, owned/forbidden scope, expected artifacts, validation/proof ceiling, and focused tests.
- Reuse registered builders, schemas, skills, capabilities, triggers, and validators. Product behavior belongs in code/schemas/registries/contracts, not only in prompt prose.
- Regenerate the canonical website/artifact deterministically and require exact parity before merge.

## Copy-safe and reference surfaces

Canonical Prompt Kit records live in registered sources such as `docs/prompts.json` and extension registries. Reference metadata belongs in the registered reference surface. Copy-safe content must follow the repository allowlist/registry contract; index-only or reference-only material must not be silently promoted into copyable prompt bodies.

## External expert-insight intake

Expert knowledge captured outside Git may feed Prompt Kit work only through an explicit authority boundary. A Google Sheet or other collaboration source remains authoritative for its raw knowledge rows; Git remains authoritative for Prompt Kit implementation, review history, validation, and integration.

- Normalize external insight rows through a validated schema before repository use. Do not track private source IDs, credentials, raw private exports, or lossy round-trip copies merely to make CI convenient.
- Captured/untriaged rows are evidence only. Their full text must not be promoted into repository review artifacts until an explicit publication state and canonical owner are present.
- Repository-ready rows must identify an existing owner or a deliberate ADD decision plus acceptance/proof criteria and validation lenses. `UNKNOWN` ownership is not mergeable input.
- Intake/eval automation may emit review candidates, summaries, failure cases, or evidence. It must declare `mutation_authority: false` and must not allocate prompt IDs, edit registries, or rewrite prompt templates autonomously.
- Approved additions use `scripts/prompt_registry_ops.py`; approved strengthening edits the proven canonical owner and then runs that owner's focused validators and generated-site parity.
- The current Google Sheet contract, fixture/live CI modes, and credential gate are documented in `docs/PROMPT_KIT_EXPERT_INSIGHT_INTAKE.md`.

## Prompt-language quality

Run the canonical audit:

```bash
python scripts/evaluate_prompt_language.py --summary
python -m unittest tests.test_prompt_language_audit -v
```

The audit must cover the effective combined registry rather than a sample. Each registered prompt receives an explicit disposition and coverage must be complete. Repair canonical sources, not generated HTML. Empty/placeholder/non-executable next actions, operator reconstruction, ownership ambiguity, proof inflation, and stale generated output are defects.

## Panels, chats, and parallelism

A prompt panel is a transport container; a chat is an execution instance. One panel may map to one independently schedulable chat only when its complete sprint contract is self-contained.

Parallel execution does not weaken ownership or proof. Units that write the same file, schema, registry, generated artifact, branch, PR, deployment target, or mutable runtime must be serialized or assigned one writer. Every parallel group needs explicit dependencies/collision ownership and one convergence unit that validates the combined result.

### Parallel capability ladder and autonomy

Parallelism is derived from the work graph, not from the presence of one favorite worker product. First determine whether at least two meaningful dependency-ready lanes can proceed without conflicting writes. When graph width is at least two, probe available execution adapters in this order and dispatch at the first safe rung with sufficient capacity: native sub-agent/child-agent/delegated-agent APIs; repository/local agent runners; connected remote/provider/MCP execution surfaces; CI/job/matrix fan-out; then genuinely concurrent local processes or tool jobs for deterministic non-LLM lanes. A missing rung never proves later rungs absent. In particular, `no connected self-hosted workers` is one capability fact, not proof that parallel execution is globally unavailable.

Serial multi-tool use is not parallel execution. The local-process/tool rung counts only when independent jobs are actually launched concurrently and rejoined. Graph width one is `PARALLEL EXECUTION: NOT_APPLICABLE`. When graph width is at least two and every safe rung is evidenced unavailable or blocked, useful work may continue serially only as degraded execution: report `PARALLEL EXECUTION: DEGRADED` and an `AUTONOMY_GAP` naming the smallest executable adapter/bootstrap/repair route. Parallel proof remains UNPROVEN until a real dispatch occurs.

Planning surfaces must produce a machine-executable `PARALLEL DISPATCH MANIFEST` as the primary orchestration artifact. Each ready lane names its dependencies, mutation owner, forbidden surfaces, branch/worktree or read-only posture, chosen adapter/rung, exact launch action, return artifact/contract, validator, convergence owner, and status. Copyable chat panels are portability/recovery fallback only. Do not make the operator create chats, paste prompts, shuttle context, or act as the scheduler when any autonomous adapter can carry the lane.

## Validation boundary

Use the specific registry, Prompt Kit web, discovery, language, ordering, portability, or release-identity validators owned by the changed surface. Static/CI proof never becomes browser/device/production proof without observation.
