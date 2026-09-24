# Prompt Kit program architecture — prototype-earned seams

## Purpose

This document is the program-design owner for the browser Prompt Kit. It sits between repository governance/harness and broad feature implementation. It defines runtime vocabulary, state ownership, dependency direction, command/query seams, side-effect ports, failure contracts, and executable prototypes that must stay coherent as new Prompt Kit features are proposed.

It does **not** replace:

- governance (`AGENTS.md` and repository work rules);
- the operational harness, validators, workflows, artifact registries, or responsive-layout harness;
- full production implementation in `docs/prompt-kit*.js`;
- generated `web/prompt-kit/index.html`, which remains builder-owned.

Broad production migration is intentionally outside this design sprint.

## Fresh evidence floor for this design session

Initial design floor: `main@f36de4f4f8c40ee6d29bfa9127dd3b2085823b13` on 2026-08-24.

Before final proof the branch was reconciled non-destructively with `main@9c5639ff4d01268c034cc36344cfae1843bce494`, which includes the current P113 generated-site parity hardening. The focused prototype workflow must prove the reconciled candidate SHA explicitly rather than GitHub's synthetic pull-request merge ref.

Current evidence establishes:

- one canonical Prompt Kit registry/build path and generated web artifact;
- `docs/prompt-kit-polish.js` currently owns substantial view, filter, clipboard, favorites, and keyboard behavior;
- configured prompt-ID shortcuts have already converged on **copy + reveal prompt** rather than opening detail;
- the existing hotkey design/prototype remains the single shortcut owner;
- browser geometry, real Clipboard API policy, and operator ergonomics remain runtime proof ceilings.

This design therefore generalizes the layer above individual hotkeys: how any entrypoint reaches semantic Prompt Kit behavior without becoming a second state, persistence, or side-effect owner.

## Observable done checklist

The architecture is design-ready only when evidence proves:

1. user outcomes and invariants are named independently of DOM implementation;
2. transient session state, durable preferences, semantic completion usage, catalog data, shortcuts, and generated artifacts each have one owner;
3. at least two materially different execution seams are compared with executable code;
4. copy/reveal and Favorite mutation traverse real domain decisions and fake only external boundaries;
5. asynchronous clipboard rejection and preference-persistence failure retain truthful state;
6. opening/inspecting a prompt is not falsely counted as copying it;
7. telemetry degradation cannot retroactively turn successful user value into failure;
8. command handlers must return a validated `CommandResult`;
9. a new command can register without changing every entrypoint;
10. the selected design has exact-head CI proof and broad production migration remains deferred.

## User outcomes

The Prompt Kit should let a user reach the intended prompt outcome from multiple surfaces without caring which UI entrypoint initiated it.

Current user-value journeys include:

- copy a prompt and receive completion only after the clipboard write resolves successfully;
- reveal/locate a prompt when a command targets it;
- inspect a prompt when inspection is the intended terminal action;
- save/remove Favorites durably and fail closed when persistence fails;
- search/filter/navigate without transient view choices becoming durable preference truth;
- invoke semantic commands from keyboard, cards, finder/tutorial surfaces, or future surfaces without duplicating business rules;
- preserve keyboard accessibility and editable-field safety;
- optionally project semantic completion events without counting incidental views/focus as product usage.

## Core invariants

1. **Terminal value beats intermediate UI.** A copy command is complete only after the asynchronous clipboard write resolves; reveal/focus are supporting states, not success.
2. **Inspection is not completion telemetry.** Opening detail must never count as a copied prompt.
3. **Durable preference writes publish after persistence.** A failed Favorite/shortcut save leaves the prior in-memory state authoritative.
4. **Transient view state is not preference state.** Search text, filters, selected section, active detail, and copy target are session-owned.
5. **One semantic completion ledger.** If usage/personalization ships, it records completed domain actions; dashboards/recommendations are projections, never writers.
6. **Telemetry is subordinate to user value.** Telemetry degradation cannot undo a completed clipboard write or durable preference mutation.
7. **Catalog identity is canonical.** Commands target prompt IDs resolved by the effective prompt registry.
8. **Generated HTML is not a state owner.** Production source changes flow through the registered builder.
9. **Entrypoints translate; they do not own policy.** Hotkeys, cards, finder/tutorial UI, and future surfaces create commands/queries and render results.
10. **Async boundaries are awaited.** External Promise-returning ports must settle before a command reports terminal success.
11. **Command results are typed at runtime.** The kernel validates a handler result before recording `command_completed`; invalid results fail as `INVALID_COMMAND_RESULT` rather than crashing after the fact.

## Domain vocabulary

### Core records

- **PromptRecord** — canonical prompt identity, copyable content, and metadata.
- **PromptTarget** — validated prompt identity used by runtime commands.
- **PromptCommand** — imperative request for terminal behavior, e.g. `COPY_REVEAL_PROMPT`, `TOGGLE_FAVORITE`, `OPEN_PROMPT_DETAIL`.
- **PromptQuery** — read-only request for search/filter/list/ranking projections.
- **CommandResult** — validated terminal outcome such as `COPIED`, `DETAIL_OPEN`, or `FAVORITE_CHANGED`.
- **ProgramError** — classified failure with stable code and safe recovery metadata.

### State owners

- **PromptCatalog** — read-only effective prompt records produced by the registry/build pipeline.
- **SessionState** — transient browsing state: view, search, filters, active prompt, open detail, keyboard copy target.
- **FavoritePreferences** — authoritative Favorite set after successful persistence.
- **ShortcutRegistry** — existing durable configured shortcut owner; it is not duplicated here.
- **UsageLedger** — semantic completed-action events only, local/private/resettable if productized.

### Runtime services and ports

- **CommandKernel** — application seam mapping command IDs to handlers; public interface is `execute(command) -> Promise<CommandResult>`.
- **PromptActionHandler** — owns complete success/failure ordering for one semantic action.
- **ClipboardPort** — asynchronous external boundary: `writeText(text) -> Promise`.
- **PreferenceStore** — durable browser storage boundary for Favorites/preferences.
- **PromptSurfacePort** — DOM/presentation adapter for reveal, focus, detail, and preference projection.
- **UsageLedger** — semantic completion sink; owns retention/privacy/reset if ever productionized.

### Entrypoints

- **HotkeyEntrypoint** — keyboard resolution → PromptCommand.
- **PromptCardEntrypoint** — card control → PromptCommand.
- **FinderEntrypoint** — finder/tutorial result → PromptCommand or PromptQuery.

Future entrypoints must translate to the same semantic interfaces rather than call persistence, clipboard, or DOM internals directly.

## External prior-art inspection

The session inspected mechanisms, not foreign file layouts or implementation code.

### VS Code command registry/service

Source inspected: `microsoft/vscode`, `src/vs/platform/commands/common/commands.ts`.

Transferable mechanism: a small execute-command service, stable command IDs, handler registration, and boundary validation. Callers do not need handler internals.

### Redux store/reducer

Source inspected: `reduxjs/redux`, `src/createStore.ts`.

Transferable mechanism: one dispatch seam, explicit state ownership, serializable action identity, and guarded state mutation.

Both inspected repositories are MIT licensed. This design copies no external implementation and adds no dependency.

## Candidate architectures

### Candidate A — existing local handlers, made slightly more disciplined

Each UI surface continues calling copy/detail/Favorite/render/storage helpers directly.

**Advantage:** smallest first patch.

**Failure:** terminal semantics and failure ordering remain scattered; new surfaces can duplicate reveal → focus → clipboard → completion rules and create split-brain state ownership.

**Disposition:** baseline only.

### Candidate B — global reducer + effect runner

Every interaction dispatches an action. A reducer computes pending state and effect descriptors. A runner executes critical precommit effects, commits state, then postcommit presentation/telemetry.

**Advantages:** explicit state transition model and replay/debug discipline.

**Prototype cost:** copy is principally an asynchronous terminal side effect, not a state transition. Fail-closed Favorite persistence requires precommit effects, and clipboard/persistence/presentation/telemetry require phase and criticality metadata. The reducer becomes an effect-plan protocol rather than a simple reducer.

**Disposition:** executable and viable, but rejected for current Prompt Kit.

### Candidate C — command kernel + deep state owners + ports

Entrypoints translate user intent into semantic commands. `await CommandKernel.execute(command)` resolves one handler. The handler owns ordering and coordinates only the state owners/ports required for that terminal action.

**Advantages:**
- one small seam for hotkeys/cards/finder/future entrypoints;
- async failure ordering remains local to the command;
- durable preferences and transient session state remain separate;
- external adapters are explicit without framework ceremony;
- a future command registers without rewriting every entrypoint;
- aligns with the existing hotkey architecture instead of replacing it.

**Disposition:** selected.

### Candidate D — generic publish/subscribe event bus

**Advantage:** loose coupling.

**Failure:** terminal action ownership, ordering, error propagation, and compensation become implicit subscriber behavior. Commands and semantic completion events become easy to confuse.

**Disposition:** rejected as primary orchestration. A completion event stream may later live behind UsageLedger, but it cannot replace command ownership.

## Selected module/interface map

| Module | Responsibility / state | Public interface | Side effects | Failure contract | Test seam |
| --- | --- | --- | --- | --- | --- |
| `PromptCatalog` | effective prompt records | `require(promptId)` | none | `UNKNOWN_PROMPT` | fake/registry fixture |
| `CommandKernel` | registration + application dispatch | `register(type, handler)`, `execute(command) -> Promise<CommandResult>` | none directly | invalid/unknown/duplicate command, `INVALID_COMMAND_RESULT`, normalized handler error | deterministic trace |
| `SessionState` | transient browsing/navigation/copy target | intention-level transitions + `snapshot()` | none until projected | future illegal transition classification | pure/component test |
| `FavoritePreferences` | authoritative Favorites after persistence | `has`, `toggle`, `snapshot` | PreferenceStore | `PREFERENCE_PERSISTENCE_FAILED`; prior state retained | memory/failing store |
| existing `ShortcutRegistry` | configured shortcuts | existing hotkey seam | browser storage | existing hotkey contract | existing prototype/tests |
| `ClipboardPort` | external clipboard | `writeText(text) -> Promise` | clipboard | `CLIPBOARD_WRITE_FAILED` | resolving/rejecting fake |
| `PromptSurfacePort` | DOM projection | reveal/focus/detail/favorite projection | DOM/focus/scroll | handler classifies consequential presentation failure | fake surface + browser proof |
| `UsageLedger` | semantic completion events | `recordCompletion`, `reset` | local storage if enabled | degradation does not negate terminal success | memory/failing fake |

## State/data ownership

| State/data | Canonical owner | Persistence | Mutator |
| --- | --- | --- | --- |
| effective prompt records | PromptCatalog / canonical registry build | tracked registry → generated site | registry/build pipeline |
| view/search/filter/detail/copy target | SessionState | none by default | explicit transitions |
| Favorite set | FavoritePreferences | PreferenceStore | FavoritePreferences only |
| configured prompt shortcuts | existing ShortcutRegistry | versioned shortcut store | shortcut owner only |
| completed usage events | UsageLedger, if enabled | local/private | successful domain commands only |
| DOM focus/classes/scroll | PromptSurface adapter | none | presentation adapter |
| clipboard contents | ClipboardPort/browser | external | ClipboardPort |
| generated website bytes | canonical builder | repository artifact | builder only |

No dashboard, help panel, finder, or recommendation feature may become a second writer for these records.

## Dependency direction

```text
USER / BROWSER EVENT
  -> ENTRYPOINT CONTROLLER
  -> await CommandKernel.execute(command)
  -> PromptActionHandler
       -> PromptCatalog
       -> SessionState / FavoritePreferences / existing ShortcutRegistry
       -> ClipboardPort / PreferenceStore / PromptSurfacePort / UsageLedger
  <- Promise<CommandResult> or classified ProgramError
  -> PRESENTATION FEEDBACK
```

Read paths stay separate:

```text
SEARCH / FINDER / FILTER INPUT
  -> QUERY CONTROLLER
  -> PromptCatalog + SessionState snapshot
  -> pure ranking/filter/projection
  -> render result
```

A query may lead to a later command when the user chooses a terminal action, but the query must not smuggle copy/persistence side effects.

## Prototype A — selected command-kernel vertical slice

Executable: `docs/prompt-kit-program-prototype.js`.

It uses real domain decisions and fakes only external boundaries.

### Copy/reveal journey

**Terminal user value:** canonical prompt text is on the clipboard.

- typed shortcut/card action: **ENTRYPOINT**
- reveal/center state: **REQUIRED INTERMEDIATE**
- focused Copy control: **REQUIRED INTERMEDIATE / recovery target**
- resolved clipboard write: **TERMINAL ACTION**
- toast/glow: completion feedback

```text
USER TYPES CONFIGURED FAVORITE SHORTCUT
  -> HotkeyEntrypoint.copyFavorite(P07)
  -> await CommandKernel.execute(COPY_REVEAL_PROMPT)
  -> PromptCatalog.require(P07)
  -> SessionState.revealPrompt(P07)
  -> PromptSurface.revealPrompt(P07)
  -> PromptSurface.focusCopy(P07)
  -> await ClipboardPort.writeText(copyContent)
  -> UsageLedger.recordCompletion(PROMPT_COPIED)
  -> validate CommandResult
  -> {status:COPIED, terminalValue:PROMPT_TEXT_ON_CLIPBOARD}
```

The card invokes the same command. Entrypoint changes; terminal ownership does not.

### Finder inspection journey

```text
USER CHOOSES FINDER RESULT
  -> FinderEntrypoint.inspect(P95)
  -> await CommandKernel.execute(OPEN_PROMPT_DETAIL)
  -> PromptCatalog.require(P95)
  -> SessionState.openDetail(P95)
  -> PromptSurface.openDetail(P95)
  -> validate {status:DETAIL_OPEN}
```

No `PROMPT_COPIED` event is recorded.

### Favorite mutation journey

```text
USER TOGGLES FAVORITE
  -> PromptCardEntrypoint.toggleFavorite(P95)
  -> await CommandKernel.execute(TOGGLE_FAVORITE)
  -> PromptCatalog.require(P95)
  -> FavoritePreferences constructs candidate
  -> PreferenceStore.saveFavorites(candidate)       [transaction boundary]
  -> FavoritePreferences publishes candidate
  -> PromptSurface.projectFavorite(P95, true)
  -> UsageLedger.recordCompletion(FAVORITE_CHANGED)
  -> validate CommandResult
```

## Failure call stacks

### Async clipboard rejection

```text
COPY_REVEAL_PROMPT
  -> target validated
  -> reveal + Copy focus established
  -> await ClipboardPort.writeText
  -> Promise rejects / CLIPBOARD_WRITE_FAILED
  -> no PROMPT_COPIED event
  -> no COPIED result
  -> ProgramError recovery=COPY_CONTROL_FOCUSED
```

The executable prototype deliberately defers its clipboard fake one microtask and proves there is still zero completion telemetry while the Promise is pending.

### Favorite persistence failure

```text
TOGGLE_FAVORITE
  -> candidate constructed
  -> PreferenceStore.saveFavorites(candidate)
  -> PREFERENCE_PERSISTENCE_FAILED
  -> candidate NOT published
  -> UI Favorite projection NOT changed
  -> no false durable success
```

### Telemetry degradation

```text
COPY_REVEAL_PROMPT
  -> awaited clipboard write resolves            [terminal value achieved]
  -> UsageLedger degrades
  -> CommandResult remains COPIED
  -> telemetry.degraded=true
```

### Invalid handler result

```text
CommandKernel.execute(BAD_RESULT)
  -> handler resolves undefined/null/malformed value
  -> validateCommandResult rejects it
  -> INVALID_COMMAND_RESULT
  -> command_completed is never emitted
```

This does not pretend the kernel can roll back arbitrary side effects performed by a malformed extension handler. The contract instead makes the handler's invalid result explicit and prevents the kernel from dereferencing an undefined result or falsely reporting a completed command. Production command registration should remain internal/trusted unless an extension system later requires stronger pre-execution capability contracts.

## Prototype B — reducer + effect-plan comparison

The same executable contains `ReducerEffectProgram` and `reducerPlan`.

For copy it requires:
1. critical precommit awaited clipboard write;
2. postcommit reveal;
3. postcommit focus-copy;
4. postcommit semantic usage record.

For Favorites it requires critical precommit persistence before state publication.

It satisfies the same invariants, but introduces effect descriptors, phases, criticality metadata, a state-commit protocol, and an asynchronous effect runner. That machinery is justified when replayable state transitions dominate; Prompt Kit's current risk is terminal side-effect ordering, so the async command kernel is the smaller deep module.

## Executable evidence

```text
node docs/prompt-kit-program-prototype.js
python -m unittest tests.test_prompt_kit_program_prototype -v
```

Expected prototype report:
- `status: PASS`;
- selected design `COMMAND_KERNEL_WITH_OWNED_STATE_AND_PORTS`;
- PASS for async copy success/rejection, Favorite success/failure, inspection telemetry separation, telemetry degradation, extension collision, invalid CommandResult, and reducer comparison;
- structured kernel/reducer traces.

The dedicated workflow additionally runs the adjacent hotkey prototype/tests, generated-site parity, patch hygiene, emits a JSON trace artifact, and verifies the exact pull-request head SHA.

## State model

### Session projection

Independent transient dimensions: view, search text, category/section/type/color filters, active prompt, detail prompt, copy target.

`COPY_REVEAL_PROMPT(Pxx)` changes only transient dimensions needed to reveal the target. It must not modify Favorites or configured shortcuts. Usage changes only after awaited clipboard success.

### Favorite lifecycle

```text
AUTHORITATIVE(old)
  -> CANDIDATE(new)
  -> PERSISTING
     -> PERSISTED -> PUBLISHED(new)
     -> FAILED    -> AUTHORITATIVE(old)
```

### Copy lifecycle

```text
TARGET_RESOLVED
  -> REVEALED_AND_FOCUSED
  -> AWAITING_CLIPBOARD
     -> RESOLVED -> COPIED -> completion event + success feedback
     -> REJECTED -> focused-copy recovery, no copy completion event
```

## Testability and observability

Unit/component proof covers target validation, registration/collision, result validation, session transitions, Favorite publish-after-save, deferred/rejected clipboard Promises, semantic completion counts, and reducer transaction semantics.

Repository integration proof covers exact-head execution, adjacent hotkey compatibility, canonical generated-site parity, and patch hygiene.

Browser proof remains required for real Clipboard API permissions/fallback behavior, scroll/focus visibility, keyboard layouts/native Enter, responsive geometry, and browser-storage policy/quota/private-mode behavior.

Structured traces identify the decision layer without logging prompt bodies or user-entered text.

## Second-pass architecture critique

Executable and review evidence changed the design in eight concrete ways:

1. **No global reducer now.** Fail-closed behavior requires a larger effect-phase protocol than the current product needs.
2. **Command handlers own orchestration.** Terminal ordering should not be spread across generic subscribers.
3. **UsageLedger is subordinate.** Telemetry failure cannot negate already-achieved user value.
4. **Reveal/focus survives clipboard failure as recovery.** This is useful intermediate state, not false completion.
5. **Favorites have a dedicated owner.** A generic UI store would make publish-before-persist mistakes easy.
6. **Queries remain outside the command kernel.** Search/ranking are read paths until a user chooses an action.
7. **Clipboard completion is asynchronous.** Review caught that a synchronous prototype would falsely pass against a Promise-returning browser API; the seam is now `await execute(...)` and awaits `ClipboardPort.writeText` before telemetry/result completion.
8. **CommandResult is validated.** Review caught that an undefined handler result could be dereferenced after side effects; the kernel now emits `INVALID_COMMAND_RESULT` and never records `command_completed` for malformed output.

A separate proof review also found that GitHub's default pull-request checkout used a synthetic merge ref. The workflow was hardened to checkout and assert the exact candidate SHA, fetch current main independently, and rerun after main moved.

The design has reached a bounded architectural fixed point when these repaired seams pass on the reconciled head. Remaining uncertainty belongs to production migration order and live browser behavior, not state/command/failure ownership.

## Feature admission checklist

Before broad implementation of a new Prompt Kit feature, answer:

1. What is the terminal user value?
2. Is it a command, query, or presentation projection?
3. Which canonical state owner changes?
4. Which external side effect occurs?
5. Is that side effect synchronous or Promise-returning?
6. Which handler owns ordering and compensation/recovery?
7. Which stable error codes matter?
8. Does it create semantic completion telemetry, and after exactly which terminal condition?
9. Can every relevant entrypoint invoke the same semantic behavior without copying policy?
10. What valid `CommandResult` returns?
11. What are the thinnest executable success and failure stacks?
12. Which proof is component, generated-site, browser, or operator-only?

A proposal that cannot answer these belongs in a prototype/design lane, not broad implementation.

## Exact implementation seam ready for the next build sprint

The next production build should introduce the smallest async CommandKernel-compatible seam around existing behavior, not rewrite Prompt Kit into a framework:

```text
existing hotkey/card copy entrypoint
  -> await executePromptCommand({type:'COPY_REVEAL_PROMPT', promptId, source})
  -> one handler
       -> existing reveal/focus functions
       -> await existing clipboard path
       -> existing completion feedback only after resolution
  -> validated CommandResult
```

Then migrate `TOGGLE_FAVORITE` only after copy is proved.

Do not migrate all globals at once, do not add Redux, do not add a generic event bus, and do not create a second shortcut registry. Search/filter/finder query extraction waits for a concrete duplication or complexity problem.

## Unresolved decisions

Intentionally unresolved until a feature needs them:

- whether semantic usage/personalization ships at all and its retention/reset UX;
- whether active prompt/view becomes shareable URL/hash state;
- whether future finder complexity warrants a dedicated PromptQueryService;
- presentation-degradation UX after a terminal side effect has already succeeded;
- production file/module split for CommandKernel after the first bounded migration proves the seam;
- whether a future third-party extension system would require stronger handler capability/result schemas before registration.

## Proof ceiling

This sprint can prove vocabulary, ownership, dependency direction, command/reducer alternatives, representative success/failure orchestration, asynchronous clipboard completion ordering, fail-closed Favorite mutation, CommandResult validation, semantic completion timing, extension collision behavior, exact-head CI execution, and compatibility with the current generated Prompt Kit floor.

It cannot prove production DOM wiring because broad runtime migration is deliberately deferred. It also cannot prove real browser clipboard permissions, focus/scroll ergonomics, mobile behavior, private-mode storage, or operator acceptance until a later build/browser sprint exercises those environments.
