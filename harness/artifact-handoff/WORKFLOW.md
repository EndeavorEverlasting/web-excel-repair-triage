# Share Artifact Alias / Download Handoff Workflow

## Trigger

Use this workflow when an operator wants to download/share a current artifact under a clean human-facing filename without renaming the canonical machine/provider artifact.

## Pick up the task

1. Resolve the exact canonical artifact and its authority.
2. Record its current basename, extension, size, and SHA-256 when bytes are available.
3. Resolve the requested or registered human alias.
4. Preserve the canonical artifact; create a copy rather than renaming the canonical identity.

## Build the alias copy

1. Create the alias with literal filename characters. Do **not** create a local/provider file whose basename contains URL escapes such as `%20`.
2. Preserve the canonical extension exactly by type (`.xlsm` remains `.xlsm`, `.xlsx` remains `.xlsx`, etc.).
3. Do not insert `Deprecated`, internal variable names, source IDs, hashes, or implementation mechanics into an outward alias unless the audience contract requires them.
4. If a Markdown/URL transport encodes spaces, decode its final path segment and prove that it resolves to the literal alias basename.
5. Compare canonical and alias SHA-256 values. A rename/copy-only handoff must be byte-identical.

## Validate before handing off

```bash
python scripts/validate_artifact_handoff_harness.py \
  --canonical <canonical-file> \
  --alias <alias-copy> \
  --expected-alias "Human Alias.ext" \
  --output Outputs/share-artifact-alias-handoff.json \
  --summary
```

The validator fails closed on encoded literal filenames, basename drift, extension drift, transport mismatch, missing files, and byte mismatch.

## Handle failures

- **Literal `%20` or other percent octets in actual basename:** create a new correctly named alias copy; do not tell the operator to rename it manually.
- **Extension mismatch:** regenerate the alias with the source extension; do not convert formats in a rename-only lane.
- **Hash mismatch:** stop. The alias is no longer a pure copy and needs the owning artifact workflow.
- **Transport mismatch:** fix the link target; do not change the file to match a malformed URL.
- **Canonical identity moved:** refresh source truth before producing another alias.

## Handoff

Report the canonical identity, alias basename, extension, byte-equality result, receipt path/ID, and the exact download/open target. The operator should receive a file that is ready to use without manual filename repair.
