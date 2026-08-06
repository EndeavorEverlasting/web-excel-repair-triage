# Web Interfaces

## Prompt Kit Control Panel

**Canonical access guide:** [`../PROMPT_KIT_ACCESS.md`](../PROMPT_KIT_ACCESS.md)

The fastest normal Windows path is `Open-Latest-PromptKit.cmd`: it finds or creates a safe canonical checkout, syncs `main`, validates exact Prompt Kit parity, and opens the website without a configuration dialog.

`Acquire-Latest-PromptKit.cmd` remains the advanced technician GUI when a destination or generator surface must be selected manually.

From an existing validated checkout, open the deployed operator surface from the repository root:

```powershell
start web\prompt-kit\index.html
```

Canonical release artifact: `web/prompt-kit/index.html`.

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

A short click-delay continues to distinguish desktop single-click from double-click. Mobile users never need to rely on double-tap timing because **Open** is explicit. Prompt cards are semantic groups containing explicit Favorite/Open/Copy buttons rather than button containers with nested buttons.

### Category and type filtering

There are three separate browsing layers:

1. **Library view:** All / Standard / GNHF / Doctrine.
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

The current browser continues to store Favorites under `promptKit.favoritePromptIds.v1`, but that local storage is no longer the only preservation mechanism.

- Select the star on any prompt card to save or remove it.
- Visible favorited prompts are promoted into one **Favorites** section before the normal sections.
- A favorited prompt appears only once during a render.
- Active library/category/type/search filters still apply before Favorites are promoted.
- **Export Favorites** downloads a portable JSON backup using schema `prompt-kit-favorites/v1`.
- **Import Favorites** validates, normalizes, deduplicates, and merges a backup without deleting Favorites already saved in the current browser.
- Legacy array backups remain accepted.
- Prompt IDs missing from the current release remain preserved in storage so a future release can restore them automatically.
- Imports are capped at 64 KiB, reject unsupported schemas and malformed IDs, and never execute imported content.

Use export before replacing a local site copy, clearing browser data, moving to another browser profile, or moving to another device. Open the upgraded Prompt Kit and use import to restore the same collection.

The editable runtime is `docs/prompt-kit-favorites-portability.js`. The canonical registry builder embeds that runtime into the standalone `web/prompt-kit/index.html`; generated HTML must not be hand-edited.

The machine-readable policy is `harness/contracts/prompt-kit-portability.v1.json`, and the human-readable contract is `docs/PROMPT_KIT_PORTABILITY.md`.

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

Implementation ownership stays in `docs/prompt-kit.js`; portable Favorites behavior is isolated in `docs/prompt-kit-favorites-portability.js`. `web/prompt-kit/index.html` is regenerated output and must not be hand-edited.

### Mobile layout contract

Mobile is a responsive form of the existing Prompt Kit, not a second application.

- The header becomes a compact stacked layout rather than a tall sticky surface.
- Library, category, and type controls keep their existing semantics and become horizontally scrollable touch rails where needed.
- Prompt cards render in one column.
- Category expand/collapse remains explicit and touch-sized.
- Favorite, **Open**, **Copy**, **Export Favorites**, and **Import Favorites** actions remain directly reachable on coarse-pointer devices.
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

| Key | Action |
|---|---|
| `/` | Focus search |
| `1` | All prompts |
| `2` | Standard prompts |
| `3` | GNHF prompts |
| `4` | Doctrine |
| `R` | Toggle reference panel |
| `Esc` | Close the active surface or clear filters |

### Header navigation contract

The first three library-view filters are fixed and ordered:

1. All
2. Standard
3. GNHF

Their keyboard shortcuts are `1`, `2`, and `3` respectively. Doctrine may use shortcut `4`, but it must never displace GNHF.

### Validation

```powershell
node --check docs\prompt-kit.js
node --check docs\prompt-kit-favorites-portability.js
python tests\test_prompt_kit_header_contract.py
python -m unittest tests.test_prompt_kit_product_interactions -v
python -m unittest tests.test_prompt_kit_filtering_access -v
python -m unittest tests.test_prompt_kit_mobile -v
python -m unittest tests.test_prompt_kit_discovery -v
python -m unittest tests.test_prompt_kit_portability -v
python scripts\validate_prompt_kit_interactions.py --require-implementation --output Outputs\prompt-kit-interaction-audit.json --summary
python scripts\validate_prompt_kit_discovery.py --summary
python scripts\validate_prompt_kit_portability.py --summary
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
```

Repository validation does not substitute for physical phone/tablet touch acceptance, browser download/file-picker policy restrictions, cross-device transfer, or a Windows field run of the quick launcher.
