# FUN NTH Producer / Consumer Contract — 2026-08-03

## Ownership

| Surface | Canonical owner |
|---|---|
| Evidence truth, attendance controls, workstream claims, share-safe tabs | `EndeavorEverlasting/FUN` |
| NTH packet, artifact-manifest, and validation-result schemas | `EndeavorEverlasting/FUN` |
| Workbook generation, repair, and semantic preservation | `EndeavorEverlasting/web-excel-repair-triage` |
| Artifact-manifest production from actual workbook bytes | `EndeavorEverlasting/web-excel-repair-triage` |
| Final byte-level artifact acceptance | `EndeavorEverlasting/FUN` |

## Data flow

```text
FUN packet specification
  -> triage workbook generator or repair engine
  -> triage FUN manifest exporter
  -> artifact manifest + producer receipt
  -> FUN resolver and XLSX validator
  -> FUN validation result and production registry disposition
```

## Pinned donor contract

The producer pins FUN commit `9ba432808f823e52c6ba80ffd05ec673d2e15acf` through:

- `contracts/upstream/fun/nth-artifact-contract.lock.json`;
- `contracts/upstream/fun/schemas/nth-packet-spec.schema.json`;
- `contracts/upstream/fun/schemas/nth-artifact-manifest.schema.json`;
- `contracts/upstream/fun/schemas/nth-validation-result.schema.json`.

The lock records each source path, Git blob SHA, byte count, and SHA-256. Snapshot drift fails closed.

## Producer inputs

1. Actual workbook bytes.
2. A reviewed `fun-nth-packet-spec/v1` packet specification.
3. A `web-excel-fun-nth-export-profile/v1` artifact assertion profile containing only:
   - packet ID;
   - sheet contract;
   - cell assertions;
   - reconciliations;
   - optional required text;
   - optional row-color contracts.
4. Artifact type, builder version, exact producer commit, generation mode, and publication posture.

The profile may not carry evidence claims, labor allocation logic, device counts, or management conclusions.

## Producer outputs

### FUN manifest

`fun-nth-artifact-manifest/v1` contains the actual filename, byte count, SHA-256, artifact type, reviewed sheet contract, cell assertions, reconciliations, and optional text/color checks.

### Triage producer receipt

`web-excel-fun-nth-producer-receipt/v1` records:

- exact triage producer commit;
- exact FUN donor commit;
- lockfile and schema hashes;
- packet/profile identities;
- actual artifact identity;
- publication posture;
- producer proof level and ceiling.

The receipt is integration provenance. It is not a replacement for FUN's validation result.

## Fail-closed boundaries

- Share-ready sheet order must exactly match FUN-approved tabs.
- Hidden sheets must be forbidden for share-ready artifacts.
- Every FUN forbidden-content marker must remain in the sheet contract.
- Artifact identity is always computed from the local bytes.
- A sanitized fixture cannot claim private, protected, or production runtime posture.
- Production artifact types cannot use fixture posture.
- Unsupported profile fields fail rather than silently carrying evidence or labor logic.
- Triage does not decide whether evidence claims are true.

## Cross-repo acceptance gate

Producer proof is complete when focused tests pass and a sanitized artifact, manifest, and receipt are emitted.

Cross-repo behavior proof is complete only when FUN's exact resolver and artifact validator consume the emitted manifest and actual fixture bytes successfully.

Production byte proof remains blocked until the protected workbook bytes are fetched from their registered location and validated by FUN.

## Commands

```text
python -m unittest tests.test_fun_nth_artifact_export -v
python scripts/export_fun_nth_artifact_manifest.py --help
```

The operator must then run FUN's `resolve_nth_artifact.py` and `validate_nth_artifact.py` from the pinned or approved FUN checkout.
