from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "docs/prompts.json"
OVERRIDES = ROOT / "registry/prompts/prompt-overrides.v1.json"
SPEC = ROOT / "harness/specs/prompt-operations.md"
TEST = ROOT / "tests/test_p02_p07_autonomous_iteration.py"
SKILL_TEST = ROOT / "tests/test_skill_prompt_registry.py"
NEW_TEST = ROOT / "tests/test_prompt_parallel_execution_contract.py"

LADDER = """PARALLEL CAPABILITY LADDER / AUTONOMY GATE
Parallelism is a requirement of the dependency graph, not a feature of one preferred worker product.
- First build the owned dependency graph. If at least two meaningful dependency-ready lanes can proceed without conflicting writes, graph width is at least two and parallel dispatch remains required.
- Probe execution adapters in order, using only mechanisms actually evidenced in the current environment: (1) native sub-agent/child-agent/delegated-agent/task-worker APIs; (2) repository/local agent runners and orchestrators such as repo-proven AgentSwitchboard, GNHF, OpenCode, Cursor/Codex/Claude wrappers; (3) connected remote/provider/MCP execution surfaces that can independently own bounded lanes; (4) CI/job/matrix fan-out capable of executing the lane safely; (5) genuinely concurrent local processes/tool jobs for deterministic non-LLM lanes. Do not invent an adapter merely because it appears in this list.
- Absence of one adapter class is not global absence. In particular, `no connected self-hosted workers` rules out only that adapter class; continue down the capability ladder before declaring degraded execution.
- At the first safe rung with enough capacity for at least two dependency-ready lanes, dispatch immediately. Record adapter, lane identity, mutation owner, launch action, return artifact/proof, and convergence owner.
- Serial calls to multiple tools are not parallelism. A tool/process rung counts only when independent jobs are actually launched concurrently and their results are rejoined.
- If graph width is one after real dependency/collision analysis, report `PARALLEL EXECUTION: NOT_APPLICABLE — dependency graph width is 1.` Serial execution is then correct, not degraded.
- If graph width is at least two but every safe rung is genuinely unavailable or blocked, serial progress may continue only to avoid deadlock. Report `PARALLEL EXECUTION: DEGRADED — <exhausted capability-ladder evidence>.` and `AUTONOMY_GAP: <smallest executable adapter/bootstrap/repair route>.` Parallel-execution proof remains UNPROVEN; do not convert degraded serial progress into a clean parallel pass.
- Never make the operator create chats, paste lane prompts, shuttle context, or act as the scheduler when any autonomous adapter can carry the lane. Human copy panels are portability/recovery fallback only.
- When the owned scope includes the missing adapter seam, build or repair the smallest durable adapter now. Otherwise route the AUTONOMY_GAP to its canonical owner as a machine-executable follow-on without blocking independent safe progress."""

MANIFEST = """PARALLEL DISPATCH MANIFEST
For every lane record: lane_id; mission; dependencies; owned mutation surfaces; forbidden surfaces; branch/worktree or read-only posture; selected execution adapter and ladder rung; exact launch action/tool/API/workflow; expected artifact/return contract; validation; convergence owner; and status. The manifest is the primary orchestration artifact. Copyable chat panels may mirror it for portability, but a plan that requires the operator to launch dependency-ready lanes manually is not automation-complete."""


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prompt_by_id(items, pid: str):
    for item in items:
        if item.get("id") == pid:
            return item
    raise SystemExit(f"missing prompt {pid}")


def replace_method(text: str, method: str, replacement: str) -> str:
    pattern = rf"(?ms)^    def {re.escape(method)}\(self\).*?(?=^    def |^\nif __name__)"
    updated, count = re.subn(pattern, replacement.rstrip() + "\n\n", text, count=1)
    if count != 1:
        raise SystemExit(f"expected one method {method}, got {count}")
    return updated


prompts = load(PROMPTS)
p04 = prompt_by_id(prompts, "P04")
p07 = prompt_by_id(prompts, "P07")
p59 = prompt_by_id(prompts, "P59")

p04["sprintRole"] = "Factor remaining work into dependency-aware lanes and produce an automation-ready parallel dispatch manifest with explicit convergence ownership"
p04["expectedOutput"] = "A durable factoring plan whose primary orchestration artifact is a PARALLEL DISPATCH MANIFEST: dependency graph, graph width, collision ownership, execution-adapter ladder resolution, executable launch actions, validation/proof gates, and convergence owner. Human copy panels are portability fallback only, not the primary scheduler."
p04["nextStep"] = "Persist the accepted factoring plan and dispatch manifest to the canonical plan/handoff owner. Route execution to P07 from the manifest. If graph width is at least two, every dependency-ready lane must have an autonomous execution adapter or an explicit AUTONOMY_GAP with a machine-executable bootstrap/repair owner; do not make the operator launch chats."
p04["proofGate"] = "Dependencies, graph width, collision ownership, adapter choice, executable launch action, return contract, successor phases, convergence owner, and proof gates are explicit for every lane; the plan is durable; no dependency-ready parallel lane silently depends on human chat creation when an autonomous adapter exists; all-rungs failure is recorded as DEGRADED plus AUTONOMY_GAP rather than clean serial completion."
marker = "OUTPUT ORDER — LAUNCH ORDER FIRST"
if "PARALLEL CAPABILITY LADDER / AUTONOMY GATE" not in p04["copyContent"]:
    if marker not in p04["copyContent"]:
        raise SystemExit("P04 output marker missing")
    p04["copyContent"] = p04["copyContent"].replace(marker, LADDER + "\n\n" + MANIFEST + "\n\n" + marker, 1)
p04["copyContent"] = p04["copyContent"].replace(
    "State: one prompt panel goes into one new chat.",
    "Copy-panel portability fallback only: one panel maps to one lane when no autonomous adapter can carry that lane. This is not the primary dispatch path.",
)
p04["copyContent"] = p04["copyContent"].replace("3. NEXT-CHAT SPRINT PANELS", "3. PORTABILITY FALLBACK SPRINT PANELS")
p04["copyContent"] = p04["copyContent"].replace(
    "Emit each complete next-chat prompt in its own separate writing block or copyable panel.",
    "After the dispatch manifest, emit each complete lane prompt in its own separate writing block or copyable panel strictly as a portability/recovery fallback.",
)

p59["sprintRole"] = "Factor a large sprint into collision-safe parallel lanes and resolve each dependency-ready lane to an autonomous execution adapter and convergence contract"
p59["expectedOutput"] = "An automation-ready parallel sprint plan with dependency graph/width, lane ownership, isolated mutation surfaces, a PARALLEL DISPATCH MANIFEST, selected execution adapter and exact launch action per ready lane, return contracts, integration strategy, and validation. Copyable lane cards are fallback mirrors only."
p59["nextStep"] = "Hand the machine-executable PARALLEL DISPATCH MANIFEST to P07 for autonomous dispatch and convergence. Do not make the operator spawn chats or shuttle prompts. If graph width is at least two and no adapter rung is usable, preserve DEGRADED plus AUTONOMY_GAP evidence rather than treating serialization as success."
p59["proofGate"] = "Each lane has one mutation owner, explicit dependencies/collisions, branch/worktree or read-only posture, selected adapter/launch action or evidenced AUTONOMY_GAP, return artifact, validator, and convergence owner. A plan whose dependency-ready lanes require manual operator chat creation is incomplete."
p59_marker = "STEP 2: DEFINE PARALLEL LANES"
if "PARALLEL CAPABILITY LADDER / AUTONOMY GATE" not in p59["copyContent"]:
    if p59_marker not in p59["copyContent"]:
        raise SystemExit("P59 lane marker missing")
    p59["copyContent"] = p59["copyContent"].replace(p59_marker, LADDER + "\n\n" + MANIFEST + "\n\n" + p59_marker, 1)
p59["copyContent"] = p59["copyContent"].replace(
    "- Validation commands for this lane",
    "- Validation commands for this lane\n- Selected execution adapter / capability-ladder rung\n- Exact autonomous launch action and return contract\n- Convergence owner",
)
p59["copyContent"] = p59["copyContent"].replace(
    "Then output the integration sequence.",
    "Output the PARALLEL DISPATCH MANIFEST first, then the integration sequence. Lane cards are portability mirrors and must not make the operator the scheduler.",
)

p07["expectedOutput"] = "Repository progress executed from a refreshed/reconciled floor through bounded implementation, validation, evidence review, critique, improvement, and authorized mainline convergence. Parallel work is driven by dependency-graph width and a capability ladder, not by one preferred worker class: when graph width is at least two, P07 exhausts native subagents, repo/local runners, connected execution providers, CI/job fan-out, and genuine concurrent deterministic jobs until a safe adapter dispatches independent lanes. One missing adapter such as self-hosted workers is not global unavailability. If every safe rung is unavailable, serial progress is explicitly DEGRADED with an AUTONOMY_GAP and parallel proof UNPROVEN; width one is NOT_APPLICABLE. User scheduling is never the fallback. Generated-surface ownership, structural editability, strategic follow-on routing, explicit gaps/risks/blockers/proof ceiling, and first executable continuation remain required."
p07["nextStep"] = "Before broad serial execution, build or refresh the dependency graph and determine its width. For width >= 2, walk the parallel capability ladder and dispatch at the first safe rung with enough capacity; keep the coordinator on an independent lane, rejoin evidence, and run combined validation. Do not stop after finding one unavailable adapter. If all safe rungs are exhausted, report PARALLEL EXECUTION: DEGRADED plus AUTONOMY_GAP, continue safe serial progress without claiming parallel proof, and build/route the smallest adapter repair. For width 1 report NOT_APPLICABLE. Continue IMPLEMENT -> VALIDATE -> INSPECT EVIDENCE -> CRITIQUE -> IMPROVE and integrate coherent green slices until the bounded fixed point or exact external blocker."
p07["proofGate"] = "Remote/default-branch and evidence floors are fresh; deliberate second-pass review closes practical in-scope gaps; authorized integration reaches current default branch or an exact blocker is proven. Parallel proof is dependency-graph based: width >= 2 requires evidence that the capability ladder continued past unavailable rungs and dispatched at the first safe usable adapter, with lane identities, mutation ownership, returned artifacts/results, coordinator revalidation, and convergence evidence. `no connected self-hosted workers` alone never proves global unavailability. If all safe rungs are exhausted, only DEGRADED plus AUTONOMY_GAP is valid and parallel proof remains UNPROVEN even if serial work progresses; width 1 is NOT_APPLICABLE. No agent-capable scheduling is delegated to the user. Generated-surface, readability/P124, paradigm/P128, strategic-follow-on, phase-continuity, gap/risk/blocker, and default-branch containment gates remain mandatory."
start = "PARALLEL EXECUTION IS AN EXECUTION REQUIREMENT, NOT A PLANNING OR REPORTING TOPIC."
end = "REPOSITORY-GENERATED UPDATE COEXISTENCE CONTRACT"
if start not in p07["copyContent"] or end not in p07["copyContent"]:
    raise SystemExit("P07 parallel section boundaries missing")
before, rest = p07["copyContent"].split(start, 1)
_, after = rest.split(end, 1)
p07_parallel = """PARALLEL EXECUTION IS AN EXECUTION REQUIREMENT, NOT A PLANNING OR REPORTING TOPIC.
- Before substantial serial work, build or refresh the dependency graph for owned work. Identify dependency-ready, meaningful lanes and enforce one writer per mutation surface. `graph width >= 2` means at least two such lanes can safely proceed now.
""" + LADDER + """
- A fresh P04/P59 dispatch manifest is reusable after refreshing it against the current repository floor. Do not replan merely to satisfy the dispatch gate.
- Every dispatched lane receives the pinned base/evidence floor, owned scope, forbidden scope, mutation surfaces, dependencies, expected artifact/proof, validation responsibility, and exact return contract.
- The coordinator owns synthesis and integration. Workers/runners/jobs must not independently merge default, rewrite shared history, broaden scope, or declare the sprint complete. Treat returned completion claims as hypotheses until coordinator validation.
- Do not idle while autonomous lanes run when the coordinator has another safe action. If one lane blocks, continue other independent safe work and isolate the blocker.
- Final closeout reports graph width, capability rungs actually probed, lanes actually dispatched, mutation ownership, return evidence, rejoin validation, and convergence state. Never report hypothetical workers as executed.
- Do not make the user manually create chats, paste lane prompts, shuttle context, or act as the parallel-work scheduler."""
p07["copyContent"] = before + p07_parallel + "\n\n" + end + after
dump(PROMPTS, prompts)

overrides = load(OVERRIDES)
p13 = prompt_by_id(overrides["overrides"], "P13")
p13["expectedOutput"] = "A mandatory P114 execution-posture canary/access matrix; immediate critical-path advancement; P07-owned dependency-graph and capability-ladder dispatch when graph width is at least two; one missing adapter never authorizes clean serialization; all-rungs failure is DEGRADED plus AUTONOMY_GAP with parallel proof UNPROVEN while safe serial progress continues; the smallest durable prevention; specialist routing without duplication; and validated default-branch convergence or an exact external/user-only blocker."
p13["proofGate"] = "The recurrence is evidence-backed; the P114 canary resolves material execution posture; P07 proves dependency graph width and walks the capability ladder rather than treating one missing worker class as global unavailability; width >= 2 dispatches at the first safe usable rung, or all-rungs exhaustion is reported DEGRADED plus AUTONOMY_GAP with parallel proof UNPROVEN; width 1 is NOT_APPLICABLE. Durable prevention has one canonical owner, focused regression/build/parity checks pass, second-pass review reaches a bounded fixed point, and the validated owned head converges to current default branch when authorized."
p13_start = "5. PARALLEL EXECUTION — P07 OWNS ACTUAL DISPATCH"
p13_end = "6. INSTALL THE SMALLEST DURABLE PREVENTION"
if p13_start not in p13["copyContent"] or p13_end not in p13["copyContent"]:
    raise SystemExit("P13 parallel section boundaries missing")
b, r = p13["copyContent"].split(p13_start, 1)
_, a = r.split(p13_end, 1)
p13_parallel = """5. PARALLEL EXECUTION — P07 OWNS ACTUAL DISPATCH
P13 treats missing parallelism as recurring friction; P07 owns dispatch/coordinator semantics. Do not replace execution with a lane list.
- Require P07 to establish dependency-graph width, then walk its full capability ladder. Native subagents, repo/local agent runners, connected execution providers, CI/job fan-out, and genuinely concurrent deterministic jobs are separate adapter classes; absence of one does not settle the others.
- `no connected self-hosted workers` is evidence about one rung only. It is not sufficient evidence for `parallel unavailable` and must not cause immediate clean serialization.
- For width >= 2, P07 dispatches at the first safe usable rung and returns worker/job identities, mutation ownership, artifacts/diffs/findings, validation, and rejoin evidence.
- If every safe rung is evidenced unavailable/blocked, P07 may keep useful serial work moving but must report `PARALLEL EXECUTION: DEGRADED — <exhausted capability-ladder evidence>.` plus `AUTONOMY_GAP: <smallest executable adapter/bootstrap/repair route>.` Parallel proof remains UNPROVEN.
- Width 1 is `PARALLEL EXECUTION: NOT_APPLICABLE — dependency graph width is 1.`
- Do not emit a copy-paste worker packet as the primary path and do not make the operator create chats or shuttle context. Planning surfaces must provide an executable dispatch manifest; human panels are portability fallback only.
- If repeated missing parallelism is caused by a missing reusable adapter inside owned scope, repair that smallest durable seam now; otherwise route the machine-executable AUTONOMY_GAP to the canonical owner and continue independent safe work.
- P13 remains recurrence/prevention/convergence owner; P07 remains actual execution owner. Do not duplicate P07's full worker protocol here."""
p13["copyContent"] = b + p13_parallel + "\n\n" + p13_end + a
p13["copyContent"] = p13["copyContent"].replace(
    "- MISSING_PARALLELISM — an independent lane should have been dispatched through P07 when usable worker capacity and collision-safe independence were available.",
    "- MISSING_PARALLELISM — dependency graph width was at least two but P07 failed to continue through its capability ladder and dispatch at the first safe usable adapter, or mislabeled degraded serial work as a clean parallel pass.",
)
p13["copyContent"] = p13["copyContent"].replace(
    "- actual P07 dispatch evidence when worker capacity and collision-safe lanes exist, or the exact unavailable-capability limitation when they do not;",
    "- P07 dependency-graph width plus capability-ladder evidence: actual dispatch at the first safe usable rung, NOT_APPLICABLE only for width one, or DEGRADED + AUTONOMY_GAP after all safe rungs are exhausted;",
)
dump(OVERRIDES, overrides)

spec = SPEC.read_text(encoding="utf-8")
old = "Parallel execution does not weaken ownership or proof. Units that write the same file, schema, registry, generated artifact, branch, PR, deployment target, or mutable runtime must be serialized or assigned one writer. Every parallel group needs explicit dependencies/collision ownership and one convergence unit that validates the combined result."
new = old + """

### Parallel capability ladder and autonomy

Parallelism is derived from the work graph, not from the presence of one favorite worker product. First determine whether at least two meaningful dependency-ready lanes can proceed without conflicting writes. When graph width is at least two, probe available execution adapters in this order and dispatch at the first safe rung with sufficient capacity: native sub-agent/child-agent/delegated-agent APIs; repository/local agent runners; connected remote/provider/MCP execution surfaces; CI/job/matrix fan-out; then genuinely concurrent local processes or tool jobs for deterministic non-LLM lanes. A missing rung never proves later rungs absent. In particular, `no connected self-hosted workers` is one capability fact, not proof that parallel execution is globally unavailable.

Serial multi-tool use is not parallel execution. The local-process/tool rung counts only when independent jobs are actually launched concurrently and rejoined. Graph width one is `PARALLEL EXECUTION: NOT_APPLICABLE`. When graph width is at least two and every safe rung is evidenced unavailable or blocked, useful work may continue serially only as degraded execution: report `PARALLEL EXECUTION: DEGRADED` and an `AUTONOMY_GAP` naming the smallest executable adapter/bootstrap/repair route. Parallel proof remains UNPROVEN until a real dispatch occurs.

Planning surfaces must produce a machine-executable `PARALLEL DISPATCH MANIFEST` as the primary orchestration artifact. Each ready lane names its dependencies, mutation owner, forbidden surfaces, branch/worktree or read-only posture, chosen adapter/rung, exact launch action, return artifact/contract, validator, convergence owner, and status. Copyable chat panels are portability/recovery fallback only. Do not make the operator create chats, paste prompts, shuttle context, or act as the scheduler when any autonomous adapter can carry the lane."""
if old not in spec:
    raise SystemExit("shared parallel paragraph missing")
SPEC.write_text(spec.replace(old, new, 1), encoding="utf-8")

tests = TEST.read_text(encoding="utf-8")
tests = replace_method(tests, "test_p07_parallel_execution_is_binary_and_requires_actual_dispatch_proof", '''    def test_p07_parallel_execution_uses_capability_ladder_and_actual_dispatch_proof(self) -> None:
        prompt = self.effective["P07"]
        content = prompt["copyContent"]
        self.assertEqual("BUILD", prompt["type"])
        self.assertIn("dependency graph", prompt["expectedOutput"].lower())
        self.assertIn("capability ladder", prompt["expectedOutput"].lower())
        self.assertIn("graph width >= 2", content)
        for phrase in (
            "PARALLEL CAPABILITY LADDER / AUTONOMY GATE",
            "native sub-agent/child-agent/delegated-agent/task-worker APIs",
            "repository/local agent runners and orchestrators",
            "connected remote/provider/MCP execution surfaces",
            "CI/job/matrix fan-out",
            "genuinely concurrent local processes/tool jobs",
            "no connected self-hosted workers",
            "continue down the capability ladder",
            "dispatch immediately",
            "one writer per mutation surface",
            "The coordinator owns synthesis and integration",
            "Do not make the user manually create chats",
        ):
            self.assertIn(phrase, content)
        self.assertIn("returned artifacts/results", prompt["proofGate"])
        self.assertIn("parallel proof remains UNPROVEN", prompt["proofGate"])
        self.assertIn("readability/P124", prompt["proofGate"])
        self.assertIn("paradigm/P128", prompt["proofGate"])''')
tests = replace_method(tests, "test_p07_unavailable_parallelism_is_one_binary_capability_report", '''    def test_p07_missing_one_worker_class_cannot_authorize_clean_serial_fallback(self) -> None:
        prompt = self.effective["P07"]
        content = prompt["copyContent"]
        self.assertNotIn("proceed serially without enumerating hypothetical parallel lanes", content)
        self.assertNotIn("PARALLEL EXECUTION: unavailable — <exact capability limitation>.", content)
        self.assertIn("Absence of one adapter class is not global absence", content)
        self.assertIn("no connected self-hosted workers", content)
        self.assertIn("PARALLEL EXECUTION: DEGRADED", content)
        self.assertIn("AUTONOMY_GAP:", content)
        self.assertIn("parallel proof remains UNPROVEN", prompt["proofGate"])
        self.assertIn("PARALLEL EXECUTION: NOT_APPLICABLE", content)
        self.assertIn("dependency graph width is 1", content)
        self.assertIn("User scheduling is never the fallback", prompt["expectedOutput"])''')
TEST.write_text(tests, encoding="utf-8")

skill = SKILL_TEST.read_text(encoding="utf-8")
skill = skill.replace(
    '"PARALLEL EXECUTION: unavailable — <exact capability limitation>",',
    '"PARALLEL EXECUTION: DEGRADED — <exhausted capability-ladder evidence>",\n            "AUTONOMY_GAP: <smallest executable adapter/bootstrap/repair route>",\n            "no connected self-hosted workers",',
)
skill = skill.replace(
    '"Do not emit a hypothetical lane list or copy-paste worker packet merely because dispatch is unavailable",',
    '"Do not emit a copy-paste worker packet as the primary path",',
)
SKILL_TEST.write_text(skill, encoding="utf-8")

NEW_TEST.write_text('''from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PromptParallelExecutionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = {p["id"]: p for p in json.loads((ROOT / "docs/prompts.json").read_text(encoding="utf-8"))}
        overrides = json.loads((ROOT / "registry/prompts/prompt-overrides.v1.json").read_text(encoding="utf-8"))["overrides"]
        cls.overrides = {p["id"]: p for p in overrides}
        cls.spec = (ROOT / "harness/specs/prompt-operations.md").read_text(encoding="utf-8")

    def test_shared_contract_uses_graph_width_and_capability_ladder(self) -> None:
        for phrase in (
            "Parallel capability ladder and autonomy",
            "no connected self-hosted workers",
            "PARALLEL EXECUTION: NOT_APPLICABLE",
            "PARALLEL EXECUTION: DEGRADED",
            "AUTONOMY_GAP",
            "PARALLEL DISPATCH MANIFEST",
            "Copyable chat panels are portability/recovery fallback only",
        ):
            self.assertIn(phrase, self.spec)

    def test_planners_produce_machine_executable_dispatch_before_human_panels(self) -> None:
        for pid in ("P04", "P59"):
            prompt = self.raw[pid]
            text = prompt["copyContent"]
            self.assertIn("PARALLEL CAPABILITY LADDER / AUTONOMY GATE", text)
            self.assertIn("PARALLEL DISPATCH MANIFEST", text)
            self.assertIn("exact launch action", text.lower())
            self.assertIn("portability", text.lower())
            self.assertIn("operator", text.lower())
            self.assertIn("AUTONOMY_GAP", text)
        self.assertIn("machine-executable PARALLEL DISPATCH MANIFEST", self.raw["P59"]["nextStep"])
        self.assertIn("do not make the operator launch chats", self.raw["P04"]["nextStep"].lower())

    def test_cursor_regression_cannot_stop_at_missing_self_hosted_workers(self) -> None:
        p07 = self.raw["P07"]
        p13 = self.overrides["P13"]
        regression = "no connected self-hosted workers"
        for prompt in (p07, p13):
            text = " ".join(str(prompt.get(k, "")) for k in ("expectedOutput", "nextStep", "proofGate", "copyContent"))
            self.assertIn(regression, text)
            self.assertIn("capability ladder", text.lower())
            self.assertIn("DEGRADED", text)
            self.assertIn("AUTONOMY_GAP", text)
        self.assertNotIn("PARALLEL EXECUTION: unavailable — <exact capability limitation>", p07["copyContent"])
        self.assertNotIn("PARALLEL EXECUTION: unavailable — <exact capability limitation>", p13["copyContent"])

    def test_serial_execution_has_only_two_honest_dispositions(self) -> None:
        p07 = self.raw["P07"]["copyContent"]
        self.assertIn("dependency graph width is 1", p07)
        self.assertIn("parallel proof remains UNPROVEN", p07)
        self.assertIn("serial progress may continue only to avoid deadlock", p07)


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")
