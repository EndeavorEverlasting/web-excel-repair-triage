from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry


POLICY = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
SPEC = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
MARKER = "CONVERSATION-TO-ARTIFACT CONTINUITY CONTRACT"


class ConversationArtifactContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))
        cls.spec = json.loads(SPEC.read_text(encoding="utf-8"))
        cls.effective = {
            prompt["id"]: prompt for prompt in build_prompt_kit_registry.load_prompt_registry()
        }

    def test_shared_policy_materializes_reusable_chat_truth_without_artifact_theater(self) -> None:
        appendix = self.policy["copy_content_appendix"]
        for phrase in (
            MARKER,
            "Materialize throughout the work at evidence-changing checkpoints",
            "Reuse the smallest existing canonical owner",
            "another competent agent continue without reconstructing the originating chat",
            "Persist distilled repository-relevant truth, not a raw transcript",
            "artifactization must reduce drift, not fossilize stale truth",
            "For prototypes, prefer executable seams plus focused tests, fixtures, traces, or receipts",
            "classify durability as BLOCKED",
            "Avoid artifact theater",
            "A durable artifact must govern behavior, prove it, route continuation, or preserve a material decision",
        ):
            self.assertIn(phrase, appendix)

        self.assertIn(
            "materialize the distilled safe truth into the smallest existing canonical artifact",
            self.policy["next_step_suffix"],
        )

        forbidden = "\n".join(self.policy["forbidden_solo_actions"])
        for phrase in (
            "leave accepted execution-relevant or reusable conversation state only in chat",
            "copy raw chat transcripts, secrets, private content, hidden reasoning",
            "create duplicate summaries, second sources of truth, or consumerless artifacts",
        ):
            self.assertIn(phrase, forbidden)

    def test_artifact_continuity_reaches_every_effective_prompt(self) -> None:
        self.assertGreater(len(self.effective), 1)
        for prompt_id, prompt in self.effective.items():
            with self.subTest(prompt=prompt_id):
                self.assertIn(MARKER, prompt["copyContent"])

    def test_p95_specializes_continuous_prototype_materialization_without_growing_copy_body(self) -> None:
        p95 = next(prompt for prompt in self.spec["prompts"] if prompt["id"] == "P95")
        self.assertIn(
            "Prototype-derived design decisions that later work depends on are materialized",
            p95["expectedOutput"],
        )
        self.assertIn(
            "At each evidence-changing prototype checkpoint",
            p95["nextStep"],
        )
        self.assertIn(
            "Prototype-derived continuation truth is not accepted as durable proof when it exists only in chat",
            p95["proofGate"],
        )
        for keyword in (
            "artifact continuity",
            "chat to artifact",
            "prototype evidence durability",
        ):
            self.assertIn(keyword, p95["keywords"])
        self.assertLessEqual(len(p95["copyContent"]), 10000)


if __name__ == "__main__":
    unittest.main()
