# Web Interfaces

## Prompt Kit Control Panel

**Canonical access guide:** [`../PROMPT_KIT_ACCESS.md`](../PROMPT_KIT_ACCESS.md)

**Operator guide and tutorials:** [`../docs/PROMPT_KIT_OPERATOR_GUIDE.md`](../docs/PROMPT_KIT_OPERATOR_GUIDE.md)

The fastest normal Windows path is `Open-Latest-PromptKit.cmd`. It finds or creates a safe canonical checkout, syncs `main`, validates exact Prompt Kit parity, generates a portable runtime artifact, and opens the stable origin `http://127.0.0.1:8765/` without a configuration dialog.

The stable origin preserves the browser's Favorites storage across repository and website upgrades. The generated runtime artifact and hash receipt are written to:

```text
Outputs/prompt-kit-portable/index.html
Outputs/prompt-kit-portable/manifest.json
```

`Acquire-Latest-PromptKit.cmd` remains the advanced technician GUI when a destination or generator surface must be selected manually.

The canonical tracked release artifact remains `web/prompt-kit/index.html`. Opening that file directly is useful for static inspection, while the supported Windows portable path supplies stable-origin persistence and Favorites transfer controls without modifying the tracked site. Browser and phone users may continue to use the public GitHub Pages surfaces documented in `PROMPT_KIT_ACCESS.md`.

### Home / reset control

The **AI Harness Prompt Kit** title/logo is the stable return-to-home action on desktop and mobile.

Activating it by pointer, tap, Enter, or Space restores:

- All prompts;
- All Categories;
- All Types;
- empty search;
- every prompt category expanded;
- closed prompt detail and reference surfaces;
- the top of the page.

It does not reload the browser or create a second filter state. Saved Favorites are intentionally preserved because they belong to user state, not temporary filter state.

### Prompt card interaction contract

- **Single-click/tap** a prompt card to copy that prompt to the clipboard.
- **Double-click** a prompt card to expand the full prompt detail on desktop.
- **Open** explicitly expands prompt detail and is always exposed for mobile/coarse-pointer users.
- **Click outside** an open prompt detail to collapse it and return focus to the originating prompt card without clearing search or filters.
- **Enter** expands a focused prompt card; **Space** copies it.
- Explicit **Copy** controls remain available on cards and inside prompt detail.
- The **star** control saves or removes that prompt from Favorites without triggering copy/open.
- **Esc** closes an open prompt detail before falling back to broader filter clearing.

A short click-delay continues to distinguish desktop single-click from double-click. Mobile users never need to rely on double-tap timing because **Open** is explicit. Prompt cards are semantic groups containing explicit Favorite/Open/Copy buttons rather than button containers with nested buttons. The generated site also includes the current non-overlapping action rail and green clipboard confirmation owned by `docs/prompt-kit-polish.js`.

### Guided prompt tutorial

Use the glowing **Tutorial · Find My Prompt** control when the correct prompt is not obvious. The current browser questionnaire asks exactly four questions, uses the same registry/search/synonym ranking functions as the normal search box, and returns one primary recommendation with no more than two additional candidates. Its behavior is owned by `docs/prompt-kit-guided-recommendations.js`; it does not create a second prompt database or private routing table.

For the full current workflow—including the direct **P83** path when another agent claims work is complete—see [`../docs/PROMPT_FINDER_QUESTIONNAIRE_TUTORIAL.md`](../docs/PROMPT_FINDER_QUESTIONNAIRE_TUTORIAL.md) and [`../docs/PROMPT_KIT_OPERATOR_GUIDE.md`](../docs/PROMPT_KIT_OPERATOR_GUIDE.md).

### Five-tab named profiles

The top rail exposes five persistent keyboard slots, `A` through `E`. Every slot can be renamed and assigned the built-in All, Standard, Favorites, or Doctrine view, or a custom union of profile packs from the Hotkeys panel. Defaults are **All / Standard / Favorites / SAS / PM**; SAS selects the SAS pack, while PM composes PM + FUN + TRIAGE + H&H. Built-in packs also include CYBERSEC, AGENTIC LOOPING, GNHF, Gardening, and Future Projects. Doctrine is a dedicated view mode rather than a prompt-filter pack, so assigning it to a slot opens the canonical Doctrine renderer instead of filtering the normal prompt list.

Imported profile packs use `prompt-kit-profile-import/v1` JSON and pass a bounded parse → validate → compile evaluator. Imports are data only: JavaScript `eval`, `Function`, and `new Function` are not used. The runtime caps import size, pack count, installed pack count, rule nodes/depth, matcher length, and packs selected per tab, and rejects malformed or unknown operators before persistence. See `docs/PROMPT_KIT_FIVE_TAB_PROFILES.md`.

### Category and type filtering

There are three separate browsing layers:

1. **Profile tab:** five configurable slots A–E, defaulting to All / Standard / Favorites / SAS / PM.
2. **Category:** All Categories, Foundation, Discover & Plan, Build & Repair, Validate & Protect, Integrate & Ship, or Autonomy & Night Shift.
3. **Type:** All Types or one concrete prompt type.

Category behavior is deterministic:

- **All Categories** renders every category with matching prompts exactly once.
- Every category contains only prompts mapped to that category.
- Prompts are sorted by numeric prompt sequence inside the category, even when prompt IDs skip numbers.
- Selecting one category renders only that category heading and matching prompts.
- Selecting a type may further narrow results; the remaining category heading is still shown.
- Search, library-view, category, and type filters compose without duplicate category headings.

### Search relevance contract

Search is relevance-ranked rather than a raw full-text dump.

- Prompt ID, prompt name, canonical keywords, `SYNONYMS`, type, and `When To Use` metadata are stronger signals than full prompt-body text.
- Existing synonym routing remains active. Partial terms may resolve a related canonical synonym key, such as `close` matching `closeout`.
- Full `copyContent` remains searchable as a low-signal fallback, but copy-body-only matches are suppressed when stronger metadata or synonym matches exist.
- Within a visible section, stronger search matches sort ahead of weaker matches; numeric prompt sequence remains the tiebreaker.
- Search still composes with library, category, and type filters.

This specifically prevents common policy words such as `artifact` from making nearly every prompt appear merely because that word exists in shared prompt boilerplate.

### Portable Favorites

The current browser stores Favorites under `promptKit.favoritePromptIds.v1`. The Windows portable launcher keeps that storage under the stable loopback origin `http://127.0.0.1:8765/`, so ordinary Prompt Kit upgrades retain the saved collection automatically.

- Select the star on any prompt card to save or remove it.
- Favorites remain in the normal chronological/numeric library order by default; saving a Favorite does not promote that prompt ahead of the ordinary library.
- Use the explicit **Favorites** profile tab or press **C** to show the complete saved Favorites collection.
- A favorited prompt still renders once; Favorites are stored user state, not a second prompt registry.
- **Export Favorites** downloads a portable JSON backup using schema `prompt-kit-favorites/v1`.
- **Import Favorites** validates, normalizes, deduplicates, and merges a backup without deleting Favorites already saved in the current browser.
- Legacy browser keys and legacy array backups are merged into current Favorites rather than being skipped when current Favorites already exist.
- Well-formed prompt IDs missing from the current release remain preserved so a future release can restore them automatically.
- Malformed IDs are rejected or removed from stored portable state.
- Imports are capped at 64 KiB, reject unsupported schemas, and never execute imported content.

For an ordinary Windows upgrade, run `Open-Latest-PromptKit.cmd` again. The launcher validates and refreshes the repository, rebuilds the portable artifact, records SHA-256 evidence, disables browser caching, reuses the stable origin, and opens the new version.

Use Export Favorites before clearing browser data, moving to another browser profile, changing devices, or abandoning the old origin. Use Import Favorites from the supported portable site to restore the same collection.

Implementation ownership:

- base Favorites state: `docs/prompt-kit.js`;
- transfer runtime: `docs/prompt-kit-favorites-portability.js`;
- stable-origin builder/server: `scripts/serve_prompt_kit_portable.py`;
- portable acquisition/open launcher: `scripts/Open-LatestPromptKitPortable.ps1`;
- Windows entry point: `Open-Latest-PromptKit.cmd`;
- machine policy: `harness/contracts/prompt-kit-portability.v1.json`;
- human contract: `docs/PROMPT_KIT_PORTABILITY.md`.

The runtime generator reads the exact tracked `web/prompt-kit/index.html`, injects the tracked portability runtime into a gitignored artifact, and leaves the canonical site untouched.

### Collapsible category sections

Every rendered category divider is also an independent expand/collapse control, matching the familiar GitHub disclosure pattern.

- Categories start expanded.
- Select the category name/chevron to collapse or expand only that category.
- **Top** and **Bottom** remain separate controls and never toggle the category.
- Collapse state survives search, library, category, and type rerenders during the current page session.
- The prompt count remains visible while collapsed so the hidden scope is still obvious.
- The toggle uses a native button with `aria-expanded`, so pointer, touch, Enter, and Space work without custom keyboard logic.
- Section-toggle foreground color is explicitly defined for the dark surface; browser-default button text color must never leak through.
- Activating the main title/reset expands every category again.

Base interaction ownership stays in `docs/prompt-kit.js`; guided recommendations and polish stay in their supplemental tracked runtimes; portable Favorites behavior is isolated in `docs/prompt-kit-favorites-portability.js`. `web/prompt-kit/index.html` remains canonical generated output and must not be hand-edited.

### Mobile layout contract

Mobile is a responsive form of the existing Prompt Kit, not a second application.

- The header becomes a compact stacked layout rather than a tall sticky surface.
- Library, category, and type controls keep their existing semantics and become horizontally scrollable touch rails where needed.
- Prompt cards render in one column.
- Category expand/collapse remains explicit and touch-sized.
- Favorite, **Open**, and **Copy** actions remain directly reachable; **Export Favorites** and **Import Favorites** are also touch-sized when the portable runtime is served.
- Prompt detail uses the available mobile viewport and keeps the existing close/copy behavior.
- The existing reference panel expands to the mobile viewport.
- Search uses a touch-sized control and avoids mobile browser zoom caused by undersized input text.
- The floating reference control remains reachable.
- Prompt display fields are escaped before insertion into rendered card/detail HTML.

### Distributed page navigation

Every visible prompt category divider exposes:

- **Top** on the left, linked to `#page-top`.
- **Bottom** on the right, linked to `#page-bottom`.

These remain touch-usable and do not reset library view, category, type, search state, Favorites state, or category collapse state.

### Hotkeys

The glowing **Hotkeys** module beside the floating reference control is the in-product shortcut reference, five-tab profile editor, profile-pack importer, and favorite-prompt shortcut configurator. Select it or press the unmodified **backtick** key (`` ` ``) to toggle it; select outside it, use its close control, or press **Esc** to dismiss it. The five header identities are always `A`–`E`; their visible names and profile compositions are user configuration. Numeric keys are not header navigation, and no header key uses `P`, so configured prompt sequences such as `P111` retain the digit stream.

| Key | Action |
|---|---|
| `` ` `` | Show / hide Hotkeys |
| `/` | Focus search |
| `A` | All |
| `B` | Standard |
| `C` | Favorites |
| `D` | SAS |
| `E` | PM |
| `R` | Toggle reference panel |
| `F` | Show / hide filters |
| `[` | Hide filters |
| `]` | Show filters |
| `Home` | Scroll to top |
| `End` | Scroll to bottom |
| `Esc` | Close the active surface or clear filters |

Favorite-prompt shortcuts are configured from the Hotkeys panel. Favorite a prompt first, enter its canonical ID such as `P95`, and save it; the persisted binding is then the lower-case prompt ID (`p95`). Typed prompt sequences expire after 1.2 seconds and are ignored in editable fields. If one configured ID prefixes another, the shorter exact match waits for that boundary and continued typing selects the longer exact ID. Dots may be typed as separators inside an active sequence (`p1.1` → `P11`, `p1.11` → `P111`). Completing a configured sequence clears the transient restrictions needed to reveal the target, scrolls the canonical prompt card into view, and copies the canonical prompt through the normal copy path **without opening prompt detail**. The Hotkeys panel labels configured rows as **Copy + reveal P##**.

A configured shortcut is rejected when its target is unknown or not currently a Favorite. Shortcut storage uses the versioned key `promptKit.promptShortcuts.v1` and publishes an in-memory binding only after the browser storage write succeeds. Once a configured prompt sequence buffer is active, it owns the following digits. Numeric keys have no header-navigation meaning, so `P111` and other configured prompt IDs cannot fall through into a tab command.

Registry prompts may additionally publish a **recommended shortcut** by shipping `sharedShortcut: true` in their canonical registry record (currently `P95`). Recommended sequences are the lowercase prompt ID, are active for every user without favoriting, use the same copy + reveal path, and appear in the Hotkeys panel labeled **Recommended** without a Remove control because the registry owns them. Personal bindings and built-ins keep precedence, and configuring or removing a personal binding still requires the Favorite gate and a durable storage write.

Navigation shortcuts are ignored while typing in an input, textarea, select, or content-editable surface. Modified backtick chords are ignored. Top/bottom scrolling respects reduced-motion preferences.

### Header navigation contract

The five visible profile slots have stable letter identities: `A` All, `B` Standard, `C` Favorites, `D` SAS, and `E` PM by default. Their labels/profile packs may be customized without changing those key identities. Header navigation has no numeric shortcuts and does not reserve `P`, leaving digit-bearing prompt sequences such as `p11`, `p13`, and `p111` exclusively to the prompt shortcut dispatcher.

### Validation

The owning `Prompt Kit web contracts` workflow compiles and runs `tests/test_prompt_kit_hotkey_completion.py`; shortcut changes must keep that focused contract green in addition to the broader interaction, discovery, ordering, filtering, mobile, portability, and generated-parity gates. Operator-documentation assertions live in the existing `tests/test_prompt_kit_discovery.py` discovery owner.

```powershell
node --check docs\prompt-kit.js
node --check docs\prompt-kit-guided-recommendations.js
node --check docs\prompt-kit-polish.js
node --check docs\prompt-kit-favorites-portability.js
python scripts\serve_prompt_kit_portable.py --build-only
python scripts\validate_prompt_kit_portability.py --require-artifact --output Outputs\prompt-kit-portability-validation.json --summary
python -m unittest tests.test_prompt_kit_portability tests.test_prompt_kit_portability_regressions tests.test_prompt_kit_portable_health tests.test_prompt_library_portability -v
python tests\test_prompt_kit_header_contract.py
python -m unittest tests.test_prompt_kit_product_interactions -v
python -m unittest tests.test_prompt_kit_filtering_access -v
python -m unittest tests.test_prompt_kit_mobile -v
python -m unittest tests.test_prompt_kit_discovery tests.test_prompt_kit_guidance -v
python -m unittest tests.test_prompt_kit_hotkey_completion -v
python scripts\validate_prompt_kit_interactions.py --require-implementation --output Outputs\prompt-kit-interaction-audit.json --summary
python scripts\validate_prompt_kit_discovery.py --summary
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
```

Repository validation does not substitute for physical browser download/file-picker behavior, browser-profile transfer, cross-device acceptance, phone/tablet touch acceptance, clipboard permissions in every browser, live Pages publication, or a Windows field run of the quick launcher.

### External resources

The **Resources** control uses `docs/prompt-kit-external-resources.js` and lazily fetches the compact `prompt-kit/resources.v1.json` sidecar only after the user opens it. Donor skill bodies are never embedded in the main generated page; results are paged and existing Operant prompt coverage is preferred before upstream links.
