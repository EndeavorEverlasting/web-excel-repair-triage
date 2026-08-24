# Prompt Kit interaction modality + profile design — executable extension

## Purpose

This document is a bounded program-design extension to `docs/PROMPT_KIT_PROGRAM_ARCHITECTURE.md`. The parent architecture remains the canonical owner for the Prompt Kit command kernel, state-owner boundaries, terminal-value semantics, and external ports. This extension answers two unresolved product questions before broad implementation:

1. how the same Prompt Kit capability remains productive for mouse/pointer-only and keyboard-only users without branching business logic by input device;
2. how a user can operate with one Prompt Profile or assume one of many Prompt Profiles without duplicating the catalog, resetting transient browsing state, or corrupting Favorites/shortcut preferences across profiles.

This is **program design + executable prototype**, not broad production migration. It must not become a second hotkey registry, a second Favorite owner, a generated-HTML patch, a dashboard/gameplay expansion, or a framework rewrite.

## Fresh evidence floor

Design extension floor: `main@bf4af1d40ccf4801e60317675ba7be83319dfc22` on 2026-08-24.

That mainline already contains the prototype-earned async `CommandKernel` architecture from PR #282. Current evidence also establishes:

- `docs/PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md` is the existing shortcut-program owner;
- configured prompt shortcuts are accelerators over semantic prompt actions, not a separate feature system;
- `FavoritePreferences` and the existing `ShortcutRegistry` are the semantic preference owners;
- `SessionState` owns transient browsing state;
- `PromptSurfacePort` owns DOM/focus/scroll projection;
- production browser geometry, real Clipboard API policy, pointer ergonomics, keyboard layout diversity, and storage migration remain live-runtime proof ceilings.

No open PR discovered at this floor owns this program-design extension. Existing broader Favorite/gameplay and guided-discovery PRs do not justify duplicating or replacing the merged command architecture.

## Observable done checklist

This extension is design-ready only when executable evidence proves:

1. essential user actions have both a visible pointer path and a keyboard-operable path;
2. hotkeys remain accelerators rather than the only way to reach an essential capability;
3. pointer and keyboard entrypoints dispatch the same semantic command rather than owning separate business rules;
4. input modality is an invocation fact, not global mutable application state;
5. keyboard shortcut copy may reveal/focus a recovery target without forcing equivalent focus movement on a pointer click whose target is already visible;
6. one-profile users can remain on an implicit/default profile with no required profile-switching ceremony;
7. named profiles scope durable user preferences without cloning the canonical prompt catalog or transient browsing state;
8. the default profile can delegate to the current legacy preference storage seam, avoiding a mandatory migration merely to adopt the architecture;
9. a profile-scoped persistence failure leaves that profile and all other profiles truthful and unchanged;
10. an unknown profile cannot become active;
11. an in-flight asynchronous command remains attributed to the profile that initiated it rather than being silently retargeted after a profile switch;
12. the selected seam extends the existing `CommandKernel` architecture and broad production wiring remains a later build sprint.

## Primary user outcomes

### Mouse / pointer-only user

- Every essential command exposed through a shortcut also has a visible native control or equivalent pointer-reachable action.
- Clicking a visible Copy control reaches clipboard value directly; the architecture does not require the user to enter a keyboard-navigation mode.
- A pointer-originated action does not receive an unnecessary keyboard-style focus jump merely because keyboard users need a recovery target for a different entrypoint.
- Profile activation is reachable from a visible profile control when more than one profile exists.

### Keyboard-only user

- Visible controls remain naturally reachable/activatable through native keyboard semantics.
- Configured shortcuts accelerate existing semantic commands rather than bypassing the program architecture.
- A shortcut that targets a prompt may reveal the prompt and focus its Copy control so `Enter` remains an immediate recovery/repeat action.
- Editable-field suppression and existing shortcut collision policy remain owned by the hotkey subsystem.
- Profile activation can traverse the same semantic `ACTIVATE_PROFILE` command from a keyboard-operable profile control.

### One-profile user

- The application exposes an implicit `default` Prompt Profile.
- No profile switcher is required when only one profile exists.
- Existing durable Favorite/shortcut storage can remain the default profile's backing store through a compatibility adapter.
- Prompt catalog, generated artifact, and transient browsing behavior remain unchanged merely because profile-capable architecture exists.

### Multi-profile user

- The user can assume a named Prompt Profile without cloning the whole application state.
- Favorites and configured shortcuts can be scoped by active profile.
- Switching profile does not silently clear the current search, filters, prompt location, or detail state.
- Mutating Favorites in one profile cannot change another profile's Favorite set.
- Semantic completion telemetry, if enabled, records the profile that initiated the command.

## Core invariants

1. **Capability parity, not input-mode parity.** Pointer and keyboard may use different entrypoints or presentation recovery, but must converge on the same terminal domain command.
2. **No global input mode.** The application never stores `mouseMode` or `keyboardMode`. Hybrid users may alternate input devices freely; modality belongs to one invocation.
3. **Visible controls are canonical capability surfaces.** Shortcuts accelerate them; shortcuts do not become exclusive access paths.
4. **Native semantics first.** Production controls should prefer native buttons/selects/links so mouse, keyboard, and assistive technology behavior does not require custom reimplementation.
5. **Profile identity is explicit at command initiation.** Profile-scoped mutations and semantic usage attribution use the initiating profile snapshot carried in `InteractionContext`.
6. **Prompt catalog is profile-independent.** A profile does not duplicate canonical prompts or generated HTML.
7. **Transient browsing state is not profile-owned by default.** Search/filter/detail/current location remain `SessionState` until a separate user requirement proves they should persist per profile.
8. **Preference semantics keep their owners.** Favorites remain owned by `FavoritePreferences`; shortcuts remain owned by the existing `ShortcutRegistry`. Profiles change persistence namespace, not semantic ownership.
9. **Default profile is a compatibility boundary.** Production may map the default profile to today's existing storage keys; named profiles may use namespaced records. The prototype does not invent new production key names.
10. **Profile activation is reversible session state.** Activating another profile changes the active preference context, not the prompt registry or current page location.
11. **Fail closed on scoped persistence.** A failed write publishes no new Favorite/shortcut state for the target profile and touches no other profile.
12. **Async commands retain initiation context.** A profile switch during a pending clipboard write does not rewrite that command's profile attribution.
13. **Presentation differences stay at the presentation seam.** Focus/scroll/reveal policy may inspect interaction context; clipboard, persistence, catalog validation, and completion semantics may not fork by modality.

## Domain vocabulary

### Interaction records

- **InteractionModality** — invocation-level value: `pointer` or `keyboard` for the current prototype. It is not durable state.
- **InteractionSource** — semantic UI origin such as `prompt-control`, `favorite-shortcut`, or `profile-switcher`.
- **InteractionContext** — immutable snapshot `{source, modality, profileId}` attached before a command enters the kernel.
- **PresentationPlan** — adapter-level decision describing whether this invocation needs reveal/focus recovery. It never changes terminal domain semantics.
- **CapabilityParity** — invariant that every essential semantic action has a pointer-reachable visible control and a keyboard-operable route.

### Profile records and owners

- **PromptProfile** — stable user-facing profile identity (`id`, `name`, `isDefault`). It scopes selected durable preferences; it does not clone prompts or DOM/session state.
- **ProfileCatalog** — canonical runtime list of available Prompt Profiles and the one default profile.
- **ActiveProfile** — session owner of the currently assumed profile ID.
- **ProfilePreferenceStore** — persistence port that loads/saves preference records for one profile namespace.
- **DefaultProfileCompatibilityAdapter** — production adapter concept that maps the default profile to existing preference storage so adopting profiles does not force a migration first.
- **ProfiledFavoritePreferences** — prototype proof that the existing Favorite semantic owner can operate over a profile-scoped persistence port without becoming a second Favorite system.

### Existing parent-architecture records retained

- `PromptCatalog`
- `PromptCommand`
- `CommandResult`
- `ProgramError`
- `CommandKernel`
- `SessionState`
- `FavoritePreferences`
- existing `ShortcutRegistry`
- `ClipboardPort`
- `PromptSurfacePort`
- `UsageLedger`

## External prior-art inspection

The extension inspected mechanisms only; it copies no external implementation and adds no dependency.

### VS Code user-data profiles

Source inspected: `microsoft/vscode`, `src/vs/platform/userDataProfile/common/userDataProfile.ts`.

Transferable mechanisms:

- a stable default profile exists alongside named profiles;
- resource ownership is explicit rather than represented as one opaque cloned application snapshot;
- profile identity is stable and separate from the resources that may be scoped by that profile.

License implication: VS Code is MIT licensed. No code is copied.

### WAI-ARIA Authoring Practices toolbar pattern

Source inspected: `w3c/aria-practices`, `content/patterns/toolbar/toolbar-pattern.html` and repository `LICENSE.md`.

Transferable mechanisms:

- visible grouped controls remain actual controls;
- focus management exists to make keyboard use efficient, not to replace pointer operation;
- keyboard navigation should reduce friction while keeping controls discoverable.

License implication: the repository documents are under the W3C Software and Document License. No code or markup is copied.

Security/dependency implication: this design introduces no library, browser permission, remote service, or third-party runtime dependency.

## Candidate designs

### Candidate A — per-entrypoint branching with one global active profile variable

Each click/hotkey handler decides whether to focus/scroll/copy and reads a global `activeProfileId`; each preference helper appends the profile ID to storage keys.

**Advantage:** smallest initial diff.

**Failure:** modality logic and profile storage policy leak into every caller. An async handler can observe a different global profile at completion than at initiation. Pointer and keyboard business behavior can silently diverge. Storage naming becomes a distributed convention rather than an owned port.

**Disposition:** rejected.

### Candidate B — clone the complete app state per profile

Each profile owns prompt catalog, view/search/filter state, Favorites, shortcuts, usage, and presentation state. Switching profile swaps the entire snapshot.

**Advantage:** intuitive mental model if every state truly belongs to a workspace.

**Failure:** the current requirements do not justify duplicating canonical prompts or transient browsing state. It creates unnecessary reset behavior, larger persistence/migration surface, stale catalog copies, and pressure to persist incidental UI state merely because profiles exist.

**Disposition:** rejected.

### Candidate C — explicit InteractionContext + profile-scoped preference ports

Every user event is normalized into immutable `InteractionContext` before calling the existing semantic command kernel. `ActiveProfile` supplies the profile snapshot. The prompt catalog and transient `SessionState` remain shared. Existing preference owners operate through a profile-scoped persistence port. The default profile delegates to legacy preference storage; named profiles use their own namespace.

**Advantages:**

- no second command system;
- no global input mode;
- no duplicated prompt registry;
- no forced session reset on profile switch;
- pointer/keyboard differences are limited to presentation recovery;
- existing Favorite and Shortcut semantic owners remain authoritative;
- asynchronous operations retain initiation context;
- single-profile users incur almost no product complexity;
- named profiles become a bounded productivity extension instead of an app fork.

**Disposition:** selected and executable.

### Candidate D — persistent “workspace profile” including filters/view/layout

Persist the current search/filter/view/detail state alongside Favorites and shortcuts and restore all of it whenever a profile is assumed.

**Advantage:** could eventually support deeply customized workspaces.

**Failure at current evidence floor:** it converts transient state into durable product truth without a demonstrated user requirement and increases migration, invalidation, and surprising-navigation risk.

**Disposition:** deferred. Reconsider only when actual user evidence says profile switching should restore browsing/layout state.

## Selected module/interface map

| Module | Responsibility / owned state | Public interface | Hidden complexity | Side effects | Failure contract | Test seam |
| --- | --- | --- | --- | --- | --- | --- |
| `InteractionContextFactory` | snapshots source, modality, active profile | `create(source, modality)` | validates allowed modality/source and resolves current profile | none | `INVALID_INTERACTION_CONTEXT`, `INVALID_INTERACTION_MODALITY`, `UNKNOWN_PROFILE` | pure + trace |
| `ProfileCatalog` | available profiles + one default | `require(id)`, `defaultProfile()`, `needsSwitcher()` | duplicate/default validation | none | `UNKNOWN_PROFILE`, `INVALID_PROFILE_CATALOG` | fixture |
| `ActiveProfile` | current assumed profile ID | `current()`, `activate(profileId)` | reversible transition trace | none | target must be validated before activation | pure/component |
| existing `CommandKernel` | semantic command dispatch | `execute(command)` | handler/result/error normalization | none directly | parent architecture | existing prototype |
| existing `SessionState` | transient search/filter/detail/location | existing intention-level transitions | does **not** reset on profile activation | none | parent architecture | snapshot comparison |
| `ProfilePreferenceStore` | profile namespace persistence boundary | `loadFavorites(profileId)`, `saveFavorites(profileId, candidate)` prototype seam; analogous namespace for shortcuts | default-legacy compatibility vs named namespace | browser storage in production | scoped persistence failure | memory/failing fake |
| existing `FavoritePreferences` semantic owner | Favorite set semantics per profile context | `has/toggle/snapshot(profileId)` after production adaptation | validation + candidate publication | ProfilePreferenceStore | failed save publishes nothing | memory/failing fake |
| existing `ShortcutRegistry` semantic owner | effective bindings for active profile | existing registry API over a profile-scoped store | collision/target policy remains unchanged | existing ShortcutStore via profile namespace | existing hotkey contract | existing hotkey prototype + future profile fixture |
| `PromptSurfacePort` | DOM projection and focus/reveal policy | `prepareCopy(promptId, context)`, profile projection | native focus/scroll/visibility details | DOM/focus/scroll | presentation recovery classified by command | fake + browser proof |
| `UsageLedger` | semantic completion events | existing `recordCompletion` | event adds initiating `profileId`/modality when productized | local/private store if enabled | degradation cannot negate user value | memory/failing fake |

## State and data ownership

| State/data | Canonical owner | Profile-scoped? | Persistence | Notes |
| --- | --- | --- | --- | --- |
| effective prompt records | PromptCatalog / registry builder | no | tracked registry → generated site | same prompts for every profile |
| active assumed profile ID | ActiveProfile | n/a | session-only initially | explicit durable “remember last profile” is a later product decision |
| profile definitions | ProfileCatalog | n/a | future ProfileStore if productized | prototype uses fixtures |
| search/filter/detail/current prompt | SessionState | no by default | none | profile switch must not reset it |
| Favorites | FavoritePreferences | yes | ProfilePreferenceStore | default may map to legacy store |
| configured shortcuts | existing ShortcutRegistry | yes | existing ShortcutStore through profile namespace | no second shortcut registry |
| semantic usage events | UsageLedger | event records initiating profile | local/private only if enabled | not a state owner for Favorites/shortcuts |
| focus/scroll/highlight | PromptSurface adapter | no durable scope | none | invocation-specific presentation |
| clipboard contents | ClipboardPort/browser | no | external | same terminal action for every profile/modality |

## Dependency direction

```text
MOUSE CLICK / KEYBOARD CONTROL / HOTKEY
  -> ENTRYPOINT
  -> InteractionContextFactory
       -> ActiveProfile.current()
       -> ProfileCatalog.require(activeProfileId)
  -> existing CommandKernel.execute(command + InteractionContext)
  -> semantic handler
       -> PromptCatalog
       -> SessionState (only if the journey needs transient reveal/detail state)
       -> FavoritePreferences / existing ShortcutRegistry
            -> ProfilePreferenceStore(profileId)
       -> PromptSurfacePort(context)        [presentation only]
       -> ClipboardPort / UsageLedger
  <- CommandResult or classified ProgramError
  -> native completion feedback
```

Profile activation is separate:

```text
VISIBLE PROFILE CONTROL (pointer or keyboard)
  -> ProfileSwitcherEntrypoint
  -> InteractionContextFactory captures OLD initiating profile
  -> CommandKernel.execute(ACTIVATE_PROFILE targetProfileId)
  -> ProfileCatalog.require(targetProfileId)
  -> ActiveProfile.activate(targetProfileId)
  -> PromptSurface projects active-profile label/control
  <- PROFILE_ACTIVE
```

The command that activates a profile does not clear `SessionState` and does not rewrite preference records.

## Executable prototype

Executable: `docs/prompt-kit-profile-modality-prototype.js`.

It imports the already-merged program-kernel prototype and extends it without changing production runtime code. External boundaries remain fakes; the command seam, profile decisions, context snapshot, and failure ordering are real prototype logic.

## Success call stack — mouse/pointer Copy control

**Starting state:** visible prompt card exists; default profile active.

**Terminal user value:** canonical prompt text is on the clipboard.

```text
MOUSE CLICK ON VISIBLE COPY BUTTON                       [ENTRYPOINT]
  -> PromptControlEntrypoint.copy(P07, pointer)
  -> InteractionContextFactory
       -> {source:prompt-control, modality:pointer, profileId:default}
  -> CommandKernel.execute(COPY_REVEAL_PROMPT)
  -> PromptCatalog.require(P07)
  -> PromptSurface.prepareCopy
       -> preserve current pointer-origin focus; no keyboard-only focus jump
  -> await ClipboardPort.writeText(copyContent)          [TERMINAL ACTION]
  -> UsageLedger records PROMPT_COPIED + initiating profile
  <- COPIED / PROMPT_TEXT_ON_CLIPBOARD
```

No shortcut is required.

## Success call stack — keyboard activation of visible Copy control

**Terminal user value:** same clipboard result.

```text
TAB / NATIVE FOCUS -> ENTER ON COPY BUTTON               [ENTRYPOINT]
  -> PromptControlEntrypoint.copy(P07, keyboard)
  -> InteractionContextFactory
  -> same COPY_REVEAL_PROMPT command
  -> same catalog/clipboard/completion owners
  <- COPIED
```

Because the native Copy control is already the keyboard focus target, the presentation adapter does not perform a redundant reveal/focus cycle.

## Success call stack — configured favorite shortcut

```text
USER TYPES CONFIGURED FAVORITE SHORTCUT                  [ENTRYPOINT]
  -> FavoriteShortcutEntrypoint.copy(P07)
  -> InteractionContextFactory
       -> {source:favorite-shortcut, modality:keyboard, profileId:<active>}
  -> CommandKernel.execute(COPY_REVEAL_PROMPT)
  -> PromptCatalog.require(P07)
  -> SessionState.revealPrompt(P07)                       [REQUIRED INTERMEDIATE]
  -> PromptSurface.revealPrompt(P07)
  -> PromptSurface.focusCopy(P07)                         [RECOVERY TARGET]
  -> await ClipboardPort.writeText(copyContent)           [TERMINAL ACTION]
  -> UsageLedger completion attributed to initiating profile
  <- COPIED
```

Shortcut acceleration reaches the same terminal command; it does not own copy policy.

## Success call stack — assume a named profile

```text
POINTER CLICK OR KEYBOARD ACTIVATE PROFILE CONTROL       [ENTRYPOINT]
  -> ProfileSwitcherEntrypoint.activate(work, modality)
  -> InteractionContextFactory captures current profile
  -> CommandKernel.execute(ACTIVATE_PROFILE, target=work)
  -> ProfileCatalog.require(work)
  -> ActiveProfile.activate(work)
  -> PromptSurface.projectProfile(work)
  <- PROFILE_ACTIVE / ACTIVE_PROFILE_CHANGED              [TERMINAL VALUE]
```

The current search/filter/detail location remains intact.

## Success call stack — profile-scoped Favorite mutation

```text
USER TOGGLES FAVORITE IN ACTIVE WORK PROFILE
  -> PromptControlEntrypoint.toggleFavorite(P07, modality)
  -> InteractionContextFactory profileId=work
  -> CommandKernel.execute(TOGGLE_FAVORITE)
  -> PromptCatalog.require(P07)
  -> FavoritePreferences builds work-profile candidate
  -> ProfilePreferenceStore.saveFavorites(work, candidate) [TRANSACTION BOUNDARY]
  -> publish work-profile Favorite state
  -> PromptSurface.projectFavorite(work, P07, true)
  -> UsageLedger FAVORITE_CHANGED profileId=work
  <- FAVORITE_CHANGED
```

The default profile Favorite set is untouched.

## Failure call stacks

### Invalid interaction modality

```text
ENTRYPOINT supplies unsupported modality
  -> InteractionContextFactory
  -> INVALID_INTERACTION_MODALITY
  -> kernel is not invoked
  -> no DOM/storage/clipboard mutation
```

No fallback global mode is inferred.

### Unknown profile activation

```text
ACTIVATE_PROFILE(target=missing)
  -> ProfileCatalog.require(missing)
  -> UNKNOWN_PROFILE
  -> ActiveProfile remains previous value
  -> no preference mutation
```

### Profile-scoped persistence failure

```text
TOGGLE_FAVORITE while work profile is active
  -> candidate built for work
  -> ProfilePreferenceStore.saveFavorites(work, candidate)
  -> PROFILE_PREFERENCE_PERSISTENCE_FAILED
  -> work prior set remains authoritative
  -> default profile remains untouched
  -> no Favorite projection / no completion event
```

### Async copy while user switches profile

The prototype deliberately begins a deferred clipboard command in `default`, activates `work` while the write is pending, and then completes the copy.

```text
COPY starts with InteractionContext.profileId=default
  -> Clipboard Promise pending
  -> ACTIVATE_PROFILE(work) completes
  -> original clipboard Promise resolves
  -> PROMPT_COPIED event remains profileId=default
```

This is intentional snapshot semantics. A running command is not silently reassigned to whatever profile happens to be active at completion time.

## State model

### Profile catalog cardinality

```text
DEFAULT_ONLY
  -> named profile created later -> MULTI_PROFILE
MULTI_PROFILE
  -> profiles may be added/removed later through a future profile-management owner
```

The prototype does not implement profile creation/deletion because those lifecycle requirements were not requested. It proves activation and scoped preference use only.

### Active profile transition

```text
ACTIVE(default)
  -- ACTIVATE_PROFILE(work) / valid --> ACTIVE(work)
  -- ACTIVATE_PROFILE(missing) ------> ACTIVE(default) + UNKNOWN_PROFILE
```

A valid activation does not imply a `SessionState` transition.

### Interaction context lifecycle

```text
USER EVENT
  -> snapshot {source, modality, current profileId}
  -> immutable for command lifetime
  -> discarded after terminal result/error
```

No interaction context is persisted.

## Prototype comparison result

The executable comparison is intentionally narrower than the parent command-kernel-vs-reducer comparison. The parent architecture already selected the async command kernel.

The remaining profile/modality choice is:

| Criterion | Global mode + cloned profile state | Explicit InteractionContext + scoped preferences |
| --- | --- | --- |
| pointer/keyboard policy locality | leaks across callers | presentation seam only |
| hybrid input | global mode can become stale | every invocation independent |
| single-profile complexity | profile machinery still visible | default profile can stay implicit |
| profile switch effect | swaps/reset broad app state | changes preference context only |
| prompt catalog ownership | pressure to duplicate | remains canonical/global |
| async attribution | can observe later active profile | initiating snapshot is stable |
| preference isolation | distributed key convention | one profile persistence port |
| migration risk | high | default compatibility adapter bounds it |

**Selected:** explicit `InteractionContext` + `ActiveProfile` + profile-scoped preference ports over the already-selected async command kernel.

## Productivity feature admission

This architecture gives future feature work a concrete admission test instead of feature brainstorming by intuition alone.

A proposed feature is safe enough for a build prototype only when it can answer:

1. What is the terminal user value?
2. What visible pointer path reaches it?
3. What keyboard-operable path reaches it?
4. Is the keyboard shortcut merely an accelerator of a visible capability?
5. Is its state global catalog data, transient session state, or profile-scoped durable preference?
6. Which module is the one state owner?
7. Which external side effects need ports?
8. What is the consequential failure path and truthful recovery state?
9. Does a one-profile/default user retain existing behavior and storage?
10. Does switching profile leave unrelated transient UI untouched?
11. What semantic completion event, if any, belongs in the UsageLedger?
12. What repository proof is possible, and what still requires a real browser/operator?

## Feature shortlist after this design session

### Admit next: profile-specific Favorite + shortcut worksets

**Why:** directly improves prompt retrieval productivity for users with multiple contexts while reusing existing Favorite and Shortcut owners.

**Safe boundary:** scope only durable Favorite/shortcut preference storage by profile; preserve the default profile as compatibility behavior; do not persist search/filter/layout merely because profiles exist.

### Admit later: universal Actions surface as a projection of semantic commands

A visible Actions control could project the same semantic command catalog for mouse users while a documented keyboard accelerator opens the same surface. This can improve discovery without inventing a second action owner.

**Gate:** build only after the command catalog/entrypoint projection contract is explicit; the Actions surface must never become a second command registry.

### Defer: full profile-specific view/filter/layout restoration

Current evidence does not prove that users want profile switching to move or reset their browsing context. Persisting it now would blur transient and durable state.

### Defer: automatic recommendations/gameplay from usage

The parent architecture intentionally keeps `UsageLedger` optional/local/private. Recommendation or gameplay features should wait until retention/privacy/reset semantics are explicitly productized and tested.

## Tests and traces

Focused repository proof should execute:

```text
node --check docs/prompt-kit-profile-modality-prototype.js
node docs/prompt-kit-profile-modality-prototype.js
python -m unittest tests.test_prompt_kit_profile_modality_prototype -v
python -m unittest tests.test_prompt_kit_program_prototype tests.test_prompt_kit_hotkey_completion -v
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
```

The prototype JSON report must expose:

- selected extension identity;
- mouse/pointer, keyboard, single-profile, and multi-profile archetype PASS markers;
- pointer/keyboard command parity;
- keyboard-shortcut reveal/focus recovery;
- default-profile compatibility behavior;
- profile isolation;
- unknown-profile rejection;
- profile persistence failure isolation;
- in-flight profile snapshot attribution;
- trace events naming interaction source/modality/profile without logging prompt bodies.

## Second-pass architecture critique

Prototype design changed the initial intuition in several useful ways:

1. **Do not model “mouse user” and “keyboard user” as durable modes.** The same person can switch devices between consecutive actions; modality belongs to the invocation.
2. **Do not force shortcut focus behavior onto visible-control clicks.** Reveal/focus is valuable recovery for a typed shortcut, but a pointer click or keyboard activation on an already-focused native Copy control should not be bounced elsewhere.
3. **Do not make Profile a synonym for whole-app snapshot.** Current evidence only justifies durable preference scoping. Catalog and transient navigation stay shared.
4. **Do not mint `ProfiledShortcutRegistry`.** The existing `ShortcutRegistry` remains the semantic owner; only its persistence namespace becomes profile-aware in a later build.
5. **Do not require migration before value.** A default-profile compatibility adapter lets current users retain existing preference storage while named profiles get a namespace.
6. **Do not read active profile at command completion.** Async actions keep the profile snapshot captured at initiation so telemetry and scoped mutation cannot drift.
7. **Do not persist last active profile yet.** Session-only activation is sufficient to prove architecture; durable resume semantics need an explicit product decision.

No safer bounded design improvement remains in this prototype scope without crossing into broad production implementation or inventing unrequested profile lifecycle semantics.

## Exact implementation seam ready for the next build sprint

The next production build should be intentionally narrower than “add profiles everywhere.”

1. Add one production `PromptProfileContext`/`InteractionContextFactory` owner near the existing Prompt Kit runtime.
2. Ship **default-only behavior first**: one implicit default profile, no new profile-switcher UI, and no visible behavior change.
3. Route existing Favorite and Shortcut persistence through a profile-aware storage adapter whose default namespace delegates to the current storage contract.
4. Stamp semantic commands with `{source, modality, profileId}` at entrypoint boundaries; do not create global modality state.
5. Keep prompt catalog and `SessionState` unchanged.
6. Add named profile activation and a visible keyboard-operable profile control only after default compatibility and persistence isolation are proven.
7. Reuse the existing `CommandKernel`, `FavoritePreferences`, `ShortcutRegistry`, and PromptSurface owners; do not introduce parallel owners.

Broad production profile management (create/rename/delete/import/export), profile-specific layout persistence, dashboards, and recommendations are outside that next seam.

## Unresolved decisions

These are deliberately not guessed by this design sprint:

- whether users should be able to create/rename/delete profiles inside Prompt Kit or only import predefined profiles;
- whether last active profile should persist across browser sessions;
- whether any preferences beyond Favorites and configured shortcuts should become profile-scoped;
- whether profile switching should eventually restore a saved view/search/filter workspace;
- exact visible profile-switcher placement and responsive layout;
- whether usage history should be global, profile-partitioned, or disabled by default if productized.

Each requires either explicit product preference or browser/user evidence; none blocks the current executable architecture seam.

## Proof ceiling

Repository/Node/Python/CI proof can establish:

- one semantic command path for pointer and keyboard entrypoints;
- no global interaction modality state in the prototype;
- default-only and multi-profile state ownership;
- default-legacy compatibility seam in the fake store;
- profile-scoped Favorite isolation and fail-closed persistence;
- unknown-profile rejection;
- initiating-profile attribution across an async profile switch;
- compatibility with the existing program/hotkey prototypes and generated Prompt Kit parity.

It cannot establish:

- real browser focus behavior or whether every native control receives focus identically across browsers/platforms;
- real mouse, touch, screen-reader, keyboard-layout, or switch-device ergonomics;
- actual localStorage migration against a user's existing browser data;
- subjective productivity improvement for real users;
- ideal profile-switcher placement or profile lifecycle UX;
- production behavior until the later build sprint wires these seams into `docs/prompt-kit*.js` and the canonical generated site.

Those are live/browser/product proof gates, not reasons to duplicate the architecture now.
