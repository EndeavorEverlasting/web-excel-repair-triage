# Prompt Kit Browser-Proof Scratch Cleanup Workflow

## Pick up the task

Use this workflow when an operator presents a local path whose first directory below the OS temp root is named `prompt-kit-browser-proof-*`, or asks to classify/remove detached Prompt Kit browser-proof copies.

Before mutation: read `AGENTS.md`, inspect this manifest/report, verify the path is scratch rather than a canonical checkout or `Outputs/` evidence, and run preview mode first. Never infer that generic `%TEMP%` contents are safe to delete.

## Preview

Run `scripts/Clear-PromptKitBrowserProofScratch.ps1` without `-Apply`. Preview is the default and writes `Outputs/prompt-kit-browser-proof-cleanup-report.json` without deleting anything. Add `-TargetPath "<path>"` to inspect one exact candidate.

## Apply cleanup

Only after preview identifies the expected candidate, close browser tabs still using that file URL and rerun the exact target with `-Apply`. The default minimum age is 60 minutes. Set `-MinimumAgeMinutes 0` only when the operator has positively identified the exact scratch path and wants immediate cleanup.

The runner must never widen a failed exact target into wildcard deletion.

## Failure handling

- outside OS temp root → fail closed;
- unexpected leaf name → fail closed;
- missing `web/prompt-kit/index.html` → preserve;
- reparse point/symlink → preserve;
- too new → preserve and report age;
- deletion error or lock → record failure and exit nonzero;
- report path outside repository `Outputs/` → fail closed.

Never react to failure by deleting the parent temp directory, browser profile, repository checkout, or unrelated siblings.

## Validate before committing harness changes

```text
python -m py_compile scripts/validate_prompt_kit_browser_proof_cleanup.py tests/test_prompt_kit_browser_proof_cleanup_harness.py
python scripts/validate_prompt_kit_browser_proof_cleanup.py --summary
python -m unittest tests.test_prompt_kit_browser_proof_cleanup_harness -v
git diff --check
```

CI additionally exercises preview and explicit apply against a test-owned temporary fixture.

## Handoff

Report exact candidate paths, preview/apply mode, eligible/preserved/deleted/failed counts, report artifact path, reasons for preserved paths, proof ceiling, and one executable next action. Never claim filesystem scratch deletion cleared browser localStorage or Favorites; those are separate browser-origin state.
