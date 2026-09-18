from __future__ import annotations

import ast
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_privacy_preserving_failure_observatory import validate as validate_observatory

from scripts.failure_observatory import (
    CAPSULE_KEYS,
    CONTENT_BEARING_HOOKS,
    ObservatoryError,
    adapt_cursor_hook,
    apply_signal,
    compile_capsule,
    derive_local_run_key,
    load_state,
    new_state,
    receipt_signal,
    save_state,
)

ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE = json.loads((ROOT / "harness/contracts/execution-boundary-enforcement.v1.json").read_text(encoding="utf-8"))
TAXONOMY = json.loads((ROOT / "harness/contracts/execution-boundary-taxonomy.v1.json").read_text(encoding="utf-8"))
CONTRACT = json.loads((ROOT / "harness/contracts/privacy-preserving-failure-observatory.v1.json").read_text(encoding="utf-8"))
HOOKS = json.loads((ROOT / "harness/prototypes/failure-observatory/cursor-hooks.example.json").read_text(encoding="utf-8"))


class PrivacyPreservingFailureObservatoryTests(unittest.TestCase):
    def apply(self, state, hook_name, raw):
        return apply_signal(state, adapt_cursor_hook(hook_name, raw), ARCHITECTURE, TAXONOMY)

    def test_static_validator_passes(self) -> None:
        summary = validate_observatory()
        self.assertEqual(summary["hooks"], 5)
        self.assertEqual(summary["capsule_fields"], len(CAPSULE_KEYS))

    def test_contract_defaults_local_only(self) -> None:
        self.assertEqual(CONTRACT["default_mode"], "LOCAL_ONLY")
        self.assertEqual(CONTRACT["deployment_operating_model"]["selected"], "LOCAL_PROCESS")
        phases = {item["phase"]: item["status"] for item in CONTRACT["phase_map"]}
        self.assertEqual(phases["P2_ANONYMOUS_CONTRIBUTION"], "BLOCKED_BY_PRIVACY_DESIGN_APPROVAL")

    def test_before_submit_keeps_only_bounded_public_marker(self) -> None:
        secret = "TOP-SECRET-PROMPT-CONTENT"
        signal = adapt_cursor_hook(
            "beforeSubmitPrompt",
            {
                "prompt": f"[[AFK_PROMPT:P07@2026.09]] {secret}",
                "attachments": [{"type": "file", "file_path": f"/private/{secret}.txt"}],
                "email": "private@example.com",
            },
        )
        encoded = json.dumps(signal, sort_keys=True)
        self.assertEqual(signal, {"kind": "RUN_STARTED", "prompt_id": "P07", "prompt_release": "2026.09"})
        self.assertNotIn(secret, encoded)
        self.assertNotIn("private@example.com", encoded)

    def test_marker_inside_user_content_is_not_attributed(self) -> None:
        signal = adapt_cursor_hook(
            "beforeSubmitPrompt",
            {"prompt": "ordinary user text [[AFK_PROMPT:P07@2026.09]]"},
        )
        self.assertEqual(signal["prompt_id"], "UNKNOWN")
        self.assertEqual(signal["prompt_release"], "UNKNOWN")

    def test_tool_failure_adapter_drops_command_error_path_and_ids(self) -> None:
        secret = "INTERNAL-HOSTNAME-DO-NOT-LEAK"
        signal = adapt_cursor_hook(
            "postToolUseFailure",
            {
                "tool_name": "Shell",
                "tool_input": {"command": f"curl https://{secret}"},
                "tool_use_id": secret,
                "cwd": f"/repo/{secret}",
                "error_message": f"failed contacting {secret}",
                "failure_type": "timeout",
                "duration": 999999,
                "is_interrupt": False,
            },
        )
        encoded = json.dumps(signal, sort_keys=True)
        self.assertEqual(signal["failure_type"], "timeout")
        self.assertEqual(signal["tool_category"], "Shell")
        self.assertNotIn(secret, encoded)
        self.assertNotIn("duration", signal)

    def test_content_bearing_cursor_hooks_fail_closed(self) -> None:
        for hook in CONTENT_BEARING_HOOKS:
            with self.subTest(hook=hook):
                with self.assertRaisesRegex(ObservatoryError, "content-bearing"):
                    adapt_cursor_hook(hook, {"text": "private reasoning"})

    def test_success_receipt_prevents_false_abandonment(self) -> None:
        state = new_state()
        state = self.apply(state, "beforeSubmitPrompt", {"prompt": "[[AFK_PROMPT:P07@2026.09]] private body"})
        state = self.apply(state, "afterFileEdit", {"file_path": "/secret/file.py"})
        state = apply_signal(state, receipt_signal("P07", "2026.09", "VALIDATED"), ARCHITECTURE, TAXONOMY)
        state = self.apply(state, "stop", {"status": "completed", "loop_count": 0})
        capsule = compile_capsule(state)
        self.assertEqual(capsule["outcome"], "SUCCESS")
        self.assertEqual(capsule["boundary_class"], "NONE")
        self.assertTrue(capsule["receipt_present"])

    def test_stop_without_receipt_after_tool_failure_is_semantic_abandonment(self) -> None:
        state = new_state()
        state = self.apply(state, "beforeSubmitPrompt", {"prompt": "[[AFK_PROMPT:P07@2026.09]]"})
        state = self.apply(
            state,
            "postToolUseFailure",
            {"tool_name": "Shell", "failure_type": "timeout", "is_interrupt": False, "error_message": "private"},
        )
        state = self.apply(state, "afterFileEdit", {"file_path": "/private/a.py"})
        state = self.apply(state, "stop", {"status": "completed", "loop_count": 0})
        capsule = compile_capsule(state)
        self.assertEqual(capsule["boundary_class"], "EC_SEMANTIC_ABANDONMENT")
        self.assertEqual(capsule["contract_clause"], "EBE.NO_SILENT_STOP")
        self.assertEqual(capsule["failure_type"], "timeout")
        self.assertEqual(capsule["mutation_bucket"], "ONE")
        self.assertFalse(capsule["receipt_present"])

    def test_user_abort_is_stable_stop_not_recovery_loop(self) -> None:
        state = new_state()
        state = self.apply(state, "beforeSubmitPrompt", {"prompt": "[[AFK_PROMPT:P07@2026.09]]"})
        state = self.apply(
            state,
            "postToolUseFailure",
            {"tool_name": "Shell", "failure_type": "error", "is_interrupt": True},
        )
        state = self.apply(state, "stop", {"status": "aborted", "loop_count": 0})
        capsule = compile_capsule(state)
        self.assertEqual(capsule["boundary_class"], "UC_CANCELLED")
        self.assertEqual(capsule["recovery_disposition"], "QUIESCE_UNCHANGED_BLOCKER")
        self.assertEqual(capsule["terminal_state"], "QUIESCENT_BLOCKED")

    def test_session_error_normalizes_to_hard_termination(self) -> None:
        state = new_state()
        state = self.apply(state, "beforeSubmitPrompt", {"prompt": "[[AFK_PROMPT:P07@2026.09]]"})
        state = self.apply(
            state,
            "sessionEnd",
            {"session_id": "PRIVATE-ID", "reason": "error", "error_message": "secret failure"},
        )
        capsule = compile_capsule(state)
        self.assertEqual(capsule["boundary_class"], "HT_HOST_FORCED_TERMINATION")
        self.assertEqual(capsule["recovery_disposition"], "SYNTHESIZE_TERMINATION")
        self.assertEqual(capsule["terminal_state"], "HARD_TERMINATED_SYNTHETIC")

    def test_privacy_canaries_never_reach_state_or_capsule(self) -> None:
        canaries = [
            "PROMPT-SECRET-93f1",
            "RESPONSE-SECRET-a03c",
            "THOUGHT-SECRET-61bd",
            "PATH-SECRET-70ee",
            "COMMAND-SECRET-e8af",
            "ERROR-SECRET-b122",
            "EMAIL-SECRET-c991",
            "SESSION-SECRET-dd72",
        ]
        state = new_state()
        state = self.apply(
            state,
            "beforeSubmitPrompt",
            {
                "prompt": f"[[AFK_PROMPT:P07@2026.09]] {canaries[0]}",
                "attachments": [{"file_path": f"/{canaries[3]}"}],
                "email": canaries[6],
            },
        )
        state = self.apply(
            state,
            "postToolUseFailure",
            {
                "tool_name": "Shell",
                "tool_input": {"command": canaries[4]},
                "tool_use_id": canaries[7],
                "cwd": f"/{canaries[3]}",
                "error_message": canaries[5],
                "failure_type": "error",
                "is_interrupt": False,
                "text": canaries[1],
                "thought": canaries[2],
            },
        )
        state = self.apply(state, "stop", {"status": "completed", "loop_count": 0})
        encoded_state = json.dumps(state, sort_keys=True)
        encoded_capsule = json.dumps(compile_capsule(state), sort_keys=True)
        for canary in canaries:
            self.assertNotIn(canary, encoded_state)
            self.assertNotIn(canary, encoded_capsule)

    def test_capsule_schema_is_exact_allowlist(self) -> None:
        self.assertEqual(set(CONTRACT["contribution_capsule_allowlist"]), CAPSULE_KEYS)

    def test_example_hooks_never_subscribe_to_response_or_thought(self) -> None:
        self.assertFalse(set(HOOKS["hooks"]) & CONTENT_BEARING_HOOKS)
        self.assertEqual(
            set(HOOKS["hooks"]),
            {"beforeSubmitPrompt", "postToolUseFailure", "afterFileEdit", "stop", "sessionEnd"},
        )

    def test_prototype_imports_no_network_client(self) -> None:
        forbidden = {"requests", "urllib", "httpx", "aiohttp", "socket", "websockets"}
        for rel in ("scripts/failure_observatory.py", "scripts/cursor_failure_sentinel.py"):
            tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
            self.assertFalse(imports & forbidden, f"{rel} imports network module(s): {imports & forbidden}")

    def test_local_hmac_correlation_is_nonportable_and_not_exported(self) -> None:
        generation_id = "CURSOR-GENERATION-PRIVATE-123"
        key_a = derive_local_run_key(generation_id, b"a" * 32)
        key_b = derive_local_run_key(generation_id, b"b" * 32)
        self.assertNotEqual(key_a, key_b)
        self.assertEqual(len(key_a), 24)
        self.assertNotIn(generation_id, key_a)
        state = new_state()
        state = self.apply(state, "beforeSubmitPrompt", {"prompt": "[[AFK_PROMPT:P07@2026.09]]"})
        state = self.apply(state, "stop", {"status": "completed", "loop_count": 0})
        capsule = compile_capsule(state)
        self.assertNotIn("run_key", capsule)
        self.assertNotIn(generation_id, json.dumps(capsule, sort_keys=True))

    def test_independent_generations_resolve_to_distinct_local_keys(self) -> None:
        secret = b"z" * 32
        first = derive_local_run_key("generation-one", secret)
        second = derive_local_run_key("generation-two", secret)
        self.assertNotEqual(first, second)

    def test_zero_content_state_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            state = new_state()
            state = self.apply(state, "beforeSubmitPrompt", {"prompt": "[[AFK_PROMPT:P07@2026.09]] PRIVATE"})
            save_state(path, state)
            loaded = load_state(path)
            self.assertEqual(loaded, state)
            self.assertNotIn("PRIVATE", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
