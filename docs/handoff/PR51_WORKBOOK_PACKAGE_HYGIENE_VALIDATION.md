# PR #51 Workbook Package Hygiene Validation

## Context

- Repo: `EndeavorEverlasting/web-excel-repair-triage`
- Branch: `docs/workbook-copy-surface-ooxml-lessons`
- PR: #51
- Lane: read-only OOXML package hygiene and clipboard-risk diagnostics
- Validation commit: `4ec677fda17414c3f05b2ea0840799cbd2ed42b5`
- Workflow run: `29166975682` (`Artifact engine tests`, run 142)

## Why CI was split

The package-hygiene test initially ran inside the broad `artifact-engines` job. The focused test passed, but the job still concluded failure because an unrelated broad artifact-engine test failed afterward.

That structure erased the distinction between:

- proof that the new workbook package hygiene lane works, and
- proof that the repository's broader artifact-engine battery is fully green.

The workflow now exposes a separate job:

```text
workbook-package-hygiene
```

The existing broad lane remains:

```text
artifact-engines
```

This is evidence isolation, not failure suppression. The broad job still runs and remains authoritative for its own scope.

## Focused CI proof

The `workbook-package-hygiene` job completed successfully with all of these steps green:

- checkout
- Python 3.11 setup
- pytest installation
- `triage.workbook_package_hygiene` import
- `tests/test_workbook_package_hygiene.py`
- `python -m triage.workbook_package_hygiene --help`

This establishes:

- import proof,
- synthetic test proof,
- CLI entry-point proof.

It does not establish:

- Excel for Web acceptance,
- Microsoft clipboard behavior,
- operator acceptance of every workbook,
- broad artifact-engine health.

## Broad-suite posture

The `artifact-engines` job remains separate. A failure in that job must be investigated on its own evidence and must not be attributed to the workbook package hygiene lane unless the traceback points to the files changed by PR #51.

Do not set `continue-on-error` and do not weaken the broad suite to make this PR appear green.

## Files in the package-hygiene lane

```text
triage/workbook_package_hygiene.py
tests/test_workbook_package_hygiene.py
docs/WORKBOOK_COPY_SURFACE_AND_OOXML_TRIAGE_LESSONS.md
docs/AI_PROMPT_KIT_V10_XML_AND_CLIPBOARD_RECORD.md
.github/workflows/artifact-engines.yml
```

## Acceptance statement

PR #51 has isolated harness proof for the new workbook package hygiene validator.

Merge readiness still depends on repository policy for unrelated failing checks. If branch protection requires the broad `artifact-engines` job to pass, repair that failure in its owning lane rather than weakening or disguising it here.
