# Lua Embedding-Readiness Workflow

## 1. Pick up a Lua task

1. Read `AGENTS.md` and the root harness before changing anything.
2. Read `harness/lua/manifest.v1.json`, the Lua readiness contract, current report, capability, trigger, and skill.
3. Record current Git state and open PR collisions. Preserve other writers and use an isolated branch/worktree for substantial mutation.
4. Classify the request as **HARNESS READINESS** or **PRODUCT RUNTIME**. This workflow owns only readiness infrastructure. Actual interpreter/host integration belongs to a separately declared product lane.
5. If the request changes runtime behavior, stop at an explicit implementation handoff after producing the readiness evidence; do not smuggle product code into this harness.

## 2. Establish the host/script boundary

A future product design must answer these questions before implementation:

- Which host component owns the process and main execution loop?
- Which dynamic logic is intentionally delegated to Lua?
- Which performance-critical, resource-critical, filesystem, network, workbook, and lifecycle operations remain host-side?
- How many independent Lua states may coexist, who owns each, and where are normal/error teardown paths?
- Which host functions are individually allow-listed?
- Which Lua standard libraries are deliberately unavailable?
- What types cross the boundary and where are runtime checks performed?
- What script errors can occur and which host layer owns catch, rollback, cleanup, and reporting?
- Is bytecode used? If JIT is proposed, why is it needed and how is deoptimization state reconstructed?
- How will human reviewers audit AI-generated Lua without hidden or magical behavior?

## 3. Validate readiness before product implementation

Run in order:

```bash
python -m py_compile scripts/validate_lua_harness.py tests/test_lua_harness_contract.py
python scripts/validate_lua_harness.py --output Outputs/lua-embedding-readiness.json --summary
python -m unittest tests.test_lua_harness_contract -v
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
python -m unittest tests.test_harness_contract -v
python -m triage.gitignore_hygiene
git diff --check
```

A green result means the repository has a complete, connected **readiness contract**. It does not mean a Lua runtime exists.

## 4. Product-lane handoff

When product implementation is authorized, the next product sprint should consume the readiness contract rather than rewrite it. Its acceptance tests must produce observed evidence for:

1. host-owned main loop;
2. at least two independent VM states;
3. destruction of one state without corruption of another or the host;
4. explicit state release on success and failure;
5. script error caught by host with deterministic cleanup/rollback;
6. default denial of OS, IO, and native-module loading;
7. explicit allow-listed host API only;
8. runtime type checks at the host/Lua boundary;
9. performance/resource-critical work remaining host-owned;
10. optional JIT semantics with reconstructible deoptimization state if JIT is ever introduced;
11. readable, auditable Lua with Lua-native 1-based indexing and no hidden translation layer.

## 5. Failure handling

- **Missing component or registry drift:** repair the canonical `harness/lua` owner and add a regression test.
- **Unsafe sandbox proposal:** keep the contract red; do not weaken default-deny rules to make validation pass.
- **Product implementation absent:** report `not_implemented`; this is an expected state until a product sprint owns it.
- **Runtime claim without observed proof:** downgrade the claim to the strongest actually observed level.
- **Concurrent harness collision:** preserve the other branch and stack/reconcile semantically; never take an entire shared file side just to make Git green.

## 6. Handoff fields

Report repository, branch/PR, Lua runtime status, host/script boundary, sandbox policy, state-lifecycle policy, error boundary, type discipline, JIT posture, artifacts, validator results, commit/push/PR evidence, collision state, proof ceiling, and one exact executable next action.
