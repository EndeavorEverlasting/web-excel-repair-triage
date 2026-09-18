# Prompt Strength / Execution Reliability Closeout Plan

## Current floor

- Repository: `EndeavorEverlasting/web-excel-repair-triage`
- Reconciled default branch: `main@2ecf9136611e2f26559afd90cde22e3f082e59b9`
- Integrated prerequisites: #533 (`fc5fca0d...`), #535 (`f3126a3a...`), #536 (`80ead456...`), #542 (`ae09d616...`), #548 (`e4c2fe12...`).
- Current main also contains the execution-boundary/release-publication strengthening through #545.
- Provider-only execution is active in this runtime; no mounted local checkout is available.

## Active Wave — graph width 2

### Lane A — PR #543 local-proof continuity

Owned source: compiler policy, P07 semantics, repository action registry, prompt-compilation regression, generated Prompt Kit projection.

Execution:
1. Reconcile the branch to the refreshed main floor.
2. Use a branch-scoped provider adapter that delegates to canonical `prompt-kit-build-proof`; the adapter is temporary, pinned, credential-isolated, and must be deleted before integration.
3. Preserve the uploaded repository-action receipt as provider proof.
4. Regenerate `web/prompt-kit/index.html` only through the canonical repository action/builder.
5. Resolve review, rerun exact-head checks, merge when all gates pass, then verify main containment.

### Lane B — PR #537 prompt-strength semantic floor

Owned source: prompt-strength contract/matrix/validator/focused test, deterministic-test-floor registration, and current durable plan/dispatch artifacts.

Convergence law:
- rebuild from current main rather than merging stale whole-file snapshots;
- retain the 21-dimension / 31-case semantic floor and PSA-031 silent-stop regression;
- retain PSA-029 without false `fixed_point_continuation` credit;
- refresh #535 from stale OPEN state to integrated head `22d5560e...` / merge `f3126a3a...`;
- drop the stale branch copy of `harness/contracts/prompt-quality-history.v1.json`;
- drop retired per-lane playbooks/templates that describe already-integrated #542/#548 work;
- register the focused test in current `harness/test-floor.v1.json`;
- validate and merge from the exact current head.

## Durable parallel execution

The primary manifest and its regression seed are byte-identical:
- `Outputs/prompt-parallel-dispatch/manifest.json`
- `harness/evals/prompt-strength/parallel-dispatch-manifest.seed.v1.json`

The active adapter is the connected GitHub provider (rung 3). The two isolated PR branches are independent mutation surfaces and are dispatched concurrently. Runtime-tool evidence is preserved through provider commits, review state, CI runs, and the #543 repository-action artifact. No manual operator scheduling is required.

## Successor phase — publication / release

After both active PRs are integrated:

1. Refresh current main and verify canonical Prompt Kit builder parity plus Pages.
2. Recompute the existing Operant release carrier #538 through the canonical release workflow/external publication seam introduced by #545. Do not manually patch version/changelog/generated HTML and do not create a duplicate release PR.
3. Validate the refreshed exact candidate, merge when gates pass, and verify tag/GitHub Release identity.

## Successor phase — observed effectiveness

After final publication/release freezes the treatment identity, route to the existing P67 compute-authority evaluation owner. Run the canonical paired external-agent pilot when its adapter/credentials are available. Repository/static/provider proof does not become downstream model-obedience proof.

## Definition of done

1. #543 integrated with canonical build-proof receipt and generated-site parity.
2. #537 integrated with current-main semantic floor, deterministic-test registration, and no stale shared-owner snapshots.
3. final main Prompt Kit publication verified.
4. existing #538 refreshed, validated, integrated, and release/tag identity verified.
5. P67 runtime effectiveness either OBSERVED through its canonical adapter or explicitly BLOCKED/UNPROVEN_RUNTIME at the exact external gate.

## Proof ceiling

Repository/provider evidence can prove source, regression, exact-head CI, generated projection, integration, Pages, and release identity when observed. It does not prove unavailable workstation-local execution, universal downstream model obedience, or operator acceptance.
