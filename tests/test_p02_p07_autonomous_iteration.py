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

    def test_p07_parallel_execution_uses_capability_ladder_and_actual_dispatch_proof(self) -> None:
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
        self.assertIn("paradigm/P128", prompt["proofGate"])

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

    def test_p07_missing_one_worker_class_cannot_authorize_clean_serial_fallback(self) -> None:
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
        self.assertIn("User scheduling is never the fallback", prompt["expectedOutput"])

    def test_p07_strategic_follow_on_captures_leverage_without_expanding_scope(self) -> None:
        prompt = self.effective["P07"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["type"], "BUILD")
        for phrase in (
            "STRATEGIC FOLLOW-ON — CAPTURE LEVERAGE WITHOUT EXPANDING THE SPRINT",
            "does not authorize widening owned scope",
            "RECURRING CONTRACT GAP",
            "CROSS-CUTTING LEVERAGE",
            "ARCHITECTURAL PRESSURE",
            "LATENT COMBINATION",
            "NEWLY FEASIBLE CAPABILITY",
            "SYSTEMATIC EVIDENCE GAP",
            "STRATEGIC SIMPLIFICATION",
            "observation | supporting evidence | broader opportunity | why current scope must not absorb it",
            "DO NOT IMPLEMENT THE FOLLOW-ON HERE",
            "routing artifact, not additional owned work",
            "EXISTING OWNER; OWNER STRENGTHENING; NEW CONTRACT CANDIDATE; INVESTIGATE FIRST; REJECT / DEFER",
            "unresolved internal program/system design -> P95",
            "external systems, reusable prior art, or analogues -> P97",
            "cheap measured prototype/experiment -> P82",
            "Prompt Kit owner strengthening/new behavior -> P79",
            "clear bounded implementation after uncertainty is resolved -> P07",
            "repository-wide comparison of multiple long-term opportunities -> P141 Repository Strategic Opportunity Scout",
            "If no qualifying opportunity was exposed, omit the section entirely",
            "must not replace or weaken the normal NEXT ACTION / NEXT STEPS",
            "The sprint remains incomplete whenever safe owned execution or integration work remains",
        ):
            self.assertIn(phrase, content)
        self.assertNotIn("Always emit a STRATEGIC FOLLOW-ON", content)
        self.assertNotIn("Implement the strategic follow-on", content)
        self.assertIn("evidence-triggered", prompt["expectedOutput"])
        self.assertIn("does not replace", prompt["nextStep"])
        self.assertIn("never authorizes unfinished owned work", prompt["proofGate"])

    def test_effective_prompts_keep_shared_actionability_policy(self) -> None:
        policy = build_prompt_kit_registry.load_actionability_policy()
        for prompt_id in ("P02", "P07"):
            prompt = self.effective[prompt_id]
            self.assertEqual(prompt["actionabilityPolicy"], policy["policy_id"])
            self.assertIn(policy["marker"], prompt["copyContent"])


if __name__ == "__main__":
    unittest.main()
