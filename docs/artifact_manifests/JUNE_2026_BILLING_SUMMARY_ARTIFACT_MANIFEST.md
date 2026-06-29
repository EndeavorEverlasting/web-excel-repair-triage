# June 2026 Billing Summary Artifact Manifest

## Status

Generated locally from the uploaded June billing draft and the April/May formatted summary template.

This manifest records the artifact fingerprint without committing the private workbook itself.

## Output artifact

- File name: `Final June Billing Summary - 2026-06-30.xlsx`
- SHA-256: `63e05aff82bc5bad6adda9c2ef15cecf72e1cb0142ad486ae822377709139ff5`
- Size: `115679` bytes
- Template family: `Final April & May Billing Summary - 2026-06-10.xlsx`

## Preserved workbook format

The generated workbook uses the same five-sheet delivery structure as the April/May summary:

1. `Billing Summary`
2. `Project Summary`
3. `Tech Summary`
4. `Daily Summary`
5. `Billing Detail`

The June source dashboard was remapped into that structure rather than delivered as a new dashboard format.

## Validation notes

- Common spreadsheet error scan returned no matches for `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, or `#N/A`.
- The workbook was rendered for visual review after generation.
- The private workbook contents are intentionally not committed here.

## Privacy posture

This repository documentation already warns against committing private workbook/client data. This manifest is therefore the repository-side checkpoint; the actual `.xlsx` should stay in the private delivery channel.
