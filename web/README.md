# Web Interfaces

## Prompt Kit Control Panel

Open the exact deployed operator surface from the repository root:

```powershell
start web\prompt-kit\index.html
```

### Prompt card interaction contract

- **Single click** a prompt card to copy that prompt to the clipboard.
- **Double-click** a prompt card to expand the full prompt detail.
- **Click outside** an open prompt detail to collapse it and return focus to the originating prompt card without clearing the current search or filters.
- **Enter** expands a focused prompt card; **Space** copies it.
- The explicit **Copy** buttons remain available on cards and inside prompt detail.
- **Esc** closes an open prompt detail before falling back to the broader filter-clearing behavior.

A short click-delay distinguishes a single click from a double-click so the double-click gesture does not leave duplicate copy actions behind.

### Distributed page navigation

Every repeated prompt section divider exposes:

- **Top** on the left, linked to the canonical `#page-top` target.
- **Bottom** on the right, linked to the canonical `#page-bottom` target.

These are same-document anchors. They do not reset the current category, section, type, or search state, and any section divider that remains visible after filtering keeps both controls.

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

The first three prompt filters are fixed and ordered:

1. All
2. Standard
3. GNHF

Their keyboard shortcuts are `1`, `2`, and `3` respectively. Do not derive, rename, reorder, or replace these controls from prompt data or secondary views. Doctrine may use shortcut `4`, but it must never displace GNHF. Validate the exact deployed file at `web/prompt-kit/index.html`.

Run the focused contracts with:

```powershell
python tests\test_prompt_kit_header_contract.py
python -m unittest tests.test_prompt_kit_product_interactions -v
python scripts\validate_prompt_kit_interactions.py --require-implementation --output Outputs\prompt-kit-interaction-audit.json --summary
```
