# P55 Repository Bootstrap Recovery Sprint Map

**Canonical work owner:** PR #623 — `feat(prompt-kit): strengthen P55 repository bootstrap`  
**Plan status:** TRACKED recovery plan; implementation remains unmerged.  
**Planning floor:** `main@bd5136561466b31f8623ca3f9a61020cb9ced5f7`  
**Current PR head at planning:** `373019f33b0ef577443f7e56bdd441c06c203814`  
**PR divergence at planning:** 17 commits ahead / 32 behind current `main`; provider reports not mergeable.  
**Local path/worktrees:** not observable from the connected provider surface; local executor must refresh and inspect before mutation.

## Mission

Recover the existing P55 strengthening work onto current Prompt Kit authority, close the two remaining semantic defects, regenerate lifecycle/profile/site state from current canonical owners, re-prove the exact reconciled head, and integrate the exact green result into the current default branch. Reuse PR #623 unless current repository evidence proves replacement is safer.

The work is a recovery/convergence program, not a new prompt identity and not a second repository-creation owner.

## Completed floor to preserve

PR #623 already established useful donor behavior:

- P55 identity: `Context-Grounded Repository Bootstrapper`;
- context recovery before questioning;
- Repository Identity Manifest;
- `ASK | INFER | HYBRID` parameter-completion policy;
- exact/root/adjacent namespace collision screening;
- GitHub / Entire / other Git-compatible provider-adapter model;
- non-public visibility safety;
- provider collision-state vocabulary;
- P55 discovery synonyms;
- focused P55 regression coverage;
- prompt lifecycle/profile/history integration;
- metadata keyword type-safety repair;
- deterministic-floor registration repair.

Historical exact-head proof on `373019f3...` was 23 successful provider workflows plus 1 intentional skip, but that proof is stale for integration because current `main` moved materially afterward.

## Current blockers and owners

| Blocker | Evidence | Owner | Required transition |
|---|---|---|---|
| PR #623 is 32 commits behind current main and non-mergeable | provider compare / PR metadata | P55 recovery convergence lane | reconcile current main before any new proof or merge |
| `REMOTE_ONLY` P55 mode conflicts with unconditional `nextStep` requiring a local root | unresolved Codex review thread on `docs/prompts.json` | P55 canonical prompt record | make `nextStep` mode-aware and add regression |
| P55 declares manifest statuses exactly `RESOLVED | INFERRED | USER_ONLY` but self-check also permits `UNKNOWN` | unresolved Codex review thread on `docs/prompts.json` | P55 canonical prompt record | use one manifest-status vocabulary and add regression |
| Current main added P65 semantic migration and test-floor state after #623 proof | `main@bd513656...` and current canonical files | prompt lifecycle + test-floor owners | preserve current main records; never replace them with stale branch copies |
| Generated Prompt Kit changed after #623 proof | current main contains newer Prompt Kit generated/site work | canonical Prompt Kit builder | regenerate from current sources after reconciliation |
| Stale review thread questions metadata-only lifecycle semantics | outdated Codex thread on `scripts/prompt_registry_ops.py` | prompt lifecycle helper | preserve explicit semantic-vs-metadata boundary, prove it, then resolve thread |
| Global dispatch manifest path is actively owned by TRQ-020 | `Outputs/prompt-parallel-dispatch/manifest.json` run_id `upstream-capability-watch-20260920-u1-blocked` | TRQ-020 / upstream capability watch | do not overwrite for P55; P55 graph width is 1 and needs no parallel dispatch |

## Collision / dependency graph

Mutation graph width is **1**.

The following surfaces form one serialized convergence chain:

`scripts/prompt_registry_ops.py`
→ `docs/prompts.json:P55`
→ semantic/profile migration records
→ `harness/test-floor.v1.json`
→ `web/prompt-kit/index.html`
→ exact-head CI/review
→ merge.

Although review inspection and provider-status inspection are read-only and may happen concurrently, there are not two meaningful dependency-ready mutating lanes with disjoint owners.

**PARALLEL EXECUTION: NOT_APPLICABLE — dependency graph width is 1.**

## Sprint 1 — Reconcile current main and rebuild the final P55 lifecycle transaction

**Goal:** produce one current-main-based P55 candidate whose canonical prompt, lifecycle metadata, regression tests, deterministic-floor registration, and generated site are internally coherent.

**Hard dependency:** refresh current default branch/provider truth immediately before work.

**Owned mutation surfaces:**
- `scripts/prompt_registry_ops.py`;
- `docs/prompts.json` P55 only;
- `build_prompt_kit.py` P55 discovery synonyms only;
- `tests/test_p55_repository_bootstrap.py`;
- `harness/prompt-compilation/prompt-semantic-migrations.v1.json` only the P55 lifecycle addition generated from current authority;
- `harness/prompt-topology/prompt-capability-migrations.v1.json` only the P55 lifecycle addition generated from current authority;
- `harness/prompt-topology/prompt-capability-profiles.v1.json` P55 accepted profile;
- `harness/test-floor.v1.json` P55 regression registration only;
- `web/prompt-kit/index.html` generated output only.

**Forbidden:**
- overwrite or remove current P65 migration/test-floor/site state;
- hand-edit generated Prompt Kit output as the source of truth;
- create P55 replacement prompt identity;
- create a second PR before proving reuse of #623 unsafe;
- modify TRQ-020 dispatch manifest;
- weaken lifecycle or deterministic-floor validators;
- force-reset shared work.

**Implementation requirements:**
1. Refresh `origin/main`, resolve the real default branch, inspect dirty/worktree state, and pin the recovery base.
2. Reconcile #623 with current main in an isolated writer lane if the existing checkout is dirty, separately owned, or cannot safely host the merge.
3. Preserve current-main records first. Treat #623's P55 lifecycle/profile/migration entries as donor evidence, not final truth.
4. Keep the semantic-vs-metadata edit boundary explicit. Metadata may accompany a semantic edit; metadata-only edits must not masquerade as semantic lifecycle advancement unless the canonical lifecycle contract is intentionally redesigned.
5. Add `nextStep` to the supported accompanying metadata set if needed so the final P55 transition can remain one atomic lifecycle operation.
6. Final P55 must:
   - keep `RESOLVED | INFERRED | USER_ONLY` as the identity-manifest status enum consistently;
   - use `UNKNOWN_AUTH | UNKNOWN_PERMISSION | UNKNOWN_NETWORK | UNKNOWN_PROVIDER` only for remote collision/provider outcome classification, not manifest field status;
   - provide a mode-aware continuation:
     - local root available → enter verified root and route to P03/P07;
     - `REMOTE_ONLY` → first clone/adopt the verified remote into an approved local parent, then route to P03/P07;
     - `LOCAL_ONLY` → advance the remote-provider/auth gate rather than claim remote completion.
7. Add focused negative/positive regressions for both outstanding Codex findings.
8. Execute one final P55 lifecycle edit through `scripts/prompt_registry_ops.py` against the reconciled current-main floor so canonical hash/profile/history records match the final P55 body.
9. Regenerate `web/prompt-kit/index.html` through the canonical builder.

**Validation:**
- `python -m unittest tests.test_p55_repository_bootstrap -v`;
- `python -m unittest tests.test_spec_architecture_prompt_registry tests.test_prompt_kit_discovery tests.test_skill_prompt_registry tests.test_actionable_prompt_registry tests.test_p02_continuity_regression_matrix -v`;
- `python scripts/prompt_registry_ops.py validate`;
- `python scripts/evaluate_prompt_language.py --summary`;
- `python scripts/validate_prompt_kit_discovery.py --summary`;
- `python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check`;
- `python scripts/run_deterministic_test_floor.py --report Outputs/p55-recovery-deterministic-floor.json`;
- `git diff --check`;
- `git diff --cached --check` before commit.

**Completion gate:** exact candidate is current-main-based, P55 semantic defects are covered by tests, lifecycle/profile/history parity is valid, deterministic floor passes, generated site is exact, and no current-main prompt/migration/test-floor state was lost.

**Proof ceiling:** repository/local deterministic proof only until provider exact-head CI/review passes.

## Sprint 2 — Exact-head provider proof and review closure

**Goal:** prove the reconciled head in provider CI and eliminate all actionable review blockers without broadening scope.

**Dependency:** Sprint 1 exact candidate committed and pushed.

**Owned surfaces:**
- PR #623 review threads/comments and branch commits required to close P55-specific findings;
- no unrelated product surfaces.

**Forbidden:**
- merge with pending/failing required checks;
- dismiss valid review findings without code/test evidence;
- change P65 or other prompt behavior to make P55 green;
- treat stale pre-reconciliation CI as current proof.

**Tasks:**
1. Re-fetch current main immediately before evaluating CI freshness.
2. If proof-relevant current-main inputs moved, reconcile first and rerun affected validation.
3. Require exact-head provider runs, especially deterministic repository floor, prompt quality history, semantic topology/lifecycle, Prompt Kit web/pages/privacy/storage, and repository AI evals when triggered.
4. Re-evaluate every unresolved review thread:
   - metadata/hash thread → close only after proving the semantic/metadata boundary is intentional and regression-covered;
   - remote-only continuation thread → close after mode-aware next-step regression passes;
   - manifest-status vocabulary thread → close after one-vocabulary regression passes.
5. Inspect any new review/CI failure as new sprint evidence; repair in Sprint 1 ownership surfaces and rerun exact-head proof.

**Completion gate:** exact current head is mergeable, all required/provider gates are successful or intentionally skipped by contract, zero unresolved actionable review threads remain, and main has not moved in a proof-relevant way.

**Proof ceiling:** exact provider candidate proof; not integration until merge and post-merge containment are verified.

## Sprint 3 — Mainline integration, stale-owner cleanup, and durable closeout

**Goal:** integrate the exact green P55 candidate into current default branch and retire superseded recovery residue.

**Dependency:** Sprint 2 gate closed.

**Owned surfaces/actions:**
- merge PR #623 using repository-accepted method;
- verify default-branch containment/content;
- close stale donor PR #367 after successful integration;
- update this plan and TRQ-021 ledger state to DONE;
- optional feature-branch cleanup only after unique-work preservation check.

**Forbidden:**
- close #367 before replacement integration is proven;
- delete feature branches/worktrees containing unique unmerged work;
- claim local workstation/runtime proof from provider-only evidence.

**Post-merge proof:**
1. refresh default branch/provider truth;
2. prove merge/integration SHA is contained in refreshed default;
3. verify current default still contains final P55 behavior and current P65 state;
4. run or observe the owning deterministic/provider validation required by repository policy;
5. close #367 as superseded with a pointer to integrated #623;
6. mark TRQ-021 DONE with merge/workflow evidence.

**Completion gate:** final P55 is on refreshed default branch, current P65/Prompt Kit authority is preserved, #367 is safely superseded, and no safe P55 recovery work remains.

**Proof ceiling:** integrated repository/provider proof. Real GitHub CLI, Entire, or other provider repository-creation behavior remains a separate runtime/field proof surface exercised when P55 is subsequently used in those environments.

## Harness / skill / capability / trigger factoring

No new skill, capability, trigger, or workflow is justified by this recovery.

- **Prompt semantic coverage skill:** KEEP. Trigger `prompt-semantic-lifecycle-change` remains the correct deterministic activation owner for P55 canonical mutation.
- **Prompt language audit skill:** KEEP. Trigger `prompt-language-change` applies because canonical prompt language changes.
- **Skill evaluation:** KEEP but not primary for this recovery; runtime compliance is a downstream proof surface, not required to reconcile the registry.
- **Harness infrastructure maintenance:** KEEP; only route here if merge/reconciliation exposes a harness contract defect rather than a P55 defect.
- **Repository hook integration:** NOT APPLICABLE.
- **Repository-native update:** KEEP; generated Prompt Kit output remains builder-owned.
- **Parallel dispatch:** KEEP globally, but NOT_APPLICABLE to this recovery because mutating graph width is 1.
- **New P55-specific skill/capability/trigger:** REJECT. P55 is prompt/product behavior governed by existing prompt semantic/language owners.

## Application logic factoring

No conventional application-service, persistence, UI state-machine, deployment, or runtime adapter implementation belongs in this recovery. Provider-specific GitHub/Entire operations remain runtime adapters selected by P55 at execution time; their actual syntax/behavior must be evidenced in the environment where P55 runs rather than hard-coded into this recovery plan.

## Durable artifacts and ownership

- Canonical recovery plan: `docs/plans/P55_REPOSITORY_BOOTSTRAP_RECOVERY_SPRINT_MAP.md`.
- Continuity index: `.ai/WORK_QUEUE.md#TRQ-021`.
- Implementation/review owner: PR #623.
- Superseded donor: PR #367, close only after #623 integrates.
- Shared parallel-dispatch manifest: currently owned by TRQ-020; do not overwrite for this width-1 recovery.

## Next executable action

Owner: local/repository executor for PR #623.  
Dependency: refreshed current main and safe isolated writer lane.  
Action: reconcile `feat/p55-provider-neutral-repo-bootstrap-20260920` with current default branch, then reconstruct the final P55 lifecycle transaction from current-main authority before running Sprint 1 validation.  
Expected proof: one exact current-main-based branch head with focused P55 tests, semantic lifecycle validation, deterministic floor, generated-site parity, and patch hygiene green.
