# Workbook Visual Integrity Harness

Start with `CODEBASE_MAP.md`, select the artifact profile from `registry.json`, and follow `WORKFLOWS.md`.

Canonical focused validation:

```powershell
python scripts\validate_workbook_visual_harness.py --output Outputs\workbook-visual-harness.json --summary
python -m unittest tests.test_workbook_visual_integrity tests.test_workbook_visual_harness -v
python scripts\validate_workbook_visual_integrity.py --validate-profiles --output Outputs\workbook-visual-profile-audit.json --summary
```

Exact artifact validation:

```powershell
python scripts\validate_workbook_visual_integrity.py --workbook <artifact.xlsx> --profile <profile.json> --output Outputs\workbook-visual-validation.json --summary
```

Add `--baseline <pre-style.xlsx>` to every style-only pass. Static PASS does not replace Excel for Web operator review.
