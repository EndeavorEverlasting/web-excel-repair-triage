# Canonical Path Operator State

**Repository:** `EndeavorEverlasting/web-excel-repair-triage`
**Machine authority:** `harness/canonical-paths.v1.json`
**Focused validator:** `scripts/validate_canonical_paths.py`
**Deep repair owner:** P92 Canonical Path Prompt

## Working

The repository now has one machine-readable owner for the distinction between the canonical development checkout, the application production/use path, the approved temporary writer worktree root, and the real operator entrypoint. The contract covers repository source work, public Prompt Kit browser use, Windows portable use, and phone/tablet PWA use.

The source-development profile does not hard-code a user or machine path. It resolves the existing canonical-origin checkout at runtime with `git rev-parse --show-toplevel`. If no such checkout is proven, agents must route through the acquisition workflow or an explicit operator-selected parent rather than choose a directory themselves.

Parallel writers use a Git worktree derived under `<canonical-checkout-parent>/.worktrees/web-excel-repair-triage/<branch-slug>`. A second mutable clone is explicitly rejected as a substitute for writer isolation.

## Application use paths

| Profile | Production/use path | Real operator entrypoint |
|---|---|---|
| repository-development | Not applicable; this is source-work state | proven repository root / repository commands |
| public-web | `https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/` | same public Prompt Kit URL |
| windows-portable | `Outputs/prompt-kit-portable/index.html`, served at `http://127.0.0.1:8765/` | `Open-Latest-PromptKit.cmd` |
| phone-tablet-pwa | `https://endeavoreverlasting.github.io/web-excel-repair-triage/` | same URL in the system browser |

## Proof states

These states are intentionally separate and non-promoting:

1. `remote_main_contains_sha`
2. `canonical_development_checkout_current`
3. `production_use_path_current`
4. `operator_entrypoint_observes_current`

A GitHub merge proves only the first state. A current local checkout does not prove a generated/deployed use path. A current use path does not prove the real operator entrypoint actually observed it.

## Broken or missing

No static repository contract can prove the current path/state of an arbitrary operator workstation, deployed Pages bytes, locally generated portable artifact, browser cache, or real operator entrypoint. Those remain runtime observations and must not be inferred from repository success.

## Validation

```bash
python scripts/validate_canonical_paths.py --summary
python -m unittest tests.test_canonical_paths -v
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
python -m unittest tests.test_harness_contract -v
git diff --check
```

## Proof ceiling

This report describes the tracked repository contract and its intended routing. It is not a deployment receipt and is not proof that a specific workstation, public site, portable loopback server, or operator browser currently reflects a particular commit.
