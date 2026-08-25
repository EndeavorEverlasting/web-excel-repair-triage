# Prompt Kit interaction modality + profile design — executable extension

## Purpose

This document is a bounded program-design extension to `docs/PROMPT_KIT_PROGRAM_ARCHITECTURE.md`. The parent architecture remains the canonical owner for the Prompt Kit command kernel, terminal-value semantics, state-owner boundaries, and external ports. This extension answers two product questions before broad implementation:

1. how the same capability remains productive for mouse/pointer-only and keyboard-only users without branching domain behavior by input device;
2. how one user can operate with one Prompt Profile or assume one of many Prompt Profiles without duplicating prompts, resetting browsing state, or leaking Favorites and custom shortcuts across profiles.

This is **program design + executable prototype**, not broad production migration. It must not become a second command system, second Favorite owner, second shortcut authority, generated-site patch, dashboard/gameplay expansion, or framework rewrite.

Initial design floor: `main@bf4af1d40ccf4801e60317675ba7be83319dfc22`, which already contains the async `CommandKernel` architecture from PR #282. The final integration floor must be refreshed again before merge.

## Observable done checklist

The design is prototype-earned only when executable evidence proves all of the following:

1. essential actions have a visible pointer path and a keyboard-operable path;
2. shortcuts accelerate visible capabilities rather than becoming exclusive capability owners;
3. pointer and keyboard entrypoints converge on the same semantic command;
4. modality is invocation context, not global mutable app state;
5. a keyboard shortcut may reveal/focus Copy as recovery without imposing that focus jump on a pointer click or already-focused native Copy control;
6. one-profile users can remain on an implicit default profile without profile-switch ceremony;
7. defaultness is `ProfileCatalog` metadata, not a magic profile ID;
8. the catalog-defined default profile can delegate existing preference storage, avoiding a forced migration merely to adopt the architecture;
9. named profiles isolate durable Favorites and custom shortcuts;
10. canonical `FavoritePreferences` remains the Favorite semantic owner;
11. canonical `ShortcutRegistry` remains the shortcut semantic owner and hydrates scoped persisted bindings through its existing policy;
12. switching profile refreshes profile-dependent projection before reporting `PROFILE_ACTIVE`;
13. switching profile does not reset transient search/filter/detail/location state;
14. failed profile persistence does not publish candidate state or contaminate another profile;
15. unknown profiles cannot become active;
16. an asynchronous command remains attributed to the profile that initiated it even if another profile becomes active before completion;
17. semantic traces contain opaque profile IDs/action metadata, not profile display names or prompt bodies;
18. the slice stays prototype-only and leaves broad production wiring to the normal build executor.

## Primary user outcomes

### Mouse / pointer-only

- Every essential command exposed through a shortcut also exists as a visible control or equivalent pointer-reachable action.
- Clicking visible Copy reaches the clipboard terminal value directly.
- A pointer-originated Copy does not suffer a keyboard-recovery focus jump when its control is already visible.
- When multiple profiles eventually become productized, profile activation must be available from a visible pointer-reachable control.

### Keyboard-only

- Native controls remain keyboard-operable through their normal semantics.
- Configured shortcuts are accelerators over the same semantic commands used by visible controls.
- A typed prompt shortcut may reveal the prompt and focus Copy so `Enter` remains an immediate recovery/repeat action.
- Existing editable-field suppression and collision rules stay in the hotkey subsystem.
- Profile activation traverses the same `ACTIVATE_PROFILE` command whether initiated through keyboard or pointer.

### One-profile

- Exactly one catalog-defined default profile can remain implicit.
- No switcher is required when `ProfileCatalog.needsSwitcher()` is false.
- Current Favorite/shortcut storage can remain the default profile's compatibility namespace.
- Adding profile-capable architecture does not clone prompts or persist transient view state.

### Multi-profile

- A user can assume a named profile without cloning the whole application.
- Favorites and custom shortcuts remain isolated per profile.
- Profile activation reprojects the target profile's Favorite state before success returns.
- Search/filter/detail/current-location state remains intact unless a later explicit product decision says otherwise.
- In-flight command attribution cannot drift to a profile activated later.

## Core invariants

1. **Capability parity, not input-mode parity.** Pointer and keyboard may differ at entrypoint/presentation recovery but converge on terminal domain behavior.
2. **No global input mode.** No `mouseMode`, `keyboardMode`, or mutable `currentModality`; modality belongs to one `InteractionContext`.
3. **Visible controls are canonical capability surfaces.** Shortcuts accelerate them.
4. **Native semantics first.** Production should prefer native buttons/selects/links over recreating basic keyboard/pointer semantics.
5. **Profile identity is snapshotted at initiation.** Profile-scoped mutation and semantic completion use the initiating context.
6. **Prompt catalog is shared.** Profiles do not duplicate canonical prompt records or generated HTML.
7. **Transient browsing state is not profile-owned by default.** `SessionState` remains shared until user evidence proves workspace restoration is valuable.
8. **Favorites keep one semantic owner.** Profile adapters select storage; canonical `FavoritePreferences` decides Favorite set mutation/publication.
9. **Shortcuts keep one semantic owner.** Profile adapters select storage; canonical `ShortcutRegistry` owns validation, collision policy, publication, and hydration.
10. **Default profile is a compatibility boundary, not a magic ID.** The catalog-defined default maps to legacy storage.
11. **Profile activation is a projection transaction.** Validate target -> activate -> refresh profile-dependent projection -> report success.
12. **Fail closed on persistence.** Candidate state becomes visible only after the owning persistence call succeeds.
13. **Presentation differences stay at the presentation seam.** Focus/scroll/reveal policy may inspect interaction context; clipboard, catalog, persistence, and command semantics may not fork by modality.
14. **Profile attribution is privacy-bounded.** Traces/events may carry opaque initiating profile ID and semantic action metadata, but not prompt bodies or profile display names.

## Domain vocabulary

### Interaction records

- **InteractionModality** — `pointer` or `keyboard` for this prototype; invocation-only.
- **InteractionSource** — semantic UI origin such as `prompt-control`, `favorite-shortcut`, or `profile-switcher`.
- **InteractionContext** — immutable `{source, modality, profileId}` snapshot created before command dispatch.
- **PresentationPlan** — adapter-level decision about reveal/focus recovery; never changes terminal command semantics.
- **CapabilityParity** — essential action reachable through visible pointer and keyboard-operable surfaces.

### Profile records and owners

- **PromptProfile** — stable identity `{id, name, isDefault}` that scopes selected durable preferences.
- **ProfileCatalog** — validates profiles, owns exactly one default, resolves target identity.
- **ActiveProfile** — session owner of currently assumed profile ID.
- **MemoryProfilePreferenceStore / production ProfilePreferenceStore** — persistence namespace boundary for Favorites.
- **BoundProfileFavoriteStore** — tiny adapter exposing canonical `FavoritePreferences`' existing `loadFavorites()/saveFavorites()` contract for one profile.
- **FavoritePreferenceContexts** — profile-to-canonical-owner selector/cache. It owns no Favorite set semantics.
- **MemoryProfileShortcutStore / production profile-aware ShortcutStore** — persistence namespace boundary for custom bindings.
- **BoundProfileShortcutStore** — one-profile adapter exposing canonical shortcut store `load()/save()` behavior.
- **ShortcutRegistryContexts** — profile-to-canonical-`ShortcutRegistry` selector/cache; hydration remains inside the canonical registry.
- **ActiveShortcutRegistry** — resolves the active canonical registry for dispatcher calls; owns no collision/binding semantics.

### Parent architecture retained

- `PromptCatalog`
- `PromptCommand`
- `CommandResult`
- `PromptKitProgramError`
- `CommandKernel`
- `SessionState`
- canonical `FavoritePreferences`
- canonical `ShortcutRegistry`
- canonical `ShortcutDispatcher`
- `ClipboardPort`
- `PromptSurfacePort`
- `UsageLedger`

## External prior-art inspection

No external code is copied and no new dependency is introduced.

### `microsoft/vscode` user-data profiles

Inspected source: `src/vs/platform/userDataProfile/common/userDataProfile.ts`.

Transferable mechanisms:
- stable default profile plus named profiles;
- profile identity separate from the resources scoped by that profile;
- resource ownership is explicit rather than represented as a cloned opaque application snapshot.

License: MIT. No implementation copied.

### `w3c/aria-practices` toolbar pattern

Inspected source: `content/patterns/toolbar/toolbar-pattern.html` and repository license.

Transferable mechanisms:
- visible grouped actions remain actual controls;
- keyboard focus management improves efficiency without replacing pointer access;
- keyboard navigation reduces friction while preserving discoverability.

License: W3C Software and Document License. No markup or implementation copied.

## Candidate designs

### Candidate A — per-entrypoint branching + global active variables

Each click/hotkey handler implements copy/focus/profile rules and reads global input/profile state.

**Benefit:** tiny initial patch.

**Failure:** domain behavior forks by caller, global modality becomes stale for hybrid users, async commands can observe the wrong profile, and storage-key conventions leak everywhere.

**Disposition:** rejected.

### Candidate B — clone the complete application state per profile

Each profile owns catalog, view/search/filter/detail, Favorites, shortcuts, and presentation state.

**Benefit:** superficially simple workspace mental model.

**Failure:** duplicates canonical prompt state, turns transient UI into durable truth without evidence, causes surprising navigation resets, and multiplies migration/invalidation surface.

**Disposition:** rejected.

### Candidate C — explicit InteractionContext + profile-scoped preference ports

Each user event snapshots `{source, modality, profileId}` before entering the existing `CommandKernel`. `PromptCatalog` and transient `SessionState` stay shared. Profile adapters bind **existing semantic preference owners** to scoped persistence. The catalog-defined default profile delegates current/legacy storage; named profiles use isolated namespaces.

**Benefits:**
- one command system;
- no global input mode;
- no duplicated prompt registry;
- no forced browsing reset;
- pointer/keyboard differences local to presentation recovery;
- canonical Favorite/Shortcut owners remain authoritative;
- async attribution is stable;
- one-profile users incur almost no visible complexity.

**Disposition:** selected and executable.

### Candidate D — persistent workspace profile including view/filter/layout

Persist and restore search/filter/layout/detail with preferences.

**Benefit:** potentially useful deep workspaces later.

**Failure at current evidence floor:** no user requirement proves that switching profile should move the user around the page. It expands persistence and invalidation risk before value is established.

**Disposition:** deferred.

## Selected module/interface map

| Module | Responsibility / owned state | Interface | Side effects | Failure contract | Test seam |
| --- | --- | --- | --- | --- | --- |
| `InteractionContextFactory` | snapshot source/modality/active profile | `create(source, modality)` | none | invalid modality/context/profile rejected before kernel | pure/trace |
| `ProfileCatalog` | available profiles + exactly one default | `require`, `defaultProfile`, `needsSwitcher` | none | `UNKNOWN_PROFILE`, invalid catalog | fixture |
| `ActiveProfile` | currently assumed profile ID | `current`, `activate` | session mutation | target validated first | component |
| existing `CommandKernel` | semantic dispatch/result normalization | `execute(command)` | through handlers only | parent contract | existing prototype |
| existing `SessionState` | transient browsing | existing transitions | session mutation | parent contract | snapshot comparison |
| profile Favorite store adapters | choose profile persistence namespace | canonical `loadFavorites/saveFavorites` | storage in production | scoped persistence error | memory/failing fake |
| canonical `FavoritePreferences` | Favorite set semantics + publish-after-save | existing `has/toggle/snapshot` | adapter persistence | candidate unpublished on fail | canonical owner fixture |
| profile shortcut store adapters | choose profile binding namespace | canonical `load/save` | storage in production | adapter failure | memory/failing fake |
| canonical `ShortcutRegistry` | binding validation/collision/publication/hydration | existing `effectiveBindings/configure` + optional initial hydration | adapter persistence | canonical `HotkeyError` | canonical owner fixture |
| `ActiveShortcutRegistry` | select registry for active profile | `effectiveBindings/configure` | none itself | delegated | profile switch fixture |
| `PromptSurfacePort` | DOM/focus/scroll/profile-dependent projection | `applyCopyPlan`, Favorite-set projection, profile projection | DOM/focus/scroll in production | presentation error stays presentation-owned | fake + later browser |
| `ClipboardPort` | clipboard terminal side effect | `writeText` | browser clipboard | classified copy failure | fake + later browser |
| `UsageLedger` | optional semantic completion | existing record/reset | local/private store if productized | degradation cannot negate completed value | memory/failing fake |

## State and data ownership

| State/data | Canonical owner | Profile-scoped? | Persistence policy |
| --- | --- | --- | --- |
| prompt records | PromptCatalog / registry builder | no | tracked registry -> generated site |
| active assumed profile | ActiveProfile | n/a | session-only in this design |
| profile definitions | ProfileCatalog | n/a | future product decision |
| search/filter/detail/current location | SessionState | no | transient |
| Favorites | canonical FavoritePreferences | yes through adapter | default compatibility + named namespace |
| custom shortcuts | canonical ShortcutRegistry | yes through adapter | scoped binding records |
| built-in shortcuts/collision policy | canonical ShortcutRegistry/ShortcutPolicy | no | code/config |
| semantic usage event | UsageLedger | event carries initiating profile ID | local/private only if enabled |
| focus/scroll/highlight | PromptSurface adapter | invocation-specific, not durable | none |
| clipboard contents | Clipboard/browser | no | external |

## Dependency direction

```text
POINTER / KEYBOARD CONTROL / HOTKEY
  -> ENTRYPOINT
  -> InteractionContextFactory
       -> ActiveProfile.current()
       -> ProfileCatalog.require(profileId)
  -> existing CommandKernel.execute(command + InteractionContext)
  -> semantic handler
       -> PromptCatalog
       -> SessionState only when journey needs reveal/navigation state
       -> canonical FavoritePreferences
            -> BoundProfileFavoriteStore -> ProfilePreferenceStore(profileId)
       -> canonical ShortcutRegistry / ShortcutDispatcher
            -> BoundProfileShortcutStore -> ShortcutStore(profileId)
       -> PromptSurfacePort(context)
       -> ClipboardPort / UsageLedger
  <- CommandResult or classified error
```

Profile activation:

```text
VISIBLE PROFILE CONTROL
  -> ProfileSwitcherEntrypoint
  -> InteractionContextFactory captures initiating context
  -> CommandKernel.execute(ACTIVATE_PROFILE target)
  -> ProfileCatalog.require(target)
  -> ActiveProfile.activate(target)
  -> canonical FavoritePreferences(target).snapshot()
  -> PromptSurface.projectFavoriteSet(target, snapshot)
  -> PromptSurface.projectProfile(target)
  <- PROFILE_ACTIVE
```

`SessionState` is deliberately absent from the profile-activation mutation chain.

## Executable prototypes and call stacks

Executable program: `docs/prompt-kit-profile-modality-prototype.js`.
Adjacent canonical shortcut seam: `docs/prompt-kit-hotkey-prototype.js`.

The prototype imports the merged program architecture and canonical hotkey classes. External browser/storage boundaries are faked; the ownership seams being evaluated are not faked.

### Pointer visible Copy

**Terminal value:** canonical prompt text on clipboard.

```text
CLICK VISIBLE COPY                                       [ENTRYPOINT]
  -> PromptControlEntrypoint.copy(P07, pointer)
  -> InteractionContextFactory {prompt-control,pointer,profile}
  -> CommandKernel COPY_REVEAL_PROMPT
  -> PromptCatalog.require(P07)
  -> presentation plan preserves existing pointer origin
  -> await ClipboardPort.writeText(copyContent)           [TERMINAL ACTION]
  -> UsageLedger PROMPT_COPIED(profileId)
  <- COPIED
```

### Keyboard activation of visible Copy

```text
TAB / FOCUS -> ENTER ON NATIVE COPY CONTROL              [ENTRYPOINT]
  -> same PromptControlEntrypoint
  -> InteractionContext modality=keyboard
  -> same COPY_REVEAL_PROMPT handler
  -> same ClipboardPort
  <- COPIED                                               [TERMINAL VALUE]
```

No redundant reveal/focus is required because the native Copy control is already the focus target.

### Typed favorite shortcut

```text
CONFIGURED PROMPT SHORTCUT                               [ENTRYPOINT]
  -> InteractionContext {favorite-shortcut,keyboard,profile}
  -> same COPY_REVEAL_PROMPT
  -> SessionState.revealPrompt(P07)                      [REQUIRED INTERMEDIATE]
  -> PromptSurface reveal + focus Copy                  [RECOVERY TARGET]
  -> await ClipboardPort.writeText(copyContent)          [TERMINAL ACTION]
  -> semantic completion
  <- COPIED
```

### Profile-scoped Favorite mutation

```text
TOGGLE FAVORITE IN ACTIVE WORK PROFILE
  -> command context profileId=work
  -> PromptCatalog.require(P07)
  -> FavoritePreferenceContexts selects canonical FavoritePreferences(work)
  -> canonical FavoritePreferences.toggle(P07)
  -> BoundProfileFavoriteStore.saveFavorites(candidate) [TRANSACTION]
  -> canonical owner publishes only after save
  -> PromptSurface.projectFavorite(work,P07,true)
  <- FAVORITE_CHANGED
```

### Profile-scoped shortcut configuration and dispatch

```text
CONFIGURE P95 SHORTCUT IN ACTIVE PROFILE
  -> ActiveShortcutRegistry.current()
  -> canonical ShortcutRegistry.configure(binding)
  -> ShortcutPolicy validates collision/target
  -> BoundProfileShortcutStore.save(candidate)           [TRANSACTION]
  -> canonical registry publishes userBindings
  <- CONFIGURED

TYPE P 9 5
  -> canonical ShortcutDispatcher
  -> ActiveShortcutRegistry selects active canonical registry
  -> canonical buffered-sequence precedence
  -> semantic prompt action
```

The executable prototype then switches profile and proves that the first profile's binding is absent, configures another profile, switches back, and creates fresh registry contexts to prove persisted bindings hydrate through canonical `ShortcutRegistry` policy rather than through a parallel registry implementation.

## Failure call stacks

### Invalid modality

```text
ENTRYPOINT provides unsupported modality
  -> InteractionContextFactory
  -> INVALID_INTERACTION_MODALITY
  -> kernel never starts
  -> no clipboard/storage/DOM mutation
```

### Unknown profile

```text
ACTIVATE_PROFILE(missing)
  -> ProfileCatalog.require(missing)
  -> UNKNOWN_PROFILE
  -> ActiveProfile unchanged
  -> no preference projection
```

### Favorite persistence failure

```text
canonical FavoritePreferences.toggle in work profile
  -> BoundProfileFavoriteStore.saveFavorites(candidate)
  -> PROFILE_PREFERENCE_PERSISTENCE_FAILED
  -> canonical owner keeps prior set
  -> no Favorite projection / completion event
  -> default profile untouched
```

### Shortcut persistence failure

```text
canonical ShortcutRegistry.configure in work profile
  -> BoundProfileShortcutStore.save(candidate)
  -> storage failure
  -> canonical registry transforms to PERSISTENCE_FAILED
  -> candidate userBinding not published
  -> default profile registry untouched
```

### Async copy while profile switches

```text
COPY starts with InteractionContext.profileId=default
  -> clipboard Promise pending
  -> ACTIVATE_PROFILE(work) completes
  -> original clipboard Promise resolves
  -> result / PROMPT_COPIED remain profileId=default
```

The initiating snapshot, not later global state, owns attribution.

## State model

### Profile catalog

```text
DEFAULT_ONLY
  -> named profiles introduced -> MULTI_PROFILE
MULTI_PROFILE
  -> activation changes current preference context only
```

Profile create/rename/delete is intentionally not prototyped because lifecycle semantics were not requested or evidenced.

### Active profile

```text
ACTIVE(A)
  -- ACTIVATE_PROFILE(B), valid --> ACTIVE(B) + B Favorite projection
  -- ACTIVATE_PROFILE(missing) --> ACTIVE(A) + UNKNOWN_PROFILE
```

### Interaction context

```text
USER EVENT
  -> snapshot {source, modality, current profileId}
  -> immutable through async command lifetime
  -> discard after terminal result/error
```

No interaction context is persisted.

## Tests and traces

Owning proof commands:

```text
node --check docs/prompt-kit-program-prototype.js
node --check docs/prompt-kit-hotkey-prototype.js
node --check docs/prompt-kit-profile-modality-prototype.js
node docs/prompt-kit-program-prototype.js
node docs/prompt-kit-hotkey-prototype.js
node docs/prompt-kit-profile-modality-prototype.js
python -m unittest tests.test_prompt_kit_program_prototype -v
python -m unittest tests.test_prompt_kit_profile_modality_prototype -v
python -m unittest tests.test_prompt_kit_hotkey_completion -v
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
```

The JSON report exposes PASS markers for:
- all four requested archetypes;
- pointer/keyboard terminal copy convergence;
- keyboard shortcut reveal/focus recovery;
- catalog-defined default legacy compatibility;
- canonical Favorite owner reuse;
- Favorite isolation and active projection refresh;
- canonical ShortcutRegistry isolation, dispatch, rehydration, and persistence failure;
- invalid modality and unknown profile rejection;
- in-flight profile snapshot attribution;
- privacy-bounded traces.

Traces record layer, semantic event, opaque profile ID, prompt ID where needed, source/modality, and counts. They intentionally omit prompt body text and profile display names.

## Productivity feature admission

Future feature proposals should answer these before a build sprint:

1. What is the terminal user value?
2. What visible pointer path reaches it?
3. What keyboard-operable path reaches it?
4. Is any shortcut merely an accelerator of that visible capability?
5. Is state canonical catalog data, transient session state, or profile-scoped durable preference?
6. Who is the one semantic owner?
7. Which external side effects require ports/adapters?
8. What consequential failure path leaves truthful state?
9. Does the one-profile/default user retain existing behavior/storage?
10. Does profile switching leave unrelated transient browsing untouched?
11. What semantic completion event, if any, is justified and privacy-bounded?
12. What can repository CI prove, and what still requires a browser/operator?

## Feature shortlist after this design session

### Admit next: profile-specific Favorite + shortcut worksets

This directly advances prompt retrieval productivity for users who assume different contexts while reusing existing preference owners.

Safe boundary:
- default-only compatibility first;
- then named profile activation;
- only Favorites/custom shortcuts scoped initially;
- prompt catalog and transient browsing stay shared;
- no full profile CRUD or workspace restore in the first build.

### Admit later: universal Actions surface as a projection

A visible Actions control could project the same semantic command catalog for pointer users while a keyboard accelerator opens that same surface. It must never become a second command registry.

### Defer: profile-specific search/filter/layout restoration

There is no current evidence that a profile switch should reposition the user or restore an old view. Persisting it now would blur transient and durable state.

### Defer: recommendations/gameplay from usage

`UsageLedger` remains optional/local/private. Recommendation or gameplay behavior should wait until retention, reset, privacy, and user-control semantics are explicitly productized.

## Second-pass architecture critique and reconciliation

Executable proof and PR review materially changed the first design. Findings are retained here rather than disappearing after repair.

1. **Invocation modality beats durable user mode.** A user can alternate pointer and keyboard between consecutive actions. The design removed any reason for global input-mode state.
2. **Shortcut recovery should not become universal focus behavior.** Typed shortcut reveal/focus is useful; clicking or pressing Enter on an already-targeted Copy control should not bounce focus elsewhere.
3. **Profile is not whole-app snapshot.** Only evidenced durable preferences are scoped; catalog and transient browsing remain shared.
4. **Default role must not be a magic ID.** First prototype incorrectly hard-coded `default` in persistence selection while `ProfileCatalog` allowed another ID to be marked default. Repair: the store receives `ProfileCatalog.defaultProfile().id`; the one-profile executable fixture uses `solo` to prove compatibility is role-based.
5. **Do not prototype a second Favorite authority.** Automated review correctly found that the first `ProfiledFavoritePreferences` duplicated set semantics. Repair: it was removed. `FavoritePreferenceContexts` only selects a bound store and instantiates canonical `FavoritePreferences`.
6. **Shortcut scoping needs an actual canonical registry journey.** Running the hotkey prototype beside the profile prototype did not prove scoped persistence. Repair: canonical `ShortcutRegistry` gained bounded initial-binding hydration and is now exercised through configure, `ShortcutDispatcher`, profile switch, rehydration, and failed persistence.
7. **Profile activation must refresh dependent projection.** Merely changing `ActiveProfile` could leave stale Favorite stars. Repair: activation snapshots canonical target-profile Favorites and replaces the active Favorite projection before `PROFILE_ACTIVE` returns.
8. **Async work must retain initiating profile.** Completion attribution reads immutable `InteractionContext`, not current profile at completion.
9. **Semantic traces stay privacy-bounded.** Opaque profile IDs are sufficient for attribution; profile display names and prompt bodies remain outside trace payloads.
10. **Do not persist last active profile yet.** Session-only activation proves architecture without inventing resume semantics.

After these repairs, no safe bounded design improvement remains without crossing into broad production implementation or inventing profile lifecycle requirements.

## Exact implementation seam ready for the next build sprint

The next production build should be narrower than “add profiles everywhere”:

1. add one production `PromptProfileContext` / `InteractionContextFactory` near the existing Prompt Kit runtime;
2. ship **default-only compatibility first** — one implicit default profile, no new switcher UI, no visible behavior change;
3. route current Favorite persistence through a profile-aware adapter whose catalog-defined default delegates the existing storage contract;
4. route current custom shortcut persistence through a profile-aware adapter and hydrate the existing `ShortcutRegistry` through the proved seam;
5. stamp semantic commands with `{source, modality, profileId}` at entrypoint boundaries; never create global modality state;
6. keep `PromptCatalog` and `SessionState` ownership unchanged;
7. prove default compatibility and scoped failure isolation against current production storage before exposing named profiles;
8. add named profile activation plus one visible native keyboard-operable profile control;
9. on activation, refresh all profile-dependent projections before success;
10. reuse existing `CommandKernel`, canonical `FavoritePreferences`, canonical `ShortcutRegistry`, `ShortcutDispatcher`, and PromptSurface owners.

Broad profile management CRUD/import/export, profile-specific layouts/search, dashboards, recommendations, and telemetry productization are outside that implementation seam.

## Unresolved decisions

These are intentionally not guessed:

- whether profiles can be created/renamed/deleted inside Prompt Kit or arrive through predefined/imported configuration;
- whether last active profile persists across browser sessions;
- whether any preference beyond Favorites and configured shortcuts becomes profile-scoped;
- whether a future profile switch should restore a saved search/filter/layout workspace;
- exact profile-switcher placement and responsive treatment;
- whether usage history, if productized, is global, profile-partitioned, or disabled by default.

None blocks the proved program seam.

## Proof ceiling

Repository/Node/Python/CI can prove:
- one semantic copy command for pointer and keyboard entrypoints;
- invocation-only modality context;
- default-only and multi-profile ownership;
- role-based default legacy compatibility;
- canonical `FavoritePreferences` reuse, isolation, publish-after-save failure behavior, and profile activation projection refresh;
- canonical `ShortcutRegistry` validation, scoped persistence, `ShortcutDispatcher` dispatch, rehydration, and failure isolation;
- shared prompt catalog and transient `SessionState`;
- initiating-profile attribution across async profile switching;
- privacy-bounded trace payloads;
- compatibility with parent program/hotkey prototypes and canonical generated-site parity.

It cannot prove:
- real-browser focus/scroll geometry;
- mouse, touch, screen-reader, switch-device, or keyboard-layout ergonomics;
- migration against a user's actual existing browser storage;
- subjective productivity improvement;
- ideal profile-switcher placement;
- production behavior until a later build sprint wires these seams into `docs/prompt-kit*.js` and the canonical generated site.

Those are browser/product/runtime gates, not reasons to duplicate the architecture now.
