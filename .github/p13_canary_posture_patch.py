from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    overrides_path = Path("registry/prompts/prompt-overrides.v1.json")
    payload = json.loads(overrides_path.read_text(encoding="utf-8"))
    p13 = next(item for item in payload["overrides"] if item["id"] == "P13")

    p13["sprintRole"] = (
        "Recover recurring pain and ambiguous inherited execution state through a mandatory "
        "P114 canary/posture gate, then advance the critical path with P07-owned parallel execution, "
        "durable prevention, and verified mainline convergence through a bounded fixed point"
    )
    p13["useWhen"] = (
        "A mistake, explanation, setup problem, execution stall, urgency complaint, proof-floor loop, "
        "deployment delay, missing parallel execution, or ambiguous inherited repository/runtime state "
        "repeats and the operator expects the agent to recover truth and sprint immediately instead of "
        "asking them to reconstruct the environment."
    )
    p13["inspectFirst"] = (
        "Current conversation and repeated operator corrections; P114 Conversation Context Canary & Handoff Guard "
        "signals relevant to this task; repository/provider default branch, current head, worktrees, dirty state, "
        "open/recent overlapping PRs and commits; Replit/runtime/workstation posture; available tools/connectors; "
        "account/role/access and mutation authority; current proof/stage floor; deployment/release/runtime gate; "
        "work ledger; AGENTS.md and scoped rules; prompt/workflow/skill/validator owners; artifacts and blockers."
    )
    p13["expectedOutput"] = (
        "A mandatory P114-owned execution-posture canary and capability/access matrix that separates executable "
        "from access-blocked lanes; immediate advancement of the current critical path; actual P07-owned parallel "
        "worker dispatch when usable capacity and collision-safe lanes exist, otherwise one exact capability "
        "limitation and serial continuation; the smallest implemented durable prevention; specialist repair routed "
        "to its canonical owner instead of duplicated into P13; and the exact validated owned change integrated into "
        "the current default branch and verified there, or an exact external/user-only blocker plus advancing action."
    )
    p13["proofGate"] = (
        "The recurrence or inherited-state ambiguity is evidence-backed; the P114-owned canary resolves enough "
        "repository/provider, Replit/runtime, workstation, network/EXEC, account/role/access, tool/connectivity, and "
        "mutation-authority posture to distinguish executable lanes from blocked ones without guessing; current proof "
        "floor and next gate are explicit; P07 parallel execution is actually dispatched when its capacity and "
        "collision-safety conditions hold, or the exact unavailable-capability limitation is reported once and work "
        "continues serially; one correct authority owns prevention; specialist doctrine is referred rather than copied; "
        "focused regression/build/parity validation passes; a deliberate second pass finds no practical in-scope "
        "improvement; and the exact validated owned head is integrated into and verified on the current default branch "
        "when authorized. A branch, PR, plan-only parallelism note, or unresolved posture guess is insufficient completion."
    )

    content = p13["copyContent"]
    canary_marker = "\n\n1. RECOVER THE RECURRENCE WITHOUT MAKING THE OPERATOR RETYPE IT"
    if canary_marker not in content:
        raise SystemExit("P13 canary insertion marker moved")
    canary = """

0A. MANDATORY CANARY / EXECUTION POSTURE GATE — P114 OWNER
Before choosing the next sprint gate or declaring a lane executable, resolve the task-relevant execution posture. P114 Conversation Context Canary & Handoff Guard owns the canary semantics; P13 consumes its resolved signals and must not copy or fork P114's full doctrine.

Build one compact CAPABILITY / ACCESS MATRIX from current evidence. Resolve only fields that can change what can safely execute now:
- REPOSITORY / PROVIDER: canonical repository, checkout/worktree presence, remote default branch, current/tracking head, dirty/diverged state, open/recent overlapping PRs or claims, provider reachability, and current branch/PR mutation path.
- REPLIT / RUNTIME: whether Replit or another hosted/local runtime is actually in play; project/repl/runtime identity when evidenced; current run/deploy state; reachable runtime/CI/browser/device surfaces; and whether the relevant target is live, local, simulated, or UNKNOWN.
- WORKSTATION POSTURE: workstation/profile alias when relevant, OS/shell/kernel/EXEC context, network posture, available binaries/tooling, connected tools/connectors, and whether the current machine can reach the repository/runtime surfaces needed by this sprint.
- ACCOUNT / ROLE / ACCESS: active account alias when relevant, resource owner, current role, required role, repository/provider permissions, runtime/deploy permissions, credential or secret availability as a yes/no capability only, and any ACCOUNT SWITCH GATE or role insufficiency already established by P114.
- AUTHORITY: commit, push, PR, review, merge, release, deploy, live-target, destructive, and physical/operator-only authority required by each candidate lane.

Use `UNKNOWN` for unresolved posture; do not invent machine identity, Replit state, credentials, permissions, or authority. An UNKNOWN blocks only actions whose safety or correctness depends on it. Do not freeze the whole sprint because one unrelated lane lacks access.

Partition candidate work into `EXECUTABLE NOW`, `BLOCKED BY ACCESS/AUTHORITY`, and `SERIALIZED BY DEPENDENCY`. For every blocked lane name the exact missing capability or user-only gate. If any safe lane is executable, continue immediately instead of stopping for a global permission question.
"""
    content = content.replace(canary_marker, canary + canary_marker, 1)

    failure_marker = "- TOOL_OR_SETUP_FRICTION — the same environment/command/setup failure keeps recurring.\n"
    if failure_marker not in content:
        raise SystemExit("P13 failure-class marker moved")
    content = content.replace(
        failure_marker,
        failure_marker
        + "- AMBIGUOUS_EXECUTION_POSTURE — inherited repo/runtime/workstation/access claims disagree or are incomplete enough to change which sprint can execute safely.\n",
        1,
    )

    critical_marker = "- work that is useful but not critical and therefore must not displace the gate.\n"
    if critical_marker not in content:
        raise SystemExit("P13 critical-path marker moved")
    content = content.replace(
        critical_marker,
        critical_marker
        + "Do not select or launch the next gate from remembered repo state alone when the canary shows material ambiguity. Use the capability/access matrix to choose every lane that is executable now and isolate only the lanes that are truly blocked.\n",
        1,
    )

    start_marker = "5. SUB-PART AGENT PLAN IS MANDATORY WHEN PARALLEL WORK IS SAFE OR WHEN MISSING PARALLELISM CAUSED DELAY"
    end_marker = "6. INSTALL THE SMALLEST DURABLE PREVENTION"
    start = content.find(start_marker)
    end = content.find(end_marker, start)
    if start < 0 or end < 0:
        raise SystemExit("P13 parallel section markers moved")
    parallel = """5. PARALLEL EXECUTION — P07 OWNS ACTUAL DISPATCH
P13 treats missing parallelism as recurring friction, but P07 owns the execution/coordinator contract. Do not replace execution with a parallelization plan.
- Probe whether the current environment exposes a usable sub-agent/child-agent/delegated-worker mechanism and at least two concurrent worker slots.
- If that mechanism exists and at least two meaningful lanes are independent and collision-safe, dispatch them immediately under P07's one-writer-per-surface and coordinator-rejoin rules. Evidence must identify the workers/lanes and their returned artifacts, diffs/heads, tests, or findings.
- If dispatch capability is unavailable or capacity is below two, continue serially and report exactly once: `PARALLEL EXECUTION: unavailable — <exact capability limitation>.` Do not emit a hypothetical lane list or copy-paste worker packet merely because dispatch is unavailable.
- Serial use of multiple tools, connectors, commands, tabs, or repository reads is not parallel execution.
- If independent work exists but needs formal collision-safe factoring before dispatch, use P59 only for that factoring and return directly to P07 execution; planning must not become a terminal state.
- Missing access on one lane does not collapse other executable lanes. Dispatch or execute the safe lanes and isolate the blocked lane with its exact access/authority gate.
- P13 remains the recurrence/prevention/convergence owner; P07 remains the actual parallel execution owner. Do not duplicate P07's full worker protocol here.

"""
    content = content[:start] + parallel + content[end:]
    p13["copyContent"] = content

    for keyword in (
        "execution posture",
        "canary",
        "workstation posture",
        "replit state",
        "access matrix",
        "ambiguous repo state",
        "capability gate",
    ):
        if keyword not in p13["keywords"]:
            p13["keywords"].append(keyword)

    overrides_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    test_path = Path("tests/test_skill_prompt_registry.py")
    tests = test_path.read_text(encoding="utf-8")
    old = '''            "SUB-PART AGENT PLAN IS MANDATORY",\n            "Sub-Part Agent: none — serialized dependency",\n            "Never use a Sub-Part Agent plan as an excuse to stop the primary critical path",'''
    new = '''            "MANDATORY CANARY / EXECUTION POSTURE GATE",\n            "P114 Conversation Context Canary & Handoff Guard",\n            "CAPABILITY / ACCESS MATRIX",\n            "REPLIT / RUNTIME",\n            "WORKSTATION POSTURE",\n            "AMBIGUOUS_EXECUTION_POSTURE",\n            "PARALLEL EXECUTION — P07 OWNS ACTUAL DISPATCH",\n            "P07 owns the execution/coordinator contract",\n            "PARALLEL EXECUTION: unavailable — <exact capability limitation>",\n            "Do not emit a hypothetical lane list or copy-paste worker packet merely because dispatch is unavailable",'''
    if old not in tests:
        raise SystemExit("P13 focused regression marker moved")
    tests = tests.replace(old, new, 1)
    test_path.write_text(tests, encoding="utf-8")

    required = [
        "MANDATORY CANARY / EXECUTION POSTURE GATE — P114 OWNER",
        "REPOSITORY / PROVIDER",
        "REPLIT / RUNTIME",
        "WORKSTATION POSTURE",
        "ACCOUNT / ROLE / ACCESS",
        "EXECUTABLE NOW",
        "BLOCKED BY ACCESS/AUTHORITY",
        "P07 OWNS ACTUAL DISPATCH",
        "P59 only for that factoring",
    ]
    for phrase in required:
        if phrase not in content:
            raise SystemExit(f"missing semantic phrase: {phrase}")
    for phrase in (
        "SUB-PART AGENT PLAN IS MANDATORY",
        "Sub-Part Agent: none — serialized dependency",
        "emit one self-contained copy-paste Sub-Part Agent prompt",
    ):
        if phrase in content:
            raise SystemExit(f"stale parallel-plan phrase remains: {phrase}")


if __name__ == "__main__":
    main()
