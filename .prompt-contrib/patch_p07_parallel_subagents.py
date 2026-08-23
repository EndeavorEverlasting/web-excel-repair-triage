from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "docs" / "prompts.json"
TESTS = ROOT / "tests" / "test_p02_p07_autonomous_iteration.py"

payload = json.loads(PROMPTS.read_text(encoding="utf-8"))
matches = [item for item in payload if item.get("id") == "P07"]
if len(matches) != 1:
    raise SystemExit(f"expected exactly one P07, found {len(matches)}")
p07 = matches[0]

if "PARALLEL SUB-AGENT EXECUTION CONTRACT" in p07["copyContent"]:
    raise SystemExit("P07 already contains the parallel sub-agent contract")

p07["sprintRole"] = (
    "Execute any bounded repo change through parallel-safe sub-agent orchestration, "
    "repeated evidence passes, and validated mainline convergence"
)
p07["expectedOutput"] += (
    " When supported by the execution environment, safe independent agent-capable lanes "
    "are dispatched to parallel sub-agents under explicit dependency, collision, and "
    "single-writer boundaries, then rejoined and independently validated by the coordinator "
    "instead of being serialized by default."
)
p07["nextStep"] = (
    "Before broad serial execution, re-evaluate the owned scope for independent lanes and "
    "dispatch safe parallel sub-agents when the environment supports them; keep the coordinator "
    "on an independent lane while they run, then rejoin their evidence and combined validation. "
    + p07["nextStep"]
)
p07["proofGate"] += (
    " Parallel-execution proof requires an explicit lane/collision assessment; when a supported "
    "sub-agent mechanism and at least two meaningful independent lanes exist, those lanes are "
    "dispatched concurrently unless a named dependency, shared-write, proof-ordering, security/runtime, "
    "tool, or disproportionate-overhead constraint makes serialization safer. Every write lane has one "
    "mutation owner, sub-agent outputs are revalidated rather than trusted as completion claims, and the "
    "coordinator proves the combined result before integration."
)
for keyword in (
    "parallel sub-agents",
    "parallel subagents",
    "sub-agent orchestration",
    "parallel sprint execution",
    "concurrent agents",
):
    if keyword not in p07["keywords"]:
        p07["keywords"].append(keyword)

parallel_block = """PARALLEL SUB-AGENT EXECUTION CONTRACT
- After the fresh preflight and before broad serial implementation, factor the current owned scope into dependency and collision lanes. If a P04/P05 factoring or launch map exists in current context, reuse its lane/dependency/collision evidence after refreshing it against the current repository floor instead of rediscovering the decomposition from scratch.
- When the execution environment exposes a sub-agent, child-agent, delegated-agent, or equivalent parallel-worker mechanism AND at least two meaningful lanes can proceed independently without a hard dependency or conflicting writes, you MUST dispatch those lanes concurrently. Parallelism is mandatory in that condition, not an optional optimization.
- Do not serialize safe independent agent-capable work merely because the coordinator could perform every task alone. If sub-agent tooling is available but execution remains serial, record the exact reason: hard dependency, shared mutation surface, proof ordering, runtime/security boundary, tool limitation, or coordination overhead that is disproportionate to the bounded work.
- Use the smallest useful fan-out. Split by real ownership/proof boundaries, not artificial microtasks. Every dispatched sub-agent must receive: the pinned base/evidence floor, owned scope, forbidden scope, files or surfaces it may mutate, dependencies, expected artifact/proof, validation responsibility, and an exact return contract.
- Enforce one writer per mutation surface. Parallel write lanes must own non-overlapping files/surfaces or use repository-approved isolated branches/worktrees. Shared registries, schemas, generators, manifests, workflows, lockfiles, and the default branch get one mutation owner at a time; other sub-agents may inspect, review, test, or falsify those surfaces read-only.
- Even when there is only one safe writer, parallelize useful supporting work when it materially shortens the critical path: repository/code discovery, test-selection analysis, review/falsification, contract/docs analysis, or runtime-risk analysis may run beside the writer if those lanes do not create competing mutations.
- The coordinator owns synthesis and integration. Sub-agents must not independently merge the default branch, rewrite shared history, silently broaden scope, or declare the sprint complete. Collect each lane's exact head/diff or changed files, artifacts, tests, assumptions, gaps, and blockers; treat sub-agent completion claims as hypotheses; reconcile them against the refreshed floor; then run combined validation after rejoin.
- Do not idle while sub-agents are running when the coordinator has an independent safe lane. Continue agent-capable work, consume completed lane evidence as it arrives, and turn conflicts or new findings into the next bounded iteration.
- A sub-agent result does not bypass the iterative fixed-point contract. Evidence from any lane becomes input to IMPLEMENT -> VALIDATE -> INSPECT EVIDENCE -> CRITIQUE -> IMPROVE. If one lane blocks, continue independent safe lanes and isolate the blocker rather than collapsing the whole sprint into a wait state.
- If the current environment has no sub-agent mechanism, continue autonomously in the current agent and report that capability ceiling. Do not make the user manually create chats, shuttle context, or act as the parallel-work scheduler.
- Final closeout must report the parallelization disposition: lanes considered, lanes dispatched, mutation owners, any justified serial exceptions, rejoin/combined-validation evidence, and whether parallel execution changed or exposed any gap before integration.

"""
marker = "AUTONOMOUS EXECUTION / USER-ONLY GATE"
if p07["copyContent"].count(marker) != 1:
    raise SystemExit("P07 autonomous gate marker missing or duplicated")
p07["copyContent"] = p07["copyContent"].replace(marker, parallel_block + marker, 1)

PROMPTS.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

test_text = TESTS.read_text(encoding="utf-8")
if "test_p07_coerces_safe_parallel_subagents_and_rejoins" in test_text:
    raise SystemExit("parallel sub-agent regression already exists")
insert_before = "    def test_effective_prompts_keep_shared_actionability_policy(self) -> None:\n"
if test_text.count(insert_before) != 1:
    raise SystemExit("focused P07 insertion point missing or duplicated")
new_test = '''    def test_p07_coerces_safe_parallel_subagents_and_rejoins(self) -> None:\n        prompt = self.raw["P07"]\n        content = prompt["copyContent"]\n        self.assertEqual("BUILD", prompt["type"])\n        self.assertEqual("PLAN", self.raw["P04"]["type"])\n        self.assertIn("[PARALLEL]", self.raw["P04"]["name"])\n        self.assertIn("parallel-safe sub-agent orchestration", prompt["sprintRole"])\n        self.assertIn("parallel sub-agents", prompt["expectedOutput"])\n        self.assertIn("dispatch safe parallel sub-agents", prompt["nextStep"])\n        self.assertIn("Parallel-execution proof requires", prompt["proofGate"])\n        for phrase in (\n            "PARALLEL SUB-AGENT EXECUTION CONTRACT",\n            "If a P04/P05 factoring or launch map exists",\n            "you MUST dispatch those lanes concurrently",\n            "Parallelism is mandatory in that condition",\n            "one writer per mutation surface",\n            "The coordinator owns synthesis and integration",\n            "treat sub-agent completion claims as hypotheses",\n            "Do not idle while sub-agents are running",\n            "continue independent safe lanes",\n            "Do not make the user manually create chats",\n            "parallelization disposition",\n        ):\n            self.assertIn(phrase, content)\n\n'''
test_text = test_text.replace(insert_before, new_test + insert_before, 1)
TESTS.write_text(test_text, encoding="utf-8")
