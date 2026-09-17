# Prompt Operations Contract

Binding for Prompt Kit prompt addition/repair, language audit, generated Prompt Kit parity, and prompt-panel/chat orchestration. For vocabulary and navigation, use `GLOSSARY.md`; it is not a second behavior specification.

## Canonical contribution path

- Change the canonical prompt registry source or registered extension; never edit generated HTML as the source of truth.
- Inspect existing IDs/sequences and ownership before adding a record. Sequence identity is append-only within its registry contract; do not renumber established prompts to make room.
- Every prompt needs deterministic identity/use condition, complete copy-safe content where allowed, owned/forbidden scope, expected artifacts, validation/proof ceiling, and focused tests.
- Reuse registered builders, schemas, skills, capabilities, triggers, and validators. Product behavior belongs in code/schemas/registries/contracts, not only in prompt prose.
- Regenerate the canonical website/artifact deterministically and require exact parity before merge.

### Hosted-provider / local-proof continuity

`harness/contracts/repository-local-proof-continuity.v1.json` is the canonical cross-cutting contract for repository planning, build/repair, validation, and integration prompts.

- Planning prompts that schedule repository implementation or validation must identify the repository-native local proof owner, exact command/entrypoint, required base and proof-relevant inputs, expected receipt/result, nonzero-exit behavior, and any hosted-only gate that local proof cannot close.
- Build/repair prompts must establish or reuse that path before hosted CI becomes a single point of failure. `QUOTA_EXHAUSTED`, `RATE_LIMITED`, `RUNNER_UNAVAILABLE`, and `PERMISSION_DENIED` are execution-posture evidence, not automatic whole-sprint blockers when reviewed local actions can advance the gate.
- If provider state remains `UNKNOWN` after a bounded refresh, continue every honestly provable local gate, suppress blind hosted retries while that state is unchanged, and keep genuinely hosted-only gates `BLOCKED` until observed.
- The reviewed action registry is `harness/repository-actions.v1.json`; the canonical executor is `scripts/run_repository_action.py`. Actions are allow-listed, record exact candidate/base and versioned proof inputs, propagate nonzero exits, and confine receipts to `Outputs/repository-actions/`.
- `.github/workflows/repository-local-action.yml` is an optional provider adapter to the same action IDs, never the semantic owner. Local PASS never becomes hosted-runner, deployment, live-runtime, device, or operator-acceptance proof by inference.

### Current P79 admission candidate

`harness/prompt-topology/DURABLE_CONTRACT_FORMALIZER_CANDIDATE.md` is a **PROVISIONAL / P79 ADMISSION PENDING** contract candidate for the `DESIGNED / DECIDED -> CONTRACTED` transition. It is not prompt-registry authority. Before any identity mutation, run the registered P79 prior-art/overlap helper path recorded in that candidate and either STRENGTHEN an existing owner or ADD only through `scripts/prompt_registry_ops.py` if the distinct residual survives.

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

Canonical executable surfaces:

- contract: `harness/contracts/prompt-parallel-dispatch.v1.json`;
- manifest: `Outputs/prompt-parallel-dispatch/manifest.json` using `prompt-parallel-dispatch/v1`;
- validator/argv dispatcher: `scripts/prompt_parallel_dispatch.py`;
- receipt: `Outputs/prompt-parallel-dispatch/receipt.json` using `prompt-parallel-dispatch-receipt/v1`;
- `validate` must pass before launch; `run` launches command-addressable lanes in deterministic dependency waves; `verify-receipt` rejects REQUIRED width >= 2 claims without observed parallel dispatch evidence;
- `runtime_tool` records remain machine-readable but are executed only by the active agent runtime. The CLI fails closed rather than pretending to own unavailable tool APIs.

A planning response that prints manifest-shaped prose without materializing and validating the JSON artifact is incomplete. A validated manifest without actual launch/receipt evidence is planning/validation proof, not parallel execution proof.

## Validation boundary

Use the specific registry, Prompt Kit web, discovery, language, ordering, portability, or release-identity validators owned by the changed surface. Static/CI proof never becomes browser/device/production proof without observation.
