---
name: harness-inspector
description: Use when entering the repo for the first time, or when asked to inspect the harness, codebase map, validators, known traps, or workflow specs. Also use when asked "what's in this repo" or "how do I navigate this codebase".
---

# Harness Inspector

Use this skill to understand the repository structure, available workflows, validators, and known pitfalls.

## Quick start

1. Read `.ai/codebase_map.json` — full module map with paths and purposes
2. Read `.ai/known_traps.json` — 9 documented pitfalls with symptoms and fixes
3. Read `.ai/validators.json` — all validation commands and when to run them
4. Read `.ai/artifact_registry.json` — what files are produced where
5. Read `AGENTS.md` — agent rules and workflow directions

## Lifecycle directories

| Directory | Rule |
|-----------|------|
| `Candidates/` | READ-ONLY operator input |
| `Active/` | READ-ONLY operator input |
| `Outputs/` | All generated workbooks go here |
| `References/` | Blessed reference workbooks |
| `Repaired/` | Excel-repaired files |
| `Deprecated/` | Legacy scripts and fragments |

## Workflow directions (from AGENTS.md)

1. **Roster Log → Admin Sheet** (high priority)
2. **Roster Log → Task Tracker** (medium priority)
3. **Task Tracker → Roster Log** (low priority, review-gated)

## Validation ladder (from docs/XLSX_STRUCTURE_PRESERVATION_CONTRACT.md)

1. ZIP opens
2. XML/rels parse
3. Required parts exist
4. Content types valid
5. Relationship targets resolve
6. Sheet names/order match
7. Tables/charts valid
8. calcChain absent
9. Stop-ship terms absent
10. Target sheet renders
11. Non-target sheets stable
12. Excel Web validation passes

## Stop-ship rules

If Excel repairs the workbook → artifact is FAILED. Do not bless it.
See `docs/WEB_EXCEL_COMPATIBILITY_STOP_SHIP_RULES.md` for full rules.
