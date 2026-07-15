# Agent Instructions

## Purpose

This repository diagnoses, diffs, classifies, generates, applies, and verifies `.xlsx` workbooks that trigger Excel for Web repair banners.

A fresh agent entering this repo should:
1. Read this file (AGENTS.md)
2. Read `.ai/codebase_map.json` for module layout
3. Read `.ai/known_traps.json` for pitfalls
4. Read `.ai/validators.json` for validation commands
5. Choose a workflow direction (below)
6. Run the right validators
7. Produce artifacts under `Outputs/`
8. Hand off cleanly

## Billing Pipeline Directional Contract

Agents must identify the requested workflow direction before generating scripts, workbook patches, summaries, or corrections.

### Supported Directions

#### 1. Roster Log to Admin Sheet (high priority)

One-shot output path for Friday billing/submission review.

Rules:
- Produce admin-facing output only.
- Default workbook scope is Project Team tab only unless explicitly requested.
- Use resolved worked-project logic, including assignments and overrides.
- Do not expose internal exception machinery, confidence fields, private notes, or task-tracker context.

#### 2. Roster Log to Task Tracker (medium priority)

Internal contextualization workflow.

Rules:
- Treat this as internal context, not submission output.
- Map staff, date, hours, project assignment, and override logic into task context.
- Preserve useful contribution evidence.
- Do not reshape into admin-facing workbook unless explicitly requested.

#### 3. Task Tracker to Roster Log (low priority, review-gated)

Backfill workflow. Must be review-gated.

Rules:
- Propose updates only unless direct roster mutation is explicitly approved.
- Never silently mutate the roster log.
- Rejected updates stay as tracker-only context.

### Priority Order

1. Roster Log to Admin Sheet
2. Roster Log to Task Tracker
3. Task Tracker to Roster Log

## Core Logic Rules

- Overrides beat default assignment.
- Resolved worked-project logic beats raw assumption.
- Raw notes that conflict with resolved logic should create exceptions.
- Admin-facing output stays narrow and clean.
- Internal task-tracker context may be richer, but it must not leak into admin submission artifacts.
- Backfill into the roster log must be proposed, reviewed, and approved before mutation.

## Operator Source Immutability

**Candidates/** and **Active/** are read-only operator inputs (backup/emulator files).

- Never write, overwrite, or copy engine output into these paths.
- Never set `--output` equal to `--input`.
- All generated workbooks, sidecars, and forensic reports go under **Outputs/**.
- Overwrites elsewhere require timestamped backup under `Outputs/backups/`.
- Delivery requires baseline fingerprint compare against the declared source; fail if sheets are deleted.

See [`docs/ONE_MARCUS_SOURCE_OVERWRITE_INCIDENT_2026_06_04.md`](docs/ONE_MARCUS_SOURCE_OVERWRITE_INCIDENT_2026_06_04.md) for the incident that motivated this rule.

## Stop-Ship Rules

If Excel repairs the workbook → artifact is FAILED. Do not bless it. Do not continue from it without labeling it as a repaired source. Rebuild clean if possible.

Read `configs/web_excel_stop_ship_tokens.json` for the full token list.
Read `docs/WEB_EXCEL_COMPATIBILITY_STOP_SHIP_RULES.md` for the full rules.

### Filename STOP-SHIP

Reject outputs when the basename contains: `repaired_`, `Deprecated_repaired_`, `web_repaired_`.

### Package STOP-SHIP tokens

Scan all XML parts for: `_xlfn.`, `_xludf.`, `_xlpm.`, `AGGREGATE(`, `#REF!`, `#VALUE!`, `#NAME?`.

### Structural STOP-SHIP

| Check | Failure |
|-------|---------|
| XML parse | Any `.xml` part fails `ElementTree` parse |
| Relationship targets | `.rels` Target does not resolve in package |
| Content types | Missing `[Content_Types].xml` or bad overrides |
| calcChain | `xl/calcChain.xml` survives programmatic edits |
| External links | `xl/externalLinks/` exists in delivery artifact |
| Serializer pollution | XML contains `ns0:` or `xmlns:ns0` leakage |

## XLSX Structure Preservation Contract

Read `docs/XLSX_STRUCTURE_PRESERVATION_CONTRACT.md` for the full contract.

Key doctrine: The OOXML package structure is part of the artifact, not an implementation detail.

- Prefer in-place mutation of a known-good workbook over wholesale regeneration.
- When only one tab needs adjustment, only that tab and its directly required style ranges should change.
- A visually correct workbook is not accepted until its package structure passes the structural contract.

### Mutation Classes

| Class | Description | Allowed posture |
|-------|-------------|-----------------|
| A | Value-only update | Preserve package shape, no formulas |
| B | Style-only update | Preserve values, reuse style IDs |
| C | Sheet-local rebuild | Snapshot manifest before/after |
| D | Structural migration | Requires new compatibility lane |

## Validation Ladder

A workbook candidate must climb this ladder in order:

1. ZIP opens as a package.
2. XML and `.rels` parts parse.
3. Required package parts exist.
4. Content types are valid.
5. Relationship targets resolve.
6. Sheet names/order match expected contract.
7. Tables and charts have valid part relationships.
8. `calcChain.xml` is absent after programmatic edits.
9. Stop-ship terms and formula errors are absent.
10. Target sheet renders correctly.
11. Non-target sheets remain stable.
12. Excel Web field validation passes.

Do not skip from step 1 to "send it".

## Friday Reporting Rule

Friday is the reporting batch marker. Work performed Monday through Friday maps to that Friday's reporting/submission batch. Weekend work generally rolls into the next Friday reporting batch unless explicitly handled otherwise.

## Known Traps

Read `.ai/known_traps.json` for the full list. Key traps:

| ID | Name | Symptom | Fix |
|----|------|---------|-----|
| TRAP-001 | inlineStr causes repair | Excel repair dialog | Call fix_inlinestr() after pkg.write() |
| TRAP-002 | OOXML dxf schema order | styles.xml repair | Insert dxfs between cellStyles and tableStyles |
| TRAP-003 | openpyxl styles.xml + dxfs | COM fails, repair dialog | Strip openpyxl attributes or write clean XML |
| TRAP-004 | Hardcoded C:\\ path in roster_parser | CI failure | Use relative paths |
| TRAP-005 | Hardcoded C:\\ path in tests | CI failure | Use relative paths |
| TRAP-006 | No __main__ in web_excel_compatibility_rules | Silent no-op | Use function directly |

## Validation Commands

Read `.ai/validators.json` for the full list. Quick reference:

```bash
# Static tests (always safe)
python -m pytest tests/test_cf_engine.py tests/test_roster_log_review_queue.py -q

# CI gate (before push/PR)
python -m pytest tests/test_cybernet_targets.py tests/test_nw_prj_neuron_track_hours.py tests/test_nw_prj_neuron_track_hours_bonita.py tests/test_admin_billing_summary.py tests/test_one_marcus_recon.py tests/test_one_marcus_generate.py tests/test_one_marcus_immutability.py tests/test_sidecar_html_portal.py tests/test_artifact_compare.py tests/test_roster_log_compare.py tests/test_same_family_compare.py tests/test_gitignore_hygiene.py tests/test_roster_log_review_queue.py -q

# Gitignore hygiene (before commit)
python -m triage.gitignore_hygiene

# Imports check (before push)
python -c "import triage.cybernet_targets.cli; import triage.nw_prj_neuron_track_hours.cli; import triage.nw_prj_neuron_track_hours.bonita_cli; import triage.admin_billing_summary.cli; import triage.one_marcus_recon.cli; import triage.sidecar_html; import triage.artifact_fingerprint; import triage.artifact_profiles; import triage.artifact_compare; import triage.same_family_compare; import triage.roster_log_compare.compare; import triage.roster_log_review_queue.cli; import triage.gitignore_hygiene; print('imports ok')"
```

## Codebase Map

Read `.ai/codebase_map.json` for the full module map with paths and purposes.

### Key directories

| Path | Purpose |
|------|---------|
| `triage/` | Core engine (72 entries) |
| `tests/` | 43 test files + 8 fixture dirs |
| `configs/` | JSON configs for CF rules, profiles, stop-ship tokens |
| `docs/` | 56 entries: contracts, specs, findings |
| `.ai/` | Harness spine: map, validators, traps, registry |
| `.opencode/` | Agent rules, skills, commands |
| `scripts/` | Utility scripts (7 files) |
| `Outputs/` | Generated workbooks (gitignored) |

## Artifact Registry

Read `.ai/artifact_registry.json` for the full registry of generated files, config files, test fixtures, and docs.

## CI

Read `.github/workflows/artifact-engines.yml` for the CI workflow. Runs on push to main and PRs. Executes import checks, gitignore hygiene, and 12 pytest test files.

## Sprint Rules

For sprint work:

- Repair prompt = stop-ship. Never claim higher proof level from lower.
- Use `NOT_RUN` for unavailable gates.
- Proof levels: static_proof → structural_proof → runtime_proof → harness_proof → launcher_proof.

## Recommended Script Names

```text
roster_to_admin_submission.py
roster_to_task_context.py
task_tracker_to_roster_backfill.py
```
