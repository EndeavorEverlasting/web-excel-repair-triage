# Workbook Visual Integrity Artifact Registry

## Tracked control-plane artifacts

| Artifact | Path | Producer | Gate |
|---|---|---|---|
| Canonical visual policy | `configs/workbook_visual_integrity_v1.json` | harness lane | completeness + profile audit |
| Visual profiles | `harness/workbook-visual-integrity/profiles/*.json` | artifact-profile owner | profile audit + focused tests |
| Harness registry | `harness/workbook-visual-integrity/registry.json` | harness lane | completeness validator |
| Generator bindings | `harness/workbook-visual-integrity/generator-bindings.v1.json` | harness lane | completeness validator |
| FUN/Triage receipt contract | `harness/workbook-visual-integrity/fun-triage-contract.v1.json` | integration lane | completeness validator |
| Scoped skill | `.ai/skills/workbook-visual-integrity/SKILL.md` | harness lane | required-section check |
| Operator report | `reports/harness/workbook-visual-integrity-state.md` | harness lane | completeness validator |

## Runtime artifacts

| Artifact | Default path | Naming | Tracking |
|---|---|---|---|
| Harness completeness report | `Outputs/workbook-visual-harness.json` | stable | gitignored / CI artifact |
| Profile audit | `Outputs/workbook-visual-profile-audit.json` | stable | gitignored / CI artifact |
| Exact workbook validation | `Outputs/workbook-visual-validation.json` | stable or `<artifact-stem>_visual_validation.json` | beside runtime artifact or CI |
| Style-only baseline comparison | same validation report | include candidate and baseline SHA-256 | gitignored / protected evidence |

## Required receipt fields

Every delivered validation result includes artifact filename, size, SHA-256, policy ID/hash, profile ID/hash, rule count, violation count, stable rule IDs and locations, PASS/FAIL, and proof ceiling. It never needs to quote private workbook cell text.

## Artifact lifecycle

1. Resolve profile from the registry rather than guessing from a filename alone.
2. Generate exact output bytes.
3. Run font, visual, artifact-specific semantic, and package gates.
4. Confirm all receipts identify the same artifact SHA-256.
5. Open those exact bytes in Excel for Web.
6. Record operator acceptance separately from static PASS.
7. Deliver only the registered current artifact; deprecate earlier copies through the owning repository or document system.

## Naming conventions

- Profiles: `<artifact-family-or-period>.v1.json`.
- Runtime validation: `<artifact-stem>_visual_validation.json` when multiple artifacts share one output folder.
- Operator state reports: `reports/harness/<domain>-state.md`.
- No private workbook bytes or screenshots are committed to this public repository.
