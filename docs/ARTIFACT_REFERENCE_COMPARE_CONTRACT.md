# Artifact Reference Compare Contract

## Purpose

Generated workbooks should be compared against approved reference artifacts without committing private workbook files to the repo.

The comparison must support three layers:

1. Raw file SHA-256 for exact byte identity.
2. Canonical package hash for normalized XLSX package comparison.
3. Semantic workbook hash for visible workbook meaning.

Raw SHA mismatch is usually a warning. Semantic mismatch is a stop-ship condition unless an approved delta is supplied.

## Approved references

Approved reference workbooks belong outside git, for example:

```text
References/approved/
```

The folder may contain private workbooks locally, but those files must remain ignored. Commit profiles and comparison code only.

## Required compare behavior

A generated workbook should fail comparison when:

- required sheets are missing
- required headers are missing
- visible title/sentinel cells are blank
- shared strings collapse into generic ColumnN labels
- known tech/project labels disappear
- Neuron or billing totals change unexpectedly
- semantic hash differs and no approved delta exists

Warnings are acceptable for:

- raw byte hash mismatch
- workbook creator metadata changes
- ZIP timestamp changes
- harmless relationship ID changes

## CLI target

```powershell
python -m triage.artifact_compare --reference <approved.xlsx> --candidate <generated.xlsx> --profile <profile.json> --out <compare.json>
```

## Output fields

```json
{
  "raw_sha_match": false,
  "canonical_package_match": true,
  "semantic_match": true,
  "comparison_status": "PASS"
}
```

## Relationship to format profiles

Comparison should consume profiles from:

```text
configs/artifact_profiles/
```

The profile supplies expected sheets, headers, and forbidden text. This keeps artifact expectations durable without committing private files.
