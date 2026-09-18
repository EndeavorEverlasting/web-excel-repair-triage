# LANE 08 — Publish Prompt Kit and Refresh Operant Release

**Repo:** EndeavorEverlasting/web-excel-repair-triage  
**Release PR:** #538 / `automation/operant-release-v0.9.0` or its automation-refreshed successor identity  
**Wave:** D  
**Hard dependency:** Lane 07 integrated into main  
**Canonical owners:** Prompt Kit builder, Pages workflow, Operant versioning workflow

## Mission

Make the strengthened prompts visible on the public Prompt Kit and refresh the existing release carrier from accepted mainline state without creating a second release workspace.

## Read first

- `docs/PROMPT_KIT_PROMOTION_PIPELINE.md`
- `docs/OPERANT_VERSIONING.md`
- `harness/contracts/operant-product-identity.v1.json`
- `.github/workflows/prompt-kit-pages.yml`
- `.github/workflows/operant-versioning.yml`
- current #538 metadata/checks
- refreshed main head and final generated Prompt Kit identity

## Authority

- `scripts/build_prompt_kit_registry.py` is the only Prompt Kit generation authority.
- Pages deployment is owned by `.github/workflows/prompt-kit-pages.yml` and deploys only accepted default-branch state.
- Existing open Operant release PR refresh is Actions-owned. Do not manually create a duplicate release PR or hand-edit version/changelog around automation.

## Tasks

1. Refresh main and confirm Lane 07 merge is an ancestor.
2. Run builder parity on exact main.
3. Observe the main Pages workflow for that exact accepted main lineage; if it fails, diagnose/repair the owning cause.
4. Verify the public Pages deployment corresponds to the accepted main artifact; a PR preview is insufficient.
5. Refresh #538 metadata. The open release branch should be refreshed in place by Operant versioning after accepted main changes.
6. If automation did not run, use the repository/provider-supported manual workflow dispatch pinned to main; do not mutate the release branch manually unless the canonical workflow explicitly delegates a bounded repair.
7. Validate exact refreshed release candidate and stale-candidate rejection.
8. Merge #538 when release checks are green.
9. Verify the resulting `operant-vX.Y.Z` tag/GitHub Release points to the exact merged release commit.

## Validation order

```bash
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
python scripts/validate_prompt_kit_release_identity.py --summary
python -m unittest tests.test_operant_product_identity tests.test_operant_versioning_workflow -v
git diff --check
```

Provider-side Pages/release observations are required after local/static validation.

## Safety

No second editable Prompt Kit. No manual release-version decrement/reuse. No treating PR Pages preview as production. No direct version/changelog rewrite that bypasses Operant authority.

## Proof level / ceiling

Target: DEPLOYED Prompt Kit + INTEGRATED/RELEASED Operant identity.  
Ceiling: public Pages/release observation only; no claim that downstream agents behave better.

## Exact final response

Report final main SHA, Prompt Kit artifact identity, Pages run/deploy result, #538 refreshed head, release validation, merge SHA, tag/release identity, and next P67 runtime-eval gate.

## NEXT COMMAND

```bash
git fetch --all --prune --tags && git switch main && git pull --ff-only && python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
```
