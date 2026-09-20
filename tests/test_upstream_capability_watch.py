from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness/contracts/operant-external-resource-intake.v1.json"
EDGES = ROOT / "registry/resources/upstream-capability-impact-edges.v1.json"


def transition_id(resource_id: str, previous: str, observed: str) -> str:
    payload = "|".join((resource_id, previous, observed))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class UpstreamCapabilityWatchContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))["capability_watch"]
        self.edges = json.loads(EDGES.read_text(encoding="utf-8"))

    def test_identity_separates_repository_revision_from_capability_identity(self) -> None:
        identity = self.contract["identity"]
        self.assertEqual(identity["repository_revision_field"], "source_sha")
        self.assertEqual(identity["capability_identity_field"], "resource_identity")
        self.assertEqual(identity["capability_identity_algorithm"], "git_blob_sha")

    def test_observed_and_processed_identity_are_distinct_and_routing_failure_fails_closed(self) -> None:
        state = self.contract["state"]
        self.assertIn("last_observed_identity", state["required_fields"])
        self.assertIn("last_processed_identity", state["required_fields"])
        before = {"last_observed_identity": "A", "last_processed_identity": "A"}
        after_poll = {**before, "last_observed_identity": "B"}
        after_routing_failure = dict(after_poll)
        self.assertEqual(after_routing_failure["last_processed_identity"], "A")
        self.assertIn("leaves last_processed_identity unchanged", state["routing_failure_rule"])

    def test_transition_dedupe_a_b_replay_and_b_c(self) -> None:
        first = transition_id("source:capability", "A", "B")
        replay = transition_id("source:capability", "A", "B")
        second = transition_id("source:capability", "B", "C")
        self.assertEqual(first, replay)
        self.assertNotEqual(first, second)
        self.assertEqual(
            self.contract["events"]["transition_key_fields"],
            ["resource_id", "previous_processed_identity", "observed_identity"],
        )

    def test_missing_impact_edge_retains_event(self) -> None:
        self.assertEqual(self.edges["edges"], [])
        self.assertTrue(self.edges["policy"]["zero_edge_is_valid"])
        self.assertTrue(self.contract["events"]["zero_impact_event_retained"])
        self.assertEqual(self.contract["impact_edges"]["missing_edge_status"], "NO_IMPACT_EDGE")

    def test_promotion_cannot_jump_changed_to_integrated(self) -> None:
        promotion = self.contract["promotion"]
        self.assertIn(["UPSTREAM_CHANGED", "INTEGRATED"], promotion["forbidden_direct_transitions"])
        self.assertNotIn(["UPSTREAM_CHANGED", "INTEGRATED"], promotion["allowed_transitions"])
        self.assertFalse(promotion["automatic_prompt_authoring"])


if __name__ == "__main__":
    unittest.main()
