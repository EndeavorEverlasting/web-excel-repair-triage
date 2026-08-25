# App Harness Validation

## Canonical owner

**P11 · End-to-End Harness Validator — aggregate safe repository harness proof into one exact-head offline/synthetic PASS/SKIP/FAIL gate.**

The canonical local and CI command is:

```text
python scripts/validate_app_harness.py --output Outputs/app-harness-validation.json
```

## Healthy matrix

```text
APP HARNESS VALIDATION
[PASS] required files
[PASS] run context
[PASS] artifact registry
[PASS] report renderer
[SKIP] optional MCP symbol smoke: lsp_project_not_loaded
[PASS] hook hygiene
Result: 5 passed / 1 skipped / 0 failed
```

## Gate semantics

Every check carries `REQUIRED`, `OPTIONAL`, `ENVIRONMENT_BLOCKED`, or `INAPPLICABLE` classification plus `PASS`, `SKIP`, or `FAIL`. Any required check that is not `PASS` makes the aggregate gate fail. Optional missing LSP/MCP readiness is an honest `SKIP`, never an inferred pass.

The JSON receipt records schema, proof level, `runtime_proof=false`, branch, exact head SHA, canonical command, validator set, required checks, skipped checks/reasons, P11 identifier/name/purpose, summary, final status, and proof ceiling. A moved head or required dependency requires a new receipt.

## Prompt-reference identity contract

When this harness, its reports, or a consuming agent refers an operator to a Prompt Kit prompt, the reference is incomplete unless it gives the **canonical identifier + canonical name + concise purpose** together, for example `P11 · End-to-End Harness Validator — one-command offline/synthetic harness proof`. Resolve those fields from the canonical prompt registry; never guess an ID from a description.

## CI/CD boundary

GitHub Actions invokes the canonical command exactly once and uploads its receipt; YAML does not reimplement the matrix. This receipt is one promotion-pipeline gate. Application/browser/service/device E2E, deployment, provider-runtime proof, and post-promotion containment remain separate downstream gates.

## Safety / proof ceiling

The validator uses an explicit subprocess allowlist. It does not launch products, games, browsers, servers, network probes, deployment tools, save/account operations, target mutations, or secret collection. Its proof ceiling is offline/synthetic repository harness readiness for the observed exact head.
