# Prompt Kit hotkey program design

## Scope
Design the keyboard-command subsystem before configurable prompt shortcuts are broadly implemented. This design extends the existing Prompt Kit runtime; it must not create a second shortcut system, patch generated HTML directly, or turn the responsive-layout harness into a keyboard implementation owner.

## User outcomes and invariants
- Filters support semantic **show**, **hide**, and **toggle** commands through one state owner.
- A user may bind a favorite prompt to a typed sequence such as `p95`.
- Keyboard commands do not fire in `input`, `textarea`, `select`, or content-editable surfaces.
- Built-ins and user bindings cannot silently collide.
- A prompt binding is valid only when its target exists in the canonical prompt catalog.
- Durable binding writes are fail-closed: storage failure does not publish a new in-memory binding.
- Hotkey help is a projection of the effective shortcut registry, not a second truth source.

## Domain vocabulary
- **ShortcutGesture**: normalized key or typed sequence (`f`, `[`, `]`, `p95`).
- **ShortcutCommand**: semantic action such as `FILTER_HIDE`, `FILTER_SHOW`, `FILTER_TOGGLE`, or `OPEN_PROMPT`.
- **PromptTarget**: canonical prompt identity such as `P95`.
- **ShortcutBinding**: gesture → command + optional PromptTarget.
- **ShortcutPolicy**: normalization, reserved gestures, collisions, target validation, editable-target suppression.
- **ShortcutRegistry**: canonical effective map of built-ins plus persisted user bindings.
- **ShortcutDispatcher**: keyboard-event orchestration and typed-sequence buffer owner.
- **FilterVisibility**: sole owner of visible/hidden filter state.
- **PromptNavigator**: port from PromptTarget to rendered prompt navigation/open behavior.
- **ShortcutStore**: persistence port for user bindings; a namespaced/versioned `localStorage` adapter is the expected production implementation.

## Module and interface map

### ShortcutPolicy
Owns validation decisions; no DOM or storage side effects.

Public seam:
- `normalizeGesture(raw)`
- `validateBinding(binding, effectiveBindings, promptCatalog)`
- keyboard classification helpers

Expected rejections: `INVALID_GESTURE`, `RESERVED_COLLISION`, `UNKNOWN_PROMPT`, `EDITABLE_TARGET`.

### ShortcutRegistry
Owns built-ins and user bindings.

Public seam:
- `effectiveBindings()`
- `configure(binding)`
- later: `remove(gesture)`

Mutation rule: validate → assemble candidate → persist candidate → publish candidate. A failed save returns `PERSISTENCE_FAILED` and leaves the prior effective map intact.

### ShortcutDispatcher
Owns transient sequence state (`p` → `p9` → `p95`).

Public seam:
- `handleKey(event)`
- `resetSequence(reason)`

Dependencies: ShortcutRegistry, ShortcutPolicy, FilterVisibility, PromptNavigator, and existing semantic navigation actions. It must not know card selectors or storage serialization.

### FilterVisibility
Owns the one filter visibility transaction.

Public seam:
- `show()`
- `hide()`
- `toggle()`
- `isVisible()`

Production implementation should synchronize CSS class, `aria-expanded`, title, and control text in one setter. Pointer clicks and hotkeys call that setter rather than duplicating DOM mutations.

### PromptNavigator
Public seam: `openPrompt(promptId)`.

It owns translation from PromptTarget to current Prompt Kit card/render behavior. The dispatcher supplies `P95`; the navigator decides how to reveal, focus, scroll, or open it through existing product functions.

### ShortcutStore
Public seam: `load()` / `save(config)`.

Serialization ends here. Domain validation begins after loading.

## State ownership
| State | Owner | Persistence |
| --- | --- | --- |
| Built-in bindings | ShortcutRegistry | code |
| User bindings | ShortcutRegistry | ShortcutStore |
| Typed-sequence buffer | ShortcutDispatcher | none |
| Filter visible/hidden | FilterVisibility | none initially |
| Prompt identities | canonical `PROMPTS` catalog | generated registry |
| Hotkey help rows | projection of ShortcutRegistry | none |

Dependency direction:

`keydown / pointer UI → ShortcutDispatcher → ShortcutPolicy + ShortcutRegistry → semantic action → DOM/storage adapter`

No adapter may become a second policy or state owner.

## Success call stack: filters
`USER KEY EVENT`
→ keyboard entrypoint
→ `ShortcutDispatcher.handleKey`
→ binding resolution
→ `FILTER_HIDE` / `FILTER_SHOW` / `FILTER_TOGGLE`
→ `FilterVisibility.hide/show/toggle`
→ one state/DOM synchronization transaction
→ handled result + trace.

## Success call stack: `p95`
Starting state: `P95` exists and `p95 → OPEN_PROMPT(P95)` is configured.

`p` → dispatcher buffers `p` → no external side effect

`9` → dispatcher buffers `p9` → no external side effect

`5` → exact binding resolves → `PromptNavigator.openPrompt('P95')` → buffer clears → result/trace returns.

Exact prompt identifiers therefore use the normal binding path; they do not require a second global search/router implementation.

## Failure call stacks
- **Collision:** configure `f → OPEN_PROMPT(P95)` → policy sees reserved built-in → `RESERVED_COLLISION` → no store write.
- **Unknown target:** configure `p999 → OPEN_PROMPT(P999)` → catalog rejection → `UNKNOWN_PROMPT` → no store write.
- **Storage failure:** validated `p95` candidate → `ShortcutStore.save` fails → `PERSISTENCE_FAILED` → previous effective registry remains authoritative.
- **Editable target:** key event from search/input → `EDITABLE_TARGET`/ignored → sequence state and product state unchanged.

## Executable seam prototype
`docs/prompt-kit-hotkey-prototype.js` implements the domain seams without DOM coupling and self-tests:
- success: hide, show, toggle, `OPEN_PROMPT(P95)`;
- failure: editable target, reserved collision, unknown prompt, persistence failure.

Run:

```text
node docs/prompt-kit-hotkey-prototype.js
```

Expected top-level result: `status: PASS` with all eight paths represented.

## Seam comparison
**Rejected:** per-widget key listeners with local state/persistence/help rules. They minimize the first patch but duplicate collision policy, input safety, state ownership, and help truth.

**Selected:** one dispatcher + semantic state owners. It keeps the interface small while centralizing the hard behavior: collision resolution, sequence buffering, persistence publication, and command dispatch.

## Routing hook for agents
When work mentions **hotkey**, **shortcut**, **keyboard navigation**, **show/hide/toggle filters**, **favorite prompt shortcut**, **prompt-ID shortcut**, or an example such as **`p95`**, inspect these owners before creating new machinery:
1. this design;
2. `docs/prompt-kit-polish.js` for current runtime behavior;
3. focused Prompt Kit interaction/header/filter tests;
4. `scripts/build_prompt_kit_registry.py` for generated-site parity;
5. `harness/prompt-kit-layout/CODEBASE_MAP.md` for routing only.

Do not create another shortcut registry, another filter visibility owner, or a generated-site-only patch unless current ownership is proven insufficient.

## Second-pass critique
Prototype and production evidence changed the initial sketch in five useful ways:
- `p95` is an ordinary configured sequence, not a special prompt-ID handler.
- sequence state belongs in the dispatcher, not storage or PromptNavigator.
- persistence must succeed before a new binding becomes effective.
- hide/show/toggle are three commands over one filter state owner, not three DOM paths.
- when a prompt-ID buffer is active, that sequence gets first chance to consume later digits such as `1`, `4`, or `5`; built-in digit navigation retains priority only when no configured sequence is in progress.

Production decisions closed on 2026-08-22:
- unmodified backtick `` ` `` toggles the Hotkeys surface. This keeps the core shortcut cluster reachable with one hand; `/` remains dedicated to Focus search.
- modifier chords and editable fields suppress the backtick Hotkeys command.
- `F` remains filter toggle; `[` explicitly hides filters and `]` explicitly shows filters.
- configured prompt-ID sequences expire after 1.2 seconds.
- only prompts that are currently Favorites may be assigned a prompt-ID shortcut.
- a completed prompt-ID shortcut copies the canonical prompt and scrolls its card into view without opening prompt detail through `showPromptDetail`.
- shortcut persistence uses versioned `promptKit.promptShortcuts.v1` storage and publishes only after a successful durable write.
- configured shortcut rows sort by numeric prompt sequence rather than lexicographic ID text.

These production choices preserve the selected seams and remove the prior UX-policy ambiguity.

## Proof ceiling
Repository proof must cover the production source, generated-site parity, input/modifier suppression, filter commands, sequence collision ordering, timeout semantics, fail-closed persistence, target validation, and canonical prompt-detail dispatch. The user's direct browser exercise supplies additional live evidence that the existing visible hotkeys operate on the deployed UI.

The remaining ceiling is limited to environment diversity that cannot be exhaustively certified by this repository: every browser/keyboard-layout combination, future browser-storage policy changes, and subjective ergonomics on devices not exercised by the current operator. Those are not unresolved ownership or implementation gaps; future reports should name a concrete failing environment before reopening architecture.

## Fixed implementation seam
Production behavior is owned in `docs/prompt-kit-polish.js`; `web/prompt-kit/index.html` is rebuilt only through `scripts/build_prompt_kit_registry.py`. New hotkeys must extend the existing dispatcher/state owners and focused tests rather than introduce a second keyboard registry, second filter state owner, or generated-only patch.

The owning CI gate is `.github/workflows/prompt-kit-web.yml`, which compiles and executes `tests/test_prompt_kit_hotkey_completion.py` alongside the existing Prompt Kit interaction, discovery, navigation, filtering, mobile, portability, and exact-generated-site checks.