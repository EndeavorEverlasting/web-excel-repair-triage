# Artifact Derivation Harness — Current State

## Working
- Create/generate/build requests require a new output identity.
- Existing artifacts are read-only reference sources by default.
- Same-identity create and pre-existing create output are rejected.
- `Candidates/` and `Active/` are rejected as create output targets.
- Explicit same-identity update requires explicit operator update intent.
- Pre-commit, pre-push, focused unit tests, and dedicated CI exercise the guard.

## Broken
None known in the static harness contract.

## Missing
The harness is a routed safety control, not an OS/provider ACL. A caller with direct mutation access can bypass it. Individual artifact engines keep their own correctness and package safety gates.

## Proof ceiling
Static harness completeness plus runtime request/source/output identity preflight. No claim of workbook correctness, Excel for Web acceptance, provider delivery, or universal anti-mutation enforcement.

## Operator next action
Before the next artifact generator opens a writer, run the guard against the best reference artifact and the proposed distinct output identity.
