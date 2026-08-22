# Artifact Derivation and Source Preservation

## Trigger
Use for create, generate, build, produce, make, draft, or export requests, especially when an existing workbook/artifact is a useful reference.

## Required inputs
- Operator request text.
- Existing candidate/reference artifact identities when available.
- Owning artifact family/engine and output convention.
- Exact current target identity only when an in-place update is explicitly requested.

## Outputs
- A distinct new output identity for create requests.
- Derivation preflight PASS receipt/status.
- Generated artifact and focused engine validation evidence.
- Handoff listing read-only sources and confirming source preservation.

## Procedure
1. Route to the owning artifact engine.
2. Discover and inspect the strongest existing artifact/reference; do not mutate it.
3. Choose the new output identity before generation.
4. Run `python scripts/validate_artifact_derivation_harness.py` with request, source(s), and proposed output.
5. Generate using the source as template/evidence/reference only.
6. Run the focused engine validator/preflight and record identities in the handoff.

## Guardrails
- Same subject, month, audience, or filename family never authorizes overwrite.
- `Candidates/` and `Active/` are protected inputs and cannot become create outputs.
- Do not delete, rename, move, overwrite, replace, or save over a source during create_new.
- An explicit update requires a named existing target and `--explicit-update`.
- Preserve existing artifact bytes even when their layout is copied into a derivative.

## Validation
`python scripts/validate_artifact_derivation_harness.py --summary`
`python -m unittest tests.test_artifact_derivation_harness -v`

## Proof ceiling
The harness fails closed when routed through its preflight. It cannot prevent direct mutation by a caller that intentionally bypasses the harness or prove Excel/Drive acceptance of the resulting artifact.
