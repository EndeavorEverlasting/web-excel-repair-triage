# Prompt Kit Compute-Authority Evaluation

Paired Control/Treatment harness for measuring whether the strengthened Prompt Kit compute-authority contract produces **more useful compute**, not merely longer runs.

Canonical program plan: `harness/evals/COMPUTE_AUTHORITY_EVALUATION_SPRINT_PLAN.md`.

## Current proof state

- **Sprint 1:** IMPLEMENTED / WIRED / VALIDATED for fixture reachability, frozen prompt identities, deterministic graders, and aggregate scaffolding.
- **Sprint 2 harness:** provider-neutral runtime/capture seam, immutable condition resolver, disposable run isolation, deterministic balanced pilot ordering, and invalid-run receipts.
- **External-agent effectiveness:** `UNPROVEN_RUNTIME` until a real external-agent adapter executes observed pilot/main-study runs. A local fake adapter or CI harness PASS is never an effectiveness result.

## Quick start

```bash
python harness/evals/compute-authority/scripts/materialize_fixtures.py
python harness/evals/compute-authority/scripts/validate_fixtures.py --summary
python harness/evals/compute-authority/scripts/conditions.py --summary
python -m unittest tests.test_compute_authority_eval_harness tests.test_compute_authority_runtime_harness -v
python harness/evals/compute-authority/scripts/pilot.py --plan-only --pilot-id local-no-runtime --summary
```

The last command deliberately emits `UNPROVEN_RUNTIME`; it proves only that the frozen 16-run paired plan can be resolved without pretending an external runtime exists.

## Runtime adapter

An external runtime is attached with a JSON config matching `runtime/adapter-contract.v1.json`:

```json
{
  "schema_version": "compute-authority-agent-adapter/v1",
  "argv": ["agent-runner", "--workspace", "{workspace}", "--task", "{task}", "--policy", "{prompt}", "--result", "{result}"],
  "timeout_seconds": 900,
  "env_allowlist": []
}
```

The adapter command executes with `shell=false` inside the isolated fixture workspace. The harness supplies four placeholders: `{workspace}`, `{task}`, `{prompt}`, and `{result}`. The provider writes one JSON result to the temporary `{result}` path.

Only the structural allowlist in `runtime/adapter-contract.v1.json` may be persisted. Raw prompt/response/clipboard/transcript/query/identity fields are rejected. Provider stdout/stderr are not persisted. Unknown or invalid runtime evidence becomes an explicit invalid-run receipt; incomplete runs are not silently scored.

Observed pilot invocation:

```bash
python harness/evals/compute-authority/scripts/pilot.py \
  --adapter-config path/to/provider-adapter.json \
  --pilot-id <provider-model-pilot> \
  --summary
```

Provider credentials remain outside the repository and may be passed to the subprocess only through names explicitly listed in `env_allowlist`.

## Layout

- `prompts/identities.json` — Sprint 1 frozen prompt identities.
- `runtime/conditions.v1.json` — immutable Sprint 2 condition/pairing contract.
- `runtime/adapter-contract.v1.json` — provider-neutral execution/capture/privacy boundary.
- `fixtures/` — eight deterministic cases; evaluator gold stays outside agent workspaces.
- `runs/` — ignored per-run evidence bundles.
- `aggregate/` — ignored aggregate runtime outputs.
- `Outputs/repository-ai-evals/compute-authority/` — workflow/operator runtime receipts.

Hidden ground truth lives in each case's `evaluator.manifest.yaml` (and TC05 `evaluator/` oracles) and must never be copied into agent workspaces; `reset_fixture.py` enforces this.

## Evidence boundary

A successful repository/CI run proves only the harness. The 16-run pilot validates runtime capture/scoring/cost assumptions when an external runtime is actually connected. The final effectiveness verdict remains governed by the 48-valid-run Sprint 3 acceptance criteria and blinded scoring in the canonical plan.
