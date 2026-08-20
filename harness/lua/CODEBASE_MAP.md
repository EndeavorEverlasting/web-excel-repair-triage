# Lua Harness Codebase Map

This overlay is the repository entry point for **Lua embedding readiness**. It does not install Lua and it does not implement a host runtime. It records the engineering boundaries that any later product implementation must satisfy before Lua can be called integrated.

## Reading order

1. `AGENTS.md` — repository governance; read-only for this harness lane.
2. `harness/lua/manifest.v1.json` — Lua harness component inventory and validation order.
3. `harness/lua/contracts/lua-embedding-readiness.v1.json` — machine-readable design boundary.
4. `harness/lua/WORKFLOW.md` — pickup, design, validation, failure, and handoff path.
5. `harness/lua/ARTIFACT_REGISTRY.md` and `harness/lua/artifacts.v1.json` — canonical control-plane and runtime evidence paths.
6. `harness/lua/validators.v1.json` — executable gates.
7. `harness/lua/capabilities.v1.json`, `harness/lua/triggers.v1.json`, and `.ai/skills/lua-embedding-readiness/SKILL.md` — routing and repeatable procedure.
8. `harness/lua/reports/CURRENT_STATE.md` — human-readable state and proof ceiling.

## Repository relationship

```text
web-excel-repair-triage/
├── AGENTS.md                              governance authority; not mutated here
├── harness/manifest.v1.json               root harness; registers this overlay
├── harness/lua/
│   ├── manifest.v1.json                   Lua harness inventory
│   ├── CODEBASE_MAP.md                    this map
│   ├── WORKFLOW.md                        Lua embedding-readiness workflow
│   ├── ARTIFACT_REGISTRY.md               Lua artifact contract
│   ├── artifacts.v1.json                  machine artifact registry
│   ├── validators.v1.json                 focused validator profile
│   ├── capabilities.v1.json               Lua readiness capability
│   ├── triggers.v1.json                   deterministic Lua routing
│   ├── contracts/lua-embedding-readiness.v1.json
│   ├── hooks/pre-commit.sh                focused staged/commit gate fragment
│   ├── hooks/pre-push.sh                  focused exhaustive gate fragment
│   └── reports/CURRENT_STATE.md           operator-readable state
├── .ai/skills/lua-embedding-readiness/SKILL.md
├── scripts/validate_lua_harness.py        fail-closed focused validator/report writer
├── tests/test_lua_harness_contract.py     focused mutation/regression tests
└── .github/workflows/lua-harness-contract.yml
```

## Product surfaces to inspect later, not mutate in this sprint

- `app.py` — existing application entry point and a possible future host boundary only after a product sprint selects an embedding architecture.
- `mcp_server.py` — existing MCP entry point; do not expose Lua through it without an explicit host API allow-list and product contract.
- `triage/` — existing artifact engines; performance-critical/resource-critical behavior stays host-owned unless a later product design proves a safe boundary.

No `.lua` file, Lua interpreter binary, native extension, FFI bridge, or host adapter is introduced by this harness sprint.

## Design invariants

- **Language as a library:** the host owns the process and main loop; Lua is embedded.
- **Performance partitioning:** performance-critical/resource-critical code remains host-side; Lua owns dynamic policy and frequently changed logic only.
- **Independent states:** separate VM states are isolated and explicitly released.
- **Exception tunneling:** scripts may fail, but the host catches errors and owns rollback/cleanup.
- **Simple execution:** bytecode and a small interpreter are acceptable; JIT is optional, not a prerequisite.
- **Type discipline:** runtime checks plus a documented host/Lua type boundary are required.
- **Sandbox by allow-list:** OS, IO, and native module loading are unavailable by default; only required host functions are registered.
- **Conceptual integrity:** features are excluded by default when the host can solve the requirement cleanly.
- **Lua semantics:** preserve Lua's 1-based indexing rather than adding translation magic.
- **AI auditability:** generated scripting must remain readable and non-magical enough for human verification.

## Commands

```bash
python -m py_compile scripts/validate_lua_harness.py tests/test_lua_harness_contract.py
python scripts/validate_lua_harness.py --output Outputs/lua-embedding-readiness.json --summary
python -m unittest tests.test_lua_harness_contract -v
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
python -m unittest tests.test_harness_contract -v
python -m triage.gitignore_hygiene
git diff --check
```

## Known traps

- Do not treat a passing readiness report as proof that Lua is installed or executing.
- Do not let a script own process lifetime, the host main loop, rollback, or resource cleanup.
- Do not open `os`, `io`, package/native loading, or arbitrary host calls by default.
- Do not share mutable VM state as a shortcut for cross-task coordination.
- Do not require LuaJIT. If a future product chooses JIT/deoptimization, reconstructible execution state becomes a runtime gate.
- Do not move heavy workbook, file, network, or resource management into Lua merely because it is convenient to script.
- Do not hide host behavior behind metaprogramming that a human cannot audit.
