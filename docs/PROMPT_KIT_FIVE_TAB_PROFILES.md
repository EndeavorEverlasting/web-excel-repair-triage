# Prompt Kit five-tab named profiles

## Product contract

The top Prompt Kit rail is five user-configurable slots with fixed keyboard identities `A`–`E`.
The default configuration is:

| Slot | Default name | Mode | Default packs |
| --- | --- | --- | --- |
| A | All | built-in All | — |
| B | Standard | built-in Standard | — |
| C | Favorites | built-in Favorites | — |
| D | SAS | custom packs | SAS |
| E | PM | custom packs | PM + FUN + TRIAGE + H&H |

The slot key is stable; the visible name and selected mode/packs are user configuration. A user may
rename every slot. A custom slot is the union of its selected profile packs.

Favorites and favorite prompt shortcuts retain their existing canonical owners and storage keys. This
feature changes the header/profile projection only; it does not fork Favorite semantics or create a
second prompt registry.

## Predefined packs

The runtime ships declarative packs for `TRIAGE`, `FUN`, `PM`, `CYBERSEC`, `AGENTIC_LOOPING`, `SAS`,
`GARDENING`, `H_AND_H`, and `FUTURE_PROJECTS`. Packs match prompt metadata and text fields. They are
building blocks rather than cloned prompt collections.

The default PM slot intentionally composes `PM`, `FUN`, `TRIAGE`, and `H_AND_H`. The default SAS slot
selects `SAS`.

## Safe profile evaluator

Imported profile packs are JSON data with schema `prompt-kit-profile-import/v1`. The evaluator accepts
only the following rule operators:

- `all`
- `id`
- `category`
- `type`
- `keyword`
- `text`
- `not`
- `any`
- `every`

The evaluator validates and normalizes the rule tree, then compiles it into internal predicate
functions. It never calls JavaScript `eval`, `Function`, or `new Function`, and imported strings are
never executed as code. The intended analogy to Lua `load` is the controlled
**parse → validate → compile → run** boundary, not arbitrary source execution.

## Import guardrails

The runtime fails closed at these limits:

- 32 KiB maximum JSON import
- 32 packs per import
- 64 installed imported packs
- 64 rule nodes per pack
- rule nesting depth 4
- 16 children in one `any`/`every` rule
- 120 characters per matcher string
- 40 characters per pack ID
- 64 characters per pack label
- 12 selected packs per tab
- 32 characters per tab name
- duplicate, malformed, predefined-ID-shadowing, unknown-operator, over-depth, and over-limit payloads are rejected

Imported packs and tab configuration are browser-local. Canonical prompt records remain in the tracked
Prompt Kit registries and generated artifact.

## Hotkey contract

`A` through `E` are reserved for the five profile tabs. Header navigation uses no numeric shortcut and
no header shortcut uses `P`. Digits remain available to configured prompt-ID sequences such as `P111`.
When one configured prompt ID is a prefix of another (for example `P11` and `P111`), the shorter exact
match waits for the existing 1.2-second sequence boundary; continued typing selects the longer match.
Dots are accepted only as separators inside an active prompt sequence, so `p1.1` resolves as `P11` and
`p1.11` resolves as `P111`. Page navigation uses the native pair: `Home` scrolls to the true document top and `End` scrolls to the document bottom. No letter in `A`–`E` is reused for page navigation.

## Persistence

- `promptKit.profileSlots.v1` — five tab definitions
- `promptKit.activeProfileSlot.v1` — active slot key
- `promptKit.profilePacks.v1` — validated imported packs

Invalid persisted profile data falls back to the default five-slot configuration instead of becoming
runtime authority.
