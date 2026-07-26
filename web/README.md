# Web Interfaces

## Prompt Kit Control Panel

**Canonical access guide:** [`../PROMPT_KIT_ACCESS.md`](../PROMPT_KIT_ACCESS.md)

The fastest Windows path is `Acquire-Latest-PromptKit.cmd`: it clones or safely fast-forwards canonical `main`, validates the exact site, and opens it.

From an existing validated checkout, open the deployed operator surface from the repository root:

```powershell
start web\prompt-kit\index.html
```

Canonical release artifact: `web/prompt-kit/index.html`.

### Prompt card interaction contract

- **Single click** a prompt card to copy that prompt to the clipboard.
- **Double-click** a prompt card to expand the full prompt detail.
- **Click outside** an open prompt detail to collapse it and return focus to the originating prompt card without clearing the current search or filters.
- **Enter** expands a focused prompt card; **Space** copies it.
- The explicit **Copy** buttons remain available on cards and inside prompt detail.
- **Esc** closes an open prompt detail before falling back to the broader filter-clearing behavior.

A short click-delay distinguishes a single click from a double-click so the double-click gesture does not leave duplicate copy actions behind.

### Category and type filtering

There are three separate browsing layers:

1. **Library view:** All / Standard / GNHF / Doctrine.
2. **Category:** All Categories, Foundation, Discover & Plan, Build & Repair, Validate & Protect, Integrate & Ship, or Autonomy & Night Shift.
3. **Type:** All Types or one concrete prompt type.

Category behavior is deterministic:

- **All Categories** renders every category that has matching prompts exactly once.
- Every category contains only prompts mapped to that category.
- Prompts are sorted by numeric prompt sequence inside the category, even when prompt IDs skip numbers.
- Selecting one category renders only that category heading and its matching prompts.
- Selecting a type may further narrow the results; the remaining category heading is still shown.
- Search, library-view, category, and type filters compose without creating duplicate category headings.

### Distributed page navigation

Every visible prompt category divider exposes:

- **Top** on the left, linked to the canonical `#page-top` target.
- **Bottom** on the right, linked to the canonical `#page-bottom` target.

These are same-document anchors. They do not reset the current library view, category, type, or search state.

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
python scripts\validate_prompt_kit_interactions.py --require-implementation --output Outputs\prompt-kit-interaction-audit.json --summary
python scripts\build_prompt_kit_registry.py --output web\prompt-kit\index.html --check
```
