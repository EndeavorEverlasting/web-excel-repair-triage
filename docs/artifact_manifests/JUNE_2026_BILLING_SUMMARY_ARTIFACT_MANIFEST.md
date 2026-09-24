# June 2026 Billing Summary Artifact Manifest

## Status

Regenerated after rejecting the prior handoff filename and tightening the workbook compatibility scan against the Web Excel repair rules in this repo.

This manifest records the artifact fingerprint without committing the private workbook itself.

## Output artifact

- File name: `June_2026_Neuron_Deployment_Billing_Summary.xlsx`
- SHA-256: `45f5508e0e788d3200475763c2c60e5a51bdfa2168b9a058cdf6ab024fe35af9`
- Size: `115677` bytes
- Template family: `Final April & May Billing Summary - 2026-06-10.xlsx`

## Preserved workbook format

The regenerated workbook uses the same five-sheet delivery structure as the April/May summary:

1. `Billing Summary`
2. `Project Summary`
3. `Tech Summary`
4. `Daily Summary`
5. `Billing Detail`

The June source dashboard was remapped into that structure rather than delivered as a new dashboard format.

## Compatibility validation

Package scan results:

- ZIP package test: PASS
- `calcChain.xml` present: NO
- `_xlfn`: 0
- `_xlws`: 0
- `_xludf`: 0
- `SINGLE`: 0
- `AGGREGATE`: 0
- `FILTER(`: 0
- `SORT(`: 0
- `UNIQUE(`: 0
- `LET(`: 0
- `LAMBDA`: 0
- formula error tokens `#REF!`, `#VALUE!`, `#NAME?`, `#DIV/0!`, `#N/A`: 0

Artifact-tool verification:

- Imported workbook successfully.
- Confirmed the expected five-sheet structure.
- Rendered `Billing Summary`, `Project Summary`, and `Daily Summary` for visual review.
- Cell search returned no visible formula error matches.

## Privacy posture

The private workbook contents are intentionally not committed here. This manifest is the repository-side checkpoint; the actual `.xlsx` should stay in the private delivery channel.
