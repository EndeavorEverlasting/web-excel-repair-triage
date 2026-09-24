# P55 Repository Bootstrap Recovery — Remote Sprint Plan Pack

**Canonical recovery plan:** `docs/plans/P55_REPOSITORY_BOOTSTRAP_RECOVERY_SPRINT_MAP.md`
**Continuity index:** `.ai/WORK_QUEUE.md#TRQ-021`
**Implementation owner:** PR #623 / `feat/p55-provider-neutral-repo-bootstrap-20260920`
**Pack purpose:** one self-contained sprint panel per new AI chat. Do not paste multiple panels into one chat.

## LAUNCH ORDER

1. **Sprint 1 — P55 Floor Recovery + Lifecycle Helper**
   - Launch first.
   - Establishes the current-main floor and the only helper contract required by the final P55 lifecycle transaction.
   - Unlocks Sprint 2 only when the reconciled branch preserves current-main P65/test-floor/site authority and the helper boundary is green.

2. **Sprint 2 — Final P55 Semantics + Exact-Head Proof**
   - Waits for Sprint 1.
   - Repairs the two live P55 semantic defects, executes the final atomic lifecycle transaction, regenerates the Prompt Kit, runs deterministic/local proof, pushes, and closes actionable P55 review findings only after exact-head provider proof.
   - Unlocks Sprint 3 only when the exact head is mergeable, required checks are green, and no actionable P55 review thread remains.

3. **Sprint 3 — P55 Mainline Convergence + Cleanup**
   - Waits for Sprint 2 exact-head proof.
   - Merges the exact validated head, verifies refreshed-main containment/content, closes stale donor PR #367 only after replacement proof, and closes TRQ-021 / the recovery plan.

**Parallel groups:** none. Mutating dependency graph width is 1. Read-only review/provider inspection may occur concurrently inside a sprint but is not a separate writer.

## COMPACT COORDINATION PREAMBLE

- Repo: `EndeavorEverlasting/web-excel-repair-triage`
- Primary local path: UNKNOWN; resolve with `git rev-parse --show-toplevel`
- Remote floor when this pack was authored: `main@bd5136561466b31f8623ca3f9a61020cb9ced5f7`
- PR #623 head before pack publication: `a54901651981fabf755e20a0f5415c6399d5bc64`
- Observed PR divergence before pack publication: 19 ahead / 32 behind; non-mergeable
- Existing stale donor: PR #367
- First commands in every sprint: resolve root, status, branch, recent log, worktrees, remotes, fetch/prune, open PRs, PR status, and exact #623 metadata/checks/reviews
- Dirty/conflicted worktree rule: preserve unknown work; never reset/clean/overwrite; use an isolated worktree when dirt is not owned
- Worktree policy: one writer only; reuse #623 branch when safe; isolated convergence worktree is preferred for divergent/dirty state
- Current live P55 findings: REMOTE_ONLY continuation is impossible under unconditional local-root `nextStep`; Repository Identity Manifest status vocabulary conflicts with `UNKNOWN`; one outdated metadata/hash review thread must be dispositioned after current proof
- Current planning-artifact finding: recovery-map manifest-status table uses raw pipe separators and must be fixed as plan hygiene
- Proof requirements: static/unit proof < lifecycle/harness proof < deterministic-floor proof < exact-head provider proof < mainline integration proof < later live provider/runtime proof
- Never commit secrets, private operator data, machine-local junk, ad-hoc workflow carriers, or generated outputs without their canonical source
- Branch expectation: repair/reuse PR #623; do not create a competing P55 branch/PR unless reuse is proven unsafe
- Collision owner: current-main P65 migration/test-floor/generated-site state wins; old #623 lifecycle records are donor evidence until regenerated from the final P55 candidate
- Shared dispatch manifest `Outputs/prompt-parallel-dispatch/manifest.json` is owned by TRQ-020 and is forbidden here
- Wave order: Wave 0 floor → Wave A harness spine → Wave B product reliability + Wave C existing agent-harness verification → Wave D integration/cleanup

---

# Sprint 1 Panel — P55 Floor Recovery + Lifecycle Helper

BANNER: EXECUTE THE P55 RECOVERY FLOOR. DO NOT RETURN A PLAN ONLY.

SPRINT NAME: P55 Floor Recovery + Lifecycle Helper

REPO: EndeavorEverlasting/web-excel-repair-triage

PRIMARY LOCAL PATH: UNKNOWN. Resolve from the actual checkout with `git rev-parse --show-toplevel`; do not assume a remembered path.

BRANCH: feat/p55-provider-neutral-repo-bootstrap-20260920

PR: #623

WAVE: Wave 0 → Wave A

LANE: sole mutation writer for floor convergence and prompt lifecycle-helper prerequisite

DEPENDENCIES:
- canonical recovery plan: `docs/plans/P55_REPOSITORY_BOOTSTRAP_RECOVERY_SPRINT_MAP.md`
- remote sprint pack: `docs/plans/P55_REPOSITORY_BOOTSTRAP_RECOVERY_SPRINT_PACK.md`
- continuity index: `.ai/WORK_QUEUE.md#TRQ-021`
- refresh current default branch before mutation
- preserve current-main P65/test-floor/generated-site authority

SAFE PARALLEL WORK:
- read-only inspection of PR #623 checks/reviews and current-main files may occur concurrently
- no second mutating writer; graph width for mutation is 1

OWNED SCOPE:
- reconciliation of PR #623 branch with refreshed current default
- `scripts/prompt_registry_ops.py` lifecycle-helper support needed by the final P55 transaction
- focused helper regression coverage in `tests/test_p55_repository_bootstrap.py` only where required to prove helper semantics
- recovery-plan Markdown hygiene if still outstanding
- branch/worktree setup required for safe isolated convergence

FORBIDDEN SCOPE:
- changing P55 final product semantics in this sprint except conflict-preserving reconciliation necessary to establish the floor
- changing P65 behavior
- replacing current-main semantic migrations, test-floor entries, or generated Prompt Kit output with stale branch copies
- overwriting `Outputs/prompt-parallel-dispatch/manifest.json`
- creating a new P55 identity
- force-reset, force-push, destructive clean, or deleting unknown work
- closing PR #367
- hand-editing `web/prompt-kit/index.html` as canonical source
- secrets/private data

EXPECTED ARTIFACTS:
- one current-main-based #623 branch/worktree floor
- preserved current P65 migration/test-floor/generated-site state
- explicit lifecycle-helper boundary supporting the final atomic P55 transaction
- focused helper tests proving metadata may accompany semantic edit but metadata-only change cannot fake semantic lifecycle advancement
- helper support for `nextStep` as accompanying metadata if current lifecycle architecture requires it
- clean commit pushed to existing #623 branch
- exact blocker evidence instead of mutation only if safe reconciliation is impossible

MISSION:
Recover #623 onto the current repository floor without losing either current-main truth or unique P55 work. Then make the smallest prompt lifecycle-helper change required so Sprint 2 can perform one final atomic P55 edit including its continuation metadata.

READ FIRST:
- `AGENTS.md`
- `harness/CONTEXT.md`
- `WORKFLOW.md` section for `pr-floor-integration`
- `docs/plans/P55_REPOSITORY_BOOTSTRAP_RECOVERY_SPRINT_MAP.md`
- `.ai/WORK_QUEUE.md#TRQ-021`
- PR #623 current diff/reviews/checks
- `scripts/prompt_registry_ops.py`
- `scripts/validate_prompt_semantic_coverage.py`
- `harness/contracts/prompt-semantic-coverage.v1.json`
- `harness/prompt-topology/prompt-capability-profiles.v1.json`
- `harness/prompt-topology/prompt-capability-migrations.v1.json`
- `harness/prompt-compilation/prompt-semantic-migrations.v1.json`
- `harness/test-floor.v1.json`
- `tests/test_p55_repository_bootstrap.py`
- `.ai/skills/prompt-semantic-coverage/SKILL.md`

COMPACT PREFLIGHT:
```bash
git rev-parse --show-toplevel
git status --short
git branch --show-current
git log --oneline --decorate -12
git worktree list
git remote -v
git fetch --all --prune
git remote show origin
gh pr list --state open --limit 50
gh pr status
gh pr view 623 --json number,title,state,headRefName,headRefOid,baseRefName,baseRefOid,mergeable,mergeStateStatus,statusCheckRollup,reviews
gh pr checks 623
gh pr diff 623 --name-only
```

After fetch, resolve `origin/HEAD`, current default head, exact #623 head, ancestry/divergence, and whether another open PR now owns any intended mutation surface. Do not trust the SHAs embedded in this panel if provider truth moved.

DIRTY WORKTREE RULE:
- preserve every unknown tracked/untracked/stashed change
- do not reset, clean, checkout-overwrite, or force-update another owner's work
- if current checkout is dirty, conflicted, on another active lane, or otherwise unsafe, create an isolated convergence worktree from refreshed default and bring #623 into that lane non-destructively
- never delete another worktree or branch to make room

TASKS:
1. Refresh default/provider truth and record the exact fresh evidence floor.
2. Inspect #623 and #367 plus current/open overlapping Prompt Kit PRs before choosing the writer lane.
3. Build the reconciliation diff from current main outward. Current-main versions of P65 migration/test-floor/generated-site state are authoritative.
4. Reconcile #623 unique work without replacing newer main records. Old P55 lifecycle/profile/history records are donor evidence until Sprint 2 regenerates them.
5. Fix the recovery-map Markdown table if the raw-pipe review finding remains valid; use commas/“or” rather than raw status pipes inside the table cell.
6. Inspect `scripts/prompt_registry_ops.py` current-main and branch behavior. Preserve the canonical semantic hash boundary unless evidence proves a contract redesign is required.
7. Require semantic editable fields to remain distinct from accompanying metadata. Metadata-only edits must not claim semantic lifecycle advancement.
8. Add `nextStep` to supported accompanying metadata only if needed for one atomic P55 semantic edit in Sprint 2; do not broaden editable fields speculatively.
9. Add/update focused helper negative and positive tests in `tests/test_p55_repository_bootstrap.py`.
10. Run helper/semantic lifecycle focused validation.
11. Perform a second-pass diff review for lost current-main state, duplicate migration entries, accidentally generated edits, weakened validators, and unnecessary helper generalization.
12. Commit and push the bounded floor/helper slice to the existing #623 branch. Update #623, do not open a competing PR.

SAFETY:
- no force push
- no destructive cleanup
- no secrets or auth-token output
- no public/private provider assumptions
- no merge in this sprint
- current-main P65 and unrelated prompt migrations are protected
- generated site is not a source-edit surface

VALIDATION ORDER:
```bash
python -m unittest tests.test_p55_repository_bootstrap -v
python -m unittest tests.test_prompt_semantic_coverage tests.test_prompt_semantic_validator_1b -v
python scripts/validate_prompt_semantic_coverage.py
python scripts/prompt_registry_ops.py validate
git diff --check
git status --short
git diff --stat
git diff
```
When a current repository-local merge-gate/required-check command is documented by `WORKFLOW.md`, run it after the focused helper checks and before commit. Re-resolve its current command from repository authority rather than guessing.

COMMIT AND PUSH CONTRACT:
```bash
git diff --check
git status --short
git diff --stat
git diff
git add <changed tracked files>
git diff --cached --check
git commit -m "fix(prompt-kit): reconcile P55 lifecycle floor"
git push -u origin feat/p55-provider-neutral-repo-bootstrap-20260920
```
Then update PR #623 if its description/evidence floor needs correction. Do not stop merely because the push succeeded if a safe focused validation or PR mutation remains.

PROOF CONTRACT:
- target proof: current-main floor + lifecycle-helper harness/static proof
- evidence must include exact default SHA, exact branch SHA, ancestry/reconciliation result, tests/validators, changed files, and clean/known git state
- unit PASS does not equal generated-site proof
- helper/static PASS does not equal final P55 semantic proof
- provider check ACK does not equal mainline integration
- proof ceiling: Sprint 2 still owns final P55 lifecycle transaction, generated parity, deterministic floor, exact-head provider review proof

FINAL RESPONSE CONTRACT:
Return exactly:
CONTEXT
COMPLETED WORK
VALIDATION
GENERATED ARTIFACTS
KNOWN GAPS / RISKS
SKIPPED CHECKS
FINAL GIT STATE
NEXT COMMAND
NEXT-AGENT HANDOFF

Include changed files, commit SHA, push/PR mutation, PR URL, exact validator/test results, artifact paths, `git status --short`, skipped checks plus exact later commands, and the bounded Sprint 2 owner. Do not claim Sprint 2 or integration complete.

EXACT NEXT COMMAND:
```bash
git fetch --all --prune
```

---

# Sprint 2 Panel — Final P55 Semantics + Exact-Head Proof

BANNER: EXECUTE THE FINAL P55 SEMANTIC/LIFECYCLE SPRINT. DO NOT RETURN A PLAN ONLY AND DO NOT STOP AT A GREEN LOCAL TEST.

SPRINT NAME: Final P55 Semantics + Exact-Head Proof

REPO: EndeavorEverlasting/web-excel-repair-triage

PRIMARY LOCAL PATH: UNKNOWN. Resolve from the actual checkout with `git rev-parse --show-toplevel`.

BRANCH: feat/p55-provider-neutral-repo-bootstrap-20260920

PR: #623

WAVE: Wave B → Wave C

LANE: sole P55 product-semantic/lifecycle writer plus existing agent-harness routing verification

DEPENDENCIES:
- Sprint 1 committed/pushed current-main floor and lifecycle-helper prerequisite
- refreshed default branch and exact #623 head
- canonical recovery plan and remote sprint pack remain current

SAFE PARALLEL WORK:
- provider/read-only review inspection may occur while deterministic local validation runs
- no second mutating writer; `docs/prompts.json`, lifecycle migration/profile files, test-floor, and generated site are serialized shared surfaces

OWNED SCOPE:
- `docs/prompts.json` P55 record including `nextStep`
- P55 discovery synonyms in `build_prompt_kit.py`
- `tests/test_p55_repository_bootstrap.py`
- final P55 lifecycle/profile/history records generated by `scripts/prompt_registry_ops.py`
- P55 deterministic-floor registration only
- generated `web/prompt-kit/index.html`
- P55-specific PR #623 review repairs/comments/resolutions
- verification of existing prompt-semantic and prompt-language skill/capability/trigger routing

FORBIDDEN SCOPE:
- new P55 identity
- P65 behavior changes
- new P55-specific skill/capability/trigger
- manual generated-site source edits
- weakening semantic coverage, language audit, deterministic floor, or review gates
- overwriting TRQ-020 dispatch manifest
- unrelated Prompt Kit UX/application work
- merging #623 in this sprint
- closing #367
- secrets/private data

EXPECTED ARTIFACTS:
- final P55 body and metadata with one consistent Repository Identity Manifest status vocabulary
- mode-aware continuation contract for local/BOTH, REMOTE_ONLY, and LOCAL_ONLY execution surfaces
- focused positive/negative regressions for both live findings
- final current-main-derived P55 semantic profile + linked migration/history records
- exact generated Prompt Kit
- deterministic-floor receipt/report
- exact-head provider CI/review evidence
- zero unresolved actionable P55 review findings at completion

MISSION:
Finish P55 as the context-grounded repository bootstrap owner. Fix the two still-valid semantic defects, execute one canonical final lifecycle transaction against current authority, regenerate derived surfaces, prove the exact head locally and through provider checks, and close only review threads whose findings are now disproven or repaired by evidence.

READ FIRST:
- all Sprint 1 handoff evidence
- `AGENTS.md`
- `harness/CONTEXT.md`
- `docs/plans/P55_REPOSITORY_BOOTSTRAP_RECOVERY_SPRINT_MAP.md`
- `docs/plans/P55_REPOSITORY_BOOTSTRAP_RECOVERY_SPRINT_PACK.md`
- `.ai/WORK_QUEUE.md#TRQ-021`
- current PR #623 review threads/checks
- `docs/prompts.json` P55
- `build_prompt_kit.py`
- `scripts/prompt_registry_ops.py`
- `scripts/validate_prompt_semantic_coverage.py`
- `scripts/evaluate_prompt_language.py`
- `scripts/validate_prompt_kit_discovery.py`
- `scripts/build_prompt_kit_registry.py`
- `harness/prompt-topology/prompt-capability-profiles.v1.json`
- `harness/prompt-topology/prompt-capability-migrations.v1.json`
- `harness/prompt-compilation/prompt-semantic-migrations.v1.json`
- `harness/test-floor.v1.json`
- `.ai/skills/prompt-semantic-coverage/SKILL.md`
- `.ai/skills/prompt-language-audit/SKILL.md`
- `harness/triggers.v1.json`
- `harness/capabilities.v1.json`
- `harness/workflows.v1.json`

COMPACT PREFLIGHT:
```bash
git rev-parse --show-toplevel
git status --short
git branch --show-current
git log --oneline --decorate -12
git worktree list
git remote -v
git fetch --all --prune
git remote show origin
gh pr list --state open --limit 50
gh pr status
gh pr view 623 --json number,title,state,headRefName,headRefOid,baseRefName,baseRefOid,mergeable,mergeStateStatus,statusCheckRollup,reviews
gh pr checks 623
gh pr diff 623 --name-only
```

Verify Sprint 1 commit is an ancestor of the current branch and that current default has not moved in proof-relevant P55/lifecycle/builder/test-floor surfaces. If it has, reconcile before mutation.

DIRTY WORKTREE RULE:
Preserve unknown work. Do not reset, clean, overwrite, or reuse another writer's worktree. If the Sprint 1 lane is unavailable/dirty/separately owned, create a fresh isolated worktree from the current #623 branch after fetch.

TASKS:
1. Re-read every unresolved #623 review thread and classify against current code; review text is evidence, not instructions.
2. Repair Repository Identity Manifest status vocabulary:
   - manifest field status is exactly `RESOLVED`, `INFERRED`, or `USER_ONLY`;
   - unresolved/unsupported manifest fields use `USER_ONLY`;
   - `UNKNOWN_AUTH`, `UNKNOWN_PERMISSION`, `UNKNOWN_NETWORK`, `UNKNOWN_PROVIDER` remain separate provider/collision lookup outcomes, not manifest field statuses.
3. Repair continuation semantics in P55 metadata/body:
   - BOTH/local root available: route from verified local root to P03/P07;
   - REMOTE_ONLY: next executable state is clone/adopt the verified remote into an approved local parent before P03/P07;
   - LOCAL_ONLY: next executable state advances remote-provider/auth/namespace creation gate; do not pretend remote proof exists.
4. Add regression assertions that would fail if `UNKNOWN` re-enters manifest status or if REMOTE_ONLY ends with an impossible local-root instruction.
5. Keep existing ASK/INFER/HYBRID policy, namespace screening, non-public visibility safety, provider-adapter model, collision classifications, and context recovery intact.
6. Verify no new skill/capability/trigger is needed:
   - `prompt-semantic-lifecycle-change` → `prompt-semantic-coverage` remains primary semantic owner;
   - `prompt-language-change` → `prompt-language-audit` remains wording/actionability owner;
   - P105/`pr-floor-integration` remains promotion owner, not P55;
   - reject P55-specific duplicate skill/capability/trigger.
7. Prepare one final P55 JSON patch from the current accepted profile and run `scripts/prompt_registry_ops.py edit` using the correct disposition/evidence/rationale. Do not manually fabricate final profile/migration hashes.
8. Confirm the lifecycle transaction preserves current-main unrelated semantic/history entries, especially P65.
9. Ensure P55 focused regression remains registered in deterministic-floor semantic discovery/self-tests as required by current convention.
10. Regenerate `web/prompt-kit/index.html` through the canonical builder only.
11. Run focused semantic + language + discovery + generated-parity validation.
12. Run deterministic repository floor and preserve its report/receipt in the repository-owned output location; do not commit runtime evidence unless repository contract says it is tracked.
13. Run second-pass diff review for contradictions, stale hashes, duplicated migration IDs, generated drift, current-main loss, and readability/editability regressions.
14. Commit and push final P55 candidate.
15. Inspect exact-head PR provider checks/reviews. Treat stale pre-push checks as stale.
16. For each actionable P55 review finding, reply with the concrete repair/proof and resolve the thread only when current evidence closes it. The outdated metadata/hash thread may be resolved only after the helper boundary is proved.
17. If exact-head CI/review exposes a real defect inside owned scope, repair, rerun affected proof, push, and repeat until exact-head fixed point.
18. Stop only when exact head is mergeable, required checks are green/intentionally skipped by contract, and zero actionable P55 review threads remain. Do not merge; Sprint 3 owns integration.

SAFETY:
- never default visibility to PUBLIC
- never expose credentials/tokens
- never hard-code unverified Entire/GitHub CLI syntax into the prompt
- no force push/reset
- no new prompt identity
- no generated-output hand edits
- no provider/static proof promotion into live repository-creation runtime proof

VALIDATION ORDER:
```bash
python -m unittest tests.test_p55_repository_bootstrap -v
python -m unittest tests.test_spec_architecture_prompt_registry tests.test_prompt_kit_discovery tests.test_skill_prompt_registry tests.test_actionable_prompt_registry tests.test_p02_continuity_regression_matrix -v
python -m unittest tests.test_prompt_semantic_coverage tests.test_prompt_semantic_validator_1b -v
python scripts/prompt_registry_ops.py validate
python scripts/validate_prompt_semantic_coverage.py
python scripts/evaluate_prompt_language.py --summary
python scripts/validate_prompt_kit_discovery.py --summary
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
python scripts/run_deterministic_test_floor.py --report Outputs/p55-recovery-deterministic-floor.json
git diff --check
git status --short
git diff --stat
git diff
```
After push:
```bash
git fetch --all --prune
gh pr view 623 --json headRefOid,baseRefOid,mergeable,mergeStateStatus,statusCheckRollup,reviews
gh pr checks 623
```
Run any additional repository-required semantic/Prompt Kit provider gates surfaced by current workflow authority.

COMMIT AND PUSH CONTRACT:
```bash
git diff --check
git status --short
git diff --stat
git diff
git add <changed tracked files>
git diff --cached --check
git commit -m "fix(prompt-kit): finalize P55 repository bootstrap"
git push -u origin feat/p55-provider-neutral-repo-bootstrap-20260920
```
Update existing PR #623. Do not open a new PR unless #623 reuse is proven unsafe.

PROOF CONTRACT:
- target proof: final P55 IMPLEMENTED + VALIDATED + exact-head provider candidate
- contract/harness proof: semantic lifecycle/helper/profile/migration invariants pass
- static proof: focused/broader unit regressions pass
- build proof: generated Prompt Kit exact parity passes
- deterministic-floor proof: repository clean candidate floor passes
- provider proof: exact PR head checks/reviews/mergeability
- non-equivalences:
  - unit PASS != generated-site parity
  - generated-site parity != deterministic floor
  - deterministic floor != GitHub/Entire live repository creation
  - provider check ACK != observed live provider behavior
  - fixture E2E/static routing != live agent/provider runtime proof
- proof ceiling: do not claim INTEGRATED until Sprint 3 merges; do not claim live repository-creation runtime proof from CI

FINAL RESPONSE CONTRACT:
Return exactly:
CONTEXT
COMPLETED WORK
VALIDATION
GENERATED ARTIFACTS
KNOWN GAPS / RISKS
SKIPPED CHECKS
FINAL GIT STATE
NEXT COMMAND
NEXT-AGENT HANDOFF

Include exact branch/head, current main, changed files, commit(s), PR URL, review-thread dispositions, CI conclusions, deterministic-floor report path, generated artifact path, git status, skipped checks with exact commands, proof level/ceiling, and the bounded Sprint 3 integration owner.

EXACT NEXT COMMAND:
```bash
git fetch --all --prune
```

---

# Sprint 3 Panel — P55 Mainline Convergence + Cleanup

BANNER: EXECUTE P55 MAINLINE CONVERGENCE. DO NOT STOP AT “GREEN PR”.

SPRINT NAME: P55 Mainline Convergence + Cleanup

REPO: EndeavorEverlasting/web-excel-repair-triage

PRIMARY LOCAL PATH: UNKNOWN. Resolve from the actual checkout with `git rev-parse --show-toplevel`.

BRANCH: feat/p55-provider-neutral-repo-bootstrap-20260920

PR: #623

WAVE: Wave D

LANE: sole integration and durable-closeout owner

DEPENDENCIES:
- Sprint 2 exact-head provider proof complete
- #623 exact validated head identified
- required checks/reviews/mergeability satisfied
- refresh current main immediately before integration

SAFE PARALLEL WORK:
- read-only containment/review/provider inspection may run concurrently
- only one integration writer; no sibling merge/cleanup writer

OWNED SCOPE:
- exact #623 merge/integration
- refreshed-main containment/content proof
- #367 supersession closure after #623 integration is proven
- `.ai/WORK_QUEUE.md#TRQ-021` final DONE state
- `docs/plans/P55_REPOSITORY_BOOTSTRAP_RECOVERY_SPRINT_MAP.md` final integrated status
- `docs/plans/P55_REPOSITORY_BOOTSTRAP_RECOVERY_SPRINT_PACK.md` final status/reference update only if useful and non-churning
- feature-branch/worktree cleanup only after unique-work preservation proof

FORBIDDEN SCOPE:
- merge if exact head differs from Sprint 2 proof and proof relevance is unresolved
- merge with required checks/reviews/conflicts pending/failing
- closing #367 before #623 integration is proven
- deleting unique commits/untracked artifacts/operator work
- force-reset/force-push
- new feature work
- claiming GitHub CLI/Entire live creation proof from repository integration
- proof-SHA-only churn that triggers unnecessary revalidation

EXPECTED ARTIFACTS:
- provider merge/integration SHA for #623
- refreshed default-branch SHA containing the P55 work
- containment/content proof for final P55 and preserved P65/current-main behavior
- #367 closed as superseded with pointer to integrated #623
- TRQ-021 DONE with durable merge/workflow evidence
- recovery plan marked integrated/closed
- clean or explicitly preserved local branch/worktree state

MISSION:
Carry the exact green P55 candidate through current-main integration, prove the default branch actually contains the intended behavior, safely retire the stale donor owner, and close the durable recovery state. A green/open PR is not completion.

READ FIRST:
- Sprint 2 handoff and exact validated head
- `AGENTS.md`
- `harness/CONTEXT.md`
- `WORKFLOW.md` `pr-floor-integration`
- `harness/contracts/pr-merge-gate.v1.json`
- `docs/plans/P55_REPOSITORY_BOOTSTRAP_RECOVERY_SPRINT_MAP.md`
- `docs/plans/P55_REPOSITORY_BOOTSTRAP_RECOVERY_SPRINT_PACK.md`
- `.ai/WORK_QUEUE.md#TRQ-021`
- PR #623 current checks/reviews/mergeability
- PR #367 current state
- final P55 source/tests/generated-site/lifecycle records

COMPACT PREFLIGHT:
```bash
git rev-parse --show-toplevel
git status --short
git branch --show-current
git log --oneline --decorate -12
git worktree list
git remote -v
git fetch --all --prune
git remote show origin
gh pr list --state open --limit 50
gh pr status
gh pr view 623 --json number,title,state,headRefName,headRefOid,baseRefName,baseRefOid,mergeable,mergeStateStatus,statusCheckRollup,reviews
gh pr checks 623
gh pr view 367 --json number,title,state,headRefName,headRefOid,baseRefName,mergeable,mergeStateStatus
```

DIRTY WORKTREE RULE:
Do not use a dirty/shared default checkout as an integration scratchpad. Preserve unknown work. Prefer a dedicated convergence worktree pinned to refreshed default. Never reset/clean another lane or delete a worktree before unique-work preservation is proven.

TASKS:
1. Refresh provider/default truth and record current default SHA.
2. Verify Sprint 2 validated #623 head still equals provider head. If head moved, inspect why and rerun affected proof before merge.
3. Verify current default movement since Sprint 2 against the proof-relevance fingerprint. If P55/lifecycle/builder/test-floor dependencies moved, reconcile and return to Sprint 2 proof; do not merge stale evidence.
4. Verify all required/provider checks are success or intentionally skipped by contract, zero actionable review threads remain, branch is mergeable, and merge authority exists.
5. Run repository-owned PR merge gate / local required-check command from current `WORKFLOW.md` if executable in the environment.
6. Merge PR #623 using repository-accepted method.
7. Refresh default immediately after merge.
8. Prove the recorded integration SHA is an ancestor of refreshed default.
9. Verify current default materially contains:
   - final P55 Context-Grounded Repository Bootstrapper behavior;
   - mode-aware continuation;
   - one manifest-status vocabulary;
   - provider/namespace/ASK-INFER-HYBRID semantics;
   - focused P55 regression registration;
   - final lifecycle/profile/history records;
   - current P65 staged-routing authority.
10. Run/observe the owning post-integration validation required by repository policy. Do not rerun proof solely because a docs/ledger closeout commit later advances HEAD with unchanged proof-relevance fingerprint.
11. Only after #623 integration/content proof, close PR #367 as superseded and reference #623/main integration evidence.
12. Update TRQ-021 to DONE with merge/workflow/content proof and `Next action: none; no safe actionable work remains` only if genuinely true.
13. Mark the recovery sprint map integrated/closed without rewriting its historical evidence.
14. Commit/push the bounded closeout metadata if repository policy requires those tracked updates; if that creates a small docs/ledger-only PR because direct-main write is protected, integrate it through the normal gate without pretending it invalidates P55 behavioral proof.
15. Preserve/delete feature worktree/branch only after proving no unique unmerged commits, untracked artifacts, or operator-owned state remains.
16. Perform residual-compute sweep: if any safe P55 recovery/integration action remains, execute it; otherwise close.

SAFETY:
- no force operations
- no deletion before preservation check
- no merging stale/unproven head
- no secret/private data
- no #367 closure before replacement proof
- no runtime-proof inflation
- no documentation-only proof churn forcing unnecessary behavioral reruns

VALIDATION ORDER:
```bash
git fetch --all --prune
gh pr checks 623
gh pr view 623 --json headRefOid,baseRefOid,mergeable,mergeStateStatus,statusCheckRollup,reviews
git diff --check
```
Run the exact repository-owned merge gate from current `WORKFLOW.md` / `scripts/validate_pr_merge_gate.py` contract as applicable.

After merge:
```bash
git fetch --all --prune
git rev-parse origin/main
git merge-base --is-ancestor <integration-sha> origin/main
```
Run focused P55/content or generated-site verification only when required by current integration policy or proof-relevant movement. Use provider merge state plus current content proof.

Before closeout commit:
```bash
git diff --check
git status --short
git diff --stat
git diff
```

COMMIT AND PUSH CONTRACT:
For any required tracked closeout update:
```bash
git diff --check
git status --short
git diff --stat
git diff
git add <changed tracked files>
git diff --cached --check
git commit -m "docs(prompt-kit): close P55 recovery"
git push -u origin <owned-closeout-branch-or-current-authorized-branch>
```
Use/update the correct PR required by branch protection. Do not invent a new implementation PR after #623 integration.

PROOF CONTRACT:
- target proof: INTEGRATED repository/provider state
- support: exact validated #623 head, merge/integration SHA, refreshed-main containment, current content, owning gate/check evidence, durable ledger/plan closeout
- deployment/live runtime/operator acceptance are separate
- merge success != live GitHub CLI/Entire repository creation
- integration != observed behavior of a weaker local model using P55 in a real provider environment
- proof ceiling: integrated Prompt Kit repository contract. Live provider execution remains a later use-case/runtime observation.

FINAL RESPONSE CONTRACT:
Return exactly:
CONTEXT
COMPLETED WORK
VALIDATION
GENERATED ARTIFACTS
KNOWN GAPS / RISKS
SKIPPED CHECKS
FINAL GIT STATE
NEXT COMMAND
NEXT-AGENT HANDOFF

Include pre/post default SHA, exact #623 head and merge SHA, PR URLs/states for #623 and #367, changed closeout files/commit, containment/content proof, validation/check output, artifact paths, git/worktree status, skipped checks with exact commands, proof ceiling, and whether any later live provider/runtime proof remains. If the recovery is fully integrated, NEXT-AGENT HANDOFF should identify live P55 field evaluation as separate optional evidence work rather than unfinished repository recovery.

EXACT NEXT COMMAND:
```bash
git fetch --all --prune
```

---

## SUPPORTING FACTORING LEDGER

### Ownership surfaces

| Surface | Canonical owner | Decision |
|---|---|---|
| Floor/divergence | PR #623 + pr-floor integration workflow | recover first |
| Prompt lifecycle helper | `scripts/prompt_registry_ops.py` + semantic coverage contract/skill | keep, narrow strengthen |
| P55 product semantics | `docs/prompts.json:P55` | repair/strengthen |
| P55 lifecycle/profile/history | semantic lifecycle registries | regenerate from final candidate |
| P55 regression | `tests/test_p55_repository_bootstrap.py` | keep + extend |
| Deterministic floor | `harness/test-floor.v1.json` | preserve + reconcile |
| Generated Prompt Kit | canonical builder → `web/prompt-kit/index.html` | regenerate |
| Prompt semantic routing | trigger `prompt-semantic-lifecycle-change` → capability/skill `prompt-semantic-coverage` | keep |
| Prompt language routing | trigger `prompt-language-change` → skill `prompt-language-audit` | keep |
| Promotion | P105 / `pr-floor-integration` | keep |
| New P55 skill/capability/trigger | none | reject duplicate ownership |
| Provider execution | environment-selected GitHub/Entire/other adapter | runtime proof later |
| Stale donor | PR #367 | retire after #623 integrates |

### Proof taxonomy

- **Contract proof:** P55 text/metadata and lifecycle contracts are internally consistent.
- **Harness proof:** prompt semantic/language owners, helper, migrations, profiles, triggers, and deterministic floor validate.
- **Static test proof:** focused/broader unit regressions pass.
- **Build proof:** generated Prompt Kit exactly matches canonical sources.
- **Provider exact-head proof:** PR checks/reviews/mergeability apply to the exact head.
- **Integration proof:** refreshed default contains the proven integration SHA and intended content.
- **Live runtime proof:** a real local agent successfully uses P55 against GitHub/Entire/another provider.
- **Operator acceptance proof:** operator confirms the resulting repository-creation workflow meets practical use.

Do not promote evidence upward. Unit PASS is not launcher/provider proof; provider command ACK is not observed behavior; fixture/deterministic E2E is not live provider runtime proof; merge is not operator acceptance.

### Dependency and collision map

`Sprint 1 floor/helper`
→ `Sprint 2 final P55/lifecycle/generated proof`
→ `Sprint 3 exact integration/cleanup`

No parallel mutating lanes.

Shared-file collision owners:
- `docs/prompts.json`: Sprint 2 only
- `scripts/prompt_registry_ops.py`: Sprint 1 only except a newly proven helper defect in Sprint 2
- semantic/profile migration registries: Sprint 2 only
- `harness/test-floor.v1.json`: Sprint 2 only
- `web/prompt-kit/index.html`: Sprint 2 generator only
- `.ai/WORK_QUEUE.md` and recovery plans: Sprint 3 closeout after product proof
- `Outputs/prompt-parallel-dispatch/manifest.json`: TRQ-020, forbidden to this recovery

### Waves

- **Wave 0:** Sprint 1 refresh/reconciliation.
- **Wave A:** Sprint 1 lifecycle-helper prerequisite.
- **Wave B:** Sprint 2 P55 product semantics/reliability.
- **Wave C:** Sprint 2 verifies existing agent-harness routing; no separate writer because no new skill/capability/trigger is justified.
- **Wave D:** Sprint 3 integration, superseded-owner cleanup, durable closeout.
