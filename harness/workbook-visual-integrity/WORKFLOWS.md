# Workbook Visual Integrity Workflows

## Pick up a task

1. Record `git status --short`, branch, and recent commits.
2. Preserve dirty or separately owned work in its current worktree; use an isolated branch/worktree.
3. Identify the artifact family and resolve its profile through `registry.json` and `generator-bindings.v1.json`.
4. Capture the exact input, baseline, and generated artifact SHA-256 values.
5. Declare whether the task is harness-only, product generation, visual repair, or final acceptance.
6. Run profile audit before touching a generator. Do not invent a color when the role is artifact-specific.

## Workflow A — Harness or profile change

1. Modify policy/profile/schema/map/workflow/registry/skill/report/test surfaces only.
2. Add a positive fixture and a failing mutation for every new rule.
3. Run completeness, focused tests, and profile audit.
4. Run root harness and broad artifact tests.
5. Commit and push only the owned files.

## Workflow B — Generator adoption

1. Resolve the artifact profile from the binding registry.
2. Generate into an approved output path; never write into `Candidates/` or `Active/`.
3. Emit the visual profile ID and policy hash in the generator manifest.
4. Run the Aptos font gate on exact output bytes.
5. Run the visual validator on exact output bytes.
6. Run artifact-specific semantic/package validators.
7. Render or open the exact validated artifact in Excel for Web for operator acceptance.
8. Store the receipt beside the artifact or in approved CI/runtime evidence.

Product code changes belong to a separately declared generator lane.

## Workflow C — Style-only repair

1. Preserve the pre-style workbook as the baseline.
2. Change presentation primitives only.
3. Validate the styled artifact with `--baseline`.
4. Stop on any value, formula, sheet-order, or merge drift.
5. Run the exact profile and font gates, then operator review.

## Failure handling

- `WVI003`: fix the role-to-fill mapping or profile binding; do not recolor unrelated roles.
- `WVI004`: inspect the key-group range endpoints. Repair the generator range, not only the one bad workbook cell.
- `WVI005`: correct inclusive/exclusive bounds and add a one-row-beyond mutation test.
- `WVI006`: repair the producer that writes one summary table but not its paired visual table.
- `WVI007`: abandon the style-only candidate and restart from the preserved baseline.
- `WVI009`: repair policy/profile/registry ownership before validating a workbook.
- Excel for Web mismatch after static PASS: preserve static receipt, record field failure separately, and open a product repair lane.

Never weaken a rule merely to accept the current artifact.

## Validate before committing

```powershell
python -m py_compile scripts\validate_workbook_visual_integrity.py scripts\validate_workbook_visual_harness.py tests\test_workbook_visual_integrity.py tests\test_workbook_visual_harness.py
python scripts\validate_workbook_visual_harness.py --output Outputs\workbook-visual-harness.json --summary
python -m unittest tests.test_workbook_visual_integrity tests.test_workbook_visual_harness -v
python scripts\validate_workbook_visual_integrity.py --validate-profiles --output Outputs\workbook-visual-profile-audit.json --summary
python scripts\validate_webexcel_font_harness.py --summary
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
python -m triage.gitignore_hygiene
git diff --check
```

## Handoff

State repository, branch/worktree, artifact family, selected profile, policy/profile hashes, exact artifact SHA, files changed, commands actually run, results, commit SHA, push/PR state, known visual debt, field-proof gaps, final Git state, and one exact command that validates or consumes the artifact.
