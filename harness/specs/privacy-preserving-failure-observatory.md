# Privacy-Preserving Prompt Failure Observatory — Program Design

## Outcome

Catch and explain when Prompt Kit prompts fail in third-party agents such as Cursor **without making user content an input to repository learning**.

Selected architecture: **allowlist local sentinel + structured finalization receipt**. Transcript analysis and redact-then-send telemetry are rejected.

## Program boundary

- **Governance:** `AGENTS.md`, execution-boundary contracts, privacy contract, recurrence rules.
- **Harness:** validators, deterministic floor, fixtures, generated-site proof.
- **Program design:** host adapter -> local sentinel -> boundary engine -> zero-content compiler.
- **Broad implementation:** installable host plugins, anonymous contribution transport, aggregate repository learner. These are successor phases.

## User outcomes / invariants

1. A Cursor run that stops after a tool failure without a valid finalization receipt is explainable locally.
2. A clean completion with a valid receipt is not falsely reported as abandonment.
3. User abort is a stable stop, not a recovery loop.
4. Host/process error can be synthesized by an external sentinel even if the agent cannot self-report.
5. Prompt/code/path/command/error/response/reasoning content cannot enter the contribution capsule.
6. Local observability works with networking permanently disabled.
7. Future repository learning consumes aggregate zero-content phenotypes, never transcript evidence.

## Design space

| Candidate | Hard-stop detection | Privacy | Decision |
| --- | --- | --- | --- |
| Transcript classifier | strong | collector sees private content | reject |
| Redact-then-send telemetry | strong | starts with toxic data | reject |
| Receipt-only self-report | weak | content-minimal | reject as sole detector |
| Allowlist local sentinel + receipt | strong | raw payload dies at adapter boundary | **selected** |

Cursor currently exposes lifecycle/tool/edit/stop hooks including `beforeSubmitPrompt`, `postToolUseFailure`, `afterFileEdit`, `stop`, and local `sessionEnd`. The prototype deliberately excludes `afterAgentThought` and `afterAgentResponse`.

## Deployment operating model

**Local process only.** No PaaS, container host, Kubernetes, collector, remote database, or network sender belongs in P0. The irreducible application state is a handful of categorical fields for the active run. If anonymous contribution is later approved, its infrastructure tier must be selected from measured aggregate write rate, retention, anonymity-set requirements, privacy budget, RTO/RPO, and operating cost.

## Domain vocabulary

- **HostHookPayload:** toxic raw third-party JSON; ephemeral.
- **HostSignal:** allowlisted categorical event.
- **PromptProvenance:** public prompt id + release bucket.
- **FinalizationReceipt:** structured local terminal proof.
- **RunState:** zero-content local state.
- **FailurePhenotype:** host-independent failure classification.
- **ContributionCapsule:** fixed allowlist local preview.
- **PrivacyCanary:** injected private string proving non-reachability.

## Modules and ownership

### CursorHookAdapter
Owns only raw Cursor JSON -> HostSignal translation. No persistence. It is the only module allowed to see raw hook payloads.

### LocalRunStore
Owns cross-process RunState persistence. It stores no raw hook field and no timestamp/path/content identifier.

### FailureSentinel
Owns objective lifecycle, receipt reconciliation, stop interpretation, and selection of the observed boundary signal.

### BoundaryEnginePort
Delegates classification/recovery to the canonical execution-boundary engine. It knows nothing about Cursor.

### ZeroContentCompiler
Constructs a capsule from scratch from one fixed allowlist. It does not accept a host payload.

### RepositoryLearner
Future only. It may consume approved aggregates after P2. It has no API in P0.

## Dependency direction

```text
Cursor hook stdin
  -> CursorHookAdapter
       RAW PAYLOAD TERMINATES HERE
  -> HostSignal
  -> FailureSentinel
       -> LocalRunStore
       -> BoundaryEnginePort
            -> execution_boundary_engine
  -> FailurePhenotype / RunState
  -> ZeroContentCompiler
  -> local capsule preview

future only:
local capsule -> approved privacy mechanism -> anonymous aggregate -> RepositoryLearner
```

No reverse dependency is allowed. Repository code cannot request local transcript data.

## Success stack

```text
beforeSubmitPrompt
  -> adapter extracts bounded [[AFK_PROMPT:P07@2026.09]] marker only
  -> RUN_STARTED
  -> sentinel
  -> zero-content state

agent/local companion emits FinalizationReceipt(P07, 2026.09, VALIDATED)
  -> sentinel stores receipt

stop(completed)
  -> sentinel verifies receipt
  -> SUCCESS
  -> compiler
  -> local success capsule
```

Terminal user value: deterministic proof that the prompt reached its declared completion contract without uploading a conversation.

## Failure stack — silent stop after tool failure

```text
postToolUseFailure
  -> adapter retains only failure_type/is_interrupt/tool category
  -> TOOL_FAILURE

afterFileEdit
  -> MUTATION_OBSERVED

stop(completed), receipt absent
  -> sentinel
  -> EC_SEMANTIC_ABANDONMENT
  -> execution_boundary_engine
  -> EBE.NO_SILENT_STOP
  -> compiler
  -> local boundary capsule
```

Terminal user value: “P07 stopped in Cursor without finalization; a timeout preceded the stop; mutation occurred.” No command, path, error text, code, or transcript is needed.

## Failure stack — host error before self-report

```text
sessionEnd(error), receipt absent
  -> sentinel marks process_alive=false
  -> engine normalizes prior non-HT signal
     to HT_HOST_FORCED_TERMINATION
  -> SYNTHESIZE_TERMINATION
  -> local capsule
```

The acting agent is not responsible for reporting its own death.

## Failure stack — explicit cancellation

```text
stop(aborted) or interrupt signal
  -> UC_CANCELLED
  -> QUIESCE_UNCHANGED_BLOCKER
  -> stable stopped state
```

Cancellation is not misclassified as recovery.

## Privacy diode

Cursor may send raw JSON to the hook process; Cursor controls that invocation. The program's privacy boundary is the adapter output. The adapter constructs a new HostSignal from enumerated categorical fields.

Forbidden from durable state and capsules:

- prompt/response/reasoning text;
- error strings;
- shell commands/arguments;
- files/workspaces/repository names;
- attachments;
- account/email/device IDs;
- Cursor session/conversation/generation/tool-use IDs;
- exact timestamps.

Public provenance grammar is bounded to a marker such as `[[AFK_PROMPT:P07@2026.09]]`. Arbitrary marker payload is invalid.

## Testability / observability

Unit/integration proof targets the actual seams:
- raw payload -> HostSignal;
- HostSignal sequence -> RunState;
- terminal RunState -> boundary engine;
- RunState -> capsule;
- file store round-trip.

The privacy canary suite injects unique secrets into every toxic field and fails if any appears in serialized state or capsule. A static import gate rejects network client modules from the P0 runtime.

Diagnostics are categorical only. They are not durable product analytics.

## Second-pass critique

Receipt-only was insufficient because process loss can prevent the receipt. Transcript-based detection was unacceptable because it needs the very content we want to make irrelevant. Combining external local lifecycle observation with a narrow receipt preserves liveness and precision.

The remaining attribution compromise is the public marker in `beforeSubmitPrompt`. P0 parses only the first bounded marker and immediately discards the prompt. A later browser/Prompt Kit companion may replace marker parsing with an out-of-band local provenance handoff.

## Prior-art boundary

- Cursor hooks are host-lifecycle prior art and supply the local execution seam.
- RAPPOR/local differential privacy is future prior art for population statistics, not part of P0.
- RFC 9458 Oblivious HTTP is future prior art for relay/gateway unlinkability, not part of P0.

No networking is implemented until the local diode earns proof.

## Durable phase map

- **P0 LOCAL PROTOTYPE:** validated and integrated; local-only executable seams + privacy canaries.
- **P1 HOST INSTALLATION:** repository project hooks are installed through tracked `.cursor/hooks.json` and validated through the real sentinel CLI; synthetic stdio covers success, abandonment, user abort, and host error. Real local Cursor observation and an out-of-band provenance handoff remain required before P1 closes.
- **P2 ANONYMOUS CONTRIBUTION:** separately approved privacy design; opt-in; aggregation/thresholding/unlinkability proof.
- **P3 REPOSITORY LEARNER:** consumes only approved aggregates and proposes regression work.

Broad implementation must preserve P0 interfaces and tests rather than bypassing them.

### P1 repository installation

The project-scoped installation is `.cursor/hooks.json`. Cursor runs project hooks from the repository root in trusted workspaces, so every installed command targets the canonical `scripts/cursor_failure_sentinel.py` entry point and the gitignored `.afk-observatory/` state directory. The hooks are deliberately passive (`failClosed: false`): observability failure must not become an agent-execution blocker.

Repository proof executes the same stdin JSON -> sentinel CLI path used by Cursor for all four terminal scenarios. This proves packaging and protocol reachability, not that a particular Cursor desktop has loaded the project hooks.

P1 cannot close by prefixing or suffixing prompt text with hidden identity metadata. Canonical Prompt Kit copy identity remains unchanged. The unresolved provenance transition is an out-of-band local handoff that identifies the copied prompt without exporting raw Cursor generation/session IDs or the derived local run key.

## Proof ceiling

Repository proof establishes deterministic modeled behavior and forbidden-data non-reachability. It does not prove a real Cursor installation, OS compromise resistance, anonymous networking, differential-privacy guarantees, or repository aggregation.


## Local concurrency without exportable identity

Cursor supplies `generation_id` across agent hooks. P0 uses that value only inside the local adapter process to address concurrent runs safely:

```text
raw generation_id
  + 32-byte device-local random secret
  -> HMAC-SHA256
  -> 24-hex local run key
  -> .afk-observatory/runs/<run-key>.json
```

The raw host identifier is never written. The HMAC key is device-local and ignored by Git. The derived run key is **not a capsule field** and is never repository contribution data. Different local installations produce different run keys for the same host identifier, so the correlation primitive is useful for local concurrency without becoming a portable pseudonymous user identity.

The finalization-receipt transport remains a P1 integration seam: an installable Cursor companion/MCP tool must receive the local run key without exposing the raw host identifier or requiring transcript parsing.
