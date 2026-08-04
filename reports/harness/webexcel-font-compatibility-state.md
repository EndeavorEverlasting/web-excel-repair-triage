# WebExcel Font Compatibility Harness State — 2026-08-04

## Status

The repository now has a dedicated operational harness that treats **Aptos** as the canonical Office/Excel for Web default and fails closed when **Carlito** appears in a share-ready workbook package or workbook-producing source.

## Working surfaces

- machine-readable policy: `configs/webexcel_fonts_v1.json`;
- OOXML/source validator: `scripts/validate_webexcel_fonts.py`;
- completeness validator: `scripts/validate_webexcel_font_harness.py`;
- codebase map, workflows, artifact registry, and machine registry under `harness/webexcel-fonts/`;
- synthesized positive/negative workbook fixtures in `tests/test_webexcel_font_compatibility.py`;
- root-manifest, hook, workflow, and registry wiring tests in `tests/test_webexcel_font_harness.py`;
- reusable skill: `.ai/skills/webexcel-font-compatibility/SKILL.md`;
- pre-commit, pre-push, and dedicated CI gates;
- canonical runtime reports under `Outputs/` or CI artifact storage.

## Enforced behavior

1. `xl/styles.xml` must exist and expose Aptos as the first/default explicit font.
2. Every explicit font in the workbook style table must be `Aptos` or `Aptos Display`.
3. Every XML or relationship package part is scanned for Carlito.
4. Workbook producer and configuration sources are scanned for forbidden font tokens.
5. Reports preserve artifact identity and rule locations without reading or repeating workbook cell contents.
6. XLSX, XLSM, XLTX, and XLTM containers are supported.

## Validation sequence

```powershell
python -m py_compile scripts\validate_webexcel_fonts.py scripts\validate_webexcel_font_harness.py tests\test_webexcel_font_compatibility.py tests\test_webexcel_font_harness.py
python scripts\validate_webexcel_font_harness.py --output Outputs\webexcel-font-harness.json --summary
python -m unittest tests.test_webexcel_font_compatibility tests.test_webexcel_font_harness -v
python scripts\validate_webexcel_fonts.py --scan-source --output Outputs\webexcel-font-validation.json --summary
python scripts\validate_harness.py
python -m unittest tests.test_harness_contract -v
git diff --check
```

## What is working

- The policy makes the Aptos default and Carlito prohibition explicit.
- Synthesized OOXML tests prove Aptos acceptance and rejection of Carlito, Calibri, unsupported defaults, source regressions, and macro-enabled containers.
- The completeness validator requires every requested harness component class and root-manifest discovery.
- Hooks and CI prevent a future agent from relying on prose alone.

## Remote validation

Validated implementation head `9f755c6cb75b2f0c9d8cafab3470d4bd004cb379`:

- `WebExcel Aptos font harness` run `30922224428`: **SUCCESS**
- `Operational harness contracts` run `30922224575`: **SUCCESS**
- `Prompt Kit web contracts` run `30922224198`: **SUCCESS**
- `Artifact engine tests` run `30922224461`: **SUCCESS**

The final commit updates only this tracked operator report with the completed validation evidence; implementation files are unchanged from the validated head.

## What remains unproven

- The harness-only sprint does not change existing workbook product generators.
- No private production workbook bytes are committed.
- A real workbook-producing change must still validate its exact output bytes.
- Excel for Web visual rendering, font availability, print fidelity, and recipient acceptance remain field proof.

## Missing or future work

- Any existing producer that emits a non-Aptos default must be repaired in a separately authorized product lane, with an actual generated workbook passed through the byte validator.
- Artifact-specific workflows should call the font validator on their canonical workbook before delivery; the shared hooks and CI provide the repository floor but do not replace artifact ownership.

## Proof ceiling

Passing this harness proves tracked component completeness, policy integrity, fail-closed source and OOXML behavior, hook/CI wiring, and artifact identity reporting on supplied files. It does not prove workbook math, semantic correctness, confidentiality, macros, browser rendering, or admin acceptance.
