from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts import upstream_capability_watch as watch
from scripts import validate_operant_external_resources as validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness/contracts/operant-external-resource-intake.v1.json"
EDGES = ROOT / "registry/resources/upstream-capability-impact-edges.v1.json"
WORKFLOW = ROOT / ".github/workflows/operant-external-resource-refresh.yml"


class UpstreamCapabilityWatchContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root_contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.contract = self.root_contract["capability_watch"]
        self.edges = json.loads(EDGES.read_text(encoding="utf-8"))
        self.workflow = validator.active_workflow_text(WORKFLOW.read_text(encoding="utf-8"))

    def baseline(self, identity: str = "A") -> dict[str, object]:
        state, event = watch.observe_capability(
            watch.new_watch_state(
                source_id="mattpocock-skills",
                resource_id="mattpocock-skills:productivity/teach",
            ),
            source_id="mattpocock-skills",
            resource_id="mattpocock-skills:productivity/teach",
            observed_identity=identity,
            repository_revision="repo-a",
        )
        self.assertIsNone(event)
        return state

    def test_contract_validator_accepts_current_watch_floor(self) -> None:
        validator.validate_capability_watch_contract(self.root_contract, self.edges, self.workflow)

    def test_validator_rejects_missing_initial_transition(self) -> None:
        broken = copy.deepcopy(self.root_contract)
        broken["capability_watch"]["promotion"]["allowed_transitions"] = [
            item
            for item in broken["capability_watch"]["promotion"]["allowed_transitions"]
            if item != ["UNSEEN", "CURRENT"]
        ]
        with self.assertRaisesRegex(validator.ValidationError, "UNSEEN -> CURRENT"):
            validator.validate_capability_watch_contract(broken, self.edges, self.workflow)

    def test_identity_separates_repository_revision_from_capability_identity(self) -> None:
        identity = self.contract["identity"]
        self.assertEqual(identity["repository_revision_field"], "source_sha")
        self.assertEqual(identity["capability_identity_field"], "resource_identity")
        self.assertEqual(identity["capability_identity_algorithm"], "git_blob_sha")
        self.assertEqual(
            self.contract["events"]["transition_key_fields"],
            ["source_id", "resource_id", "previous_processed_identity", "observed_identity"],
        )

    def test_first_observation_establishes_current_baseline(self) -> None:
        state = self.baseline()
        self.assertEqual(state["status"], "CURRENT")
        self.assertEqual(state["source_id"], "mattpocock-skills")
        self.assertEqual(state["resource_id"], "mattpocock-skills:productivity/teach")
        self.assertEqual(state["last_observed_identity"], "A")
        self.assertEqual(state["last_processed_identity"], "A")
        self.assertEqual(state["last_observed_repository_revision"], "repo-a")

    def test_unchanged_identity_emits_no_event_and_refreshes_repository_provenance(self) -> None:
        state = self.baseline()
        unchanged, event = watch.observe_capability(
            state,
            source_id="mattpocock-skills",
            resource_id="mattpocock-skills:productivity/teach",
            observed_identity="A",
            repository_revision="repo-a2",
        )
        self.assertIsNone(event)
        self.assertEqual(unchanged["status"], "CURRENT")
        self.assertEqual(unchanged["last_observed_identity"], "A")
        self.assertEqual(unchanged["last_processed_identity"], "A")
        self.assertEqual(unchanged["last_observed_repository_revision"], "repo-a2")

    def test_receipt_contract_is_append_only_and_metadata_only(self) -> None:
        receipts = self.contract["receipts"]
        self.assertTrue(receipts["append_only"])
        self.assertFalse(receipts["raw_donor_body_allowed"])
        self.assertEqual(receipts["schema_version"], "upstream-capability-watch-receipt/v1")
        self.assertIn("event_id", receipts["required_fields"])
        self.assertIn("ROUTING_DEFERRED", receipts["outcomes"])
        self.assertIn("ROUTED", receipts["outcomes"])

    def test_watch_state_rejects_cross_capability_reuse(self) -> None:
        state = self.baseline()
        with self.assertRaisesRegex(watch.CapabilityWatchError, "locator"):
            watch.observe_capability(
                state,
                source_id="mattpocock-skills",
                resource_id="mattpocock-skills:other",
                observed_identity="B",
                repository_revision="repo-b",
            )

    def test_routing_failure_preserves_processed_identity_and_replay_event_id(self) -> None:
        state = self.baseline()
        changed, event = watch.observe_capability(
            state,
            source_id="mattpocock-skills",
            resource_id="mattpocock-skills:productivity/teach",
            observed_identity="B",
            repository_revision="repo-b",
        )
        self.assertIsNotNone(event)
        self.assertEqual(changed["last_observed_identity"], "B")
        self.assertEqual(changed["last_processed_identity"], "A")
        failed = watch.record_routing_result(
            changed,
            event,
            event_persisted=True,
            impact_resolution_persisted=False,
            routing_checkpoint_persisted=False,
        )
        self.assertEqual(failed["last_processed_identity"], "A")
        self.assertEqual(failed["status"], "UPSTREAM_CHANGED")

        replay, replay_event = watch.observe_capability(
            failed,
            source_id="mattpocock-skills",
            resource_id="mattpocock-skills:productivity/teach",
            observed_identity="B",
            repository_revision="repo-b2",
        )
        self.assertEqual(replay["last_processed_identity"], "A")
        self.assertEqual(replay_event["event_id"], event["event_id"])

    def test_non_boolean_checkpoint_value_does_not_advance_processed_identity(self) -> None:
        state = self.baseline()
        changed, event = watch.observe_capability(
            state,
            source_id="mattpocock-skills",
            resource_id="mattpocock-skills:productivity/teach",
            observed_identity="B",
            repository_revision="repo-b",
        )
        deferred = watch.record_routing_result(
            changed,
            event,
            event_persisted="truthy-but-not-boolean",  # type: ignore[arg-type]
            impact_resolution_persisted=True,
            routing_checkpoint_persisted=True,
        )
        self.assertEqual(deferred["last_processed_identity"], "A")
        self.assertEqual(deferred["status"], "UPSTREAM_CHANGED")

    def test_successful_route_advances_processed_identity_and_b_to_c_is_new_event(self) -> None:
        state = self.baseline()
        changed, event_b = watch.observe_capability(
            state,
            source_id="mattpocock-skills",
            resource_id="mattpocock-skills:productivity/teach",
            observed_identity="B",
            repository_revision="repo-b",
            impact_edge_ids=["teach-p96", "teach-p96", "teach-p98"],
        )
        routed = watch.record_routing_result(
            changed,
            event_b,
            event_persisted=True,
            impact_resolution_persisted=True,
            routing_checkpoint_persisted=True,
        )
        self.assertEqual(routed["status"], "EVALUATING")
        self.assertEqual(routed["last_processed_identity"], "B")

        changed_c, event_c = watch.observe_capability(
            routed,
            source_id="mattpocock-skills",
            resource_id="mattpocock-skills:productivity/teach",
            observed_identity="C",
            repository_revision="repo-c",
        )
        self.assertEqual(changed_c["status"], "UPSTREAM_CHANGED")
        self.assertEqual(event_c["previous_processed_identity"], "B")
        self.assertNotEqual(event_c["event_id"], event_b["event_id"])
        self.assertEqual(event_b["impact_edge_ids"], ["teach-p96", "teach-p98"])

    def test_missing_impact_edge_retains_diagnosable_event(self) -> None:
        state = self.baseline()
        changed, event = watch.observe_capability(
            state,
            source_id="mattpocock-skills",
            resource_id="mattpocock-skills:productivity/teach",
            observed_identity="B",
            repository_revision="repo-b",
        )
        self.assertEqual(changed["status"], "UPSTREAM_CHANGED")
        self.assertEqual(event["impact_edge_ids"], [])
        self.assertEqual(event["status"], "NO_IMPACT_EDGE")
        self.assertTrue(self.contract["events"]["zero_impact_event_retained"])
        self.assertEqual(self.contract["impact_edges"]["missing_edge_status"], "NO_IMPACT_EDGE")

    def test_promotion_cannot_jump_changed_to_integrated(self) -> None:
        promotion = self.contract["promotion"]
        self.assertIn(["UPSTREAM_CHANGED", "INTEGRATED"], promotion["forbidden_direct_transitions"])
        self.assertNotIn(["UPSTREAM_CHANGED", "INTEGRATED"], promotion["allowed_transitions"])
        self.assertFalse(promotion["automatic_prompt_authoring"])


if __name__ == "__main__":
    unittest.main()
