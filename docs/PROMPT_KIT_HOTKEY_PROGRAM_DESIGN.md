# Prompt Kit hotkey program design

## Scope
This document owns the keyboard-command boundary for Prompt Kit. Production behavior extends the existing runtime in `docs/prompt-kit-polish.js`; generated HTML is never hand-edited and the responsive-layout harness is not a second keyboard implementation owner.

## Current invariants
- The canonical `PROMPTS` catalog owns prompt-number hotkeys for every prompt.
- The bare numeric identity is the primary gesture: `126` → `P126`. `p126` remains a compatibility alias.
- A prompt does not need to be a Favorite, recommended, or manually configured before its numeric hotkey works.
- Manual prompt-shortcut persistence is retired. `promptKit.promptShortcuts.v1` is not production activation authority.
- Completing a prompt-number sequence performs canonical copy + instant snap to the rendered card; it does not open prompt detail.
- Favorites remain durable organizational state only. Favoriting and unfavoriting never create or revoke the catalog hotkey.
- `sharedShortcut: true` is recommendation/discoverability metadata only; it does not authorize activation.
- Keyboard commands are suppressed in `input`, `textarea`, `select`, and content-editable surfaces and for modified chords.
- Header navigation is letter-only (`A`–`E`). Digits belong to prompt identity and never double as profile-tab commands.
- Hotkey help is a projection of effective behavior, not a second truth source.

## Domain vocabulary
- **ShortcutGesture**: a normalized key or sequence such as `f`, `[`, `]`, `126`, or compatibility form `p126`.
- **PromptTarget**: canonical prompt identity such as `P126`.
- **ShortcutRegistry**: effective built-ins plus prompt identities derived from the canonical `PROMPTS` catalog.
- **ShortcutDispatcher**: keyboard-event orchestration and transient sequence-buffer owner.
- **FilterVisibility**: sole owner of visible/hidden filter state.
- **PromptNavigator**: translation from a PromptTarget to the existing reveal/center/copy behavior.

There is no production `ShortcutStore` for prompt-number activation. Earlier persistence experiments remain historical/prototype evidence only.

## State ownership
| State | Owner | Persistence |
| --- | --- | --- |
| Built-in commands | runtime shortcut table | code |
| Prompt-number bindings | canonical `PROMPTS` catalog | generated registry |
| Typed-sequence buffer | ShortcutDispatcher | none |
| Filter visibility | FilterVisibility | none initially |
| Favorite membership | existing Favorites owner | browser Favorites storage |
| Recommended labels | canonical prompt metadata | generated registry |
| Hotkey help rows | projection of runtime/catalog + metadata | none |

Dependency direction:

`keydown → ShortcutDispatcher → catalog-derived binding resolution → semantic action → existing DOM/copy adapters`

No Favorite store, recommendation flag, generated HTML patch, or help row may become a second activation policy.

## Prompt identity behavior
Starting state: `P11`, `P13`, `P111`, and `P126` exist in the catalog. No setup is required.

- `126` resolves `P126` immediately, copies canonical `copyContent`, and snaps its card to center.
- `p126` follows the same path as a compatibility alias.
- `13` resolves `P13` immediately when no longer catalog identity shares that prefix.
- `11` is also a prefix of `111`, so the dispatcher holds the shorter exact candidate until the 1.2-second sequence boundary.
- `111` arriving before that boundary resolves `P111` and cancels the pending `P11` candidate.
- Dots are visual separators while a prompt-number buffer is active: `p1.1` follows `P11`; `p1.11` follows `P111`.
- When the prompt-number buffer is active, a nonmatching letter can settle a pending exact prompt and then continue to its normal command domain; header `A`–`E` remains independently usable.

## Failure boundaries
- **Editable target:** ignore prompt hotkeys while the user is typing in an editable surface.
- **Modified chord:** modifier-bearing input does not enter the prompt-number buffer.
- **Unknown target:** a numeric candidate without a catalog prefix performs no prompt activation.
- **Prefix ambiguity:** the shorter exact target waits for the sequence boundary; continued valid input wins.
- **Reveal failure:** do not claim success or copy a different prompt when the canonical target cannot be rendered/revealed.

## Favorites and recommendations
Favorites answer **what the user wants grouped**, not **which prompts are keyboard-addressable**. The Hotkeys panel may label Favorite and Recommended prompts for discoverability, but every canonical prompt already has its numeric route. Removing a Favorite therefore leaves its numeric hotkey available.

## Built-in command boundary
- unmodified backtick `` ` `` toggles Hotkeys and keeps the core shortcut cluster reachable with one hand;
- `/` focuses search;
- `F` toggles filters, `[` hides them, and `]` shows them;
- `Home` and `End` navigate the page;
- `A`–`E` activate the five profile slots;
- `Escape` closes/clears the active keyboard surface and resets transient prompt sequence state.

## Executable prototype status
`docs/prompt-kit-hotkey-prototype.js` remains a seam/failure-model prototype. Its historical persistence-failure simulation is intentionally prototype-only; production prompt-number activation no longer loads, saves, configures, or validates a persisted shortcut binding.

## Superseded production decisions
The following earlier decisions are explicitly superseded and must not be reintroduced:
- Favorite-authorized prompt activation;
- a Favorite prompt-ID Save field in Hotkeys;
- `promptKit.promptShortcuts.v1` as an activation store;
- requiring `p###` as the primary typed identity;
- treating `sharedShortcut` recommendation metadata as activation authority.

## Routing hook for agents
For hotkey, shortcut, keyboard navigation, Favorite shortcut, prompt-ID shortcut, or filter-key work, inspect in order:
1. this design;
2. `docs/prompt-kit-polish.js`;
3. `tests/test_prompt_kit_hotkey_completion.py` and `tests/test_prompt_kit_hotkey_identity_runtime.py`;
4. `tests/prompt_kit_hotkey_identity_browser_proof.py` and the observed-browser workflow;
5. `scripts/build_prompt_kit_registry.py` for generated-site parity;
6. interaction/cross-input contracts for collision regression evidence.

Do not create another shortcut registry or patch generated HTML directly.

## Proof contract
Completion requires all of the following on the exact candidate head:
- production source asserts catalog-derived numeric authority and contains no manual prompt-shortcut persistence/configuration path;
- focused runtime tests prove bare numeric identities, compatibility aliases, timeout/prefix behavior, editable/modifier safety, and header-domain separation;
- generated `web/prompt-kit/index.html` is rebuilt through the canonical generator and matches source;
- observed Chromium literally types bare `126` through the page keyboard path from a non-Favorite state, then verifies canonical P126 clipboard content and centered-card geometry;
- the broader interaction/discovery/cross-input validators remain green.

Repository/browser CI cannot certify every physical keyboard layout or every browser clipboard policy. Those environments remain the proof ceiling; they do not justify weakening the catalog-derived contract.

## Fixed implementation seam
Production behavior is owned in `docs/prompt-kit-polish.js`; `web/prompt-kit/index.html` is rebuilt only through `scripts/build_prompt_kit_registry.py`. New hotkeys extend the existing dispatcher/state owners rather than introducing a second keyboard registry, second filter state owner, or generated-only patch.
