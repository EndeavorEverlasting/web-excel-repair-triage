# WebExcel Font Harness — Workflow Specifications

## 1. Pick up a task

1. Read `AGENTS.md` and the root harness spine.
2. Read this directory, `configs/webexcel_fonts_v1.json`, and the current operator report.
3. Record `git status --short`, current branch, recent commits, open PRs, and the workbook or producer paths in scope.
4. Declare owned and forbidden scope. Product-code changes require a separately authorized lane.
5. Preserve dirty work by using an isolated branch/worktree.
6. Decide whether the request is **producer-source validation**, **artifact-byte validation**, or **harness maintenance**.

## 2. Workflow selection

### A. Workbook artifact is ready for delivery

1. Resolve the exact XLSX/XLSM from the artifact registry or operator-approved path.
2. Run:

   ```powershell
   python scripts\validate_webexcel_fonts.py --workbook "<artifact>" --require-workbook --output Outputs\webexcel-font-validation.json --summary
   ```

3. Deliver only on `PASS` with `default_font: Aptos`, zero forbidden-font findings, and the expected artifact SHA-256.
4. Open the same saved bytes in Excel for Web for visual acceptance.

### B. Workbook generator, repair script, or configuration changes

1. Inspect existing helpers and font constants before adding a new one.
2. Use `Aptos` as the default font and `Aptos Display` only when the artifact design explicitly calls for it.
3. Run source validation and focused tests before product tests:

   ```powershell
   python scripts\validate_webexcel_fonts.py --scan-source --output Outputs\webexcel-font-validation.json --summary
   python -m unittest tests.test_webexcel_font_compatibility -v
   ```

4. Generate a sanitized workbook fixture or actual authorized artifact and run Workflow A against its bytes.
5. Never treat a manual ribbon-font edit as canonical generator proof.

### C. Harness infrastructure changes

1. Repair existing font-harness components instead of creating a competing font policy.
2. Update the domain registry, root harness manifest, root maps, hooks, workflow, tests, and operator report atomically.
3. Run:

   ```powershell
   python scripts\validate_webexcel_font_harness.py --output Outputs\webexcel-font-harness.json --summary
   python -m unittest tests.test_webexcel_font_compatibility tests.test_webexcel_font_harness -v
   python scripts\validate_webexcel_fonts.py --scan-source --output Outputs\webexcel-font-validation.json --summary
   python scripts\validate_harness.py
   python -m unittest tests.test_harness_contract -v
   git diff --check
   ```

### D. A validation failure occurs

- `WEBFONT001`: remove Carlito from the canonical producer or repair the workbook package through the authorized generator.
- `WEBFONT002`: set the first/default explicit workbook font to Aptos.
- `WEBFONT003`: replace unsupported explicit fonts with Aptos or Aptos Display; do not expand the allowlist without an approved compatibility decision.
- `WEBFONT004`: repair the changed producer/configuration source. Do not add an exclusion for product code.
- malformed OOXML: quarantine the artifact and route to the workbook-repair workflow before font acceptance.

Rerun the focused failing command first, then the full font sequence, then the broader repository gates.

## 3. Validate before committing

Validation order:

1. Python compilation.
2. Font compatibility unit tests.
3. Font harness completeness test.
4. Font source scan.
5. Root harness validator and contract tests.
6. Affected artifact-engine tests.
7. `git diff --check`.

A workbook-producing change is not complete until at least one generated workbook passes artifact-byte font validation.

## 4. Pre-commit and pre-push behavior

Enable tracked hooks with:

```bash
git config core.hooksPath .githooks
```

- `pre-commit` runs font harness completeness, source scan, root harness validation, and staged patch hygiene.
- `pre-push` adds font regressions, source report generation, existing exhaustive harness gates, and full patch hygiene.

Hooks are local acceleration. CI remains the remote proof gate.

## 5. Handoff contract

State:

- repository, branch/worktree, commit, and PR;
- whether the change was harness, producer, or artifact scope;
- files changed;
- workbook paths, filenames, sizes, and SHA-256 values validated;
- default and explicit fonts observed;
- rule IDs and locations for every failure without leaking private workbook content;
- commands run and exact results;
- skipped field proof, especially Excel for Web visual acceptance;
- final Git state;
- one exact next command that fetches the pinned commit into an isolated worktree, runs the owning validator, and prints the canonical report.
