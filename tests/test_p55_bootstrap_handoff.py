from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "p55_bootstrap_handoff",
    ROOT / "scripts" / "p55_bootstrap_handoff.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


def base_manifest() -> dict:
    return {
        "schema_version": "p55-bootstrap-handoff/v1",
        "handoff_id": "test-convergence",
        "plan_artifact": {
            "repository": "example/planning-owner",
            "ref": "plan/example",
            "path": "docs/plans/convergence.json",
            "write_authority": "PLAN_ONLY",
        },
        "donors": [
            {"repository": "example/a", "ref": "main", "sha": "a" * 40},
            {"repository": "example/b", "ref": "main", "sha": "b" * 40},
        ],
        "destination": {
            "name": "example-c",
            "owner": "example",
            "visibility": "PRIVATE",
            "proposal_state": "operator_proposed",
            "provider_state": "AVAILABLE",
        },
        "authority": {
            "operator_approved": False,
            "execution_authorization": False,
            "provenance": ["operator proposed name; approval still outstanding"],
        },
        "capability_dispositions": [
            {"capability": "example-capability", "disposition": "KEEP"}
        ],
        "route": "P55_CREATE",
        "next_owner": "P55",
        "proof_ceiling": "planning and provider-state proof only",
    }


class P55BootstrapHandoffTests(unittest.TestCase):
    def test_available_destination_routes_to_p55_without_minting_authority(self) -> None:
        receipt = MOD.validate_manifest(base_manifest())
        self.assertEqual(receipt["route"], "P55_CREATE")
        self.assertFalse(receipt["mutation_authorized"])

    def test_existing_owned_destination_routes_to_integration_not_creation(self) -> None:
        manifest = base_manifest()
        manifest["destination"]["provider_state"] = "EXISTS_OWNED"
        manifest["route"] = "INTEGRATE_EXISTING"
        manifest["next_owner"] = "P07"
        receipt = MOD.validate_manifest(manifest)
        self.assertEqual(receipt["next_owner"], "P07")
        self.assertFalse(receipt["mutation_authorized"])

    def test_existing_owned_destination_cannot_route_to_p55(self) -> None:
        manifest = base_manifest()
        manifest["destination"]["provider_state"] = "EXISTS_OWNED"
        with self.assertRaisesRegex(MOD.HandoffError, "P55_CREATE requires"):
            MOD.validate_manifest(manifest)

    def test_provider_availability_does_not_create_authority(self) -> None:
        manifest = base_manifest()
        manifest["authority"]["operator_approved"] = False
        manifest["authority"]["execution_authorization"] = False
        receipt = MOD.validate_manifest(manifest)
        self.assertFalse(receipt["mutation_authorized"])

    def test_conflict_or_unknown_provider_state_must_block(self) -> None:
        for state in (
            "UNVERIFIED",
            "EXISTS_CONFLICT",
            "UNKNOWN_AUTH",
            "UNKNOWN_PERMISSION",
            "UNKNOWN_NETWORK",
            "UNKNOWN_PROVIDER",
        ):
            with self.subTest(state=state):
                manifest = base_manifest()
                manifest["destination"]["provider_state"] = state
                manifest["route"] = "BLOCKED"
                manifest["next_owner"] = "BLOCKED"
                receipt = MOD.validate_manifest(manifest)
                self.assertEqual(receipt["route"], "BLOCKED")

    def test_blocked_cannot_hide_available_destination(self) -> None:
        manifest = base_manifest()
        manifest["route"] = "BLOCKED"
        manifest["next_owner"] = "BLOCKED"
        with self.assertRaisesRegex(MOD.HandoffError, "may not hide"):
            MOD.validate_manifest(manifest)

    def test_plan_artifact_is_mandatory_durable_owner(self) -> None:
        manifest = base_manifest()
        manifest["plan_artifact"]["path"] = ""
        with self.assertRaisesRegex(MOD.HandoffError, "plan_artifact.path"):
            MOD.validate_manifest(manifest)

    def test_plan_only_write_authority_is_explicit_and_bounded(self) -> None:
        manifest = base_manifest()
        manifest["plan_artifact"]["write_authority"] = "PLAN_ONLY"
        receipt = MOD.validate_manifest(manifest)
        self.assertEqual(receipt["status"], "PASS")
        manifest["plan_artifact"]["write_authority"] = "READ_ONLY"
        with self.assertRaisesRegex(MOD.HandoffError, "plan_artifact.write_authority"):
            MOD.validate_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
