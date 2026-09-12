from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "scripts" / "prompt_kit_afk_signal_router.py"
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-feedback-afk-routing.v1.json"
CAPABILITIES = ROOT / "harness" / "capabilities.v1.json"
TRIGGERS = ROOT / "harness" / "triggers.v1.json"
WORKFLOWS = ROOT / "harness" / "workflows.v1.json"
SKILL = ROOT / ".ai" / "skills" / "prompt-kit-feedback-afk-routing" / "SKILL.md"
WEB_WORKFLOW = ROOT / ".github" / "workflows" / "prompt-kit-web.yml"
FEEDBACK_WORKFLOW = ROOT / ".github" / "workflows" / "prompt-kit-feedback-hook.yml"


def load_router():
    spec = importlib.util.spec_from_file_location("prompt_kit_afk_signal_router", ROUTER)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load AFK signal router")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PromptKitFeedbackAfkRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.router = load_router()
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.capabilities = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        cls.triggers = json.loads(TRIGGERS.read_text(encoding="utf-8"))
        cls.workflows = json.loads(WORKFLOWS.read_text(encoding="utf-8"))
        cls.skill = SKILL.read_text(encoding="utf-8")
        cls.web_workflow = WEB_WORKFLOW.read_text(encoding="utf-8")
        cls.feedback_workflow = FEEDBACK_WORKFLOW.read_text(encoding="utf-8")

    @staticmethod
    def event(event_id: str, event_type: str, value: str, **extra):
        payload = {
            "event_id": event_id,
            "prompt_id": "P115",
            "event_type": event_type,
            "value": value,
            "timestamp": "2026-08-27T12:00:00Z",
            "sequence": 7,
        }
        payload.update(extra)
        return payload

    @staticmethod
    def friction_event(event_id: str, value: str, **extra):
        payload = {
            "event_id": event_id,
            "event_type": "operant_friction",
            "value": value,
            "surface_id": "tutorial",
            "evidence_kind": "repeated_local_pattern",
            "occurrence_count": 3,
            "timestamp": "2026-09-09T22:00:00Z",
            "sequence": 9,
            "source_hash": "a" * 64,
        }
        payload.update(extra)
        return payload

    def test_contract_keeps_semantic_and_promotion_owners_separate(self) -> None:
        self.assertEqual(self.contract["prompt_surface"], "standard-ai")
        self.assertEqual(self.contract["semantic_owners"]["explicit_feedback"], "P99")
        self.assertEqual(self.contract["semantic_owners"]["usage_and_friction_semantics"], "P99")
        self.assertEqual(self.contract["semantic_owners"]["afk_coordination"], "P115")
        self.assertEqual(self.contract["semantic_owners"]["general_repository_execution"], "P07")
        self.assertEqual(self.contract["semantic_owners"]["established_ci_repair"], "P32")
        self.assertEqual(self.contract["semantic_owners"]["promotion"], "P105/pr-floor-integration")
        self.assertFalse(self.contract["wakeups"]["second_scheduler_allowed"])
        self.assertFalse(self.contract["privacy"]["browser_credentials"])
        self.assertFalse(self.contract["privacy"]["raw_comment_provider_dispatch"])
        self.assertTrue(self.contract["privacy"]["raw_comment_local_worker_request"])
        self.assertFalse(self.contract["privacy"]["raw_usage_history_provider_dispatch"])
        self.assertFalse(self.contract["privacy"]["raw_search_or_typed_content"])
        self.assertFalse(self.contract["privacy"]["user_identity_in_friction_receipt"])
        self.assertTrue(self.contract["privacy"]["friction_receipts_local_first"])
        self.assertIn("source_hash", self.contract["privacy"]["provider_receipt_fields"])
        self.assertTrue(self.contract["friction_policy"]["raw_usage_is_never_directly_actionable"])
        self.assertEqual(
            self.contract["friction_policy"]["evidence_kinds"]["deterministic_runtime_failure"]["minimum_occurrences"],
            1,
        )
        self.assertEqual(
            self.contract["friction_policy"]["evidence_kinds"]["repeated_local_pattern"]["minimum_occurrences"],
            3,
        )
        self.assertTrue(self.contract["execution_adapters"]["provider_neutral_router"])
        self.assertEqual(self.contract["execution_adapters"]["github_actions_role"], "worked adapter only")

    def test_router_classifies_actionable_and_information_only_signals(self) -> None:
        cases = [
            (self.event("feedback", "prompt_feedback", "comment", comment="Needs a tighter merge handoff"), "ACTIONABLE_REPAIR"),
            (self.event("dislike", "prompt_vote", "dislike"), "ACTIONABLE_REPAIR"),
            (self.event("like", "prompt_vote", "like"), "INFORMATION_ONLY"),
            (self.event("usage", "prompt_usage", "copy"), "INFORMATION_ONLY"),
            (
                self.friction_event(
                    "runtime-failure",
                    "stale_guidance",
                    evidence_kind="deterministic_runtime_failure",
                    occurrence_count=1,
                ),
                "ACTIONABLE_REPAIR",
            ),
            (self.friction_event("two-route-misses", "route_miss", occurrence_count=2), "INFORMATION_ONLY"),
            (self.friction_event("three-route-misses", "route_miss", occurrence_count=3), "ACTIONABLE_REPAIR"),
        ]
        for payload, expected in cases:
            with self.subTest(payload=payload):
                normalized = self.router.normalize_signal(payload)
                self.assertEqual(self.router.classify_signal(normalized), expected)

    def test_router_deduplicates_information_only_signal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = root / "state.json"
            requests = root / "requests"
            payload = self.event("like-1", "prompt_vote", "like")
            first = self.router.route_signal(payload, state_path=state, requests_dir=requests)
            second = self.router.route_signal(payload, state_path=state, requests_dir=requests)
            self.assertEqual(first["status"], "CONSUMED_INFORMATION_ONLY")
            self.assertEqual(second["status"], "DUPLICATE_ALREADY_CONSUMED")
            self.assertFalse(requests.exists())

    def test_subthreshold_raw_or_derived_usage_never_creates_work_request(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = root / "state.json"
            requests = root / "requests"
            raw_usage = self.event("ordinary-copy", "prompt_usage", "copy")
            low_friction = self.friction_event("route-miss-2", "route_miss", occurrence_count=2)
            raw_result = self.router.route_signal(raw_usage, state_path=state, requests_dir=requests)
            friction_result = self.router.route_signal(low_friction, state_path=state, requests_dir=requests)
            self.assertEqual(raw_result["disposition"], "INFORMATION_ONLY")
            self.assertEqual(friction_result["disposition"], "INFORMATION_ONLY")
            self.assertFalse(requests.exists())

    def test_actionable_signal_creates_private_p115_work_request_and_can_retry_worker_block(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = root / "state.json"
            requests = root / "requests"
            payload = self.event("feedback-1", "prompt_feedback", "comment", comment="Private repair detail")
            blocked = self.router.route_signal(payload, state_path=state, requests_dir=requests)
            self.assertEqual(blocked["status"], "BLOCKED_WORKER_UNCONFIGURED")
            request_path = Path(blocked["request_path"])
            request = json.loads(request_path.read_text(encoding="utf-8"))
            self.assertEqual(request["coordinator"], "P115 AFK Feedback-Driven Development Loop Executor")
            self.assertEqual(request["preferred_mutation_owner"], "P07 Repo Sprint Executor")
            self.assertEqual(request["promotion_owner"], "P105/pr-floor-integration")
            self.assertEqual(request["telemetry_semantic_owner"], "P99")
            self.assertEqual(request["evidence"]["private_comment"], "Private repair detail")

            worker = [
                sys.executable,
                "-c",
                "import pathlib,sys; assert pathlib.Path(sys.argv[1]).is_file()",
                "{request}",
            ]
            dispatched = self.router.route_signal(payload, state_path=state, requests_dir=requests, worker_argv=worker)
            self.assertEqual(dispatched["status"], "DISPATCHED")
            duplicate = self.router.route_signal(payload, state_path=state, requests_dir=requests, worker_argv=worker)
            self.assertEqual(duplicate["status"], "DUPLICATE_ALREADY_CONSUMED")

    def test_actionable_operant_friction_creates_sanitized_surface_request_without_prompt_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = root / "state.json"
            requests = root / "requests"
            payload = self.friction_event(
                "tutorial-stale",
                "stale_guidance",
                evidence_kind="deterministic_runtime_failure",
                occurrence_count=1,
            )
            blocked = self.router.route_signal(payload, state_path=state, requests_dir=requests)
            self.assertEqual(blocked["status"], "BLOCKED_WORKER_UNCONFIGURED")
            request = json.loads(Path(blocked["request_path"]).read_text(encoding="utf-8"))
            self.assertEqual(request["target"], "Operant surface tutorial")
            self.assertEqual(request["coordinator"], "P115 AFK Feedback-Driven Development Loop Executor")
            self.assertEqual(request["preferred_mutation_owner"], "P07 Repo Sprint Executor")
            self.assertEqual(request["telemetry_semantic_owner"], "P99")
            self.assertEqual(
                request["evidence"],
                {
                    "signal_id": "tutorial-stale",
                    "event_type": "operant_friction",
                    "value": "stale_guidance",
                    "sequence": 9,
                    "timestamp": "2026-09-09T22:00:00Z",
                    "surface_id": "tutorial",
                    "evidence_kind": "deterministic_runtime_failure",
                    "occurrence_count": 1,
                    "source_hash": "a" * 64,
                },
            )
            self.assertNotIn("private_comment", request["evidence"])

    def test_router_rejects_sensitive_fields_and_malformed_feedback(self) -> None:
        cases = [
            self.event("secret", "prompt_feedback", "comment", comment="x", credential="no"),
            self.event("bad-comment", "prompt_feedback", "comment", comment=""),
            self.event("wrong-comment", "prompt_vote", "dislike", comment="not allowed"),
            {"event_id": "bad-prompt", "prompt_id": "bad", "event_type": "prompt_vote", "value": "like"},
            self.friction_event("bad-surface", "route_miss", surface_id="Tutorial / Search"),
            self.friction_event("bad-count", "route_miss", occurrence_count=0),
            self.friction_event("bad-kind", "route_miss", evidence_kind="remote_profile"),
            self.friction_event("bad-source-hash", "route_miss", source_hash="local-pseudonym"),
            self.friction_event("search-text", "route_miss", search_query="how do I deploy"),
            self.friction_event("typed-text", "route_miss", typed_text="private user text"),
            self.friction_event("user-id", "route_miss", user_id="person-123"),
            self.friction_event("history", "route_miss", navigation_history=["one", "two"]),
        ]
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(self.router.RoutingError):
                self.router.normalize_signal(payload)

    def test_friction_receipt_allows_optional_prompt_id_but_rejects_bad_prompt_id(self) -> None:
        with_prompt = self.router.normalize_signal(self.friction_event("prompt-friction", "action_failure", prompt_id="p115"))
        self.assertEqual(with_prompt["prompt_id"], "P115")
        with self.assertRaises(self.router.RoutingError):
            self.router.normalize_signal(self.friction_event("bad-prompt-friction", "action_failure", prompt_id="tutorial"))

    def test_router_is_one_shot_provider_neutral_and_has_no_merge_surface(self) -> None:
        source = ROUTER.read_text(encoding="utf-8")
        for marker in ("time.sleep(", "--poll-seconds", "gh api", "gh pr", "GITHUB_TOKEN", "shell=True"):
            self.assertNotIn(marker, source)
        self.assertNotIn("/merge\"", source)
        self.assertIn("P115 AFK Feedback-Driven Development Loop Executor", source)
        self.assertIn("P105/pr-floor-integration", source)
        self.assertIn("P99", source)
        self.assertNotIn("github.com", source.lower())
        self.assertNotIn("github actions", source.lower())

    def test_skill_capability_trigger_and_workflow_are_registered_once(self) -> None:
        capabilities = [row for row in self.capabilities["capabilities"] if row["id"] == "prompt-kit-feedback-afk-routing"]
        triggers = [row for row in self.triggers["triggers"] if row["id"] == "prompt-kit-actionable-feedback"]
        workflows = [row for row in self.workflows["workflows"] if row["id"] == "prompt-kit-feedback-afk-routing"]
        self.assertEqual(len(capabilities), 1)
        self.assertEqual(len(triggers), 1)
        self.assertEqual(len(workflows), 1)
        self.assertEqual(capabilities[0]["version"], "1.1.0")
        self.assertEqual(capabilities[0]["implementation"]["path"], "scripts/prompt_kit_afk_signal_router.py")
        self.assertIn("P99-derived Operant friction receipt", capabilities[0]["operation"])
        self.assertEqual(triggers[0]["capability_id"], "prompt-kit-feedback-afk-routing")
        self.assertTrue(any("privacy-bounded Operant friction receipt" in text for text in triggers[0]["conditions"]))
        self.assertTrue(any("raw usage observation" in text for text in triggers[0]["forbidden_conditions"]))
        self.assertTrue(any("search or typed content" in text for text in triggers[0]["forbidden_conditions"]))
        for heading in ("## Trigger", "## Required inputs", "## Outputs", "## Procedure", "## Guardrails", "## Validation", "## Proof ceiling"):
            self.assertIn(heading, self.skill)
        self.assertIn("privacy-bounded Operant friction receipt", self.skill)
        self.assertIn("Raw ordinary usage is not itself an AFK work request", self.skill)
        self.assertIn("Local and remote adapters share one provider-neutral contract", self.skill)

    def test_web_workflow_retires_stale_p122_writer_and_preserves_portability(self) -> None:
        self.assertIn("contents: read", self.web_workflow)
        self.assertNotIn("contents: write", self.web_workflow)
        for marker in ("P122 Gemini regression strengthening", "feat/gemini-youtube-ingestion-prompt-20260827", "git push origin"):
            self.assertNotIn(marker, self.web_workflow)
        for marker in (
            "scripts/serve_prompt_kit_portable.py",
            "scripts/validate_prompt_kit_portability.py",
            "tests/test_prompt_kit_portability.py",
            "tests/test_prompt_kit_portability_regressions.py",
            "Build portable Prompt Kit runtime artifact",
            "Validate portable Favorites and harness discipline",
            "prompt-kit-portable-runtime",
        ):
            self.assertIn(marker, self.web_workflow)

    def test_feedback_provider_hook_remains_read_only(self) -> None:
        self.assertIn("contents: read", self.feedback_workflow)
        self.assertNotIn("contents: write", self.feedback_workflow)


if __name__ == "__main__":
    unittest.main()
