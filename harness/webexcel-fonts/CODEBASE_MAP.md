# WebExcel Font Harness — Codebase Map

## Mission

Prevent workbook generators and repaired share-ready artifacts from silently reverting to Carlito or another non-approved default. Excel for Web delivery uses **Aptos** as the canonical Office font.

## Reading order

1. `AGENTS.md` — repository law.
2. `harness/webexcel-fonts/CODEBASE_MAP.md` — this map.
3. `harness/webexcel-fonts/WORKFLOWS.md` — task pickup, artifact validation, failure handling, and handoff.
4. `configs/webexcel_fonts_v1.json` — machine-readable font policy.
5. `harness/webexcel-fonts/ARTIFACT_REGISTRY.md` and `registry.json` — outputs and ownership.
6. `.ai/skills/webexcel-font-compatibility/SKILL.md` — repeatable operator procedure.
7. `reports/harness/webexcel-font-compatibility-state.md` — current state and known gaps.

## Owned structure

```text
configs/webexcel_fonts_v1.json                    Aptos default and forbidden-font policy
scripts/validate_webexcel_fonts.py                OOXML and source validator
scripts/validate_webexcel_font_harness.py         completeness validator
harness/webexcel-fonts/CODEBASE_MAP.md            navigation
harness/webexcel-fonts/WORKFLOWS.md               operating workflows
harness/webexcel-fonts/ARTIFACT_REGISTRY.md       artifact contract
harness/webexcel-fonts/registry.json              machine-readable ownership
.ai/skills/webexcel-font-compatibility/SKILL.md   scoped procedure
reports/harness/webexcel-font-compatibility-state.md operator report
.githooks/pre-commit                              focused local gate
.githooks/pre-push                                broader local gate
.github/workflows/webexcel-font-harness.yml       CI gate and report artifact
tests/test_webexcel_font_compatibility.py         synthesized OOXML regressions
tests/test_webexcel_font_harness.py               component and wiring regressions
```

## Entry points

| Entry point | Purpose |
|---|---|
| `python scripts/validate_webexcel_font_harness.py --summary` | Prove every harness component exists, is registered, and is wired into hooks/docs/CI. |
| `python scripts/validate_webexcel_fonts.py --scan-source --summary` | Reject forbidden font tokens in workbook producer/configuration sources. |
| `python scripts/validate_webexcel_fonts.py --workbook <path> --require-workbook --output Outputs/webexcel-font-validation.json --summary` | Inspect actual XLSX/XLSM OOXML and prove Aptos is the default explicit font. |
| `python -m unittest tests.test_webexcel_font_compatibility tests.test_webexcel_font_harness -v` | Run positive, negative, package, source, and completeness regressions. |

## Build, test, and deployment commands

This harness does not deploy product code. It validates tracked infrastructure and runtime workbook artifacts.

```powershell
python -m py_compile scripts\validate_webexcel_fonts.py scripts\validate_webexcel_font_harness.py tests\test_webexcel_font_compatibility.py tests\test_webexcel_font_harness.py
python scripts\validate_webexcel_font_harness.py --output Outputs\webexcel-font-harness.json --summary
python -m unittest tests.test_webexcel_font_compatibility tests.test_webexcel_font_harness -v
python scripts\validate_webexcel_fonts.py --scan-source --output Outputs\webexcel-font-validation.json --summary
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
git diff --check
```

Artifact-time validation:

```powershell
python scripts\validate_webexcel_fonts.py --workbook "C:\path\to\share-ready.xlsx" --require-workbook --output Outputs\webexcel-font-validation.json --summary
```

## Known traps

- **Carlito is not an acceptable fallback.** It must fail source and workbook validation.
- Changing the visible Excel ribbon font after generation is not a substitute for repairing the canonical generator or validating the saved bytes.
- A workbook may look correct in Desktop Excel while retaining a different default font in `xl/styles.xml`; validate the package.
- Theme or chart XML may repeat a forbidden typeface outside `styles.xml`; the validator scans all XML and relationship parts.
- `.xlsm` is supported as an OOXML container, but macro safety is outside this harness.
- Do not weaken the approved-font list merely to make a historical workbook pass. Repair or explicitly quarantine the artifact.
- Passing static checks does not prove Excel for Web visual rendering; open the validated artifact in WebExcel for final field proof.
