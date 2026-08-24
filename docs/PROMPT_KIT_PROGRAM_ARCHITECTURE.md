# Prompt Kit program architecture — prototype-earned seams

## Purpose

This document is the program-design owner for the browser Prompt Kit. It sits between repository governance/harness and broad feature implementation. It defines runtime vocabulary, state ownership, dependency direction, command/query seams, side-effect ports, failure contracts, and the executable prototypes that must stay coherent as new Prompt Kit features are proposed.

It does **not** replace:

- governance (`AGENTS.md` and repository work rules);
- the operational harness, validators, workflows, artifact registries, or responsive-layout harness;
- full production implementation in `docs/prompt-kit*.js`;
- generated `web/prompt-kit/index.html`, which remains builder-owned.

## Fresh evidence floor for this design session

Design floor: `main@f36de4f4f8c40ee6d29bfa9127dd3b2085823b13` on 2026-08-24.

Current evidence already establishes:

- the Prompt Kit has one canonical generated web artifact and builder;
- `docs/prompt-kit-polish.js` currently contains substantial view, filter, clipboard, favorites, and keyboard behavior;
- configured prompt-ID shortcuts have already converged on the terminal behavior **copy + reveal prompt**, rather than opening prompt detail;
- the hotkey subsystem already has a bounded design/prototype seam in `docs/PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md` and `docs/prompt-kit-hotkey-prototype.js`;
- favorites and shortcut persistence are browser-local concerns;
- browser geometry, clipboard policy, and operator ergonomics remain separate runtime proof ceilings from repository/static proof.

This program design therefore does not reopen the solved hotkey architecture. It generalizes the next layer up: how **any entrypoint** reaches a semantic Prompt Kit action without becoming a second state or side-effect owner.

## Observable done checklist for this design sprint

The architecture is design-ready only when repository evidence proves all of the following:

1. user outcomes and invariants are named independently of DOM implementation;
2. transient session state, durable preferences, semantic completion usage, catalog data, and generated artifacts each have one owner;
3. at least two materially different execution seams are compared with executable code;
4. copy/reveal and favorite mutation traverse real domain decisions and fake only external boundaries;
5. clipboard and preference-persistence failure paths execute and retain truthful state;
6. opening/inspecting a prompt is not falsely counted as copying it;
7. telemetry degradation cannot retroactively turn a successful user action into failure;
8. a new command can be registered without changing every entrypoint;
9. the selected design has a focused CI-owned regression seam;
10. broad production migration is explicitly deferred to a later build sprint.

## User outcomes

The Prompt Kit should let a user reach the intended prompt outcome from multiple surfaces without caring which UI entrypoint initiated it.

Current user-value journeys include:

- copy a prompt and receive normal completion feedback;
- reveal/locate a prompt in the library when a command targets it;
- inspect a prompt in detail when inspection is the intended terminal action;
- save/remove Favorites durably and fail closed if browser persistence fails;
- navigate/search/filter without those transient view choices becoming durable preference truth;
- invoke semantic commands from keyboard, cards, finder/tutorial surfaces, or future command surfaces without duplicating business rules;
- preserve keyboard accessibility and editable-field safety;
- let future personalization use semantic completion events rather than incidental focus/view events.

## Core invariants

1. **Terminal value beats intermediate UI.** A command named copy is complete only after clipboard success; revealing or focusing is required support, not terminal success.
2. **Inspection is not completion telemetry.** Opening detail must never count as a copied prompt.
3. **Durable preference writes publish after persistence.** A failed Favorite/shortcut save leaves the previous in-memory preference authoritative.
4. **Transient view state is not preference state.** Search text, category/type/color filters, selected section, active detail, and current copy target are session-owned.
5. **One semantic completion ledger.** If usage/personalization is enabled, it records completed domain actions after success; dashboards/recommendations are projections, never second writers.
6. **Telemetry is subordinate to user value.** A telemetry write failure may degrade observability, but it cannot undo a successful clipboard write or durable preference mutation.
7. **Catalog identity is canonical.** Commands target prompt IDs resolved by the canonical effective prompt registry; UI labels are presentation.
8. **Generated HTML is not a state owner.** Production source changes flow through the registered builder.
9. **Entrypoints translate; they do not own policy.** Hotkeys, cards, finder/tutorial UI, and future surfaces create commands/queries and render results.
10. **External boundaries stay explicit.** Clipboard, browser storage, DOM projection, browser history/URL state, and future network/export integrations deserve ports only where behavior is volatile or independently fallible.

## Domain vocabulary

### Core records

- **PromptRecord** — canonical prompt identity plus copyable content and metadata.
- **PromptTarget** — validated prompt identity used by runtime commands.
- **PromptCommand** — imperative request for terminal behavior, e.g. `COPY_REVEAL_PROMPT`, `TOGGLE_FAVORITE`, `OPEN_PROMPT_DETAIL`.
- **PromptQuery** — read-only request for data/projection, e.g. search/filter/list/finder ranking. Queries must not silently create product side effects.
- **CommandResult** — typed terminal outcome such as `COPIED`, `DETAIL_OPEN`, or `FAVORITE_CHANGED`.
- **ProgramError** — classified failure with stable code, user-safe message/recovery metadata, and original cause hidden behind the boundary.

### State owners

- **PromptCatalog** — read-only effective prompt records produced by the canonical registry/builder pipeline.
- **SessionState** — transient browsing state: current view, search text, filters, active prompt, open detail, keyboard copy target.
- **FavoritePreferences** — durable Favorite set, with fail-closed publication after the PreferenceStore succeeds.
- **ShortcutRegistry** — durable configured shortcut bindings; remains owned by the existing hotkey seam rather than being folded into generic session state.
- **UsageLedger** — semantic completed-action events only, local/private/resettable if enabled.

### Runtime services and ports

- **CommandKernel** — application seam that maps command IDs to deep handlers and provides `execute(command)`.
- **PromptActionHandler** — owns the complete success/failure orchestration for one semantic action.
- **ClipboardPort** — external clipboard write boundary.
- **PreferenceStore** — external durable local-storage boundary for Favorites/preferences.
- **PromptSurfacePort** — DOM/presentation adapter for reveal, focus, detail, and preference projection.
- **UsageLedger** — semantic completion event sink; should own storage/privacy/reset rules if productionized.

### Entrypoints

- **HotkeyEntrypoint** — keyboard resolution → PromptCommand.
- **PromptCardEntrypoint** — card control → PromptCommand.
- **FinderEntrypoint** — finder/tutorial result → PromptCommand or PromptQuery.
- Future entrypoints must translate to these same semantic interfaces rather than call persistence/clipboard/DOM internals directly.

## External prior-art inspection

The design session inspected mechanisms rather than copying foreign architecture.

### VS Code command registry/service

Source: `microsoft/vscode`, `src/vs/platform/commands/common/commands.ts`.

Transferable mechanism:

- a small `executeCommand(id, ...args)` service;
- a registry mapping stable command IDs to handlers;
- command metadata/argument validation at registration/execution boundaries;
- callers do not need to know handler internals.

This is structurally compatible with a vanilla-JavaScript Prompt Kit because it centralizes semantic action routing without requiring a UI framework or global state library.

### Redux store/reducer

Source: `reduxjs/redux`, `src/createStore.ts`.

Transferable mechanism:

- one dispatch seam;
- explicit state ownership;
- serializable action identity;
- guarded mutation during dispatch.

The design prototype uses this as the materially different alternative: a reducer computes pending state plus explicit effects, and an effect runner separates precommit from postcommit work.

### License/dependency disposition

Both inspected repositories use MIT licenses. This design copies no implementation and adds no third-party dependency. Only architectural mechanisms are compared, so there is no direct code-reuse, supply-chain, bundle-size, or runtime-security implication.

## Candidate architectures

### Candidate A — existing local handlers, made slightly more disciplined

Each UI surface continues calling existing functions such as copy, detail, Favorite, render, and localStorage helpers directly.

**Strengths**
- smallest first patch;
- zero migration layer;
- easy to understand inside one function.

**Weaknesses**
- terminal semantics remain scattered across entrypoints;
- adding another surface can duplicate ordering rules (reveal → focus → copy → completion feedback);
- error classification and usage-event ownership drift easily;
- mutable globals remain implicit state owners.

**Disposition:** baseline only. Good for tiny isolated UI behavior; insufficient as the program-level expansion seam.

### Candidate B — global reducer + effect runner

Every interaction dispatches a serializable action. A reducer computes pending state and effect descriptors. A runner executes critical precommit effects, commits state, then runs presentation/telemetry effects.

**Strengths**
- explicit state transitions;
- excellent replay/debug story;
- natural single-state-tree discipline;
- future complex multi-step state machines can be modeled deterministically.

**Prototype cost revealed**
- copy is primarily an external terminal action, not a state transition;
- fail-closed Favorite persistence requires precommit effects before publishing state;
- clipboard, persistence, presentation, and telemetry need phase/criticality metadata;
- the reducer becomes an effect-plan DSL rather than a simple state reducer.

**Disposition:** viable but rejected for the current Prompt Kit. It introduces a global runtime protocol larger than the product currently needs.

### Candidate C — command kernel + deep state owners + ports

Entrypoints translate user intent into semantic commands. `CommandKernel.execute(command)` resolves one command handler. The handler owns ordering and coordinates the specific state owner(s) and external ports required for that terminal action.

**Strengths**
- one small application seam for keyboard/card/finder/future entrypoints;
- failure ordering stays local to the command that owns it;
- durable preferences and transient session state remain separate;
- external adapters are explicit without wrapping every helper in abstraction;
- a future command can register without rewriting each entrypoint;
- matches the existing hotkey design direction rather than replacing it.

**Disposition:** selected.

### Candidate D — generic publish/subscribe event bus

Surfaces publish events and independent subscribers react.

**Strengths**
- loose coupling;
- easy to add observers.

**Weaknesses**
- terminal action ownership becomes ambiguous;
- execution order matters for clipboard/persistence/presentation but becomes implicit subscriber order;
- error propagation/compensation is harder;
- semantic events and imperative commands become easy to conflate.

**Disposition:** rejected as primary orchestration. A completion-event stream may exist behind UsageLedger later, but it must not replace command ownership.

## Selected module/interface map

| Module | Responsibility / owned state | Public interface | Hidden complexity | Side effects | Failure contract | Observability / test seam |
| --- | --- | --- | --- | --- | --- | --- |
| `PromptCatalog` | canonical effective prompt records | `require(promptId)`; later query methods | registry record shape, lookup/indexing | none | `UNKNOWN_PROMPT` | fake catalog or real generated registry fixture |
| `CommandKernel` | command registration and application dispatch | `register(type, handler)`, `execute(command)` | handler lookup, error normalization, lifecycle trace | none directly | `INVALID_COMMAND`, `UNKNOWN_COMMAND`, `COMMAND_ALREADY_REGISTERED`, normalized handler errors | deterministic command trace |
| `SessionState` | transient browsing/navigation/copy-target state | intention-level state transitions and `snapshot()` | clearing incompatible transient filters without touching preferences | none until projected | illegal/unknown transition if a future state machine needs one | pure/component tests |
| `FavoritePreferences` | authoritative in-memory Favorite set after persistence | `has`, `toggle`, `snapshot` | candidate creation and publish-after-save | through PreferenceStore | `PREFERENCE_PERSISTENCE_FAILED`; prior state retained | memory store fake + persistence-failure tests |
| existing `ShortcutRegistry` | configured shortcut bindings and sequence mapping | existing hotkey design seam | timeout, collisions, persisted bindings | local storage | existing hotkey error contract | existing hotkey prototype/tests |
| `ClipboardPort` | external clipboard write | `writeText(text)` | Clipboard API/fallback/policy | clipboard | `CLIPBOARD_WRITE_FAILED` | memory/failing fake; later browser proof |
| `PromptSurfacePort` | render/projection actions only | `revealPrompt`, `focusCopy`, `openDetail`, `projectFavorite` | DOM selectors, focus, scroll, animation | DOM/focus/scroll | presentation failure classified by handler if consequential | fake surface; browser geometry/accessibility later |
| `UsageLedger` | semantic completion events if enabled | `recordCompletion`, `reset` | local schema, retention, privacy/reset | local durable storage if productionized | degradation is reported but does not negate completed user value | memory/failing fake; event-count tests |

## State/data ownership

| State/data | Canonical owner | Persistence | Who may mutate it |
| --- | --- | --- | --- |
| effective prompt records | PromptCatalog / canonical registry build | tracked registry → generated site | registry/build pipeline only |
| current view/search/filter/detail/copy target | SessionState | none by default | command/query handlers through explicit transitions |
| Favorite set | FavoritePreferences | PreferenceStore (`localStorage` adapter expected) | FavoritePreferences only |
| configured prompt shortcuts | existing ShortcutRegistry | versioned shortcut store | existing shortcut owner only |
| semantic completed-use events | UsageLedger | local/private if enabled | domain command handlers after terminal success |
| DOM focus/classes/scroll | PromptSurface adapter | none | presentation adapter only |
| clipboard contents | ClipboardPort / browser | browser external | ClipboardPort only |
| generated website bytes | canonical builder | repository artifact | builder only |

No dashboard, help panel, finder, or recommendation feature may become a second writer for any row above. They consume projections or issue commands/queries.

## Dependency direction

```text
USER / BROWSER EVENT
  -> ENTRYPOINT CONTROLLER
  -> CommandKernel.execute(command)
  -> PromptActionHandler
       -> PromptCatalog
       -> SessionState / FavoritePreferences / existing ShortcutRegistry
       -> ClipboardPort / PreferenceStore / PromptSurfacePort / UsageLedger
  <- CommandResult or classified ProgramError
  -> PRESENTATION FEEDBACK
```

Query direction remains separate:

```text
SEARCH / FINDER / FILTER INPUT
  -> QUERY CONTROLLER
  -> PromptCatalog + SessionState snapshot
  -> pure ranking/filter/projection
  -> render result
```

A query may lead to a later command when the user chooses a terminal action, but the query itself must not smuggle copy/persistence side effects.

## Prototype A: selected command-kernel vertical slice

Executable file: `docs/prompt-kit-program-prototype.js`.

It uses real domain decisions and interfaces while faking only external boundaries (clipboard, durable preference storage, DOM projection, optional usage storage).

### Journey 1 — favorite shortcut copies and reveals a prompt

**Terminal user value:** canonical prompt text is on the clipboard.

UI-state classification:
- typed shortcut: **ENTRYPOINT**;
- prompt reveal/center state: **REQUIRED INTERMEDIATE**;
- focused Copy control: **REQUIRED INTERMEDIATE / recovery target**;
- clipboard success: **TERMINAL ACTION**;
- toast/glow: presentation feedback after success.

Call stack:

```text
USER TYPES CONFIGURED FAVORITE SHORTCUT
  -> HotkeyEntrypoint.copyFavorite(P07)
  -> CommandKernel.execute(COPY_REVEAL_PROMPT)
  -> COPY_REVEAL_PROMPT handler
  -> PromptCatalog.require(P07)
  -> SessionState.revealPrompt(P07)
  -> PromptSurface.revealPrompt(P07)
  -> PromptSurface.focusCopy(P07)
  -> ClipboardPort.writeText(canonical copyContent)
  -> UsageLedger.recordCompletion(PROMPT_COPIED, source=hotkey)
  -> CommandResult {status:COPIED, terminalValue:PROMPT_TEXT_ON_CLIPBOARD}
  -> normal success feedback
```

The same command is invoked by `PromptCardEntrypoint.copy(P07)`. The entrypoint changes; terminal ownership does not.

### Journey 2 — finder opens a prompt for inspection

**Terminal user value:** prompt detail is ready for inspection.

```text
USER CHOOSES FINDER RESULT
  -> FinderEntrypoint.inspect(P95)
  -> CommandKernel.execute(OPEN_PROMPT_DETAIL)
  -> PromptCatalog.require(P95)
  -> SessionState.openDetail(P95)
  -> PromptSurface.openDetail(P95)
  -> CommandResult {status:DETAIL_OPEN, terminalValue:PROMPT_INSPECTION_READY}
```

Invariant proved by the prototype: this path does **not** record `PROMPT_COPIED`.

### Journey 3 — Favorite preference mutation

**Terminal user value:** the Favorite preference is durably changed and accurately projected.

```text
USER TOGGLES FAVORITE
  -> PromptCardEntrypoint.toggleFavorite(P95)
  -> CommandKernel.execute(TOGGLE_FAVORITE)
  -> PromptCatalog.require(P95)
  -> FavoritePreferences creates candidate set
  -> PreferenceStore.saveFavorites(candidate)       [transaction boundary]
  -> FavoritePreferences publishes candidate
  -> PromptSurface.projectFavorite(P95, true)
  -> UsageLedger.recordCompletion(FAVORITE_CHANGED)
  -> CommandResult {status:FAVORITE_CHANGED, terminalValue:DURABLE_PREFERENCE_CHANGED}
```

## Failure call stacks

### Clipboard failure after reveal/focus

```text
COPY_REVEAL_PROMPT
  -> prompt validated
  -> session target/reveal established
  -> Copy control focused
  -> ClipboardPort.writeText
  -> CLIPBOARD_WRITE_FAILED
  -> no PROMPT_COPIED completion event
  -> ProgramError includes recovery=COPY_CONTROL_FOCUSED
  -> user can activate the already-focused native Copy control again
```

This intentionally preserves a truthful recovery state: the command failed to reach its terminal value, but the UI remains positioned for manual retry.

### Favorite persistence failure

```text
TOGGLE_FAVORITE(P95)
  -> candidate Favorite set constructed
  -> PreferenceStore.saveFavorites(candidate)
  -> PREFERENCE_PERSISTENCE_FAILED
  -> candidate is NOT published
  -> Favorite projection is NOT changed
  -> no false durable success
```

### Telemetry/storage degradation

```text
COPY_REVEAL_PROMPT
  -> clipboard succeeds                    [terminal value achieved]
  -> UsageLedger.recordCompletion fails/degrades
  -> result remains COPIED
  -> result reports telemetry.degraded=true
```

The usage layer cannot redefine user success after the terminal side effect completed.

### Unknown command / extension collision

- missing command ID → `UNKNOWN_COMMAND`;
- duplicate command registration → `COMMAND_ALREADY_REGISTERED`;
- unknown PromptTarget → `UNKNOWN_PROMPT` before external side effects.

## Prototype B: reducer + effect-plan comparison

The same executable file contains `ReducerEffectProgram` and `reducerPlan`.

For `COPY_REVEAL_PROMPT`, it must produce four effects:

1. critical precommit clipboard write;
2. postcommit reveal;
3. postcommit focus-copy;
4. postcommit semantic usage record.

For `TOGGLE_FAVORITE`, durable storage becomes a critical precommit effect so failed persistence cannot commit the candidate state.

The prototype passes the same persistence-failure invariant, but it exposes extra machinery that the command-kernel handler does not need:

- effect descriptor schema;
- precommit/postcommit phases;
- criticality metadata;
- state commit protocol;
- effect-runner routing.

That machinery is useful when state transition/replay is the dominant problem. Prompt Kit's highest-risk current journeys are instead **terminal side-effect ordering** (clipboard, persistence, focus/scroll), so the command kernel is the smaller deep seam.

## Executable evidence

Run directly:

```text
node docs/prompt-kit-program-prototype.js
```

Expected top-level fields:

- `status: PASS`;
- `selectedDesign: COMMAND_KERNEL_WITH_OWNED_STATE_AND_PORTS`;
- PASS journeys for copy success/failure, Favorite success/failure, inspection telemetry separation, telemetry degradation, extension collision, and reducer comparison;
- traces showing layer/event order for the selected kernel and reducer alternative.

Focused repository contract:

```text
python -m unittest tests.test_prompt_kit_program_prototype -v
```

## State model

The program should avoid one giant state enum, but significant state transitions must still be explicit.

### Session projection

Legal independent dimensions:

- `view`: all / favorites / doctrine / other existing registered views;
- search text;
- category / section / type / color filters;
- active prompt;
- detail prompt (nullable);
- copy target prompt (nullable).

`COPY_REVEAL_PROMPT(Pxx)` transitions only the transient dimensions required to reveal the target. It must not modify Favorites, configured shortcuts, or semantic usage except the completion event after clipboard success.

### Favorite mutation lifecycle

```text
AUTHORITATIVE(old)
  -> CANDIDATE(new)
  -> PERSISTING
     -> PERSISTED -> PUBLISHED(new)
     -> FAILED    -> AUTHORITATIVE(old)
```

There is no legal state where the UI declares the new Favorite authoritative before storage succeeds.

### Copy lifecycle

```text
TARGET_RESOLVED
  -> REVEALED_AND_FOCUSED
  -> CLIPBOARD_ATTEMPT
     -> COPIED -> completion event + success feedback
     -> FAILED -> focused-copy recovery, no copy completion event
```

## Testability and observability

### Unit/component proof

- PromptCatalog target validation;
- CommandKernel registration/collision/unknown command;
- SessionState transitions;
- FavoritePreferences publish-after-save;
- semantic event counts and non-events;
- reducer comparison transaction semantics.

### Integration/static product proof

Later build work should connect production entrypoints to the selected seam and prove source/generated parity through existing Prompt Kit validators/builders.

### Browser proof

A browser is still required for evidence that repository logic maps correctly to:

- real Clipboard API permissions/fallback behavior;
- scroll positioning and focus visibility;
- keyboard layouts and native Enter activation;
- DOM geometry/responsive behavior;
- localStorage policy/quota/private-mode differences.

### Trace shape

The prototype uses structured records such as:

```json
{"layer":"kernel","event":"command_started","commandType":"COPY_REVEAL_PROMPT","source":"hotkey"}
```

Production logging should stay sparse, local, and free of prompt bodies or sensitive user-entered text. Semantic usage events should contain prompt identity/action/source only if the product actually enables that feature.

## Second-pass architecture critique

Prototype evidence changed the initial design in six ways:

1. **Do not introduce a global reducer now.** The reducer only becomes fail-closed after inventing an effect phase/criticality protocol, which is larger than the present problem.
2. **Command handlers are orchestration owners, not thin relays.** The copy handler must know terminal ordering and telemetry timing; hiding that across generic subscribers would weaken correctness.
3. **UsageLedger must be subordinate.** The first sketch treated usage storage like another required effect. The failure prototype showed that would incorrectly turn a successful clipboard copy into failure.
4. **Reveal/focus on clipboard failure is useful recovery, not false success.** Session/presentation state may advance even though the copy command returns failure, as long as completion telemetry remains absent and the focused Copy control makes retry obvious.
5. **Favorites need a dedicated preference owner.** A generic UI store would make it too easy to publish before persistence.
6. **Queries stay outside the command kernel.** Search/finder ranking are read paths; only the user's selected action enters the command execution seam.

The design has reached a bounded fixed point for the next build: the remaining uncertainty is production migration order and live browser behavior, not ownership of commands, state, or failures.

## Feature admission checklist

Before a new Prompt Kit feature receives broad implementation, its design note or PR should answer these questions:

1. What is the terminal user value?
2. Is the request a **command**, **query**, or pure **presentation projection**?
3. Which existing state owner changes, if any?
4. Which external side effect occurs, if any?
5. Which module owns success/failure ordering?
6. What stable error codes/recovery states matter?
7. Does it create semantic completion telemetry? If yes, after exactly which terminal condition?
8. Which existing entrypoints can invoke it?
9. Can a new entrypoint invoke the same behavior without copying policy?
10. What is the thinnest executable success and failure call stack?
11. Which proof is unit/component, generated-site/static, browser, or operator-only?

A proposal that cannot answer these yet belongs in a prototype/design lane, not broad production implementation.

## Exact implementation seam ready for the next build sprint

The next production implementation should introduce the **smallest CommandKernel-compatible seam around existing runtime behavior**, not rewrite Prompt Kit into a framework.

Recommended first migration boundary:

```text
existing hotkey/card copy entrypoint
  -> executePromptCommand({type:'COPY_REVEAL_PROMPT', promptId, source})
  -> existing reveal/focus/copy functions through a single handler
```

Then migrate `TOGGLE_FAVORITE` only after the copy seam is proved. Search/filter/finder queries should remain on their existing read paths until a concrete duplication/problem justifies a query-service extraction.

Do not migrate all runtime globals at once, do not add Redux, do not add a generic event bus, and do not create a second shortcut registry.

## Unresolved decisions

These are intentionally not guessed in this design sprint:

- whether semantic usage/personalization should ship at all, and its exact retention/reset UX;
- whether active prompt/view should eventually be shareable through URL/hash state;
- whether future search/finder complexity warrants a dedicated PromptQueryService;
- whether presentation adapter failures after a successful terminal side effect need user-visible degraded status beyond existing toast/focus behavior;
- production file/module split for CommandKernel after the first bounded migration proves the seam.

Each is separable from the selected execution architecture and should be decided only when a concrete feature requires it.

## Proof ceiling

This sprint can prove program vocabulary, ownership, dependency direction, command/reducer alternatives, representative success/failure orchestration, fail-closed preference mutation, semantic completion timing, extension collision behavior, and CI execution of the prototype.

It cannot prove production DOM wiring because broad runtime migration is intentionally deferred. It also cannot prove real clipboard permissions, browser focus/scroll ergonomics, mobile behavior, private-mode storage, or operator acceptance until a later build/browser sprint exercises those environments.
