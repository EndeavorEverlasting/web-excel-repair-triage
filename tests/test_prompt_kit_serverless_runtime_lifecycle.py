from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_prompt_kit_serverless_runtime_lifecycle as lifecycle


class PromptKitServerlessRuntimeLifecycleTests(unittest.TestCase):
    def load_contract(self) -> dict:
        return json.loads(lifecycle.CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_focused_validator_passes(self) -> None:
        self.assertEqual(lifecycle.main(["--summary"]), 0)

    def test_runtime_horizon_is_complete(self) -> None:
        payload = self.load_contract()
        report = lifecycle.validate_contract(payload)
        self.assertEqual(report["capabilities"], 7)
        self.assertEqual(
            {item["id"] for item in payload["runtime_capability_horizon"]},
            lifecycle.REQUIRED_CAPABILITIES,
        )

    def test_runtime_horizon_cannot_drop_pairing(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["runtime_capability_horizon"] = [
            item for item in payload["runtime_capability_horizon"] if item["id"] != "cross-device-pairing"
        ]
        with self.assertRaisesRegex(lifecycle.LifecycleError, "horizon count drifted"):
            lifecycle.validate_contract(payload)

    def test_network_anonymity_cannot_be_promoted_without_new_proof(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        for item in payload["runtime_capability_horizon"]:
            if item["id"] == "network-anonymity":
                item["status"] = "implemented"
        with self.assertRaisesRegex(lifecycle.LifecycleError, "investigate-first"):
            lifecycle.validate_contract(payload)

    def test_personal_state_cannot_become_auto_purgeable(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["local_storage_lifecycle"]["stores"]["personal_state"]["automatic_purge"] = True
        with self.assertRaisesRegex(lifecycle.LifecycleError, "must never be automatically purged"):
            lifecycle.validate_contract(payload)

    def test_local_journal_age_and_size_limits_are_enforced(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["local_storage_lifecycle"]["stores"]["local_journal"]["max_age_days"] = 3650
        with self.assertRaisesRegex(lifecycle.LifecycleError, "local_journal.max_age_days drifted"):
            lifecycle.validate_contract(payload)

        payload = copy.deepcopy(self.load_contract())
        payload["local_storage_lifecycle"]["stores"]["local_journal"]["max_bytes"] = 2**31
        with self.assertRaisesRegex(lifecycle.LifecycleError, "local_journal.max_bytes drifted"):
            lifecycle.validate_contract(payload)

    def test_reducer_and_retry_queues_are_bounded(self) -> None:
        payload = self.load_contract()
        stores = payload["local_storage_lifecycle"]["stores"]
        self.assertEqual(stores["privacy_reducer_buffer"]["max_bytes"], 524288)
        self.assertEqual(stores["privacy_reducer_buffer"]["max_aggregate_keys"], 2048)
        self.assertEqual(stores["sync_retry_queue"]["max_items"], 64)
        self.assertEqual(stores["sync_retry_queue"]["max_age_days"], 7)

    def test_polling_history_cannot_become_a_persistent_log(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        polling = payload["local_storage_lifecycle"]["stores"]["polling_state"]
        polling["persistent_cycle_log_allowed"] = True
        with self.assertRaisesRegex(lifecycle.LifecycleError, "persistent_cycle_log_allowed must remain false"):
            lifecycle.validate_contract(payload)

    def test_polling_cursor_state_is_tightly_bounded(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["local_storage_lifecycle"]["stores"]["polling_state"]["max_persistent_cursor_records"] = 20
        with self.assertRaisesRegex(lifecycle.LifecycleError, "at most one cursor"):
            lifecycle.validate_contract(payload)

    def test_acknowledged_collective_batches_must_be_deleted(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["polling_and_telemetry_policy"]["delete_local_batch_after_positive_acknowledgement"] = False
        with self.assertRaisesRegex(lifecycle.LifecycleError, "acknowledged local batches must be deleted"):
            lifecycle.validate_contract(payload)

    def test_telemetry_write_requires_cleanup(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["polling_and_telemetry_policy"]["telemetry_write_requires_cleanup_pass"] = False
        with self.assertRaisesRegex(lifecycle.LifecycleError, "telemetry writes must require a cleanup pass"):
            lifecycle.validate_contract(payload)

    def test_collective_learning_cannot_skip_evidence_spine_gate(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["phase_map"]["phase-4-local-collective-learning"]["dependency"] = "phase-1-local-lifecycle"
        with self.assertRaisesRegex(lifecycle.LifecycleError, "Phase 4 dependency drifted"):
            lifecycle.validate_contract(payload)

    def test_collective_learning_cannot_introduce_duplicate_event_model(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["phase_map"]["phase-4-local-collective-learning"]["forbidden_scope"].remove(
            "new route/usage/outcome event model before evidence-spine ownership is resolved"
        )
        with self.assertRaisesRegex(lifecycle.LifecycleError, "duplicate evidence event model"):
            lifecycle.validate_contract(payload)

    def test_strategy_dependency_is_present_on_current_floor(self) -> None:
        lifecycle.validate_strategy_dependency()

    def test_plan_has_required_headings_and_runtime_capabilities(self) -> None:
        lifecycle.validate_plan()

    def test_known_gameplay_usage_store_must_have_clear_delete_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prompt-kit-preference-gameplay.js"
            path.write_text(
                "var STORAGE_KEY='promptKit.usage.v1'; var recent=[]; recent.slice(0,12); localStorage.setItem(STORAGE_KEY,'{}');",
                encoding="utf-8",
            )
            with mock.patch.object(lifecycle, "GAMEPLAY_PATH", path):
                with self.assertRaisesRegex(lifecycle.LifecycleError, "lacks a reachable lifecycle clear/delete path"):
                    lifecycle.validate_gameplay_if_present()

    def test_known_gameplay_usage_store_accepts_reachable_clear_delete_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prompt-kit-preference-gameplay.js"
            path.write_text(
                "var STORAGE_KEY='promptKit.usage.v1'; var recent=[]; recent.slice(0,12); "
                "function clearUsageData(){localStorage.removeItem(STORAGE_KEY)}",
                encoding="utf-8",
            )
            with mock.patch.object(lifecycle, "GAMEPLAY_PATH", path):
                lifecycle.validate_gameplay_if_present()


if __name__ == "__main__":
    unittest.main()
