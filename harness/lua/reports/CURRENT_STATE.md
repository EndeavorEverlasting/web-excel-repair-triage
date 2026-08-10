# Lua Harness Current State

**Runtime status: NOT IMPLEMENTED**

**Domain:** `lua-embedding-readiness`
**Parent workflow:** `harness-infrastructure`
**Canonical contract:** `harness/lua/contracts/lua-embedding-readiness.v1.json`

## What is working

- The repository has a versioned Lua embedding-readiness contract rather than an informal design note.
- Host ownership is explicit: the host owns the main loop, resource lifecycle, critical side effects, rollback, cleanup, and performance-critical/resource-critical work.
- Lua is bounded to dynamic scripting responsibilities rather than becoming the process controller.
- Multiple independent VM states and explicit normal/error release are mandatory runtime acceptance gates.
- Script errors are allowed to propagate to the host boundary, where the host must catch them and own cleanup/rollback.
- Sandbox defaults deny OS, IO, and native-module loading; host calls use an explicit allow-list.
- Runtime type checks and an internal host/Lua type discipline are required.
- Bytecode is allowed; JIT is optional. Any future deoptimization path must preserve reconstructible execution state.
- Lua-native 1-based indexing and conceptual minimalism are preserved.
- AI-generated Lua is required to remain human-auditable and non-magical.
- Focused validator, contract tests, machine registries, hook fragments, CI, scoped skill, codebase map, workflow, artifact registry, and this operator report are connected through `harness/lua/manifest.v1.json`.

## What is missing

- No Lua interpreter/runtime dependency is selected or installed.
- No host language or embedding library is selected by product code.
- No host adapter or C/C++/Rust/Python/native binding exists for this contract.
- No `.lua` product script is introduced by this sprint.
- No observed proof exists yet for independent VM states, state teardown, host-caught script errors, allow-listed calls, denied libraries, boundary type checks, bytecode execution, JIT/deoptimization, memory release, or application behavior.
- Performance budgets and the exact dynamic scripting use case remain product-lane decisions.

## Operator guidance

Run the focused report first:

```bash
python scripts/validate_lua_harness.py --output Outputs/lua-embedding-readiness.json --summary
python -m unittest tests.test_lua_harness_contract -v
```

Then run the root harness checks. A green static report intentionally leaves `runtime_status` as `not_implemented`; that is evidence discipline, not a failure.

The next implementation sprint must choose one concrete host integration point and satisfy the runtime checklist in `harness/lua/WORKFLOW.md` without weakening this contract.

## Proof ceiling

This overlay proves tracked harness infrastructure, static design invariants, machine-readable routing, validator/test behavior, and CI execution on the tested commit. It does **not** prove that Lua runs in the application, that sandboxes hold under hostile scripts, that VM memory is isolated or leak-free, that JIT/deoptimization works, or that an operator has accepted the runtime.
