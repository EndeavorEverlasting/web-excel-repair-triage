# P04/P05 Runtime Partition Program Design

**Status:** PROTOTYPE / pre-broad-implementation design gate
**Shared contract:** `harness/contracts/planning-runtime-partition.v1.json`
**Executable seam:** `scripts/prompt_runtime_partition.py`
**Focused tests:** `tests/test_prompt_runtime_partition_prompt.py`

## User outcomes

1. P04/P05 complete planning/evidence work in the active ChatGPT runtime when it is both capable and authorized instead of unnecessarily punting it to local agents.
2. Local-only work stays local.
3. A provider such as Google Drive or GitHub is modeled as an access/transport used by a host runtime, not as a competing host-runtime identity.
4. Already-completed current-runtime work becomes inherited evidence rather than a fake future sprint.
5. Private provider identifiers do not have to enter tracked dispatch manifests.
6. P04 and P05 share one runtime-partition decision seam while projecting it differently.

## Invariants

- One material work unit has exactly one host execution environment.
- Provider/external access is zero-or-more metadata, not host identity.
- Conflicting hard host requirements mean the work unit is not atomic and must be split.
- Tool/provider presence does not prove authentication or mutation authority.
- Inherited evidence carries source owner, revision/freshness, visibility, sanitized reference, and proof ceiling.
- P04 remains PLAN / DISTRIBUTE; P05 remains PLAN / PACK; P07/canonical implementation owners retain implementation authority.
- LAUNCH ORDER remains the first substantive emitted section for both planners.
- No tracked manifest requires a raw private provider URL/ID.

## Domain vocabulary

- **WorkUnit** — one atomic planning unit whose host placement can be decided without conflicting hard runtime requirements.
- **CapabilityFacts** — observed/authorized host constraints used for placement.
- **HostExecutionEnvironment** — CURRENT_CHAT_RUNTIME, LOCAL_AGENT_RUNTIME, CI_OR_REMOTE_RUNNER, OPERATOR_OR_PHYSICAL_RUNTIME, or UNKNOWN_RUNTIME.
- **ProviderAccess** — provider family + operation + observed authority state + mutation-authority fact.
- **InheritedEvidence** — sanitized durable reference plus owner, freshness/revision, visibility, and proof ceiling.
- **PartitionDecision** — canonical host placement and evidence/access bundle consumed by planner-specific projection.
- **P04Projection** — dispatch-manifest metadata.
- **P05Projection** — serialized panel/handoff metadata.

## Module/interface map

### planning-runtime-partition contract
Owns the vocabulary, allowed values, placement precedence, privacy rule, and P04/P05 projection obligations.

### `partition_work_unit(work_unit)`
Pure domain seam. Owns host placement and validation. It has no network or filesystem side effects.

Input:
- WorkUnit facts.

Output:
- PartitionDecision.

Errors:
- malformed facts;
- conflicting hard host requirements;
- unsafe private evidence representation.

### `project_p04(decision)`
Maps one accepted PartitionDecision into dispatch-manifest fields. It does not choose adapters or graph width.

### `project_p05(decision)`
Maps the same decision into serialized-panel fields. It does not create launch order or implementation work.

## Dependency direction

Prompt input / repository evidence
→ WorkUnit normalization
→ `partition_work_unit`
→ PartitionDecision
→ P04 graph/adapter/manifest **or** P05 ordered-pack/panels
→ downstream executor/provider

Provider adapters do not call back into runtime placement. Runtime placement does not authenticate providers.

## Success call stack — P04 with Google Drive

Operator invokes P04 with repo/context
→ P04 preflight observes ChatGPT runtime + Google Drive capability/authority
→ normalize WorkUnit
→ `partition_work_unit`
→ CURRENT_CHAT_RUNTIME + provider_access[google_drive]
→ execute authorized planning/evidence step now
→ convert result to sanitized InheritedEvidence
→ append that evidence to the WorkUnit and set `already_executed_here=true`
→ re-run `partition_work_unit` so the completed fact is part of the decision
→ P04 builds the remaining-work dependency graph
→ `project_p04`
→ typed dispatch manifest for remaining work
→ LAUNCH ORDER first, placement table after it

Terminal user value: the local executor receives only the work that actually remains, with evidence already established.

## Success call stack — P05 serialized pack

Operator invokes P05
→ preflight/normalization
→ attach any already-completed current-runtime evidence and set `already_executed_here=true` before final placement
→ `partition_work_unit` for each ordered work unit
→ if execution during planning adds evidence, update the WorkUnit and re-partition before projection
→ build serialized dependency chain
→ LAUNCH ORDER
→ runtime-placement summary
→ `project_p05` for successor panels
→ local/CI panels inherit sanitized evidence

Terminal user value: the ordered pack contains no redundant rediscovery sprint.

## Failure call stack — conflicting host requirements

WorkUnit says local toolchain required + CI-only runtime required
→ `partition_work_unit`
→ RuntimePartitionError: split work unit before placement
→ planner factors the unit into separate owned units
→ no ambiguous host selection enters a manifest.

## Failure call stack — private provider identity

Protected external evidence contains raw Drive URL
→ evidence validator
→ RuntimePartitionError
→ planner substitutes an opaque tracked alias and keeps raw identity in protected provider transport
→ tracked manifest remains safe.

## Alternatives considered

### A. Provider as an execution-environment value
Rejected: overlaps with CURRENT_CHAT_RUNTIME and cannot represent ChatGPT invoking Drive/GitHub deterministically.

### B. One generic agent/runtime string
Rejected: recreates the original failure by hiding whether work is available to current ChatGPT, local agent, CI, or operator.

### C. Shared host-placement seam + separate provider metadata
Selected: smallest interface, deterministic host ownership, clean provider separation, reusable by both P04/P05.

## Prototype proof

The prototype intentionally uses no provider mock because provider execution is not the seam under test. It tests real partition logic and planner projections while treating the true external boundary as provider metadata.

The focused test suite covers:
- current ChatGPT + Google provider;
- provider presence without host proof;
- local-only placement;
- conflicting host requirements;
- raw Google Workspace URL rejection regardless of claimed visibility;
- raw GitHub URL rejection unless public status is explicitly verified;
- opaque protected evidence;
- strict enum typing;
- strict `already_executed_here` boolean validation, current-runtime-only completion, and evidence requirement;
- projection copy isolation;
- shared P04/P05 decision projection;
- already-completed P05 current-runtime work.

## Second-pass critique

The first draft conflated CONNECTED_PROVIDER with host execution environment and allowed untyped evidence strings. Review evidence exposed both leaks.

The selected seam corrects them by:
- removing provider from host enum;
- making evidence structured;
- making privacy/freshness travel with evidence;
- refusing ambiguous multi-host WorkUnits.

No additional adapter abstraction is needed inside this domain seam.

## Broad implementation boundary

Only after this prototype is green should broad implementation mutate:
- P04/P05 canonical bodies;
- prompt-parallel-dispatch contract/validator/fixtures;
- semantic capability catalog/profiles;
- focused planner regressions;
- canonical Prompt Kit build/public surface.

The prototype remains a testable design seam; it must not become a second planner or provider client.
