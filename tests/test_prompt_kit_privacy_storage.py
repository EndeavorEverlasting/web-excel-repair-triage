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

    def test_authoritative_prohibition_cannot_be_reversed_by_matching_words(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["data_plane_architecture"]["planes"]["prompt_canon"]["must_never_receive"][0] = (
            "user identity may be exported"
        )
        with self.assertRaisesRegex(privacy_storage.PrivacyStorageError, "authoritative exact policy set"):
            privacy_storage.validate_contract(payload)

    def test_pages_bundle_matches_real_deployment_workflow(self) -> None:
        privacy_storage.validate_repository_surfaces()
        payload = self.load_contract()
        bundle = payload["deployment_surfaces"]["github_pages"]["bundle"]
        actual = {
            (item["public_path"], item["source"], item["kind"])
            for item in bundle
        }
        self.assertEqual(actual, privacy_storage.EXPECTED_PAGES_BUNDLE)

    def test_privacy_workflow_watches_publication_and_owner_inputs(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "prompt-kit-privacy-storage.yml").read_text(encoding="utf-8")
        required = (
            "docs/prompts.json",
            "registry/prompts/**",
            "harness/artifacts.v1.json",
            "harness/contracts/prompt-kit-cross-device-access.v1.json",
            "scripts/build_prompt_kit_registry.py",
            "scripts/validate_prompt_kit_cross_device_access.py",
            "tests/test_prompt_kit_cross_device_access.py",
            "web/prompt-kit-mobile/**",
            "web/prompt-kit/**",
            "web/prompt-kit-legacy-redirect/**",
            "web/operant-legacy-redirect/**",
            "web/roster-log-v2/**",
            ".github/workflows/prompt-kit-pages.yml",
        )
        for path in required:
            with self.subTest(path=path):
                self.assertGreaterEqual(workflow.count(f"- {path}"), 2)

    def test_public_source_roots_have_no_tracked_private_artifact_paths(self) -> None:
        tracked = privacy_storage.tracked_public_files()
        self.assertTrue(tracked)
        privacy_storage.validate_public_tracked_paths(tracked)

    def test_public_path_classifier_rejects_private_and_secret_artifacts(self) -> None:
        rejected = (
            "web/prompt-kit-mobile/secrets.json",
            "web/prompt-kit/example.pkenc",
            "web/prompt-kit-mobile/.promptkit/state.json",
            "web/prompt-kit/promptkit.db",
            "web/prompt-kit-mobile/saves/state.json",
            "web/prompt-kit-mobile/.env.production",
            "web/prompt-kit/private.promptkit-key",
            "web/prompt-kit-mobile/personal_state/state.json",
            "web/prompt-kit-mobile/Local_Journal/history.txt",
            "web/prompt-kit-mobile/privacy_reducer_buffer/counts.json",
            "web/prompt-kit-mobile/Secrets/readme.txt",
        )
        for path in rejected:
            with self.subTest(path=path):
                self.assertTrue(privacy_storage.is_forbidden_public_path(path))

        allowed = (
            "web/prompt-kit-mobile/index.html",
            "web/prompt-kit/resources.v1.json",
            "web/roster-log-v2/index.html",
        )
        for path in allowed:
            with self.subTest(path=path):
                self.assertFalse(privacy_storage.is_forbidden_public_path(path))

    def test_tracked_private_artifact_path_fails_closed(self) -> None:
        with self.assertRaisesRegex(privacy_storage.PrivacyStorageError, "tracked private/secret-like artifacts"):
            privacy_storage.validate_public_tracked_paths(
                ["web/prompt-kit-mobile/index.html", "web/prompt-kit-mobile/.promptkit/state.json"]
            )

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


    def test_conversation_to_repository_promotion_is_impersonal_and_all_of(self) -> None:
        payload = self.load_contract()
        promotion = payload["conversation_repository_promotion_contract"]
        states = promotion["states"]
        self.assertFalse(states["private_user_context"]["repository_eligible"])
        self.assertFalse(states["working_specification"]["repository_eligible"])
        self.assertFalse(states["repository_candidate"]["repository_eligible"])
        self.assertTrue(states["repository_truth"]["repository_eligible"])
        self.assertEqual(promotion["promotion_gate"]["mode"], "all-of")
        self.assertEqual(
            set(promotion["promotion_gate"]["required_checks"]),
            privacy_storage.EXPECTED_PROMOTION_GATE_CHECKS,
        )
        self.assertIn(
            "raw user messages or conversation transcripts",
            promotion["repository_worthy_artifacts"]["forbidden"],
        )
        self.assertIn(
            "learning records, quiz results, mistakes or mastery history",
            promotion["repository_worthy_artifacts"]["forbidden"],
        )
        self.assertIn(
            "repository requirements and constraints",
            promotion["repository_worthy_artifacts"]["allowed"],
        )
        self.assertFalse(promotion["provenance_policy"]["personal_identity_required"])
        self.assertIn("Interrogate privately; publish impersonally.", promotion["governing_invariants"])

    def test_conversation_promotion_cannot_weaken_impersonal_gate(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        checks = payload["conversation_repository_promotion_contract"]["promotion_gate"]["required_checks"]
        checks.remove("impersonal_repository_statement")
        checks.append("raw_dialogue_is_repository_truth")
        with self.assertRaisesRegex(
            privacy_storage.PrivacyStorageError,
            "authoritative exact policy set",
        ):
            privacy_storage.validate_contract(payload)

    def test_learning_or_reasoning_state_cannot_be_reclassified_as_repo_artifact(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        forbidden = payload["conversation_repository_promotion_contract"]["repository_worthy_artifacts"]["forbidden"]
        forbidden.remove("personal reasoning history or hidden chain-of-thought")
        with self.assertRaisesRegex(
            privacy_storage.PrivacyStorageError,
            "authoritative exact policy set",
        ):
            privacy_storage.validate_contract(payload)


if __name__ == "__main__":
    unittest.main()
