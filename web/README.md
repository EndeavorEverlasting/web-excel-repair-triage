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
- closed prompt detail and reference surfaces;
- the top of the page.

It does not reload the browser or create a second filter state.

### Prompt card interaction contract

- **Single-click/tap** a prompt card to copy that prompt to the clipboard.
- **Double-click** a prompt card to expand the full prompt detail on desktop.
- **Open** explicitly expands prompt detail and is always exposed for mobile/coarse-pointer users.
- **Click outside** an open prompt detail to collapse it and return focus to the originating prompt card without clearing search or filters.
- **Enter** expands a focused prompt card; **Space** copies it.
- Explicit **Copy** controls remain available on cards and inside prompt detail.
- **Esc** closes an open prompt detail before falling back to broader filter clearing.

A short click-delay continues to distinguish desktop single-click from double-click. Mobile users never need to rely on double-tap timing because **Open** is explicit. Prompt cards are semantic groups containing explicit Open/Copy buttons rather than button containers with nested buttons.

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

### Mobile layout contract

Mobile is a responsive form of the existing Prompt Kit, not a second application.

- The header becomes a compact stacked layout rather than a tall sticky surface.
- Library, category, and type controls keep their existing semantics and become horizontally scrollable touch rails where needed.
- Prompt cards render in one column.
- **Open** and **Copy** are visible, touch-sized actions on coarse-pointer devices, including wide touch tablets.
- Prompt detail uses the available mobile viewport and keeps the existing close/copy behavior.
- The existing reference panel expands to the mobile viewport.
- Search uses a touch-sized control and avoids mobile browser zoom caused by undersized input text.
- The floating reference control remains reachable.
- Prompt display fields are escaped before insertion into rendered card/detail HTML.

### Distributed page navigation

Every visible prompt category divider exposes:

- **Top** on the left, linked to `#page-top`.
- **Bottom** on the right, linked to `#page-bottom`.

These remain touch-usable and do not reset library view, category, type, or search state.

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
python tests\test_prompt_kit_header_contract.py
python -m unittest tests.test_prompt_kit_product_interactions -v
python -m unittest tests.test_prompt_kit_filtering_access -v
python -m unittest tests.test_prompt_kit_mobile -v
python scripts\validate_prompt_kit_interactions.py --require-implementation --output Outputs\prompt-kit-interaction-audit.json --summary
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
```

Repository validation does not substitute for physical phone/tablet touch acceptance or a Windows field run of the quick launcher.
