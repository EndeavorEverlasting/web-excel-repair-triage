# Workbook Visual Integrity Harness State — 2026-08-05

## Status

The repository now has a dedicated harness for semantic cell colors, exact formatting ranges, paired visual surfaces, style-only preservation, generator/profile binding, and FUN/Triage receipt alignment.

## Working surfaces

- canonical policy and stable rule IDs in `configs/workbook_visual_integrity_v1.json`;
- three initial profiles for May admin NTH, July admin NTH, and internal NTH Math Packets;
- a standard-library OOXML validator for exact fills, semantic rows, same-key style parity, boundary bleed, paired-range parity, selected layout fields, and baseline preservation;
- a fail-closed harness completeness validator;
- positive and negative synthesized workbook fixtures;
- root manifest, hooks, scoped skill, dedicated CI, generator binding, and cross-repo receipt wiring.

## Errors the harness now classifies

- one row of a same-date May block retaining the previous block's fill;
- a style range extending one row or column beyond its declared boundary;
- a workstream row using another workstream's fill;
- a summary table and its paired visual table using different row fills;
- a style-only pass changing a value, formula, sheet order, or merged range;
- a profile assigning one fill to multiple visual meanings;
- unbounded date/person striping;
- a generator or FUN receipt referring to different workbook bytes.

## Current contract posture

- Canonical workstream colors are shared through one policy.
- Go-Live Support, Documentation, and Cleanup/Disposal require explicit artifact-profile colors rather than invented global defaults.
- The historical May date-band design is a bounded exception only.
- July and future NTH rows are expected to be semantic by primary workstream.
- Aptos/Aptos Display remains the font contract supplied by the stacked font harness.

## What is working

- Fresh agents can resolve profiles, commands, failure routing, artifact outputs, and handoff requirements without reconstructing the visual contract from chat history.
- Tests use synthesized OOXML and do not commit private workbook data.
- Static receipts identify exact artifact, policy, and profile hashes without quoting workbook cell contents.
- Triage remains the producer/validator; FUN remains the evidence and final-acceptance authority.

## What remains broken or missing

- Existing workbook generators are not changed in this harness-only sprint and may still emit legacy colors or incorrect range endpoints.
- Current private May and July artifacts must be tested in a protected runtime; they are not committed as CI fixtures.
- Generator manifests still need product-lane wiring to emit visual profile and receipt fields.
- FUN must consume the pinned receipt contract in a separately authorized cross-repo implementation lane.
- Excel for Web visual rendering and operator acceptance remain field proof.

## Validation order

```powershell
python scripts\validate_workbook_visual_harness.py --output Outputs\workbook-visual-harness.json --summary
python -m unittest tests.test_workbook_visual_integrity tests.test_workbook_visual_harness -v
python scripts\validate_workbook_visual_integrity.py --validate-profiles --output Outputs\workbook-visual-profile-audit.json --summary
python scripts\validate_webexcel_font_harness.py --summary
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
python -m triage.gitignore_hygiene
git diff --check
```

## Proof ceiling

Static profile/harness completeness, synthesized OOXML behavior, exact artifact identity, and source/receipt alignment only. No workbook math, private artifact acceptance, Excel for Web rendering, print fidelity, or recipient acceptance is claimed.
