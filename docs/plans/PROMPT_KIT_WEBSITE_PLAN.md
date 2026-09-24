# Prompt Kit Website - Integration & Enhancement Plan

**Created:** 2026-07-19
**Status:** Active
**Owner:** AgentSwitchboard / web-excel-repair-triage

---

## What Was Built

A self-contained dark-theme control panel (`prompt-kit.html`) for the AI Harness Prompt Kit v39. Extracted all 58 prompts from the Excel spreadsheet into a searchable, filterable, copy-ready web interface.

### Current Features
- **58 prompts** with full copy-safe text embedded as JSON
- **Category tabs** (All / Standard / GNHF) with keyboard shortcuts (1/2/3)
- **Section navigation** with color-coded tabs and glowing dividers:
  - Foundation (Slate) - SETUP, HARVEST, CLOSEOUT
  - Discover & Plan (Amber) - DISCOVERY, PLAN, PORTFOLIO, ANALYZE
  - Build & Repair (Green) - BUILD, CLEANUP, REPAIR, REVIEW
  - Validate & Protect (Teal) - VALIDATE, SAFETY, RUNTIME PROOF
  - Integrate & Ship (Indigo) - INTEGRATE, INTEROP, MAINTENANCE, ENABLEMENT
  - Autonomy & Night Shift (Violet) - AUTONOMY, RECOVER, HARNESS, GNHF
- **Type filter chips** with colored left borders matching class colors
- **Real-time search** across name, type, ID, class, use-when, sprint role, proof gate, and prompt body
- **Synonym system** - "generate artifact" finds P56, "night shift" finds P37-P44, etc.
- **Color legend** - click to filter by prompt class color
- **One-click copy** to clipboard with toast notification
- **Expandable cards** showing all prompt details + full copy-safe text
- **Reference sidebar** with Night Shift Runbook, GNHF Workflow, Variables, Hotkeys
- **Interactive sidebar** - click runbook entries to jump to prompts, click variables to search
- **Keyboard shortcuts**: `/` search, `1/2/3` tabs, `R` sidebar, `Esc` cascade (collapse -> clear -> unfilter -> reset)
- **Mobile responsive** - single-column layout, touch-friendly, no overlap/jumbling

### Architecture
- Single self-contained HTML file (~298KB)
- Zero dependencies - no frameworks, no build step
- Inline CSS + JS, data baked in as JSON
- Opens in any browser, works offline
- Event delegation for click handling (no inline onclick quote escaping issues)

---

## Next Steps

### Phase 1: Deploy to Triage Repo (Current Sprint)
- [ ] Copy `prompt-kit.html` to `triage/web/prompt-kit/` in the triage repo
- [ ] Add a launch script or README entry for local access
- [ ] Verify mobile experience on actual devices

### Phase 2: Synonym Expansion
- [ ] Audit prompt names and use-when text for common search terms
- [ ] Add domain-specific synonyms (e.g., "PR" -> P14/P15/P36, "commit" -> P07/P31)
- [ ] Add natural language aliases ("what do I use when entering a new repo" -> P03)
- [ ] Consider fuzzy matching for typo tolerance

### Phase 3: Artifact Generation Site (Separate Website)
- [ ] Plan a second local website for artifact generation
- [ ] Scope: spreadsheet generation, report building, template filling
- [ ] Keep it separate from the prompt kit (different purpose, different audience)
- [ ] Share the same dark theme design language
- [ ] Consider a shared navigation bar between the two sites

### Phase 4: Integration with Triage Repo
- [ ] Add prompt kit as a sidecar tab in the Streamlit app (optional)
- [ ] Link triage gate check results to relevant prompts
- [ ] Auto-suggest prompts based on triage findings (e.g., "DXFS_INSERTION detected -> P07")

### Phase 5: Prompt Kit Enhancements
- [ ] Export filtered results as markdown or JSON
- [ ] Prompt sequencing visualization (show P00 -> P01 -> ... -> P12 flow)
- [ ] Dark/light theme toggle
- [ ] Print-friendly view for offline reference
- [ ] Prompt comparison view (side-by-side)

---

## Architecture Decisions

### Why Two Separate Sites?
The prompt kit is a static reference tool - no auth, no dependencies, no server. The triage repo is a Streamlit app with Python pipelines, API calls, and complex state. Mixing them would:
- Force the prompt kit to carry Streamlit's weight (~200MB Python env)
- Make the prompt kit unavailable offline
- Couple unrelated release cycles

Better to keep them independent with shared design language and cross-links.

### Why Inline Everything?
The prompt kit must work offline on technician phones. No CDN, no npm install, no build step. A single HTML file with embedded CSS/JS/data can be:
- Airropped to a phone
- Opened from a file share
- Cached by the browser
- Version-controlled as a single blob

### Why Event Delegation?
Inline `onclick="toggleCard('P00')"` breaks when Python's `\'` escaping mangles the quotes through the build pipeline. Event delegation with `data-*` attributes and `getAttribute()` is immune to this class of bug.

---

## File Locations

| File | Location | Purpose |
|------|----------|---------|
| `prompt-kit.html` | `AgentSwitchboard/docs/` | Source of truth |
| `prompts.json` | `AgentSwitchboard/docs/` | Extracted prompt data |
| `reference.json` | `AgentSwitchboard/docs/` | Extracted reference data |
| `prompt-kit.html` | `triage/web/prompt-kit/` | Deployed copy (Phase 1) |

---

## Hotkey Reference

| Key | Action |
|-----|--------|
| `/` | Focus search |
| `1` | All prompts |
| `2` | Standard prompts only |
| `3` | GNHF prompts only |
| `R` | Toggle reference sidebar |
| `Esc` | Collapse card -> Clear search -> Unfilter type/color/section -> Reset to All |
