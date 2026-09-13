from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_prompt_kit_privacy_storage as privacy_storage


class PromptKitPrivacyStorageTests(unittest.TestCase):
    def load_contract(self) -> dict:
        return json.loads(privacy_storage.CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_focused_validator_passes(self) -> None:
        self.assertEqual(privacy_storage.main(["--summary"]), 0)

    def test_four_data_planes_are_exact_and_separate(self) -> None:
        payload = self.load_contract()
        summary = privacy_storage.validate_contract(payload)
        self.assertEqual(set(summary["planes"]), privacy_storage.REQUIRED_PLANES)
        self.assertFalse(
            payload["data_plane_architecture"]["planes"]["private_sync"][
                "prompt_kit_owned_backend_required"
            ]
        )
        self.assertFalse(
            payload["data_plane_architecture"]["planes"]["collective_learning"][
                "v1_network_ingestion_required"
            ]
        )

    def test_pages_bundle_matches_real_deployment_workflow(self) -> None:
        privacy_storage.validate_repository_surfaces()
        payload = self.load_contract()
        bundle = payload["deployment_surfaces"]["github_pages"]["bundle"]
        actual = {
            (item["public_path"], item["source"], item["kind"])
            for item in bundle
        }
        self.assertEqual(actual, privacy_storage.EXPECTED_PAGES_BUNDLE)

    def test_private_state_is_not_a_repository_or_pages_surface(self) -> None:
        payload = self.load_contract()
        repository = payload["deployment_surfaces"]["repository_authority"]
        pages = payload["deployment_surfaces"]["github_pages"]
        self.assertFalse(repository["private_user_data_allowed"])
        published_forbidden = "\n".join(pages["must_never_publish"]).lower()
        for phrase in (
            "personal state",
            "local journal",
            "encrypted save",
            "device",
            "project",
            "encryption keys",
            "privacyreducer",
        ):
            self.assertIn(phrase, published_forbidden)

    def test_sync_capsule_is_positive_allowlist_and_excludes_raw_history(self) -> None:
        payload = self.load_contract()
        capsule = payload["sync_capsule_contract"]
        self.assertEqual(capsule["serialization"], "positive-allowlist-only")
        self.assertTrue(capsule["encryption_required_before_transport"])
        self.assertEqual(set(capsule["allowed_fields"]), privacy_storage.REQUIRED_SYNC_ALLOWED_FIELDS)
        forbidden = "\n".join(capsule["forbidden_pre_encryption"]).lower()
        for phrase in (
            "raw prompt",
            "local journal",
            "repository",
            "session",
            "device",
            "privacyreducer",
            "encryption keys",
        ):
            self.assertIn(phrase, forbidden)

    def test_raw_history_cannot_be_added_to_sync_allowlist(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["sync_capsule_contract"]["allowed_fields"].append("local_journal")
        with self.assertRaisesRegex(privacy_storage.PrivacyStorageError, "sync capsule allowed fields drifted"):
            privacy_storage.validate_contract(payload)

    def test_identity_cannot_be_added_to_collective_output(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["privacy_reducer_contract"]["output_allowlist"].append("user_id")
        with self.assertRaisesRegex(privacy_storage.PrivacyStorageError, "output allowlist drifted"):
            privacy_storage.validate_contract(payload)

    def test_session_rejection_contract_fails_closed_if_session_id_is_removed(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["privacy_reducer_contract"]["forbidden_output_classes"]["session"].remove("session_id")
        with self.assertRaisesRegex(privacy_storage.PrivacyStorageError, "forbidden field missing: session_id"):
            privacy_storage.validate_contract(payload)

    def test_project_rejection_contract_fails_closed_if_repository_is_removed(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["privacy_reducer_contract"]["forbidden_output_classes"]["project"].remove("repository")
        with self.assertRaisesRegex(privacy_storage.PrivacyStorageError, "forbidden field missing: repository"):
            privacy_storage.validate_contract(payload)

    def test_device_and_private_sync_identifiers_remain_forbidden(self) -> None:
        payload = self.load_contract()
        forbidden = payload["privacy_reducer_contract"]["forbidden_output_classes"]
        self.assertIn("device_id", forbidden["device"])
        self.assertIn("installation_id", forbidden["persistent_pseudonym"])
        self.assertIn("vault_id", forbidden["private_sync"])
        self.assertTrue(set(payload["privacy_reducer_contract"]["output_allowlist"]).isdisjoint(
            {value for values in forbidden.values() for value in values}
        ))

    def test_local_batching_cannot_be_weakened_silently(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["privacy_reducer_contract"]["batching"]["minimum_local_count"] = 1
        with self.assertRaisesRegex(privacy_storage.PrivacyStorageError, "local batching profile drifted"):
            privacy_storage.validate_contract(payload)

    def test_prompt_kit_owned_backend_cannot_become_required_in_v1(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["v1_backend_policy"]["prompt_kit_owned_backend_required"] = True
        with self.assertRaisesRegex(privacy_storage.PrivacyStorageError, "no-Prompt-Kit-backend-required"):
            privacy_storage.validate_contract(payload)

    def test_future_sync_cannot_be_claimed_implemented_by_static_contract(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["v1_backend_policy"]["future_hosted_sync_status"] = "implemented"
        with self.assertRaisesRegex(privacy_storage.PrivacyStorageError, "overclaims implementation"):
            privacy_storage.validate_contract(payload)


if __name__ == "__main__":
    unittest.main()
