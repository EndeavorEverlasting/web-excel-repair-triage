# Web Interfaces

## Prompt Kit Control Panel

Open the exact deployed operator surface from the repository root:

```powershell
start web\prompt-kit\index.html
```

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

Run the focused contract with:

```powershell
python tests\test_prompt_kit_header_contract.py
```
