# Sprint Plan: Fix Prompt Kit Website

## Problem

`C:\Users\Cheex\Desktop\dev\Web Excel Triage\web\prompt-kit\index.html` (899 lines) is corrupted. Multiple `renderDoctrineList` functions, a mangled line 503 (`render();showToast('Searching for '+name)}`), and duplicate JS blocks prevent the page from rendering. The AgentSwitchboard version at `docs\prompt-kit.html` has similar corruption from incremental rebuild scripts.

## Root Cause

Previous sessions used Python scripts that did string-replace surgery on the HTML. Each rebuild inserted overlapping code blocks, creating duplicate functions and orphaned fragments that break JS parsing.

## Fix Strategy

**One clean rebuild. One script. One output file.**

Write a single Python script (`build_prompt_kit.py`) that reads `docs/prompts.json` and `docs/reference.json`, generates the entire HTML file from scratch (CSS + JS + data + doctrine), and writes it to `web/prompt-kit/index.html`. No incremental patching. The script becomes the canonical build path.

## Files to Create/Modify

| File | Action | Purpose |
|---|---|---|
| `build_prompt_kit.py` | Create | Single-source build script |
| `web/prompt-kit/index.html` | Regenerate | Clean output from build script |
| `docs/prompt-kit.html` | Sync | Copy from triage repo output |

## Deliverables

1. **`build_prompt_kit.py`** — reads prompts.json, reference.json, reads HARNESS.md for doctrine, generates complete self-contained HTML
2. **`web/prompt-kit/index.html`** — clean file with working:
   - Category tabs (All / Standard / GNHF / Doctrine) + keyboard 1-4
   - Section nav with glowing dividers
   - Type filter chips with color dots
   - Search with synonym matching + keyword matching
   - Copy-to-clipboard on each card
   - Reference sidebar (toggle with R)
   - Doctrine tab (4 doctrine cards, expandable)
   - Mobile responsive
   - Keyboard shortcuts: `/` search, `1-4` tabs, `R` ref panel, `Esc` cascade

## Validation

1. Open `web/prompt-kit/index.html` in browser — 58 prompts render
2. Press `2` — Standard tab shows 34 prompts
3. Press `3` — GNHF tab shows 24 prompts
4. Press `4` — Doctrine tab shows 4 cards
5. Type "doctrine" in search — P00 and P01 appear
6. Type "night shift" — GNHF prompts appear
7. Click copy button — clipboard receives prompt text
8. Press `R` — reference sidebar opens
9. Resize to mobile width — single column layout

## Commit

```
fix(prompt-kit): clean rebuild from single build script

- Replace corrupted HTML with clean output from build_prompt_kit.py
- All 58 prompts render, hotkeys work, search works, doctrine tab works
- Sync docs/prompt-kit.html from triage repo
```
