# Lua Embedding Readiness

## Trigger

Use this skill when Lua is proposed as an embedded scripting layer, when an existing Lua boundary needs review, or when host control, state isolation, sandbox exposure, error cleanup, type discipline, bytecode/JIT posture, or AI-generated script auditability is uncertain.

Do not use this skill to pretend a Lua runtime exists. Product/runtime implementation requires a separately declared product lane.

## Required inputs

- repository `AGENTS.md` and root harness state;
- `harness/lua/manifest.v1.json` and `harness/lua/contracts/lua-embedding-readiness.v1.json`;
- the requested scripting use case;
- candidate host entry points and resource owners;
- proposed host functions exposed to scripts;
- state lifecycle and error cleanup expectations;
- current tests/runtime evidence, if any.

## Outputs

- one explicit host/Lua responsibility boundary;
- sandbox allow-list and default-deny decision;
- VM state ownership/lifecycle contract;
- script-error-to-host cleanup boundary;
- runtime type-discipline expectations;
- bytecode/JIT decision with proof requirements;
- `Outputs/lua-embedding-readiness.json` static readiness report;
- exact product-lane runtime acceptance gates when implementation is absent.

## Procedure

1. Read governance and the root harness; preserve concurrent writers and existing product ownership.
2. Classify current state as `not_implemented`, `partial`, or `implemented` from repository/runtime evidence. Never infer implementation from this skill or contract.
3. Keep the **host in control**: the host owns the main loop, process lifetime, rollback, cleanup, performance-critical work, resource-critical work, and native side effects.
4. Give Lua only dynamic/high-frequency policy or orchestration that benefits from scripting. Prefer a host-language solution when scripting adds hidden complexity without real leverage.
5. Define independent VM states. Each state needs an owner, creation path, normal teardown, error teardown, and proof that destroying one does not corrupt another state or the host.
6. Tunnel script errors to the host. The host catches them and owns cleanup/rollback; script failure must not strand host resources.
7. Default-deny the sandbox. Do not expose OS, IO, native module loading, or arbitrary host calls by default. Register only the specific host functions required by the use case.
8. Document the host/Lua value types and runtime checks. Dynamic typing does not remove the need for an internal type discipline.
9. Prefer simple interpreter/bytecode execution until evidence justifies JIT complexity. LuaJIT is optional. If future JIT/deoptimization exists, require reconstructible execution/stack state.
10. Preserve Lua-native 1-based indexing. Do not add opaque index translation just to mimic a host convention.
11. Optimize AI-generated Lua for human audit: explicit control flow, narrow APIs, minimal metaprogramming, no hidden environment mutation, and no magical side effects.
12. Run the focused validator/tests, then the root harness gates. Hand actual runtime implementation to the product owner with the acceptance checklist.

## Guardrails

- No `AGENTS.md` mutation in this skill's harness lane.
- No Lua interpreter, `.lua` product script, native binding, FFI bridge, or host product code is added merely to make the readiness harness green.
- No default OS or IO library access.
- No unrestricted `require`, dynamic native-module loading, shell execution, filesystem access, or network access.
- No shared mutable VM state as an implicit global coordination channel.
- No script-owned process lifetime, host main loop, resource rollback, or critical cleanup.
- No requirement for JIT when the interpreter is sufficient.
- No runtime claim from static contract, tests, or CI alone.
- No weakening validation to accommodate an unsafe implementation proposal.

## Validation

```bash
python -m py_compile scripts/validate_lua_harness.py tests/test_lua_harness_contract.py
python scripts/validate_lua_harness.py --output Outputs/lua-embedding-readiness.json --summary
python -m unittest tests.test_lua_harness_contract -v
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
python -m unittest tests.test_harness_contract -v
python -m triage.gitignore_hygiene
git diff --check
```

A later product implementation must add observed runtime tests for state independence, teardown, host-caught script errors, default-deny sandbox behavior, allow-listed calls, boundary type checks, and any chosen bytecode/JIT behavior.

## Proof ceiling

This skill and its validators prove only repository harness completeness and the encoded Lua design boundary. They do not prove Lua is installed, embedded, sandboxed at runtime, memory-safe, leak-free, performant, JIT-correct, or accepted by an operator.
