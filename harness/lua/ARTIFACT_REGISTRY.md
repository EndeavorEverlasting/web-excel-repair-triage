# Lua Harness Artifact Registry

The machine-readable authority is `harness/lua/artifacts.v1.json`. This overlay records only Lua embedding-readiness control-plane and evidence artifacts; it does not declare a Lua product binary, interpreter, bytecode bundle, or application runtime.

## Tracked control-plane artifacts

| Artifact | Canonical path | Producer | Validator | Tracking |
|---|---|---|---|---|
| Lua harness control plane | `harness/lua/manifest.v1.json` | harness infrastructure sprint | `lua-harness-completeness` | Tracked. |
| Lua embedding contract | `harness/lua/contracts/lua-embedding-readiness.v1.json` | harness infrastructure sprint | `lua-harness-completeness` | Tracked versioned contract. |
| Lua workflow | `harness/lua/WORKFLOW.md` | harness infrastructure sprint | `lua-harness-completeness` | Tracked. |
| Lua scoped skill | `.ai/skills/lua-embedding-readiness/SKILL.md` | harness infrastructure sprint | `lua-harness-completeness` | Tracked. |
| Lua operator state | `harness/lua/reports/CURRENT_STATE.md` | harness infrastructure sprint | `lua-harness-completeness` | Tracked human-readable state. |

## Runtime evidence artifact

| Artifact | Canonical path | Generation | Naming | Tracking |
|---|---|---|---|---|
| Lua embedding-readiness report | `Outputs/lua-embedding-readiness.json` | `python scripts/validate_lua_harness.py --output Outputs/lua-embedding-readiness.json --summary` | Stable schema `lua-embedding-readiness-report/v1` | Gitignored or CI artifact. |

## Artifact rules

1. Resolve the runtime report from `harness/lua/artifacts.v1.json`; do not invent another output path.
2. Repository-local runtime reports must stay under `Outputs/`. CI may use runner-temporary storage outside the repository.
3. A readiness report may say the harness is complete while `runtime_status` remains `not_implemented`. That is correct and must not be promoted into runtime proof.
4. Future Lua bytecode, native libraries, generated scripts, or host bindings require a product-owned artifact contract before they are emitted.
5. No secrets, private workbook data, credentials, native library dumps, or host memory snapshots belong in this harness evidence.

## Validation

```bash
python scripts/validate_lua_harness.py --output Outputs/lua-embedding-readiness.json --summary
python -m unittest tests.test_lua_harness_contract -v
```

## Proof boundary

Tracked artifact presence proves repository integration. The report proves only the contract and harness surfaces exercised by the validator. It does not prove interpreter availability, state isolation, sandbox enforcement, bytecode execution, JIT/deoptimization, memory release, host rollback, or application behavior.
