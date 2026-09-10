from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_REGISTRY = REPO_ROOT / "docs" / "prompts.json"


class P02P07AutonomousIterationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        raw = json.loads(BASE_REGISTRY.read_text(encoding="utf-8"))
        cls.raw = {prompt["id"]: prompt for prompt in raw}
        cls.effective = {
            prompt["id"]: prompt
            for prompt in build_prompt_kit_registry.load_prompt_registry()
        }

    def test_p02_recovers_context_and_prototypes_before_presenting(self) -> None:
        prompt = self.raw["P02"]
        content = prompt["copyContent"]
        self.assertIn("CONTEXT RECOVERY + ITERATIVE PROTOTYPE CONTRACT", content)
        self.assertIn(
            "PROTOTYPE -> CHECK AGAINST RECOVERED REQUIREMENTS -> INSPECT REPO EVIDENCE -> CRITIQUE -> REVISE",
            content,
        )
        self.assertIn("Build a PRIVATE candidate launch pack first", content)
        self.assertIn("Present only the refined launch order", content)
        self.assertIn("Continue until a bounded fixed point", content)
        self.assertIn("Do not manufacture endless revisions", content)
        self.assertIn("another chat, named conversation, pasted context, handoff, plan", content)
        self.assertIn("Do not ask the user to repeat information", content)
        self.assertIn("prototype -> critique -> revise", prompt["proofGate"])

    def test_p02_keeps_agent_capable_work_off_the_user(self) -> None:
        content = self.raw["P02"]["copyContent"]
        self.assertIn("AUTONOMOUS EXECUTION / USER-ONLY GATE", content)
        self.assertIn("Keep agent-capable work with the agent", content)
        self.assertIn("perform tests the agent can run", content)
        self.assertIn("choose the smallest reversible option", content)
        self.assertIn("Involve the user only when progress requires something genuinely user-only", content)
        self.assertIn("ask one minimal concrete question", content)
        self.assertIn("do not expose the user to avoidable intermediate drafts", content)

    def test_effective_p02_requires_concise_inflight_progress_without_status_stops(self) -> None:
        prompt = self.effective["P02"]
        content = prompt["copyContent"]
        self.assertIn("0. CONCISE PROGRESS LOOP", content)
        self.assertIn("Do not work through multiple meaningful passes silently", content)
        self.assertIn("CHANGED: ... | PROVED: ... | NEXT: ...", content)
        self.assertIn("Prefer fragments over filler", content)
        self.assertIn("Maximum two short sentences", content)
        self.assertIn("Do not repeat the plan, narrate polling, or use an update as a stopping point", content)
        self.assertIn("pass count and fixed-point reason", content)
        self.assertIn("Multi-pass silent execution fails this prompt", content)
        self.assertIn("compact in-flight evidence updates", prompt["expectedOutput"])

    def test_p07_preserves_fixed_point_and_adds_user_only_gate(self) -> None:
        prompt = self.raw["P07"]
        content = prompt["copyContent"]
        self.assertIn("ITERATIVE SPRINT FIXED-POINT", content)
        self.assertIn(
            "IMPLEMENT -> VALIDATE -> INSPECT EVIDENCE -> CRITIQUE -> IMPROVE",
            content,
        )
        self.assertIn("AUTONOMOUS EXECUTION / USER-ONLY GATE", content)
        self.assertIn("Keep agent-capable work with the agent", content)
        self.assertIn("Do not turn the user into the test runner", content)
        self.assertIn("exhaust current conversation/context", content)
        self.assertIn("advance every other safe owned action first", content)
        self.assertIn("choose the smallest reversible option", content)
        self.assertIn("genuinely user-only", prompt["expectedOutput"])
        self.assertIn("genuinely user-only dependency", prompt["proofGate"])
        self.assertIn("branch or PR alone is insufficient", prompt["proofGate"])

    def test_p07_parallel_execution_is_binary_and_requires_actual_dispatch_proof(self) -> None:
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

    def test_p07_coordinates_repository_generated_mutation_lanes(self) -> None:
        prompt = self.effective["P07"]
        content = prompt["copyContent"]
        for phrase in (
            "REPOSITORY-GENERATED UPDATE COEXISTENCE CONTRACT",
            "first-class mutation lanes",
            "repair the canonical source input/template/generator and regenerate it",
            "one writer per generated mutation surface",
            "A generated diff is proposed repository work, not automatic completion",
            "canonical source boundary",
        ):
            self.assertIn(phrase, content)

    def test_p07_unavailable_parallelism_is_one_binary_capability_report(self) -> None:
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

    def test_effective_prompts_keep_shared_actionability_policy(self) -> None:
        policy = build_prompt_kit_registry.load_actionability_policy()
        for prompt_id in ("P02", "P07"):
            prompt = self.effective[prompt_id]
            self.assertEqual(prompt["actionabilityPolicy"], policy["policy_id"])
            self.assertIn(policy["marker"], prompt["copyContent"])


if __name__ == "__main__":
    unittest.main()
