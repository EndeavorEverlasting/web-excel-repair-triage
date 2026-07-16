# Prompt Kit V32 Repository Floor

## Status

This document freezes repository ownership before V32 generation work begins.

Base dependency: PR #59, `feat/harness-run-context-artifact-registry`.

The V32 workbook remains operator evidence, not a tracked source binary. Its verified SHA-256 is:

```text
46db6b6b98162587f107fa4c9a1e6bd8b08551a2a9f899946a2ed6f8ad87f115
```

## Canonical harness contracts

| Contract | Canonical path | Owner |
|---|---|---|
| Run identity and provenance | `.ai/schemas/run-context.json` | PR #59 |
| Validation result vocabulary | `.ai/schemas/validation-report.json` | PR #59 |
| Artifact types and locations | `.ai/artifact-registry.json` | PR #59 plus this floor PR |
| Workflow registration | `.ai/workflow-registry.json` | PR #59 plus this floor PR |
| Inherited CI failure classification | `.ai/ci-failure-registry.json` | This floor PR |
| Validator authority | `.ai/validator-registry.json` | This floor PR |
| Prompt-kit aggregate acceptance | `.ai/schemas/prompt-kit-acceptance-state.json` | This floor PR |
| Environment-specific acceptance | `.ai/schemas/prompt-kit-field-acceptance-record.json` | This floor PR |

The only validation states are:

```text
PASS
FAIL
NOT_RUN
NOT_APPLICABLE
BLOCKED
```

A missing Desktop, Web, clipboard, mouse, PowerShell, or operator gate must not be represented as PASS.

## Canonical validator ownership

| Surface | Canonical module | Owner PR | Disposition |
|---|---|---:|---|
| ZIP/XML/table/merge/package hygiene | `triage.workbook_package_hygiene` | #51 | Preserve unique package checks; consume through registry |
| Relationship targets, internal fragments, markup compatibility, calcChain | `triage.web_excel_compatibility_rules` | #57 | Canonical owner; absorbs the narrow #53 relationship lane after parity proof |
| Worksheet row and cell ordering | `triage.worksheet_cell_integrity` | #57 | Preserve |
| Copy-surface bounds | `triage.copy_surface_bounds` | #57 | Preserve |
| V32 prompt, GNHF, navigation, semantic style, and protection contract | `triage.prompt_kit_operability_contract` | #61 | Preserve as the V32 read-only contract |
| Desktop Excel recovery and window evidence | `triage.excel_recovery_triage` | #60 | Preserve; emit canonical validation vocabulary |

No later sprint may introduce another validator for one of these surfaces without first changing `.ai/validator-registry.json` and its tests.

## PR disposition ledger

### PR #51

**Disposition:** preserve unique package-hygiene behavior and durable repair lessons. Do not use its copy of `triage.web_excel_compatibility_rules.py` as the final relationship authority.

### PR #53

**Disposition:** superseded candidate. Close only after #57 proves equivalent or stronger relationship-target tests. Until that parity proof exists, retain the branch.

### PR #54

**Disposition:** preserve as design evidence for the later agent-harness sprint. It does not prove executable skills, capabilities, or triggers.

### PR #57

**Disposition:** canonical V21 generator and shared prompt-kit package-validator owner. Refresh against current `main` before merge. Keep workbook binaries untracked.

### PR #59

**Disposition:** canonical harness floor. This PR is stacked on it because run context, registries, proof levels, and validation states must land before V32 generation.

Its inherited `Artifact engine tests` failure is classified in `.ai/ci-failure-registry.json` as
`artifact-engines-pr59-invalid-external-reference-namespace`. Base run
[#186](https://github.com/EndeavorEverlasting/web-excel-repair-triage/actions/runs/29379460918) and confirming
run [#188](https://github.com/EndeavorEverlasting/web-excel-repair-triage/actions/runs/29458166275) fail the same
11 tests before their assertions. The synthetic stale-recon fixture adds `externalReference r:id="rIdExt1"` without
declaring the `r` namespace in `xl/workbook.xml`; the CI `lxml` parser rejects that markup. This classification is
blocking and non-waiving. Resolution belongs to #59 and requires a green rerun of the complete workflow.

### PR #60

**Disposition:** canonical Desktop Excel recovery lane. Desktop window selection remains PID/HWND-bound and separate from Excel for Web browser proof.

### PR #61

**Disposition:** canonical V32 operability and GNHF contract, stacked on #57. It provides read-only static contract proof, not deterministic V32 generation or Office field acceptance.

## Required V32 generator interfaces

The V32 generator sprint must consume, not duplicate:

- `.ai/validator-registry.json`;
- `.ai/artifact-registry.json`;
- `.ai/workflow-registry.json`;
- `.ai/schemas/run-context.json`;
- `.ai/schemas/validation-report.json`;
- `.ai/schemas/prompt-kit-acceptance-state.json`;
- `.ai/schemas/prompt-kit-field-acceptance-record.json`.

It must emit under an ignored output directory:

```text
run-context.json
manifest.json
validation-report.json
package-delta.json
acceptance-state.json
field-evidence/*.json
```

Generated `.xlsx` files, screenshots, recovery logs, browser profiles, repaired files, and operator evidence stay outside Git.

## Proof boundaries

- Package proof does not prove Desktop Excel.
- Desktop Excel proof does not prove Excel for Web.
- Graph workbook-session proof does not prove browser UI behavior.
- Browser open proof does not prove exact clipboard output.
- Command-shape proof does not prove GNHF execution.
- Rendering does not prove mouse navigation.
- Operator acceptance applies only to the exact workbook SHA recorded in the field acceptance record.

## Merge order

```text
PR #59 harness floor
-> this floor PR
-> refreshed PR #57 validator and V21 generator owner
-> PR #61 V32 operability contract
-> PR #60 Desktop recovery lane
-> V32 generator product PR
-> agent harness and release convergence
```

The order may change only after recording an evidence-based dependency update in the PR body.
