from __future__ import annotations

import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "p55_bootstrap_handoff",
    ROOT / "scripts" / "p55_bootstrap_handoff.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def provider_evidence(state: str, owner: str = "example", name: str = "example-c") -> dict:
    return {
        "provider": "github",
        "owner": owner,
        "name": name,
        "provider_state": state,
        "observed_at": now_iso(),
        "evidence_ref": "provider-api:test",
    }


def base_manifest() -> dict:
    return {
        "schema_version": "p55-bootstrap-handoff/v1",
        "handoff_id": "test-convergence",
        "plan_artifact": {
            "repository": ".",
            "ref": "HEAD",
            "path": "docs/plans/AFK_FACTORY_INTERFACE_CONVERGENCE_SPRINT_MAP.md",
            "write_authority": "PLAN_ONLY",
            "proof": {
                "kind": "LOCAL_TRACKED_FILE",
                "evidence_path": "docs/plans/AFK_FACTORY_INTERFACE_CONVERGENCE_SPRINT_MAP.md",
            },
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
            "provider_evidence": provider_evidence("AVAILABLE"),
        },
        "authority": {
            "operator_approved": False,
            "execution_authorization": False,
            "evidence": {
                "operator_approved": None,
                "execution_authorization": None,
            },
        },
        "capability_dispositions": [
            {"capability": "example-capability", "disposition": "KEEP"}
        ],
        "route": "P55_CREATE",
        "next_owner": "P55",
        "proof_ceiling": "planning and provider-state proof only",
    }


def authority_record(decision: str, manifest: dict) -> dict:
    destination = manifest["destination"]
    return {
        "decision": decision,
        "owner": destination["owner"],
        "name": destination["name"],
        "visibility": destination["visibility"],
        "route": manifest["route"],
        "recorded_at": now_iso(),
        "evidence_ref": f"operator-decision:{decision}",
    }


class P55BootstrapHandoffTests(unittest.TestCase):
    def test_available_destination_routes_to_p55_without_minting_authority(self) -> None:
        receipt = MOD.validate_manifest(base_manifest())
        self.assertEqual(receipt["route"], "P55_CREATE")
        self.assertFalse(receipt["authority_evidence_complete"])
        self.assertFalse(receipt["mutation_authorized"])

    def test_existing_owned_destination_routes_to_integration_not_creation(self) -> None:
        manifest = base_manifest()
        manifest["destination"]["provider_state"] = "EXISTS_OWNED"
        manifest["destination"]["provider_evidence"] = provider_evidence("EXISTS_OWNED")
        manifest["route"] = "INTEGRATE_EXISTING"
        manifest["next_owner"] = "P07"
        receipt = MOD.validate_manifest(manifest)
        self.assertEqual(receipt["next_owner"], "P07")
        self.assertFalse(receipt["mutation_authorized"])

    def test_existing_owned_destination_cannot_route_to_p55(self) -> None:
        manifest = base_manifest()
        manifest["destination"]["provider_state"] = "EXISTS_OWNED"
        manifest["destination"]["provider_evidence"] = provider_evidence("EXISTS_OWNED")
        with self.assertRaisesRegex(MOD.HandoffError, "P55_CREATE requires"):
            MOD.validate_manifest(manifest)

    def test_actionable_provider_state_requires_destination_bound_fresh_evidence(self) -> None:
        manifest = base_manifest()
        manifest["destination"]["provider_evidence"] = None
        with self.assertRaisesRegex(MOD.HandoffError, "requires destination-bound provider evidence"):
            MOD.validate_manifest(manifest)

        manifest = base_manifest()
        manifest["destination"]["provider_evidence"]["owner"] = "wrong-owner"
        with self.assertRaisesRegex(MOD.HandoffError, "does not match destination.owner"):
            MOD.validate_manifest(manifest)

        manifest = base_manifest()
        manifest["destination"]["provider_evidence"]["observed_at"] = "2000-01-01T00:00:00Z"
        with self.assertRaisesRegex(MOD.HandoffError, "stale or future-dated"):
            MOD.validate_manifest(manifest)

    def test_provider_availability_does_not_create_authority(self) -> None:
        receipt = MOD.validate_manifest(base_manifest())
        self.assertFalse(receipt["authority_evidence_complete"])
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
                manifest["destination"]["provider_evidence"] = None
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
        manifest["plan_artifact"]["path"] = "docs/plans/DOES_NOT_EXIST.md"
        manifest["plan_artifact"]["proof"]["evidence_path"] = "docs/plans/DOES_NOT_EXIST.md"
        with self.assertRaisesRegex(MOD.HandoffError, "proof evidence must exist"):
            MOD.validate_manifest(manifest)

    def test_local_plan_ref_must_resolve_and_match_the_handed_off_blob(self) -> None:
        manifest = base_manifest()
        manifest["plan_artifact"]["ref"] = "refs/heads/definitely-missing-p143-test-ref"
        with self.assertRaisesRegex(MOD.HandoffError, "does not resolve to a commit"):
            MOD.validate_manifest(manifest)

    def test_plan_only_write_authority_is_explicit_and_bounded(self) -> None:
        manifest = base_manifest()
        receipt = MOD.validate_manifest(manifest)
        self.assertEqual(receipt["status"], "PASS")
        manifest["plan_artifact"]["write_authority"] = "READ_ONLY"
        with self.assertRaisesRegex(MOD.HandoffError, "plan_artifact.write_authority"):
            MOD.validate_manifest(manifest)

    def test_donor_sha_must_be_pinned_commit(self) -> None:
        manifest = base_manifest()
        manifest["donors"][0]["sha"] = "main"
        with self.assertRaisesRegex(MOD.HandoffError, "40-hex commit"):
            MOD.validate_manifest(manifest)

    def test_capability_dispositions_are_closed_and_unique(self) -> None:
        manifest = base_manifest()
        manifest["capability_dispositions"][0]["disposition"] = "MAYBE"
        with self.assertRaisesRegex(MOD.HandoffError, "invalid capability disposition"):
            MOD.validate_manifest(manifest)
        manifest = base_manifest()
        manifest["capability_dispositions"].append(
            {"capability": "example-capability", "disposition": "KEEP"}
        )
        with self.assertRaisesRegex(MOD.HandoffError, "duplicate capability disposition"):
            MOD.validate_manifest(manifest)

    def test_asserted_authority_requires_separate_destination_bound_evidence(self) -> None:
        manifest = base_manifest()
        manifest["authority"]["operator_approved"] = True
        with self.assertRaisesRegex(MOD.HandoffError, "operator_approved=true requires"):
            MOD.validate_manifest(manifest)

        manifest = base_manifest()
        manifest["authority"]["operator_approved"] = True
        manifest["authority"]["evidence"]["operator_approved"] = authority_record(
            "operator_approved", manifest
        )
        manifest["authority"]["evidence"]["operator_approved"]["name"] = "other"
        with self.assertRaisesRegex(MOD.HandoffError, "does not match destination.name"):
            MOD.validate_manifest(manifest)

    def test_complete_authority_evidence_is_preserved_but_never_mints_mutation(self) -> None:
        manifest = base_manifest()
        manifest["authority"]["operator_approved"] = True
        manifest["authority"]["execution_authorization"] = True
        manifest["authority"]["evidence"]["operator_approved"] = authority_record(
            "operator_approved", manifest
        )
        manifest["authority"]["evidence"]["execution_authorization"] = authority_record(
            "execution_authorization", manifest
        )
        receipt = MOD.validate_manifest(manifest)
        self.assertTrue(receipt["authority_evidence_complete"])
        self.assertFalse(receipt["mutation_authorized"])

    def test_blocked_route_never_authorizes_mutation(self) -> None:
        manifest = base_manifest()
        manifest["destination"]["provider_state"] = "UNKNOWN_PROVIDER"
        manifest["destination"]["provider_evidence"] = None
        manifest["route"] = "BLOCKED"
        manifest["next_owner"] = "BLOCKED"
        manifest["authority"]["operator_approved"] = True
        manifest["authority"]["execution_authorization"] = True
        manifest["authority"]["evidence"]["operator_approved"] = authority_record(
            "operator_approved", manifest
        )
        manifest["authority"]["evidence"]["execution_authorization"] = authority_record(
            "execution_authorization", manifest
        )
        receipt = MOD.validate_manifest(manifest)
        self.assertFalse(receipt["mutation_authorized"])


if __name__ == "__main__":
    unittest.main()
