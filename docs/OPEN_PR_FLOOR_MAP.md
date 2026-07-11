# Open PR Floor Map

## Purpose

Keep the repository floor legible before adding or merging more workbook validator and product layers.

This map is intentionally coordinator-only. It does not claim workbook repair, Web Excel acceptance, operator acceptance, or new validator implementation. It records current open PR posture, safe merge lanes, collision risks, and next bases so future sprints do not stack work on ambiguous branches.

## Inspection snapshot

- Repository: `EndeavorEverlasting/web-excel-repair-triage`
- Default branch: `main`
- Current inspected `main` head: `3d18817f89232306cc2e7e00ed7354c43c5c1afb`
- Open PR source: GitHub open PR listing, limit 20/30
- Local worktree: not available in the connector environment
- Local dirty/conflict state: unknown; must be checked before local edits
- Local worktrees: unknown; must be checked with `git worktree list`

## Current open PR floor

| PR | Branch | Type | Current posture | Floor decision |
| --- | --- | --- | --- | --- |
| #53 | `fix/web-excel-relationship-target-audit` | executable validator / package-shape guardrail | Current, mergeable. Adds `.rels` relationship target auditing to `triage/web_excel_compatibility_rules.py` with focused tests. Artifact engine CI reported failure at last coordinator check. | Treat as the relationship-audit validator lane. Review failure before merge. Do not stack broader package-hygiene work here unless the sprint explicitly owns this PR. |
| #52 | `docs/open-pr-floor-map` | coordinator docs / floor map | Current map branch. Docs-only. Exists to keep PR order, branch bases, and acceptance-language guardrails visible. Artifact engine CI reported failure at last prior check even though the change is docs-only. | Safe floor doc lane. Keep current or merge once CI/failure context is understood. |
| #51 | `docs/workbook-copy-surface-ooxml-lessons` | executable validator + docs / prompt-kit package hygiene | Current, mergeable. No longer docs-only: adds `triage/workbook_package_hygiene.py`, tests, workflow wiring, and prompt-kit package/clipboard records. Artifact engine CI reported failure at last coordinator check. | Treat as the broader workbook-package-hygiene validator lane. Do not call it docs-only. Inspect overlap with #53 before merge. |
| #50 | `feat/nw-prj-admin-log-project-team-generator-2026-06-04` | product generator | Mergeable product lane. Builds on output-policy and company-style docs; manual Desktop/Web Excel/operator acceptance remains pending in PR body. | Do not treat as floor. Rebase/review only after floor/policy/doc dependencies are settled. |
| #49 | `docs/admin-log-style-2026-06-04` | docs / accepted layout contract | Mergeable docs lane for Project Team layout rules and visual acceptance contract. | Land before #50 if that product lane continues. |
| #48 | `feat/neuron-track-hours-repairfree-reference-gate-2026-06-04` | validator/product gate | Mergeable. Adds Bonita repair-free profile gate; depends on operator-local golden zip and manual Excel for Web proof. | Review separately. Do not claim Web Excel acceptance from local/package checks. |
| #46 | `feat/artifact-emulator-output-policy-2026-06-04` | floor / output policy | Mergeable floor/policy PR. Generalizes source immutability and output layout policy. Several product PRs depend on this concept. | High-priority floor candidate after #52/#51/#53 disposition is clear. |
| #45 | `feat/candidate-neuron-track-hours-2026-06-04` | product generator | Not mergeable. Candidate workbook generator branch. | Do not stack work here. Rebase or supersede after #46 and related docs settle. |
| #40 | `docs/client-coordination-roles-2026-06-03` | docs / classification doctrine | Mergeable older docs lane for client-coordination and Rezaul classification doctrine. | Merge if still canonical; otherwise close with replacement citation. |
| #34 | `feat/april-may-billing-summary-engine-2026-06-02` | bundled product engines | Not mergeable. Large older bundled engine PR with known private-asset test gaps. | Avoid as a base. Split/supersede before adding layers. |

## Current center of gravity

The repo has moved from pure docs/floor work into two active package-validator lanes:

1. `#51` broader workbook package hygiene and prompt-kit clipboard record.
2. `#53` narrower Web Excel relationship-target auditing.

These lanes likely overlap conceptually around ZIP/XML package validation. They should be inspected together before either becomes the next base for additional validator work.

## Recommended landing / review order

1. Review current CI failure context for #52, #51, and #53.
2. Decide whether #53 should merge before, after, or into #51.
3. Keep #52 as the floor map only if it remains accurate after the #51/#53 decision.
4. Land durable floor/policy docs before product generator branches.
5. Only then revisit product generator lanes (#50, #48, #45, #34).

Practical current order to inspect:

```text
#53 relationship audit
#51 workbook package hygiene
#52 floor map refresh
#46 output immutability policy
#49 admin log layout docs
#50 admin log product generator
```

Parallel but separate:

```text
#48 Bonita repair-free profile gate
#45 candidate generator cleanup/supersession
#40 classification doctrine cleanup
#34 split/supersede audit
```

## Safe next bases

| Sprint type | Safe base | Notes |
| --- | --- | --- |
| New docs/floor/hygiene | `origin/main` | Use isolated branch/worktree. Do not stack on open PR branches unless updating that PR. |
| Relationship-target validator follow-up | PR #53 branch only if continuing #53 | Keep scope to `.rels` targets and focused tests. |
| Broad package hygiene follow-up | PR #51 branch only if continuing #51 | Be aware #51 already includes code, tests, workflow wiring, and docs. |
| Product generator work | New branch from `origin/main` after prerequisite PRs land | Do not stack on #50/#45/#34 unless the sprint explicitly owns that branch. |
| Output immutability policy | PR #46 branch if updating that PR | Otherwise use `origin/main` and reference #46. |

## Branch ownership rules

Use one branch/worktree per sprint.

Recommended branch names:

- `docs/open-pr-floor-map`
- `fix/web-excel-relationship-target-audit`
- `feat/workbook-package-hygiene`
- `docs/clipboard-acceptance-contract`
- `docs/ai-prompt-kit-artifact-profile`
- `docs/pr51-copy-surface-closer`

Do not stack implementation commits onto:

- stale product PR branches,
- non-mergeable branches,
- branches that bundle multiple engines,
- docs-only branches when the sprint claims validator behavior,
- validator branches when the sprint only owns docs/floor cleanup.

## Collision risks

Expect conflicts or semantic overlap around these files and concepts:

- `.github/workflows/artifact-engines.yml`
- `README.md`
- `docs/OPEN_PR_FLOOR_MAP.md`
- `docs/WORKBOOK_COPY_SURFACE_AND_OOXML_TRIAGE_LESSONS.md`
- `docs/AI_PROMPT_KIT_V10_XML_AND_CLIPBOARD_RECORD.md`
- `docs/*CONTRACT*.md`
- `docs/*WEB_EXCEL*.md`
- `triage/workbook_package_hygiene.py`
- `triage/web_excel_compatibility_rules.py`
- `tests/test_workbook_package_hygiene.py`
- `tests/test_web_excel_compatibility_rules.py`
- `triage/output_policy.py`
- `triage/nw_prj_neuron_track_hours/*`
- `triage/nw_prj_admin_log/*`
- `triage/webexcel_preflight.py`
- generated workbook output layout under `Outputs/` or `artifacts/`

## Acceptance language guardrails

Do not claim:

- Web Excel acceptance from local package checks,
- operator acceptance without actual operator validation,
- docs-only PRs as implemented validator behavior,
- repair behavior from diagnostic-only validators,
- workbook safety from `openpyxl` save/rewrite paths when the sprint is supposed to inspect ZIP/XML package shape.

Diagnostic validators should prefer direct ZIP/XML inspection. A passing ZIP/XML package check is package evidence only, not browser or operator acceptance.

## Must-not-commit floor

Do not commit:

- private client workbooks,
- generated workbook outputs unless a sanitized fixture policy allows them,
- OneDrive, Graph, or browser automation tokens,
- raw production artifacts,
- local cache folders,
- logs with private names, emails, local paths, or workbook contents,
- live repair outputs unless explicitly sanitized.

## Next safe sprint candidates

### `fix/web-excel-relationship-target-audit-closeout`

Inspect PR #53, check why artifact-engine CI failed, verify the relationship-target checks are bounded, and either fix within PR #53 or document the exact blocker.

### `feat/workbook-package-hygiene-closeout`

Inspect PR #51, especially workflow wiring, interaction with #53, and whether broad package-hygiene checks should absorb relationship-target checks or stay separate.

### `docs/clipboard-acceptance-contract`

Promote clipboard acceptance from a lesson into a named artifact gate with manual proof language and fixture guidance.

### `docs/ai-prompt-kit-artifact-profile`

Document the expected prompt-kit workbook sheet profile: index/control sheets separated from copy-safe execution sheets, no wrapper quotes, no fences, and package-level validation required after style changes.

### `docs/open-pr-floor-map`

Refresh this map after any PR is merged, closed, rebased, or converted from docs-only to executable validator behavior.

## Closeout checklist for floor work

- PR branch is based on current `main`.
- Docs-only changes are not described as validator implementation.
- Product PRs name their floor dependencies.
- Diagnostic validators avoid live artifacts and use sanitized fixtures only.
- Local package checks are reported as package checks, not Web Excel acceptance.
- Local worktree state is checked before any destructive branch or cleanup action.
