# Operant Versioning System

## Decision

Operant uses repository-owned pre-1.0 Semantic Versioning with `OPERANT_VERSION` as the single human-facing product release authority. Exact Git commit and generated-artifact identities remain independent freshness proof.

The original repository-owned cutover was `0.2.0`. Operant 0.1 was established by PR #329; later releases advance only through `OPERANT_VERSION`, while this document describes the deterministic policy rather than duplicating the current version value.

## Reference architecture evidence

Evidence refreshed 2026-09-09.

| Reference | Inspected identity | License | Observed mechanism | Disposition |
|---|---|---|---|---|
| `googleapis/release-please` | `c65408d9f68b2772c6e61dcdc4a8b6f5969bb4e1` | Apache-2.0 | Parses accepted commit history, computes a next version, maintains a reviewable release PR, updates changelog/version surfaces, then tags/releases the exact merged release commit. Generic and JSON updaters synchronize extra version mirrors. | **ADAPT** — emulate staged release PR + synchronized mirrors + exact post-merge tag, but do not adopt its path/component model wholesale in this multi-product repository. |
| `semantic-release/commit-analyzer` | `b281a840fd7e3271d553afb7ddab3494d568873d` | MIT | Parses Conventional Commits, applies configured/default release rules, and chooses the highest release type across accepted commits. | **ADOPT mechanism** — deterministic per-commit classification and highest-bump reduction. Do not adopt the Node publishing stack. |
| `changesets/changesets` | `5e54cd97cabac92f02d1c6f4439ac226e347d9bf` | MIT | Assembles explicit developer-authored changeset records into a release plan and applies synchronized version/changelog changes; its action can create/update a version PR. | **REJECT as primary intake** — strong auditability, but requiring each developer/agent to author a changeset conflicts with AFK natural-development derivation. |

No upstream source code is copied. Only workflow/state-model mechanisms are emulated.

## Solved baseline versus gap

### Already solved internally

- `harness/contracts/operant-product-identity.v1.json` owns Operant identity and transition boundaries.
- `scripts/validate_operant_product_identity.py` and the harness/pre-push registration fail closed on identity drift.
- `web/prompt-kit/index.html` plus `scripts/build_prompt_kit_registry.py` already have deterministic generated-site identity and byte/content proof.
- P130 (`Repository Versioning System Establisher`) already defines the repository-level version-policy doctrine; P15 remains downstream merge/release execution ownership.

### Available to emulate externally

- Conventional-commit classification and highest bump selection.
- Reviewable, automatically prepared release candidates plus a machine-readable external publication request for both first publication and later PR-head refreshes.
- Synchronized version mirrors generated from one authority.
- Tag/release creation only after the version change is validated on the default branch.

### Project-specific gap

Operant lives inside a multi-product repository. A root-wide release tool would incorrectly treat Billing/Roster/Triage commits as Operant releases, while a single-directory component model would miss Operant changes spread across registry, web, launcher, harness, and compatibility surfaces. Therefore Operant needs a small repository-owned path/scope relevance policy rather than a foreign package-directory assumption.

GitHub repository settings prohibit the workflow `GITHUB_TOKEN` from creating the first pull request even when the job has `pull-requests: write`. A second provider boundary was observed on 2026-09-18: when `github-actions[bot]` refreshed an already-open release PR head, pull-request workflows entered `action_required` with zero jobs. Re-authoring the exact same candidate tree through the external provider caused the normal PR suites to execute. Therefore Actions owns release planning, deterministic candidate generation, validation, and staging-branch pushes; an external provider/agent owns every mutation of the stable review head, both creating/advancing it for first publication and refreshing it later. Actions never pushes a branch that may become the review head. This separates deterministic release computation from provider event provenance instead of weakening CI.

## Canonical authority and synchronized surfaces

- **Authority:** `OPERANT_VERSION` — full `MAJOR.MINOR.PATCH` only.
- **Mirror:** `harness/contracts/operant-product-identity.v1.json` → `product_version`.
- **Mirror:** same contract → `compatibility.visible_version`.
- **Generated mirrors:** HTML `<title>`, header version, and bottom version badge in `web/prompt-kit/index.html`.
- **Independent identities:** schema/protocol strings such as `operant-product-identity/v1`; prompt/resource schemas; exact Git SHA; canonical-content SHA-256. These do not bump merely because the product version changes.

## Pre-1.0 bump matrix

| Accepted release-relevant change | Bump |
|---|---|
| `feat:` | MINOR |
| Conventional Commit with `!` or `BREAKING CHANGE:` while `0.x` | MINOR |
| `fix:`, `perf:`, `revert:` | PATCH |
| `docs:`, `test:`, `refactor:`, `style:`, `chore:`, `ci:`, `build:` | no bump |
| generated-output-only changes | no bump |
| unrecognized or non-Conventional release-relevant commit | **fail closed**; classification is the narrow judgment gate |

Promotion from `0.x` to `1.0.0` is never inferred from an ordinary breaking commit. It requires an explicit operator-reviewed declaration that Operant's public compatibility contract is stable enough for 1.0. After 1.0, breaking changes map to MAJOR.

The release type for a set of accepted commits is the highest applicable bump: MAJOR > MINOR > PATCH > none. Running the same accepted range twice yields the same result.

## Multi-product relevance boundary

Product-specific Operant paths are release-relevant directly, including the renderer inputs `docs/prompts.json` and `docs/reference.json`. Shared repository governance/harness indexes are release-relevant only when their Conventional Commit scope is `operant` or `prompt-kit`. Generated `web/prompt-kit/index.html` alone never creates a bump; it mirrors canonical source changes.

The exact patterns are machine-owned in the `release_versioning` block of `harness/contracts/operant-product-identity.v1.json` and consumed by `scripts/operant_version.py`.

## AFK lifecycle

1. Developers and agents work normally and use Conventional Commit semantics for Operant-affecting commits.
2. A push to `main` runs the Operant version workflow.
3. The planner starts from the latest reachable `operant-v*` tag; before the first canonical tag it uses the PR #329 identity merge as the bootstrap floor.
4. Non-Operant and no-bump-only work produces no release candidate.
5. Release-worthy work produces a deterministic plan, a validated candidate, and `Outputs/operant-release-pr-request.json` plus `Outputs/operant-release-pr.md`. Actions always writes only to `automation/operant-release-staging-vX.Y.Z`. The stable review head remains `automation/operant-release-vX.Y.Z` (or the already-open release PR head) and is never pushed or edited by Actions.
6. The external provider/agent consumes the exact publication request. For first publication it creates or fast-forwards the stable review head from the staged candidate and then opens the PR. For an existing PR it reads the staged candidate SHA/tree, current review-head SHA, and source-main SHA, creates a non-force two-parent convergence commit whose tree is the validated candidate tree, then fast-forwards the stable review head and updates the PR metadata. The two parents preserve both review-head ancestry and the accepted mainline dependency. Pull-request CI then evaluates an externally authorized head mutation; stale-candidate validation still rejects a version/changelog that no longer matches current `main`.
7. After the release PR reaches `main`, the same workflow validates the exact mainline version change, creates `operant-vX.Y.Z`, and creates the GitHub Release against that exact commit. Manual `workflow_dispatch` runs are pinned to `main` so unaccepted feature refs cannot plan a release.
8. The tag is release identity; rollback means redeploying/restoring a previously tagged commit/artifact. Versions are never decremented, renamed, or reused.

## Commands

```bash
python scripts/operant_version.py current
python scripts/operant_version.py plan --output Outputs/operant-version-plan.json
python scripts/operant_version.py apply --plan Outputs/operant-version-plan.json
python scripts/operant_version.py validate
python scripts/operant_version.py validate-release-candidate --base origin/main
python scripts/validate_operant_product_identity.py --summary
python scripts/operant_release_pr_request.py --version X.Y.Z --source-sha <main-sha> --head <review-head> --candidate-branch <candidate-branch> --candidate-sha <candidate-sha> --candidate-tree-sha <tree-sha> --output Outputs/operant-release-pr-request.json --body-output Outputs/operant-release-pr.md
python -m unittest tests.test_operant_product_identity tests.test_operant_versioning_workflow -v
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
```

## Proof ceiling

Repository tests and pull-request CI can prove classification, idempotent version calculation, path relevance, mirror synchronization, generated-site parity, full-push version-change detection, deterministic publication-request generation, staging ownership, and workflow syntax/execution in the tested event. A successful mainline run proves only that the release candidate was generated, validated, committed, and pushed to its candidate/staging branch and that an exact external-publication request was emitted. Mutation of the review PR head is provider/runtime proof and must preserve the request's candidate tree plus review-head/mainline ancestry without force. Exact GitHub Release/tag creation is proven only after a version-changing commit reaches `main` and the push workflow completes.