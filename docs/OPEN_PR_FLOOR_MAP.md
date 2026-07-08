# Open PR Floor Map

## Purpose

Keep the repository floor legible before adding more workbook validator or product layers.

This map is intentionally docs-only. It does not claim workbook repair, Web Excel acceptance, operator acceptance, or validator implementation. It records current open PR posture, safe merge lanes, and collision risks so future sprints do not stack implementation work on ambiguous branches.

## Inspection snapshot

- Repository: `EndeavorEverlasting/web-excel-repair-triage`
- Default branch: `main`
- Current inspected `main` head: `3d18817f89232306cc2e7e00ed7354c43c5c1afb`
- Open PR source: GitHub open PR listing, limit 30
- Local worktree: not available in the connector environment

## Current open PR floor

| PR | Branch | Type | Current posture | Floor decision |
| --- | --- | --- | --- | --- |
| #51 | `docs/workbook-copy-surface-ooxml-lessons` | docs / workbook copy surface | Current, mergeable, docs-only. Captures clipboard-safe prompt surfaces, table XML, merge range, freeze-pane, and package-hygiene lessons. | Land or close first. It is a floor/doc prerequisite, not validator behavior. |
| #50 | `feat/nw-prj-admin-log-project-team-generator-2026-06-04` | product generator | Builds on earlier output-policy and company-style work. Claims operator/Web Excel acceptance as pending manual gates. | Do not treat as floor. Rebase/review only after docs/output-policy prerequisites are settled. |
| #49 | `docs/admin-log-style-2026-06-04` | docs / accepted layout contract | Documents Project Team layout rules and manual visual acceptance. | Land before #50 if that product lane continues. |
| #48 | `feat/neuron-track-hours-repairfree-reference-gate-2026-06-04` | validator/product gate | Adds repair-free golden profile gate for Bonita path. Requires operator-local golden zip and manual Excel for Web proof. | Rebase and validate separately. Do not claim Web Excel acceptance from local package checks. |
| #46 | `feat/artifact-emulator-output-policy-2026-06-04` | floor / output policy | Repo-wide emulator immutability and output layout policy. Several later product PRs depend on this policy. | High-priority floor candidate. Rebase/land before product generator lanes. |
| #45 | `feat/candidate-neuron-track-hours-2026-06-04` | product generator | Candidate workbook generator; currently not mergeable. | Do not stack new work here. Rebase or supersede after #46 and related docs settle. |
| #40 | `docs/client-coordination-roles-2026-06-03` | docs / classification doctrine | Client-coordination and Rezaul classification doctrine. | Merge if still canonical; otherwise close with replacement citation. |
| #34 | `feat/april-may-billing-summary-engine-2026-06-02` | bundled product engines | Large older bundled engine PR with known private-asset test gaps. | Avoid as a base. Split/supersede before merging additional layers. |

## Recommended landing order

1. Docs/floor rules that clarify acceptance language and artifact surfaces.
2. Output immutability and run-layout policy.
3. Diagnostic-only package hygiene validator.
4. Product workbook generator changes.
5. Repair engines only when a sprint explicitly owns repair.

Practical current order:

```text
#51 -> #46 -> #49 -> #50
```

Parallel but separate:

```text
#48 repair-free profile gate
#45 candidate generator cleanup/supersession
#40 classification doctrine cleanup
#34 split/supersede audit
```

## Branch ownership rules

Use one branch/worktree per sprint.

Recommended branch names:

- `docs/pr51-copy-surface-closer`
- `feat/workbook-package-hygiene`
- `docs/clipboard-acceptance-contract`
- `docs/ai-prompt-kit-artifact-profile`
- `docs/open-pr-floor-map`

Do not stack implementation commits onto:

- stale product PR branches,
- non-mergeable branches,
- branches that bundle multiple engines,
- docs-only branches when the sprint claims validator behavior.

## Collision risks

Expect conflicts or semantic overlap around these files and concepts:

- `.github/workflows/artifact-engines.yml`
- `README.md`
- `docs/*CONTRACT*.md`
- `docs/*WEB_EXCEL*.md`
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

Diagnostic validators should prefer direct ZIP/XML inspection.

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

### `docs/pr51-copy-surface-closer`

Close or merge #51 after confirming it remains docs-only and accurately describes clipboard acceptance and package-hygiene lessons.

### `feat/workbook-package-hygiene`

Add a diagnostic-only validator that inspects `.xlsx` ZIP/XML package shape without rewriting the workbook. First pass should check tables, merge ranges, freeze panes, formula/error drift, relationship targets, shared strings posture, and forbidden repair-risk tokens. It must not call Excel, OneDrive, Graph, browser automation, or `openpyxl` save paths.

### `docs/clipboard-acceptance-contract`

Promote clipboard acceptance from a lesson into a named artifact gate with manual proof language and fixture guidance.

### `docs/ai-prompt-kit-artifact-profile`

Document the expected prompt-kit workbook sheet profile: index/control sheets separated from copy-safe execution sheets, no wrapper quotes, no fences, and package-level validation required after style changes.

## Closeout checklist for floor work

- PR branch is based on current `main`.
- Docs-only changes are not described as validator implementation.
- Product PRs name their floor dependencies.
- Diagnostic validators avoid live artifacts and use sanitized fixtures only.
- Local package checks are reported as package checks, not Web Excel acceptance.
