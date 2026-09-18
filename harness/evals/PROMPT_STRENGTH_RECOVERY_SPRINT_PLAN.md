# Prompt Strength / Execution Reliability Closeout Plan

## Current floor

- Repository: `EndeavorEverlasting/web-excel-repair-triage`
- Frozen release/treatment floor: `main@fc9437ff3fa83ce9df82c6ad85a79d09d7e0bd17`.
- Prompt-strength closeout integration: PR #553 / `b507c421a15e1d1bec974e5d75598b80c8f0f90d`; this documentation/control-plane commit does not change the frozen treatment identity.
- Integrated prerequisites: #533, #535, #536, #542, #543, #546, #548, #551, #552, #537, and #538.
- #537 prompt-strength convergence is integrated at `96717034e595864b2ac4bb28a88d99ac3523674e`.
- #538 release v0.9.0 is integrated at `fc9437ff3fa83ce9df82c6ad85a79d09d7e0bd17`; both tag `operant-v0.9.0` and GitHub Release `Operant v0.9.0` target that exact commit.
- Provider-only repository execution is active in this runtime; no mounted local checkout or argv-addressable external-agent runtime/credential surface is available.

## Active phase — P67 observed-effectiveness runtime gate

**PARALLEL EXECUTION: NOT_APPLICABLE — dependency graph width is 1.**

Completed source lane:
- the #537 prompt-strength semantic/adversarial convergence lane is integrated and its durable dispatch manifest/seed now record `PASS`;
- the 21-dimension semantic floor, PSA-031 silent-stop regression, PSA-029 evidence discipline, deterministic-test-floor registration, and tracked-control-plane artifact hygiene remain mainline owners.

Current runtime owner:
- canonical plan: `harness/evals/COMPUTE_AUTHORITY_EVALUATION_SPRINT_PLAN.md`;
- harness: `harness/evals/compute-authority/`;
- owner: P67 Repository Eval Framework Builder + `skill-evaluation`;
- required transition: execute the real 16-run paired external-agent pilot against the frozen Control/Treatment identities;
- current proof state: `UNPROVEN_RUNTIME` / `RUNTIME_UNAVAILABLE` in this execution environment because no real argv-addressable external-agent adapter and provider credential surface is exposed.

Do not mutate treatment prompt behavior, use a fake/local adapter as effectiveness evidence, or promote repository/CI proof into downstream model-obedience proof.

## Completed parallel wave evidence

The preceding width-2 wave used the connected GitHub provider on isolated #543/#537 branches. Both branch mutations were launched concurrently and rejoined by this coordinator. #543 additionally used a temporary pinned provider adapter to execute canonical `prompt-kit-build-proof`; the adapter was removed before integration. The tracked width-1 manifest/seed now record the completed #537 convergence lane as `PASS`; they no longer advertise an already-merged lane as `DISPATCHED`.

## Completed successor phase — publication / release

- #537 integrated at `96717034e595864b2ac4bb28a88d99ac3523674e`.
- #538 integrated release v0.9.0 at `fc9437ff3fa83ce9df82c6ad85a79d09d7e0bd17`.
- `operant-v0.9.0` and GitHub Release `Operant v0.9.0` both target that exact merged commit.
- Prompt Kit publication/release identity is therefore frozen for the P67 treatment generation.

Do not manually edit `OPERANT_VERSION`, changelog, product-identity mirrors, generated Prompt Kit output, or treatment wording inside the frozen study.

## Active successor phase — observed effectiveness

The release freeze dependency is satisfied. The remaining required whole-outcome transition is the existing P67 compute-authority pilot:

```bash
python harness/evals/compute-authority/scripts/pilot.py \
  --adapter-config path/to/provider-adapter.json \
  --pilot-id <provider-model-pilot> \
  --summary
```

The adapter must satisfy `harness/evals/compute-authority/runtime/adapter-contract.v1.json` and invoke a real external agent with credentials supplied only through its explicit `env_allowlist`. This ChatGPT/GitHub-provider runtime cannot execute that argv adapter or access provider credentials, so the pilot remains explicitly `BLOCKED / UNPROVEN_RUNTIME` with blocker `RUNTIME_UNAVAILABLE`. Repository/static/provider proof never becomes downstream model-obedience proof.

## Definition of done

1. #537 is integrated with the current semantic floor and regression-hardened dispatch artifact hygiene. **PROVEN DONE** at `96717034e595864b2ac4bb28a88d99ac3523674e`.
2. final main Prompt Kit publication/release identity is observed. **PROVEN DONE** through release v0.9.0 at `fc9437ff3fa83ce9df82c6ad85a79d09d7e0bd17`.
3. #538 is validated, integrated, tagged, and released. **PROVEN DONE**; `operant-v0.9.0` and its GitHub Release target the exact merged commit.
4. P67 is OBSERVED at its runtime proof surface or explicitly BLOCKED/UNPROVEN_RUNTIME at the exact external gate. **BLOCKED / UNPROVEN_RUNTIME** here at `RUNTIME_UNAVAILABLE`; no real external-agent argv adapter/credential surface is exposed in this execution environment.

## Proof ceiling

Repository/provider evidence can prove source, regression, exact-head CI, generated projection, integration, Pages, and release identity when observed. It does not prove unavailable workstation-local execution, universal downstream model obedience, or operator acceptance.
