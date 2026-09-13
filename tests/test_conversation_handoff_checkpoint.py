import json
import unittest
from pathlib import Path

from scripts.validate_conversation_handoff_checkpoint import (
    ContractError,
    SCHEMA_VERSION,
    validate_checkpoint,
    validate_schema_contract,
)

ROOT = Path(__file__).resolve().parents[1]


def good_checkpoint():
    """Return the smallest valid nonterminal checkpoint fixture."""
    return {
        "handoff_version": SCHEMA_VERSION,
        "source_controller": "live-thread-convergence-controller",
        "source_conversation_state": "CLOSING",
        "created_at": "2026-09-13T00:00:00Z",
        "threads": [{
            "id": "thread-p02-checkpoint",
            "target": "Persist resumable live-thread handoff",
            "disposition": "HANDOFF-READY",
            "priority": {"rank": 1, "rationale": "Current context is closing."},
            "current_state": "Implementation is ready for P02 continuation.",
            "last_meaningful_action": "Validated the focused handoff contract.",
            "first_unproven_gate": "Refresh current provider truth before mutation.",
            "decisions": [{"decision": "Resume from first unproven gate.", "status": "SETTLED", "evidence": "Live/P02 continuity contract."}],
            "evidence": [{"type": "conversation", "identity": "handoff-contract", "value": "Checkpoint produced after focused convergence.", "mutable": False}],
            "changed_surfaces": ["harness/conversation-continuity/checkpoint.schema.v1.json"],
            "validations": [{"check": "checkpoint contract", "target": SCHEMA_VERSION, "result": "PASS"}],
            "remaining_work": [{"item": "Refresh mutable provider evidence.", "status": "SAFE & EXECUTABLE", "dependency": "Repository access", "consequence": "Current branch/PR state would otherwise be stale."}],
            "next_action": {"owner": "P02", "dependency": "Validated checkpoint", "action": "Refresh mutable evidence and resume first unproven gate.", "expected_output": "Current execution floor", "completion_gate": "All mutable anchors reconciled"},
            "route": "RESUME IN NEW CONVERSATION",
            "return_trigger": "P02 ingestion begins"
        }]
    }


class ConversationHandoffCheckpointTests(unittest.TestCase):
    """Exercise structural and lifecycle invariants for resumable checkpoints."""

    def test_schema_contract_is_stable(self):
        """The tracked Draft 2020-12 schema must remain internally valid."""
        validate_schema_contract()

    def test_valid_handoff_ready_checkpoint_passes(self):
        """A complete HANDOFF-READY fixture must satisfy both validation layers."""
        validate_checkpoint(good_checkpoint())

    def test_missing_required_thread_field_fails(self):
        """Required continuation fields cannot disappear from a thread."""
        payload = good_checkpoint()
        del payload["threads"][0]["first_unproven_gate"]
        with self.assertRaisesRegex(ContractError, "first_unproven_gate"):
            validate_checkpoint(payload)

    def test_unknown_top_level_field_is_rejected(self):
        """Strict schema ownership rejects undeclared top-level checkpoint state."""
        payload = good_checkpoint()
        payload["unexpected"] = True
        with self.assertRaisesRegex(ContractError, "schema validation failed"):
            validate_checkpoint(payload)

    def test_invalid_evidence_type_is_rejected(self):
        """Evidence kinds must stay inside the canonical schema enum."""
        payload = good_checkpoint()
        payload["threads"][0]["evidence"][0]["type"] = "wishful-thinking"
        with self.assertRaisesRegex(ContractError, "schema validation failed"):
            validate_checkpoint(payload)

    def test_created_at_requires_timezone(self):
        """Checkpoint timestamps must be RFC 3339 date-time values with timezone."""
        payload = good_checkpoint()
        payload["created_at"] = "2026-09-13T00:00:00"
        with self.assertRaisesRegex(ContractError, "schema validation failed"):
            validate_checkpoint(payload)

    def test_suspended_thread_requires_return_trigger(self):
        """Suspension is invalid unless an observable resumption trigger survives."""
        payload = good_checkpoint()
        payload["threads"][0]["disposition"] = "SUSPENDED"
        payload["threads"][0]["return_trigger"] = ""
        with self.assertRaisesRegex(ContractError, "return_trigger"):
            validate_checkpoint(payload)

    def test_blocked_thread_requires_exact_blocker_contract(self):
        """BLOCKED threads must preserve the unblock owner, trigger, and resume point."""
        payload = good_checkpoint()
        payload["threads"][0]["disposition"] = "BLOCKED"
        with self.assertRaisesRegex(ContractError, "blocker"):
            validate_checkpoint(payload)
        payload["threads"][0]["blocker"] = {
            "exact_blocker": "Protected runtime unavailable",
            "unblock_owner": "runtime owner",
            "unblocking_action": "Restore runtime access",
            "resume_trigger": "Runtime is reachable",
            "resume_point": "Run the first unproven runtime check"
        }
        validate_checkpoint(payload)

    def test_repository_evidence_requires_exact_repository_state(self):
        """Repository evidence must carry exact repository/head continuation state."""
        payload = good_checkpoint()
        payload["threads"][0]["evidence"].append({"type": "repository", "identity": "repo-head", "value": "abcdef1234567", "mutable": True})
        with self.assertRaisesRegex(ContractError, "repository_state"):
            validate_checkpoint(payload)
        payload["threads"][0]["repository_state"] = {
            "repository": "EndeavorEverlasting/web-excel-repair-triage",
            "default_branch": "main",
            "working_branch": "fix/example",
            "head_sha": "abcdef1234567",
            "first_unproven_repository_gate": "Refresh exact head"
        }
        validate_checkpoint(payload)

    def test_canonical_schema_rejects_optional_repository_shape_drift(self):
        """Canonical schema validation must catch optional shape drift manual rules omit."""
        payload = good_checkpoint()
        thread = payload["threads"][0]
        thread["evidence"].append({"type": "repository", "identity": "repo-head", "value": "abcdef1234567", "mutable": True})
        thread["repository_state"] = {
            "repository": "EndeavorEverlasting/web-excel-repair-triage",
            "default_branch": "main",
            "working_branch": "fix/example",
            "head_sha": "abcdef1234567",
            "changed_files": [123],
            "first_unproven_repository_gate": "Refresh exact head"
        }
        with self.assertRaisesRegex(ContractError, "schema validation failed"):
            validate_checkpoint(payload)

    def test_terminal_thread_forbids_fake_next_action(self):
        """Terminal dispositions cannot retain a misleading executable continuation."""
        payload = good_checkpoint()
        thread = payload["threads"][0]
        thread["disposition"] = "COMPLETE"
        thread["first_unproven_gate"] = None
        thread["route"] = "NO CONTINUATION REQUIRED"
        with self.assertRaisesRegex(ContractError, "next_action"):
            validate_checkpoint(payload)
        thread["next_action"] = None
        validate_checkpoint(payload)

    def test_effective_p02_consumes_validated_checkpoint_without_replay(self):
        """The effective P02 override must consume checkpoints from the unproven gate."""
        registry = json.loads((ROOT / "registry" / "prompts" / "prompt-overrides.v1.json").read_text(encoding="utf-8"))
        p02 = next(item for item in registry["overrides"] if item["id"] == "P02")
        body = p02["copyContent"]
        self.assertIn(SCHEMA_VERSION, body)
        self.assertIn("validate_conversation_handoff_checkpoint.py", body)
        self.assertIn("first_unproven_gate", body)
        self.assertIn("do not replay completed work", body.lower())


if __name__ == "__main__":
    unittest.main()
