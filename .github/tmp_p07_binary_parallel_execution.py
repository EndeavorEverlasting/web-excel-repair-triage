from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REGISTRY = Path("docs/prompts.json")
TEST = Path("tests/test_p02_p07_autonomous_iteration.py")

PARALLEL_BLOCK = """PARALLEL EXECUTION IS AN EXECUTION REQUIREMENT, NOT A PLANNING OR REPORTING TOPIC.
- Before substantial serial work, probe whether the environment exposes a usable sub-agent, child-agent, delegated-agent, or equivalent parallel-worker mechanism and whether at least two concurrent worker slots are available.
- If a usable mechanism exists, capacity is at least two, AND at least two meaningful lanes can proceed independently without a hard dependency or conflicting writes, dispatch them immediately. Do not merely describe, propose, consider, recommend, or defer parallelization. If these conditions are met and no workers are dispatched, the sprint is incomplete.
- Evidence of parallel execution must identify each dispatched worker/lane and include the returned artifact, diff/head, test result, finding, or other decision-relevant result from that worker. “Considered,” “could parallelize,” “lanes identified,” or equivalent planning language is not execution evidence.
- If no usable mechanism exists or fewer than two concurrent worker slots are available, proceed serially without enumerating hypothetical parallel lanes. Report only: `PARALLEL EXECUTION: unavailable — <exact capability limitation>.` Do not retry impossible fan-out or turn the user into a worker scheduler.
- Do not call serial use of multiple tools, connectors, commands, tabs, or repository reads "parallel execution."
- If a fresh P04/P05 factoring or launch map already exists, reuse its dependency/collision evidence after refreshing it against the current repository floor; do not create a second planning pass merely to satisfy this execution requirement.
- Use the smallest useful fan-out. Split only on real ownership/proof boundaries. Every dispatched worker must receive the pinned base/evidence floor, owned scope, forbidden scope, mutation surfaces, dependencies, expected artifact/proof, validation responsibility, and exact return contract.
- Enforce one writer per mutation surface. Parallel write lanes must own non-overlapping files/surfaces or use repository-approved isolated branches/worktrees. Shared registries, schemas, generators, manifests, workflows, lockfiles, and the default branch have one mutation owner at a time; other workers may inspect, test, or falsify those surfaces read-only.
- The coordinator owns synthesis and integration. Workers must not independently merge the default branch, rewrite shared history, silently broaden scope, or declare the sprint complete. Treat worker completion claims as hypotheses; collect their exact heads/diffs or changed files, artifacts, tests, assumptions, gaps, and blockers, reconcile them against the refreshed floor, then run combined validation after rejoin.
- Do not idle while dispatched workers run when the coordinator has an independent safe action. Continue agent-capable work and consume completed worker evidence as it arrives.
- A worker result does not bypass the iterative fixed-point contract. If one worker blocks, continue independent safe work and isolate the blocker rather than collapsing the sprint into a wait state.
- Final closeout must report only parallel lanes actually dispatched, their mutation ownership, and their rejoin evidence. If none were dispatched because the environment lacked the required mechanism or capacity, state that capability blocker once without describing hypothetical lanes.
- Do not make the user manually create chats, shuttle context, or act as the parallel-work scheduler.

"""

PARALLEL_TEST = '''    def test_p07_parallel_execution_is_binary_and_requires_actual_dispatch_proof(self) -> None:
        prompt = self.effective["P07"]
        content = prompt["copyContent"]
        self.assertEqual("BUILD", prompt["type"])
        self.assertEqual("PLAN", self.raw["P04"]["type"])
        self.assertIn("[PARALLEL]", self.raw["P04"]["name"])
        self.assertIn("parallel-safe sub-agent orchestration", prompt["sprintRole"])
        self.assertIn("parallel sub-agents", prompt["expectedOutput"])
        self.assertIn("dispatch safe parallel sub-agents", prompt["nextStep"])
        self.assertIn("Parallel-execution proof requires", prompt["proofGate"])
        for phrase in (
            "PARALLEL EXECUTION IS AN EXECUTION REQUIREMENT, NOT A PLANNING OR REPORTING TOPIC.",
            "Before substantial serial work, probe whether the environment exposes a usable sub-agent",
            "at least two concurrent worker slots are available",
            "dispatch them immediately",
            "Do not merely describe, propose, consider, recommend, or defer parallelization",
            "If these conditions are met and no workers are dispatched, the sprint is incomplete",
            "Evidence of parallel execution must identify each dispatched worker/lane",
            "returned artifact, diff/head, test result, finding",
            "one writer per mutation surface",
            "The coordinator owns synthesis and integration",
            "Treat worker completion claims as hypotheses",
            "combined validation after rejoin",
            "Do not idle while dispatched workers run",
            "Final closeout must report only parallel lanes actually dispatched",
        ):
            self.assertIn(phrase, content)
        self.assertNotIn("parallelization disposition", content)
        self.assertNotIn("lanes considered", content)

'''

SERIAL_TEST = '''    def test_p07_unavailable_parallelism_is_one_binary_capability_report(self) -> None:
        prompt = self.effective["P07"]
        content = prompt["copyContent"]
        for phrase in (
            "If no usable mechanism exists or fewer than two concurrent worker slots are available",
            "proceed serially without enumerating hypothetical parallel lanes",
            "`PARALLEL EXECUTION: unavailable — <exact capability limitation>.`",
            'Do not call serial use of multiple tools, connectors, commands, tabs, or repository reads "parallel execution."',
            "state that capability blocker once without describing hypothetical lanes",
            "Do not make the user manually create chats",
            "act as the parallel-work scheduler",
        ):
            self.assertIn(phrase, content)
        self.assertEqual(
            content.count("PARALLEL EXECUTION: unavailable — <exact capability limitation>."),
            1,
        )
        self.assertIn(
            "if those conditions held and no workers were dispatched, the sprint is incomplete",
            prompt["proofGate"].lower(),
        )
        self.assertIn(
            "serial use of multiple tools/connectors does not satisfy parallel proof",
            prompt["proofGate"].lower(),
        )

'''


def load_raw() -> tuple[list[dict], dict[str, dict]]:
    prompts = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return prompts, {prompt["id"]: prompt for prompt in prompts}


def mutate() -> None:
    prompts, by_id = load_raw()
    p07 = by_id["P07"]
    content = p07["copyContent"]
    start_marker = "PARALLEL SUB-AGENT EXECUTION CONTRACT"
    end_marker = "REPOSITORY-GENERATED UPDATE COEXISTENCE CONTRACT"
    if start_marker not in content or end_marker not in content:
        raise SystemExit("P07 parallel contract markers not found")
    start = content.index(start_marker)
    end = content.index(end_marker, start)
    p07["copyContent"] = content[:start] + PARALLEL_BLOCK + content[end:]

    proof = p07["proofGate"]
    marker = " Parallel-execution proof requires"
    if marker in proof:
        proof = proof.split(marker, 1)[0].rstrip()
    p07["proofGate"] = proof + (
        " Parallel-execution proof requires actual dispatched worker/lane identities and returned artifacts/results "
        "whenever a usable sub-agent mechanism, at least two concurrent worker slots, and at least two meaningful "
        "non-conflicting lanes exist; serial use of multiple tools/connectors does not satisfy parallel proof; if those "
        "conditions held and no workers were dispatched, the sprint is incomplete. One writer per mutation surface, "
        "coordinator revalidation after rejoin, and coordinator-owned integration remain mandatory."
    )
    REGISTRY.write_text(json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    text = TEST.read_text(encoding="utf-8")
    text, count = re.subn(
        r"    def test_p07_coerces_safe_parallel_subagents_and_rejoins\(self\) -> None:\n.*?(?=    def test_p07_coordinates_repository_generated_mutation_lanes)",
        PARALLEL_TEST,
        text,
        flags=re.S,
    )
    if count != 1:
        raise SystemExit(f"expected one P07 parallel test replacement, got {count}")
    text, count = re.subn(
        r"    def test_p07_serial_fallback_is_fail_closed_and_not_user_scheduled\(self\) -> None:\n.*?(?=    def test_effective_prompts_keep_shared_actionability_policy)",
        SERIAL_TEST,
        text,
        flags=re.S,
    )
    if count != 1:
        raise SystemExit(f"expected one P07 serial test replacement, got {count}")
    TEST.write_text(text, encoding="utf-8")


def review() -> None:
    from scripts import build_prompt_kit_registry

    _, raw = load_raw()
    effective = {p["id"]: p for p in build_prompt_kit_registry.load_prompt_registry()}
    p07 = effective["P07"]
    content = p07["copyContent"]
    assert p07["type"] == "BUILD"
    assert raw["P04"]["type"] == "PLAN"
    assert "PARALLEL EXECUTION IS AN EXECUTION REQUIREMENT, NOT A PLANNING OR REPORTING TOPIC." in content
    assert "parallelization disposition" not in content
    assert "lanes considered" not in content
    assert content.count("PARALLEL EXECUTION: unavailable — <exact capability limitation>.") == 1
    assert "dispatch them immediately" in content
    assert "no workers are dispatched, the sprint is incomplete" in content
    assert "Evidence of parallel execution must identify each dispatched worker/lane" in content
    assert "Do not call serial use of multiple tools, connectors" in content
    assert "one writer per mutation surface" in content
    assert "The coordinator owns synthesis and integration" in content
    assert "combined validation after rejoin" in content
    assert "REPOSITORY-GENERATED UPDATE COEXISTENCE CONTRACT" in content
    assert "AUTONOMOUS EXECUTION / USER-ONLY GATE" in content
    assert "MAINLINE CONVERGENCE" in content
    assert "serial use of multiple tools/connectors does not satisfy parallel proof" in p07["proofGate"]
    print("P07_BINARY_PARALLEL_REVIEW=PASS")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "mutate":
        mutate()
    elif mode == "review":
        review()
    else:
        raise SystemExit("usage: tmp_p07_binary_parallel_execution.py mutate|review")
