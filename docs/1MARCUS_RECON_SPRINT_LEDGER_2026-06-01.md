# 1 Marcus Recon Sprint Ledger — 2026-06-01

## Sprint target

Build the repo lane for 1 Marcus inventory recon automation.

The immediate goal is not a polished universal framework. The immediate goal is a narrow, testable engine that can take the updated 1 Marcus recon workbook, align the dated Part Numbers tab, rewire formulas, remove stale workbook ghosts, and produce a Web Excel-safe client candidate.

## Current branch

```text
feat/1marcus-recon-partnumber-relink-engine-2026-06-01
```

Created from current `main` after PR #28 and PR #29 were merged.

## Completed in this sprint checkpoint

- Verified PR #28 is closed and merged.
- Verified PR #29 is closed and merged.
- Confirmed legacy open PRs still exist and should not be blindly merged.
- Created clean inventory recon feature branch from merged `main`.
- Added the 1 Marcus recon part-number relink contract.
- Preserved billing as a valid repo capability while keeping this lane scoped to inventory recon.

## Known open PR state

These open PRs remain outside this sprint unless explicitly pulled in:

| PR | Status | Current handling |
| --- | --- | --- |
| #26 | Open, not mergeable | Likely superseded in part by merged Cybernet/Neuron engines, but contains broader NW PRJ local artifact work. Needs audit before close or salvage. |
| #23 | Open draft | Scaffold reader/classifier contracts. Likely superseded by later concrete engines. Needs close/comment after confirming no unique doctrine remains. |
| #17 | Open draft | Artifact checkpoint payload/manifest lane. Contains encrypted payload references. Keep untouched unless artifact-retention decision is made. |
| #14 | Open | Post-convergence validation docs. Useful historical audit, but old base. Needs rebase or close as superseded by later repo state. |
| #11 | Open | Admin billing workbook inspector. Billing-adjacent. Do not close in inventory recon cleanup without explicit billing lane decision. |
| #10 | Open | Note-tolerant roster punch parsing docs. Probably valuable doctrine, but old base and may be duplicated by merged engines. Needs doctrine audit. |

## Known gaps

1. No code module exists yet for `triage.one_marcus_recon`.
2. No sanitized 1 Marcus recon fixture exists yet.
3. No parser exists yet for detecting dated `M-D-YYYY Part Numbers` tabs.
4. No formula-rewrite function exists yet for localizing old part-number references.
5. No package-level cleanup exists yet for removing stale `xl/externalLinks/*` parts in this lane.
6. No recon-specific Web Excel preflight wrapper exists yet.
7. No dry-run report exists yet.
8. No delivery ZIP/manifest/carryover sidecars exist yet for this lane.
9. No CI workflow exists, so tests are still locally proven only unless a separate CI PR is added.
10. Open legacy PRs remain and may confuse future merge order if not annotated or retired.

## Risks

| Risk | Why it matters | Mitigation target |
| --- | --- | --- |
| Workbook rewrite damage | High-level workbook libraries can damage Excel Web compatibility or visual fidelity. | Use preserve-first, surgical XML/package patching where possible. |
| Stale external links | Excel Web may repair or reject workbook packages with unresolved external links. | Localize formulas, remove unused external link parts, scan relationships. |
| Stale calc chain | Formula rewrites can leave invalid calcChain references. | Remove `calcChain.xml` after formula edits. |
| Date ambiguity | Multiple dated Part Numbers tabs can cause the engine to choose the wrong reference. | Strict mode fails; normal mode warns and reports selected candidate. |
| Loose item-description matching | Pivots can roll up under inconsistent names instead of stable part/model identifiers. | Prefer part/model fields in helper logic. |
| Hyperlink formulas in calc labels | Prior artifact showed hyperlink formulas can interfere with validation/calculation labels. | Keep calculation labels formula-clean; allow links only in presentation-only cells. |
| Private workbook leakage | Real recon/client files must not enter repo history. | Fixtures must be sanitized/minimal; Candidates and Outputs stay gitignored. |
| Legacy PR collision | Old branches may touch same docs/helpers and conflict with new lane. | Keep new lane narrow; retire or annotate stale PRs separately. |

## Targets

### Target 1 — scaffolding

Create package:

```text
triage/one_marcus_recon/
  __init__.py
  models.py
  date_inference.py
  formula_relink.py
  package_cleanup.py
  preflight.py
  exporter.py
  cli.py
```

### Target 2 — sanitized fixtures

Create minimal test workbooks that simulate:

- old dated Part Numbers tab
- new intended date from filename
- stale formula references
- stale external workbook prefix
- stale calcChain
- unrelated tab preservation

### Target 3 — relink engine

Implement deterministic dry-run and write modes:

```bash
python -m triage.one_marcus_recon.cli --input Candidates/input.xlsx --date auto --dry-run
python -m triage.one_marcus_recon.cli --input Candidates/input.xlsx --date 2026-05-28 --output Outputs/1_Marcus_Recon_2026-05-28_WEBSAFE.xlsx
```

### Target 4 — Web Excel preflight

Produce JSON report with:

- formula errors
- stale dated references
- external links
- calc chain state
- relationship scan
- stop-ship token scan
- tab preservation summary

### Target 5 — PR hygiene

Before opening implementation PR:

- confirm branch has only intended files
- confirm no generated workbook outputs are tracked
- confirm no private `Candidates/` content is tracked
- confirm old PRs are either untouched by design or clearly commented/closed in a separate cleanup PR

## Next checkpoint definition of done

A draft PR should exist for this branch with:

- contract doc
- sprint ledger
- no private files
- no generated workbook files
- clear known gaps/risks/targets

The implementation can then proceed in small commits without carrying a dirty repo into the next feature push.
