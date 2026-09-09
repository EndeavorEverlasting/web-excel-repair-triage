from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "docs" / "prompt-kit-feedback-prototype.js"
DESIGN = ROOT / "docs" / "PROMPT_KIT_FEEDBACK_POLLING_DESIGN.md"


class PromptKitFeedbackPrototypeTests(unittest.TestCase):
    def run_prototype(self) -> dict:
        result = subprocess.run(
            ["node", str(PROTOTYPE)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_prototype_is_executable_and_all_journeys_pass(self) -> None:
        syntax = subprocess.run(
            ["node", "--check", str(PROTOTYPE)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(syntax.returncode, 0, syntax.stderr or syntax.stdout)
        report = self.run_prototype()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["schema"], "prompt-feedback-event/v1")
        self.assertEqual(report["cursorSchema"], "prompt-feedback-cursor/v1")
        self.assertTrue(report["journeys"])
        self.assertTrue(all(value == "PASS" for value in report["journeys"].values()))

    def test_event_contract_is_versioned_stable_and_privacy_bounded(self) -> None:
        text = PROTOTYPE.read_text(encoding="utf-8")
        for marker in (
            "prompt-feedback-event/v1",
            "prompt-feedback-cursor/v1",
            "event_id",
            "prompt_id",
            "event_type",
            "timestamp",
            "schema_version",
            "source",
            "supersedes_event_id",
            "SENSITIVE_FEEDBACK_PAYLOAD",
            "UNKNOWN_PROMPT",
        ):
            self.assertIn(marker, text)
        self.assertRegex(text, r"prompt\[_-\]\?body")
        self.assertIn("clipboard", text)
        self.assertIn("credential", text)

    def test_append_only_history_and_latest_vote_replacement_are_distinct(self) -> None:
        report = self.run_prototype()
        self.assertEqual(report["journeys"]["appendOnlyVoteHistory"], "PASS")
        self.assertEqual(report["journeys"]["replacementVoteAggregation"], "PASS")
        self.assertEqual(report["p99Summary"]["likes"], 0)
        self.assertEqual(report["p99Summary"]["dislikes"], 2)
        self.assertEqual(report["p99Summary"]["feedback_count"], 1)
        self.assertEqual(report["eventCount"], 5)

        text = PROTOTYPE.read_text(encoding="utf-8")
        self.assertIn("this.events.push(stored)", text)
        self.assertIn("this.latestVoteByPromptSource.set", text)
        self.assertNotIn("this.events.splice", text)
        self.assertNotIn("this.events.pop", text)

    def test_polling_is_cursor_bounded_and_checkpointed_after_processing(self) -> None:
        report = self.run_prototype()
        for journey in (
            "cursorPagination",
            "hookCheckpointResume",
            "checkpointFailureAtomicity",
            "idempotentEventReplay",
            "eventIdConflictFailsClosed",
        ):
            self.assertEqual(report["journeys"][journey], "PASS")

        text = PROTOTYPE.read_text(encoding="utf-8")
        poll_start = text.index("pollOnce({limit = 100} = {})")
        poll_end = text.index("}\n}\n\nfunction assert", poll_start)
        poll_body = text[poll_start:poll_end]
        self.assertLess(poll_body.index("this.aggregator.apply(event)"), poll_body.index("this.checkpointStore.save(page.next_cursor)"))
        self.assertIn("FUTURE_CURSOR", text)
        self.assertIn("processedEventIds", text)

    def test_votes_feedback_usage_and_favorites_remain_distinct_evidence_classes(self) -> None:
        report = self.run_prototype()
        self.assertEqual(
            report["evidenceClasses"],
            ["favorite", "semantic_usage", "prompt_vote", "prompt_feedback"],
        )
        self.assertEqual(report["journeys"]["writtenFeedbackSeparateFromVotes"], "PASS")

        design = DESIGN.read_text(encoding="utf-8")
        for phrase in (
            "**Favorite:** keep this prompt readily accessible.",
            "**Semantic usage:** the prompt/workflow was actually used/completed.",
            "**Like/dislike:** explicit quality/usefulness judgment.",
            "**Written feedback:** qualitative explanation or suggestion.",
        ):
            self.assertIn(phrase, design)
        self.assertIn("must not collapse them into one counter", design)

    def test_feedback_can_surface_review_candidates_but_has_no_rewrite_authority(self) -> None:
        report = self.run_prototype()
        self.assertEqual(report["journeys"]["maintenanceEvidenceWithoutRewriteAuthority"], "PASS")
        self.assertEqual(len(report["maintenanceCandidates"]), 1)
        self.assertEqual(report["maintenanceCandidates"][0]["prompt_id"], "P99")
        self.assertEqual(report["maintenanceCandidates"][0]["disposition"], "REVIEW_CANDIDATE")

        source = PROTOTYPE.read_text(encoding="utf-8")
        self.assertIn("typeof aggregator.rewritePrompt === 'undefined'", source)
        self.assertNotIn("updatePrompt(", source)
        self.assertNotIn("writeRegistry(", source)

        design = DESIGN.read_text(encoding="utf-8")
        self.assertIn("Feedback is **evidence, not mutation authority**", design)
        self.assertIn("bypassing `prompt_registry_ops.py`", design)

    def test_design_records_ownership_collision_boundary_and_proof_ceiling(self) -> None:
        text = DESIGN.read_text(encoding="utf-8")
        for marker in (
            "## Observable done checklist",
            "## Event contract",
            "## Explicit feedback semantics",
            "## Polling and cursor contract",
            "## Hook checkpoint transaction",
            "## Maintenance evidence boundary",
            "## Relationship to current Prompt Kit owners",
            "## Second-pass critique targets",
            "## Proof ceiling",
        ):
            self.assertIn(marker, text)
        self.assertIn("P99", text)
        self.assertIn("avoids racing the currently open Prompt Kit profile/modality", text)
        self.assertIn("cannot prove user-visible like/dislike controls", text)


if __name__ == "__main__":
    unittest.main()
