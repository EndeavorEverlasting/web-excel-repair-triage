# Canonical Path Workflow

Use this focused workflow when a task depends on **where** repository development occurs, where the application is actually used/installed/served, where an isolated writer may work, or which real entrypoint an operator uses. The machine authority is `harness/canonical-paths.v1.json`. P92 owns deep audit/repair of that authority; this workflow only operationalizes it inside the root harness.

## Trigger

Load this workflow when an agent, launcher, updater, worktree helper, operator report, or handoff would otherwise choose or assume a filesystem path, install/use location, serving URL, or entrypoint.

## Inputs

- current repository/provider floor;
- `harness/canonical-paths.v1.json`;
- requested machine/profile and whether the task is source work or application use;
- current Git state when a development checkout is involved;
- the exact evidence tier the task must prove.

## Procedure

1. Resolve the requested profile from `harness/canonical-paths.v1.json`; do not manufacture a path from memory, user name, machine name, or model preference.
2. For source work, prove the existing Git root with `git rev-parse --show-toplevel`, verify the canonical origin, and preserve unique/dirty work. If no canonical checkout is proven, route through the registered acquisition workflow or an explicit operator-selected parent rather than creating a surprise clone.
3. For parallel writers, derive the approved sibling `.worktrees/web-excel-repair-triage/<branch-slug>` root from the proven canonical checkout parent and use `git worktree`. A second mutable clone is not an isolation mechanism.
4. For application use, select the profile-specific production/use path and real entrypoint. Public browser/PWA use does not require a checkout; Windows portable use is launcher-owned.
5. Track the four proof states separately: `remote_main_contains_sha`, `canonical_development_checkout_current`, `production_use_path_current`, and `operator_entrypoint_observes_current`. Never promote an earlier state into a later one without its required evidence.
6. Run the focused validator/tests, then the root harness gate for any tracked harness change.
7. Hand off the resolved profile, evidence state actually proven, unproven higher states, artifact/entrypoint identity, commit/PR state, and next executable gate.

## Failure policy

- **Unknown checkout:** preserve state and route to acquisition/operator selection; do not guess a directory.
- **Dirty/diverged checkout:** preserve unique work and isolate through an approved worktree; do not reset, clean, or create another mutable clone.
- **Provider merge only:** record only `remote_main_contains_sha`; workstation/use/entrypoint states remain unproven.
- **Use path differs from source artifact:** stop at `production_use_path_current = UNPROVEN` until the profile-specific deployment/generation evidence is obtained.
- **Real entrypoint not observed:** do not claim operator acceptance or deployment merely because files or URLs exist.

## Validation

```bash
python scripts/validate_canonical_paths.py --summary
python -m unittest tests.test_canonical_paths -v
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
python -m unittest tests.test_harness_contract -v
git diff --check
```

## Outputs

- machine path/profile authority: `harness/canonical-paths.v1.json`;
- focused human workflow: this file;
- focused validator/tests;
- operator-readable state: `harness/reports/CANONICAL_PATHS.md`;
- root-harness registration and hook execution.

## Proof ceiling

Static validation proves that the repository has one connected path/profile authority, forbids path invention and clone sprawl, and keeps the four evidence states non-promoting. It does **not** prove a particular workstation checkout exists or is current, that GitHub Pages/portable output is current, or that an operator actually opened the real entrypoint unless those runtime observations were separately performed.
