from __future__ import annotations

import copy
import json
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from scripts import prompt_registry_grounding as grounding
from scripts import prompt_registry_ops

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = REPO_ROOT / "harness" / "specs" / "prompt-operations.md"


def fixture_draft() -> dict[str, object]:
    return {
        "name": "Grounding Gate Test Fixture",
        "type": "MAINTENANCE",
        "class": "PROMPT KIT / TEST",
        "sprintRole": "Exercise deterministic prompt grounding",
        "useWhen": "A grounding gate regression is required.",
        "inspectFirst": "Current registry truth.",
        "expectedOutput": "A source-pinned dry-run prompt record.",
        "nextStep": "Validate the grounded record.",
        "proofGate": "No protected write occurs before GROUNDED_PASS.",
        "copyContent": "EXECUTE A DETERMINISTIC GROUNDED PROMPT REGISTRY TEST. " * 12,
        "keywords": ["grounding gate fixture", "registry grounding fixture"],
        "profile": "spec-architecture",
        "color": "Cyan",
    }


class PromptRegistryGroundingTests(unittest.TestCase):
    def test_grounding_packet_is_source_pinned_and_compact(self) -> None:
        packet = prompt_registry_ops.build_grounding_packet()
        self.assertEqual(packet["schema_version"], grounding.SCHEMA_VERSION)
        self.assertEqual(packet["gate_id"], grounding.GATE_ID)
        self.assertRegex(packet["source_fingerprint"], r"^[0-9a-f]{64}$")
        self.assertRegex(packet["packet_fingerprint"], r"^[0-9a-f]{64}$")
        self.assertRegex(packet["next_identity"]["id"], r"^P\d+$")
        self.assertEqual(
            packet["next_identity"]["copySheet"],
            f"{packet['next_identity']['id']}_COPY_SAFE",
        )
        self.assertIn("id", packet["draft_fields"]["auto_owned"])
        self.assertIn("spec-architecture-prompts", {r["registry_id"] for r in packet["registries"]})
        self.assertTrue(all(len(item["sha256"]) == 64 for item in packet["sources"]))
        serialized = json.dumps(packet)
        self.assertTrue(all("prompts" not in item for item in packet["registries"]))
        self.assertTrue(
            all(set(item) == {"source_key", "path", "sha256"} for item in packet["sources"])
        )
        self.assertLess(len(serialized), 16000)
        sources = {item["source_key"]: item for item in packet["sources"]}
        for source_key in (
            "display_order_policy",
            "reference",
            "runtime:guided_recommendations",
            "runtime:prompt_journey",
            "runtime:polish",
            "runtime:correspondence",
            "runtime:management",
            "runtime:spec_architecture",
            "runtime:base_prompt_kit",
            "html_builder",
        ):
            self.assertIn(source_key, sources)
            self.assertRegex(sources[source_key]["sha256"], r"^[0-9a-f]{64}$")

    def test_valid_proposal_passes_with_resolvable_attribution(self) -> None:
        packet = prompt_registry_ops.build_grounding_packet()
        gate = prompt_registry_ops.ground_prompt_proposal(
            fixture_draft(), "spec-architecture-prompts", packet
        )
        self.assertEqual(gate["status"], grounding.GROUNDED_PASS)
        self.assertEqual(gate["record"]["id"], packet["next_identity"]["id"])
        self.assertEqual(
            gate["attribution"]["registry_id"]["selector"], "$.registry_id"
        )
        self.assertEqual(
            gate["attribution"]["draft_schema"]["path"],
            "scripts/prompt_registry_ops.py",
        )
        source_keys = {item["source_key"] for item in packet["sources"]}
        identity_keys = gate["attribution"]["identity"]["source_keys"]
        self.assertTrue(identity_keys)
        self.assertTrue(set(identity_keys).issubset(source_keys))
        self.assertIn("base_registry", identity_keys)
        self.assertTrue(any(key.startswith("registry:") for key in identity_keys))

    def test_hallucinated_registry_is_unsourced_block(self) -> None:
        gate = prompt_registry_ops.ground_prompt_proposal(
            fixture_draft(), "invented-agent-memory-registry"
        )
        self.assertEqual(gate["status"], grounding.UNSOURCED_BLOCK)
        self.assertIn("Unknown registry_id", gate["detail"])

    def test_model_supplied_auto_identity_is_schema_mismatch(self) -> None:
        draft = fixture_draft()
        draft["id"] = "P999"
        gate = prompt_registry_ops.ground_prompt_proposal(
            draft, "spec-architecture-prompts"
        )
        self.assertEqual(gate["status"], grounding.SCHEMA_MISMATCH)
        self.assertIn("auto-owned fields", gate["detail"])

    def test_tampered_packet_is_contradiction_block(self) -> None:
        packet = prompt_registry_ops.build_grounding_packet()
        tampered = copy.deepcopy(packet)
        tampered["next_identity"]["id"] = "P999"
        gate = prompt_registry_ops.ground_prompt_proposal(
            fixture_draft(), "spec-architecture-prompts", tampered
        )
        self.assertEqual(gate["status"], grounding.CONTRADICTION_BLOCK)
        self.assertEqual(gate["reason"], "tampered_grounding_packet")

    def test_coherently_stale_packet_is_contradiction_block(self) -> None:
        packet = prompt_registry_ops.build_grounding_packet()
        stale = copy.deepcopy(packet)
        stale["sources"][0]["sha256"] = "0" * 64
        stale["source_fingerprint"] = grounding.source_fingerprint(stale["sources"])
        stale["packet_fingerprint"] = grounding.packet_fingerprint(stale)
        gate = prompt_registry_ops.ground_prompt_proposal(
            fixture_draft(), "spec-architecture-prompts", stale
        )
        self.assertEqual(gate["status"], grounding.CONTRADICTION_BLOCK)
        self.assertEqual(gate["reason"], "stale_source_identity")

    def test_malformed_grounding_schema_fails_closed(self) -> None:
        packet = prompt_registry_ops.build_grounding_packet()
        packet["schema_version"] = "prompt-registry-grounding/v999"
        gate = prompt_registry_ops.ground_prompt_proposal(
            fixture_draft(), "spec-architecture-prompts", packet
        )
        self.assertEqual(gate["status"], grounding.SCHEMA_MISMATCH)
        self.assertEqual(gate["reason"], "grounding_schema_mismatch")

    def test_stale_packet_blocks_side_effect_path(self) -> None:
        packet = prompt_registry_ops.build_grounding_packet()
        stale = copy.deepcopy(packet)
        stale["sources"][0]["sha256"] = "0" * 64
        stale["source_fingerprint"] = grounding.source_fingerprint(stale["sources"])
        stale["packet_fingerprint"] = grounding.packet_fingerprint(stale)
        with mock.patch.object(prompt_registry_ops, "_apply_prompt_record") as apply:
            with self.assertRaises(SystemExit):
                prompt_registry_ops.add_prompt(
                    fixture_draft(),
                    "spec-architecture-prompts",
                    dry_run=False,
                    grounding_packet=stale,
                )
            apply.assert_not_called()

    def test_valid_gate_reaches_side_effect_path_exactly_once_under_lock(self) -> None:
        packet = prompt_registry_ops.build_grounding_packet()
        events: list[str] = []

        @contextmanager
        def fake_lock(*args: object, **kwargs: object):
            events.append("lock-enter")
            try:
                yield Path("test-lock")
            finally:
                events.append("lock-exit")

        def fake_apply(*args: object, **kwargs: object) -> dict[str, str]:
            self.assertEqual(events, ["lock-enter"])
            events.append("apply")
            return {"status": "added-for-test"}

        with mock.patch.object(grounding, "registry_write_lock", fake_lock):
            with mock.patch.object(
                prompt_registry_ops, "_apply_prompt_record", side_effect=fake_apply
            ) as apply:
                result = prompt_registry_ops.add_prompt(
                    fixture_draft(),
                    "spec-architecture-prompts",
                    dry_run=False,
                    grounding_packet=packet,
                )
        self.assertEqual(result["status"], "added-for-test")
        apply.assert_called_once()
        gate = apply.call_args.args[3]
        self.assertEqual(gate["status"], grounding.GROUNDED_PASS)
        self.assertEqual(events, ["lock-enter", "apply", "lock-exit"])

    def test_registry_write_lock_fails_closed_on_contention(self) -> None:
        with grounding.registry_write_lock(REPO_ROOT, timeout_seconds=0.1):
            with self.assertRaises(grounding.GroundingLockError):
                with grounding.registry_write_lock(REPO_ROOT, timeout_seconds=0):
                    self.fail("second writer unexpectedly acquired the registry lock")

    def test_add_reports_grounding_failure_when_write_lock_is_unavailable(self) -> None:
        packet = prompt_registry_ops.build_grounding_packet()
        with mock.patch.object(
            grounding,
            "registry_write_lock",
            side_effect=grounding.GroundingLockError("busy"),
        ):
            with self.assertRaises(SystemExit) as raised:
                prompt_registry_ops.add_prompt(
                    fixture_draft(),
                    "spec-architecture-prompts",
                    dry_run=False,
                    grounding_packet=packet,
                )
        block = json.loads(str(raised.exception))
        self.assertEqual(block["status"], grounding.GROUNDING_FAILURE)
        self.assertEqual(block["reason"], "registry_write_lock_unavailable")

    def test_dry_run_carries_grounding_receipt_without_mutation(self) -> None:
        packet = prompt_registry_ops.build_grounding_packet()
        target = REPO_ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
        before = target.read_bytes()
        result = prompt_registry_ops.add_prompt(
            fixture_draft(),
            "spec-architecture-prompts",
            dry_run=True,
            grounding_packet=packet,
        )
        self.assertEqual(result["status"], "dry-run")
        self.assertEqual(result["grounding_gate"]["status"], grounding.GROUNDED_PASS)
        self.assertEqual(target.read_bytes(), before)

    def test_prompt_operations_contract_keeps_grounding_automatic_and_jit(self) -> None:
        text = SPEC.read_text(encoding="utf-8")
        for phrase in (
            "Exact prompt-contribution grounding",
            "prompt_registry_ops.py ground",
            "prompt_registry_ops.py check",
            "`add` repeats the gate internally",
            "GROUNDED_PASS",
            "stale or tampered",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
