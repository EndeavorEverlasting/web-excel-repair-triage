# FUN NTH Artifact Export

## Trigger

Use this skill when a generated or repaired NTH workbook is ready to enter FUN's byte-level artifact-proof process and a reviewed FUN packet specification plus artifact assertion profile are available.

Do not use it when the workbook path is unresolved, the packet specification is missing, private production bytes would be committed as fixtures, or the request expects triage to infer evidence truth, labor hours, workstream attribution, or client acceptance.

## Required inputs

- Actual workbook byte path.
- A `fun-nth-packet-spec/v1` packet specification owned by FUN.
- A `web-excel-fun-nth-export-profile/v1` assertion profile.
- `contracts/upstream/fun/nth-artifact-contract.lock.json` and its pinned schema snapshots.
- Artifact type, builder version, producer commit, publication posture, and generation mode.
- Drive identifiers only when they are already authorized and the artifact remains private.

## Outputs

- A `fun-nth-artifact-manifest/v1` manifest containing computed filename, size, and SHA-256 plus the reviewed sheet/cell/reconciliation assertions.
- A `web-excel-fun-nth-producer-receipt/v1` receipt recording the triage producer identity, pinned FUN commit and schema hashes, inputs, artifact identity, publication posture, and proof ceiling.
- Nonzero failure when contract snapshots drift, inputs are incomplete, share-ready sheets diverge from approved tabs, packet forbidden content is omitted, or fixture/runtime posture is misrepresented.

## Procedure

1. Read `docs/FUN_NTH_PRODUCER_CONSUMER_CONTRACT_20260803.md` and the integration registry.
2. Verify the pinned FUN contract with the focused unit test or `verify_contract_lock`.
3. Confirm that the packet specification owns evidence truth and approved share tabs.
4. Build an assertion profile containing only artifact-validation fields. Do not place evidence claims or labor logic in it.
5. Run `scripts/export_fun_nth_artifact_manifest.py` against actual local bytes.
6. Preserve the manifest and producer receipt beside the generated artifact in the approved output directory.
7. Pass the artifact and manifest to FUN's resolver and validator from an exact FUN checkout.
8. Report producer proof separately from FUN acceptance proof and protected production proof.

## Guardrails

- FUN is the canonical schema donor and final acceptance owner.
- Triage owns generation, repair, semantic preservation, and manifest production only.
- Never create a competing manifest schema.
- Never use testing counts, install dates, device targets, or tracker status as labor multipliers while exporting.
- Never commit private production workbooks as test fixtures.
- Never copy Drive credentials or protected data into receipts.
- Never label a sanitized fixture as private, protected, or production runtime proof.
- Never weaken FUN packet restrictions to make an artifact pass.

## Validation

```text
python -m unittest tests.test_fun_nth_artifact_export -v
python scripts/export_fun_nth_artifact_manifest.py --help
python scripts/validate_harness.py
git diff --check
```

After local producer validation, run the pinned FUN resolver and artifact validator against the emitted manifest and actual artifact bytes.

## Proof ceiling

This skill can establish pinned-contract integrity, producer behavior, manifest construction, and byte identity for the supplied local artifact. It does not establish FUN's final acceptance, evidence truth, business approval, Excel desktop/web behavior, client acceptance, or protected production proof unless those separate gates are executed and recorded.
