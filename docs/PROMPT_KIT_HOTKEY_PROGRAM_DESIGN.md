# Prompt Kit hotkey program design

## Scope and boundary

This document designs the Prompt Kit keyboard-command subsystem before configurable prompt shortcuts are broadly implemented. It extends the existing navigation-hotkey work in `docs/prompt-kit-polish.js`; it does not create a second runtime or a parallel hotkey registry.

Owned outcomes:
- explicit hide, show, and toggle commands for the filter surface;
- input-safe keyboard dispatch;
- configurable prompt shortcuts, including exact prompt identifiers such as `p95`;
- one ownership point for shortcut collision rules, persisted user bindings, prompt-target validation, and filter visibility;
- concise routing hooks so later agents discover the existing owner instead of reinventing hotkeys.

Forbidden in this design slice:
- broad production implementation of configurable hotkeys;
- direct edits to generated `web/prompt-kit/index.html` outside the canonical builder;
- a new general-purpose registry/harness family merely for keyboard commands;
- duplicate shortcut tables in multiple runtime files.

## User outcomes and invariants

1. A user can hide filters, show filters, or toggle filter visibility with keyboard commands without corrupting other Prompt Kit state.
2. A user can configure a favorite prompt shortcut and may use the prompt identifier itself, for example typing `p95`, when focus is not in an editable field.
3. Keyboard commands never fire while the user is typing in an input, textarea, select, or content-editable surface.
4. Built-in navigation keys and user bindings cannot silently collide. Conflicts are rejected at configuration time.
5. A prompt shortcut must resolve to an existing canonical prompt before it can be persisted or executed.
6. Filter visibility has one state owner. Hide/show/toggle are commands against that owner, not three independent DOM mutations.
7. Persistence failure is fail-closed: the in-memory effective binding set is not advanced if durable storage fails.
8. Runtime help is derived from the effective shortcut map. It is not a separately maintained truth source.

## Domain vocabulary

- **ShortcutGesture** — normalized keyboard gesture or typed sequence, such as `f`, `[`, `]`, or `p95`.
- **ShortcutCommand** — semantic action: `FILTER_HIDE`, `FILTER_SHOW`, `FILTER_TOGGLE`, `OPEN_PROMPT`, or an existing navigation command.
- **PromptTarget** — canonical prompt identifier validated against the loaded `PROMPTS` catalog.
- **ShortcutBinding** — mapping from a gesture/sequence to a command and optional PromptTarget.
- **ShortcutPolicy** — owns normalization, reserved-key rules, collision checks, sequence validation, and editable-target suppression.
- **ShortcutDispatcher** — receives keyboard events, asks ShortcutPolicy for a command, and invokes the corresponding application action.
- **FilterVisibility** — application state owner exposing `show()`, `hide()`, and `toggle()`; the DOM class/ARIA/button text are implementation details behind this interface.
- **PromptNavigator** — port that reveals/focuses/opens a canonical prompt target without the dispatcher knowing card DOM details.
- **ShortcutStore** — persistence port for user bindings; browser `localStorage` is the likely production adapter.
- **ShortcutTrace** — structured, non-sensitive decision record used by tests and diagnostics.

## Program modules and interfaces

### `ShortcutPolicy`

Owns: normalization, collision rules, prompt-sequence grammar, reserved gestures, editable-target rejection.

Public interface:
- `normalizeGesture(raw) -> ShortcutGesture`
- `validateBinding(binding, effectiveBindings, promptCatalog) -> Result`
- `classifyKey(event, sequenceState) -> DispatchDecision`

Hidden complexity: case folding, multi-key buffer rules, sequence timeout, collision semantics, future modifier support.

Failure contract: returns typed rejection (`INVALID_GESTURE`, `RESERVED_COLLISION`, `UNKNOWN_PROMPT`, `EDITABLE_TARGET`) rather than throwing for expected user mistakes.

Test seam: pure functions plus a deterministic clock for sequence timeout.

### `ShortcutRegistry`

Owns: effective built-in bindings plus persisted user bindings. It is the only authoritative shortcut map.

Public interface:
- `effectiveBindings() -> ShortcutBinding[]`
- `configure(binding) -> Result`
- `remove(gesture) -> Result`

Side effect: delegates durable writes to `ShortcutStore` only after policy validation.

Failure contract: persistence failure returns `PERSISTENCE_FAILED` and leaves the previously effective binding set intact.

Observability: configuration accepted/rejected trace with gesture, command type, and prompt ID only.

### `ShortcutDispatcher`

Owns: keyboard-event orchestration and typed-sequence buffer state.

Public interface:
- `handleKey(event) -> DispatchResult`
- `resetSequence(reason) -> void`

Dependencies: `ShortcutRegistry`, `ShortcutPolicy`, `FilterVisibility`, `PromptNavigator`, existing navigation actions.

Side effects: none directly; delegates to application ports.

Failure contract: unknown/incomplete sequences remain non-destructive; invalid complete sequences return a typed no-op/rejection.

### `FilterVisibility`

Owns: the effective filter-visible/hidden state and the one transaction that synchronizes DOM class, `aria-expanded`, title, and button text.

Public interface:
- `show() -> FilterState`
- `hide() -> FilterState`
- `toggle() -> FilterState`
- `isVisible() -> boolean`

Production seam: refactor the existing `filterPanelToggle` click body in `docs/prompt-kit-polish.js` into one setter, then have pointer and keyboard commands call it.

### `PromptNavigator`

Owns: translation from PromptTarget to current rendered card behavior.

Public interface:
- `openPrompt(promptId) -> Result`

Likely production behavior: clear only the minimum conflicting transient view state, render if necessary, find `[data-prompt-id="P95"]`, then focus/scroll/open through existing Prompt Kit interaction functions. The dispatcher must not know those DOM details.

### `ShortcutStore`

Owns: serialized user configuration only.

Public interface:
- `load() -> StoredShortcutConfig`
- `save(config) -> Result`

Likely adapter: namespaced `localStorage`, with schema version and defensive parse. Storage serialization ends at this port; domain objects begin after validation.

## State ownership

| State | Canonical owner | Persistence | Mutation boundary |
| --- | --- | --- | --- |
| Built-in shortcut definitions | `ShortcutRegistry` source configuration | code | registry construction |
| User shortcut bindings | `ShortcutRegistry` | `ShortcutStore` | validated atomic save then publish |
| Typed sequence buffer (`p` -> `p9` -> `p95`) | `ShortcutDispatcher` | none | per accepted key / timeout / Escape |
| Filter visible/hidden | `FilterVisibility` | none initially | one setter synchronizes DOM + ARIA |
| Prompt existence / identity | loaded `PROMPTS` catalog | generated registry | read-only resolver lookup |
| Hotkey help rows | projection of effective registry | none | render from registry snapshot |

No other module may directly persist bindings or independently toggle the filter CSS class.

## Dependency direction

`keydown / pointer UI`
→ `ShortcutDispatcher`
→ `ShortcutPolicy` + `ShortcutRegistry`
→ semantic application action (`FilterVisibility` / `PromptNavigator` / existing navigation action)
→ DOM adapter or `ShortcutStore`

The DOM and storage adapters depend on the domain interfaces; the domain policy does not depend on DOM structure or `localStorage`.

## Success call stack: explicit filter hide/show/toggle

`USER KEY EVENT`
→ `installCompactBrowsingHotkeys` entrypoint
→ `ShortcutDispatcher.handleKey`
→ `ShortcutPolicy.classifyKey`
→ semantic command (`FILTER_HIDE`, `FILTER_SHOW`, or `FILTER_TOGGLE`)
→ `FilterVisibility.hide/show/toggle`
→ one DOM synchronization transaction
→ `DispatchResult{handled:true,state}`
→ optional help/status projection

Prototype proof records the command and final visibility state for hide, show, and toggle independently.

## Success call stack: `p95` prompt shortcut

Starting state: `P95` exists in the prompt catalog and `p95 -> OPEN_PROMPT(P95)` is an effective user binding.

`KEYDOWN 'p'`
→ dispatcher buffers `p`
→ no side effect

`KEYDOWN '9'`
→ dispatcher buffers `p9`
→ no side effect

`KEYDOWN '5'`
→ policy recognizes complete configured sequence `p95`
→ registry resolves binding
→ `PromptNavigator.openPrompt('P95')`
→ result is returned and sequence buffer is cleared
→ trace records `shortcut.dispatch/open_prompt/P95`

The same path can support a user-configured alias later; exact prompt IDs need no special DOM path.

## Failure call stacks

### Binding collision

`configure('f' -> OPEN_PROMPT(P95))`
→ `ShortcutRegistry.configure`
→ `ShortcutPolicy.validateBinding`
→ detects reserved built-in `FILTER_TOGGLE`
→ returns `RESERVED_COLLISION`
→ `ShortcutStore.save` is never called
→ effective registry remains unchanged.

### Unknown prompt

`configure('p999' -> OPEN_PROMPT(P999))`
→ policy validates target against canonical prompt catalog
→ returns `UNKNOWN_PROMPT`
→ no persistence and no runtime binding.

### Persistence failure

`configure('p95' -> OPEN_PROMPT(P95))`
→ validation succeeds
→ candidate config assembled without publishing
→ `ShortcutStore.save(candidate)` fails
→ registry returns `PERSISTENCE_FAILED`
→ previous effective binding set remains authoritative.

### Editable target

`keydown 'p'` while focus is in search input
→ entrypoint identifies editable target
→ policy returns `EDITABLE_TARGET`
→ dispatcher does not alter the sequence buffer and performs no action.

## Prototype and seam comparison

The executable prototype is `docs/prompt-kit-hotkey-prototype.js`. It intentionally contains no DOM code. It proves the policy/registry/dispatcher/state-owner seams using fake storage, filter, and prompt-navigation ports.

Two boundaries were considered:

1. **Per-widget listeners with local key logic.** Smallest immediate patch, but each widget owns collisions, input safety, help text, and persistence separately. This repeats the current risk and makes user-configured sequences difficult to reason about.
2. **One dispatcher + semantic state owners.** Slightly more structure, but collision rules, sequence buffering, persistence, help projection, and failure classification become centralized while existing widgets remain simple adapters.

Prototype criterion result: choose **one dispatcher + semantic state owners**. It localizes state and allows `p95` to be tested without DOM mocks.

## Agent routing hook

When work mentions **hotkey**, **shortcut**, **keyboard navigation**, **show/hide filters**, **filter toggle**, **favorite prompt shortcut**, **prompt identifier shortcut**, or examples such as **`p95`**, route to these owners before creating anything new:

1. `docs/PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md` — architecture, state ownership, and call stacks.
2. `docs/prompt-kit-polish.js` — current production hotkey/filter/help runtime owner.
3. `tests/test_prompt_kit_header_contract.py` and `tests/test_prompt_kit_filtering_access.py` — product regression owners.
4. `web/prompt-kit/index.html` — generated artifact only; rebuild through `scripts/build_prompt_kit_registry.py`.
5. `harness/prompt-kit-layout/CODEBASE_MAP.md` — responsive-layout harness; it routes hotkey behavior back here and does not own keyboard implementation.

Do not create another shortcut registry, another filter-toggle implementation, or a generated-site-only patch unless the canonical owner is proven insufficient.

## Second-pass critique after prototype

Prototype evidence changes the initial sketch in four ways:
- Treat exact prompt IDs as ordinary configured sequences, not a special-case global search handler.
- Keep the sequence buffer in the dispatcher, not persistence or PromptNavigator.
- Publish a user binding only after storage succeeds, preventing memory/storage split brain.
- Make filter `show/hide/toggle` three commands over one state owner, rather than three DOM mutation paths.

Remaining production decisions:
- final default gestures for explicit hide and explicit show (existing `F` remains the current toggle);
- sequence timeout duration and whether identifier sequences are enabled only for favorites or for every prompt;
- whether opening `P95` expands the prompt detail immediately or only navigates/focuses the card.

These are UX choices, not reasons to change the proved module boundaries.

## Proof ceiling and next implementation seam

Design/prototype proof can establish command classification, collision rejection, prompt resolution, sequence buffering, atomic persistence behavior, and state ownership. It cannot prove browser event ordering, focus behavior, localStorage permissions, rendered-card navigation, or visual accessibility.

The exact next build seam is bounded: extract a production `FilterVisibility` setter and `ShortcutDispatcher` inside `docs/prompt-kit-polish.js`, preserve existing hotkeys, wire explicit hide/show/toggle through the setter, then add persisted `pNN` bindings behind a `ShortcutStore` adapter. Rebuild only through the canonical builder and keep help rows derived from the effective registry.