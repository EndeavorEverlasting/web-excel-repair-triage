# Share Artifact Alias Handoff

## Trigger

Use when an operator needs a downloadable/shareable copy of a canonical artifact under a clean human-facing alias, especially when machine-oriented names, URL encoding, or repeated manual renaming is creating handoff friction.

## Required inputs

- Exact canonical artifact path/ID and current filename.
- Intended human alias filename.
- Canonical bytes or a provider copy operation that preserves bytes.
- The actual download/open transport URL when completing a handoff receipt.
- Owning artifact/workspace contract when identity is externally registered.

## Outputs

- A separate alias copy whose actual basename is the intended literal human filename.
- Preserved canonical extension.
- SHA-256 equality proof when both byte streams are accessible.
- Validated runtime transport target that decodes to the literal alias basename.
- Optional `Outputs/share-artifact-alias-handoff.json` receipt.
- A download/open target that resolves to that exact alias.

## Procedure

1. Resolve canonical identity from the owning registry/workspace; do not guess from a similar filename.
2. Preserve the canonical artifact unchanged.
3. Create the alias copy using literal spaces/punctuation in the actual filename.
4. Reject local/provider basenames containing percent-encoded octets such as `%20`.
5. Preserve the source extension exactly for rename/copy-only handoff.
6. Compare SHA-256 values when bytes are available.
7. Validate the actual runtime transport URL: extract its final encoded segment first, decode that segment only, and confirm it equals the literal alias basename.
8. Run the focused validator and hand the operator the alias copy directly.

## Guardrails

- Do not ask the operator to rename a file the agent can correctly materialize itself.
- Do not rename the canonical registered artifact merely to improve outward readability.
- Do not convert `.xlsm` to `.xlsx` or otherwise change format in an alias-only lane.
- Do not claim byte identity without comparing bytes/hashes.
- Do not claim transport-target proof without validating and recording the actual URL.
- Keep receipts under normalized `Outputs/`; reject traversal or alternate tracked/protected destinations.
- Do not commit private artifact bytes or external-provider credentials.

## Validation

```bash
python scripts/validate_artifact_handoff_harness.py --summary
python -m unittest tests.test_artifact_handoff_harness -v
```

For actual files:

```bash
python scripts/validate_artifact_handoff_harness.py \
  --canonical <source> \
  --alias <alias-copy> \
  --expected-alias "Human Alias.ext" \
  --transport-href <actual-download-url> \
  --output Outputs/share-artifact-alias-handoff.json \
  --summary
```

## Proof ceiling

The skill proves the tracked procedure and, when actual files plus their transport are supplied, basename/extension/SHA-256 identity and exact decoded transport targeting for that pair. It does not prove how an external provider or recipient UI will display the file after transfer unless separately observed.
