# Artifact Handoff Alias Map

This is the scoped map for **human-facing artifact download names**. Use it when a canonical workbook/document name is machine-oriented but the operator needs a clean alias copy for download or sharing.

## Flow

1. Resolve the canonical artifact from its owning registry or current authoritative workspace.
2. Keep that canonical artifact unchanged.
3. Choose the human alias name before creating the copy.
4. Materialize/copy the bytes to a file whose **actual filesystem/provider basename** equals that alias with literal spaces and punctuation.
5. Preserve the original extension.
6. Verify SHA-256 equality between canonical and alias bytes.
7. Validate the actual transport URL by extracting its final encoded path segment, decoding that segment only, and proving it equals the exact alias basename.
8. Present/download the alias copy, never a literal `%20` filename.

## Key files

| Purpose | Path |
|---|---|
| Domain manifest | `harness/artifact-handoff/manifest.v1.json` |
| Deterministic contract | `harness/artifact-handoff/contracts/share-alias-download.v1.json` |
| Workflow | `harness/artifact-handoff/WORKFLOW.md` |
| Artifact registry | `harness/artifact-handoff/artifacts.v1.json` |
| Validator | `scripts/validate_artifact_handoff_harness.py` |
| Tests | `tests/test_artifact_handoff_harness.py` |
| Skill | `.ai/skills/share-artifact-alias-handoff/SKILL.md` |
| Operator state | `harness/artifact-handoff/reports/CURRENT_STATE.md` |

## Known trap

URL encoding belongs to the **transport href**, not the saved filename. `Admin-Share%20-%20Project.xlsm` is a bad actual filename; `Admin-Share - Project.xlsm` is the intended alias. A transport href may contain `%20` only when decoding its final encoded path segment yields the exact literal alias filename. Decode that segment only; decoding a whole path first can incorrectly turn `%2F` into a path separator.

## Focused commands

```bash
python scripts/validate_artifact_handoff_harness.py --summary
python -m unittest tests.test_artifact_handoff_harness -v
```

For a real alias pair:

```bash
python scripts/validate_artifact_handoff_harness.py \
  --canonical <canonical-file> \
  --alias <alias-copy> \
  --expected-alias "Human Alias.ext" \
  --transport-href <actual-download-url> \
  --output Outputs/share-artifact-alias-handoff.json \
  --summary
```
