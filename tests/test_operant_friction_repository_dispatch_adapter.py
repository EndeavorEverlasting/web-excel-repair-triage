from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "scripts" / "prompt_kit_afk_repository_dispatch.py"
WORKFLOW = ROOT / ".github" / "workflows" / "prompt-kit-feedback-hook.yml"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-feedback-afk-routing.v1.json"


def load_adapter():
    spec = importlib.util.spec_from_file_location("prompt_kit_afk_repository_dispatch", ADAPTER)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load repository-dispatch adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OperantFrictionRepositoryDispatchAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.adapter = load_adapter()
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    @staticmethod
    def event(**payload_overrides):
        payload = {
            "schema_version": "operant-friction-receipt/v1",
            "signal_id": "tutorial-route-miss-3",
            "event_type": "operant_friction",
            "value": "route_miss",
            "surface_id": "tutorial",
            "evidence_kind": "repeated_local_pattern",
            "occurrence_count": 3,
            "timestamp": "2026-09-10T03:20:00Z",
            "sequence": 12,
            "source_hash": "a" * 64,
        }
        payload.update(payload_overrides)
        return {
            "action": "operant-friction-receipt",
            "client_payload": payload,
            "repository": {"full_name": "example/private-provider-metadata"},
            "sender": {"login": "provider-user-metadata"},
        }

    def test_repository_dispatch_routes_only_sanitized_client_payload(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = self.adapter.route_repository_dispatch(
                self.event(),
                state_path=root / "state.json",
                requests_dir=root / "requests",
            )
            self.assertEqual(result["status"], "BLOCKED_WORKER_UNCONFIGURED")
            request = json.loads(Path(result["request_path"]).read_text(encoding="utf-8"))
            self.assertEqual(request["evidence"]["signal_id"], "tutorial-route-miss-3")
            self.assertEqual(request["evidence"]["surface_id"], "tutorial")
            encoded = json.dumps(request, sort_keys=True)
            self.assertNotIn("provider-user-metadata", encoded)
            self.assertNotIn("example/private-provider-metadata", encoded)

    def test_repository_dispatch_rejects_wrong_action_or_non_friction_payload(self) -> None:
        wrong_action = self.event()
        wrong_action["action"] = "prompt-kit-feedback-receipt"
        with self.assertRaises(self.adapter.AdapterError):
            self.adapter.extract_receipt(wrong_action)

        wrong_payload = self.event(event_type="prompt_vote", value="dislike")
        with self.assertRaises(self.adapter.AdapterError):
            self.adapter.extract_receipt(wrong_payload)

        malformed = self.event()
        malformed["client_payload"] = ["not", "an", "object"]
        with self.assertRaises(self.adapter.AdapterError):
            self.adapter.extract_receipt(malformed)

    def test_workflow_binds_one_read_only_repository_dispatch_adapter(self) -> None:
        self.assertIn("repository_dispatch:", self.workflow)
        self.assertIn("operant-friction-receipt", self.workflow)
        self.assertIn("scripts/prompt_kit_afk_repository_dispatch.py", self.workflow)
        self.assertIn("contents: read", self.workflow)
        self.assertNotIn("contents: write", self.workflow)
        self.assertNotIn("pull-requests: write", self.workflow)

    def test_contract_names_adapter_without_moving_semantic_or_promotion_authority(self) -> None:
        adapter = self.contract["surfaces"]["remote_repository_dispatch_adapter"]
        self.assertEqual(adapter["path"], "scripts/prompt_kit_afk_repository_dispatch.py")
        self.assertEqual(adapter["workflow"], ".github/workflows/prompt-kit-feedback-hook.yml")
        self.assertEqual(adapter["event_type"], "operant-friction-receipt")
        self.assertEqual(self.contract["semantic_owners"]["usage_and_friction_semantics"], "P99")
        self.assertEqual(self.contract["semantic_owners"]["afk_coordination"], "P115")
        self.assertEqual(self.contract["semantic_owners"]["promotion"], "P105/pr-floor-integration")


if __name__ == "__main__":
    unittest.main()
