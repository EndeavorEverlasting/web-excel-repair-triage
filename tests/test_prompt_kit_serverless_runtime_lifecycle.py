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

    def test_secrets_are_a_distinct_protected_store(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        del payload["local_storage_lifecycle"]["stores"]["secrets"]
        with self.assertRaisesRegex(lifecycle.LifecycleError, "stores.*keys drifted"):
            lifecycle.validate_contract(payload)

        payload = copy.deepcopy(self.load_contract())
        payload["local_storage_lifecycle"]["stores"]["secrets"]["telemetry_cleanup_may_delete"] = True
        with self.assertRaisesRegex(lifecycle.LifecycleError, "outside telemetry auto-cleanup"):
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

    def test_polling_cursor_state_has_time_and_count_bounds(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["local_storage_lifecycle"]["stores"]["polling_state"]["max_persistent_cursor_records"] = 20
        with self.assertRaisesRegex(lifecycle.LifecycleError, "at most one cursor"):
            lifecycle.validate_contract(payload)

        payload = copy.deepcopy(self.load_contract())
        payload["local_storage_lifecycle"]["stores"]["polling_state"]["max_age_hours"] = 720
        with self.assertRaisesRegex(lifecycle.LifecycleError, "max age must remain 24 hours"):
            lifecycle.validate_contract(payload)

        payload = copy.deepcopy(self.load_contract())
        payload["local_storage_lifecycle"]["stores"]["polling_state"]["delete_on"].remove("age-expiry")
        with self.assertRaisesRegex(lifecycle.LifecycleError, "must delete on age expiry"):
            lifecycle.validate_contract(payload)

    def test_user_controls_cannot_disappear_via_empty_all(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["local_storage_lifecycle"]["user_controls"] = {}
        with self.assertRaisesRegex(lifecycle.LifecycleError, "user_controls.*keys drifted"):
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

    def test_phase5_cannot_skip_anonymity_investigation(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["phase_map"]["phase-5-serverless-collective-ingestion"]["dependency"] = "phase-4-local-collective-learning"
        with self.assertRaisesRegex(lifecycle.LifecycleError, "Phase 5 dependency drifted"):
            lifecycle.validate_contract(payload)

    def test_strategy_dependency_is_present_on_current_floor(self) -> None:
        lifecycle.validate_strategy_dependency()

    def test_strategy_dependency_requires_integrated_closeout_and_surviving_p95_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scout = root / "scout.md"
            closeout = root / "closeout.md"
            scout.write_text(
                "Recommended next owner:** P95\n"
                "Prompt execution evidence-spine/state-ownership architecture before Phase D Passive Learning\n",
                encoding="utf-8",
            )
            closeout.write_text(
                "**Status:** COMPLETE / INTEGRATED / POST-MERGE VALIDATED\n"
                "The next **approved** owner is **P95 — Program Design & Call-Stack Prototype Architect**.\n"
                "EVIDENCE_SPINE_ARCHITECTURE.md\n"
                "Phase D is deferred until evidence-lifecycle ownership is resolved.\n",
                encoding="utf-8",
            )
            with mock.patch.object(lifecycle, "SCOUT_PATH", scout), mock.patch.object(
                lifecycle, "PHASE_C_CLOSEOUT_PATH", closeout
            ):
                lifecycle.validate_strategy_dependency()
                closeout.write_text("**Status:** COMPLETE / INTEGRATED / POST-MERGE VALIDATED\n", encoding="utf-8")
                with self.assertRaisesRegex(lifecycle.LifecycleError, "closeout/P95 admission evidence drifted"):
                    lifecycle.validate_strategy_dependency()

    def test_plan_has_required_headings_and_runtime_capabilities(self) -> None:
        lifecycle.validate_plan()

    def _validate_gameplay_source(self, source: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prompt-kit-preference-gameplay.js"
            path.write_text(source, encoding="utf-8")
            with mock.patch.object(lifecycle, "GAMEPLAY_PATH", path):
                lifecycle.validate_gameplay_if_present()

    def test_gameplay_dead_clear_text_does_not_satisfy_reachability(self) -> None:
        source = """
var STORAGE_KEY='promptKit.usage.v1';
var state={recent:[]}; var next={recent:[]};
next.recent=next.recent.slice(0,12);
state.recent=["P1"].concat(state.recent).slice(0,12);
// function clearUsageData(){localStorage.removeItem(STORAGE_KEY);state=emptyState()}
// data-clear-usage addEventListener('click',clearUsageData)
"""
        with self.assertRaisesRegex(lifecycle.LifecycleError, "lacks clearUsageData"):
            self._validate_gameplay_source(source)

    def test_gameplay_unused_slice_does_not_prove_bounded_storage(self) -> None:
        source = """
var STORAGE_KEY='promptKit.usage.v1';
var state={recent:[]}; var next={recent:[]};
next.recent.slice(0,12);
state.recent.slice(0,12);
function clearUsageData(){localStorage.removeItem(STORAGE_KEY);state=emptyState()}
var clearButton=document.querySelector('[data-clear-usage]');clearButton.addEventListener('click',clearUsageData);
root.PromptKitPreferenceGameplay={clearUsageData:clearUsageData};
"""
        with self.assertRaisesRegex(lifecycle.LifecycleError, "assign the 12-item slice"):
            self._validate_gameplay_source(source)

    def test_gameplay_clear_function_must_delete_and_reset_state(self) -> None:
        source = """
var STORAGE_KEY='promptKit.usage.v1';
var state={recent:[]}; var next={recent:[]};
next.recent=next.recent.slice(0,12);
state.recent=state.recent.slice(0,12);
function clearUsageData(){state=emptyState()}
document.querySelector('[data-clear-usage]').addEventListener('click',clearUsageData);
root.PromptKitPreferenceGameplay={clearUsageData:clearUsageData};
"""
        with self.assertRaisesRegex(lifecycle.LifecycleError, "must delete"):
            self._validate_gameplay_source(source)

    def test_gameplay_usage_store_accepts_exported_user_wired_clear(self) -> None:
        source = """
var STORAGE_KEY='promptKit.usage.v1';
var state={recent:[]}; var next={recent:[]};
next.recent=next.recent.filter(Boolean).slice(0,12);
state.recent=['P1'].concat(state.recent).slice(0,12);
function emptyState(){return{recent:[]}}
function clearUsageData(){root.localStorage.removeItem(STORAGE_KEY);state=emptyState();renderDashboard()}
document.querySelector('[data-clear-usage]').addEventListener('click',clearUsageData);
root.PromptKitPreferenceGameplay={clearUsageData:clearUsageData};
"""
        self._validate_gameplay_source(source)

    def test_workflow_comments_do_not_satisfy_active_commands(self) -> None:
        workflow = """
on:
  pull_request:
    paths:
      - harness/contracts/prompt-kit-serverless-runtime-lifecycle.v1.json
  push:
    paths:
      - harness/contracts/prompt-kit-serverless-runtime-lifecycle.v1.json
jobs:
  validate:
    steps:
      - name: Validate serverless runtime lifecycle
        run: |
          # python scripts/validate_prompt_kit_serverless_runtime_lifecycle.py --summary
          echo nope
"""
        commands = lifecycle._workflow_run_commands(workflow)
        self.assertIn("echo nope", commands)
        self.assertNotIn(
            "python scripts/validate_prompt_kit_serverless_runtime_lifecycle.py --summary",
            commands,
        )


if __name__ == "__main__":
    unittest.main()
