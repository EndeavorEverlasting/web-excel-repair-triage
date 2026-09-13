from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry
import operant_version


class OperantProductIdentityTests(unittest.TestCase):
    def test_identity_contract_preserves_transition_boundary_and_version_authority(self) -> None:
        payload = json.loads(
            (ROOT / "harness/contracts/operant-product-identity.v1.json").read_text(encoding="utf-8")
        )
        version = str(operant_version.current_version())
        self.assertEqual(payload["schema_version"], "operant-product-identity/v1")
        self.assertEqual(payload["product_name"], "AFK Agent Flow")
        self.assertEqual(str(operant_version.SemVer.parse(version)), version)
        self.assertEqual(payload["product_version"], version)
        self.assertEqual(payload["compatibility"]["visible_version"], version)
        self.assertEqual(payload["release_versioning"]["authority_file"], "OPERANT_VERSION")
        self.assertEqual(payload["release_versioning"]["scheme"], "semver")
        self.assertEqual(payload["release_versioning"]["bootstrap"]["cutover_version"], "0.2.0")
        self.assertEqual(
            payload["release_versioning"]["bootstrap"]["identity_merge_sha"],
            "781616a1a42893fb5b521e41b217f5cef04b2701",
        )
        self.assertEqual(payload["authority"]["target_repository"], "UnderDeskDev/AFK-Agent-Flow")
        self.assertEqual(payload["authority"]["target_repository_state"], "not-created-or-unproven")
        self.assertTrue(payload["compatibility"]["internal_path_renames_deferred"])
        self.assertIn("web/prompt-kit/index.html", payload["compatibility"]["preserve_paths"])
        self.assertIn("Prompt Kit", payload["legacy_identity"]["names"])

    def test_visible_brand_is_derived_from_canonical_version(self) -> None:
        version = str(operant_version.current_version())
        html = build_prompt_kit_registry.render()
        self.assertIn(f"<title>AFK Agent Flow {version}</title>", html)
        self.assertIn(f"AFK Agent Flow <span>{version}</span>", html)
        self.assertIn(f'id="versionBadge">{version}</div>', html)
        self.assertIn("Capabilities · Skills · Implementations · Evidence", html)
        self.assertNotIn("<title>AI Harness Prompt Kit v40</title>", html)
        self.assertTrue((ROOT / "web/prompt-kit").is_dir())

    def test_governance_and_access_surface_name_afk_agent_flow(self) -> None:
        governance = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        access = (ROOT / "PROMPT_KIT_ACCESS.md").read_text(encoding="utf-8")
        self.assertIn("**AFK Agent Flow** is the operator-approved product identity", governance)
        self.assertIn("`UnderDeskDev/AFK-Agent-Flow`", governance)
        self.assertIn("legacy `operant` / `prompt-kit` paths", governance)
        self.assertTrue(access.startswith("# Get AFK Agent Flow"))
        self.assertIn("compatibility and historical release identifiers", access)

    def test_pre_one_semver_bump_matrix_is_deterministic(self) -> None:
        current = operant_version.SemVer.parse("0.2.0")
        cases = {
            "feat(operant): add keyboard route": "minor",
            "fix(operant): repair launcher": "patch",
            "perf(operant): reduce startup work": "patch",
            "docs(operant): explain routing": None,
            "test(operant): lock routing": None,
            "refactor(operant): extract helper": None,
            "feat(operant)!: replace public route": "minor",
        }
        for message, expected in cases.items():
            with self.subTest(message=message):
                self.assertEqual(operant_version.classify_message(message, current), expected)
        self.assertEqual(
            operant_version.classify_message(
                "feat(operant)!: break stable API",
                operant_version.SemVer.parse("1.2.3"),
            ),
            "major",
        )

    def test_classifier_consumes_machine_owned_policy(self) -> None:
        policy = json.loads(
            (ROOT / "harness/contracts/operant-product-identity.v1.json").read_text(encoding="utf-8")
        )["release_versioning"]
        policy = json.loads(json.dumps(policy))
        policy["pre_1_policy"]["feature"] = "patch"
        self.assertEqual(
            operant_version.classify_message(
                "feat(operant): policy-driven probe",
                operant_version.SemVer.parse("0.2.0"),
                policy,
            ),
            "patch",
        )

    def test_highest_bump_and_calculation_are_idempotent(self) -> None:
        current = operant_version.SemVer.parse("0.2.0")
        release_type = operant_version.highest_release_type([None, "patch", "minor", "patch"])
        self.assertEqual(release_type, "minor")
        first = operant_version.derive_next_version(current, release_type)
        second = operant_version.derive_next_version(current, release_type)
        self.assertEqual(first, operant_version.SemVer.parse("0.3.0"))
        self.assertEqual(first, second)

    def test_stable_major_changelog_is_not_mislabeled_minor(self) -> None:
        section = operant_version._changelog_section(
            {
                "relevant_commits": [
                    {
                        "sha": "a" * 40,
                        "subject": "feat(operant)!: replace stable API",
                        "release_type": "major",
                    }
                ]
            },
            "2.0.0",
        )
        self.assertIn("### Breaking changes", section)
        self.assertNotIn("### Features / breaking pre-1.0 changes", section)

    def test_no_bump_and_release_relevance_do_not_confuse_generated_or_other_products(self) -> None:
        self.assertFalse(
            operant_version.is_release_relevant(
                ["web/prompt-kit/index.html"], "chore(operant): rebuild generated site"
            )
        )
        self.assertTrue(
            operant_version.is_release_relevant(
                ["registry/prompts/spec-architecture-prompts.v1.json"],
                "feat(prompt-kit): add version policy",
            )
        )
        self.assertTrue(
            operant_version.is_release_relevant(
                ["docs/prompts.json"],
                "feat(prompt-kit): refine existing prompt body",
            )
        )
        self.assertTrue(
            operant_version.is_release_relevant(
                ["docs/reference.json"],
                "feat(prompt-kit): extend reference record",
            )
        )
        self.assertFalse(
            operant_version.is_release_relevant(
                ["triage/roster_log_v2/builder.py"], "feat(roster-v2): add report"
            )
        )
        self.assertTrue(
            operant_version.is_release_relevant(
                ["harness/manifest.v1.json"], "feat(operant): register capability"
            )
        )
        self.assertFalse(
            operant_version.is_release_relevant(
                ["harness/manifest.v1.json"], "feat(roster-v2): register report"
            )
        )

    def test_candidate_changelog_replacement_preserves_released_history(self) -> None:
        existing = (
            "# Operant Changelog\n\n"
            "Human-facing Operant releases. Git commit/artifact identity remains the forensic freshness proof.\n\n"
            "## 0.2.1 - 2026-09-08\n\n"
            "### Fixes / performance\n\n"
            "- fix(operant): old candidate (`aaaaaaaa`)\n\n"
            "## 0.2.0 - 2026-09-01\n\n"
            "- Cutover release.\n"
        )
        refreshed = operant_version.replace_candidate_changelog_section(
            existing,
            {
                "relevant_commits": [
                    {
                        "sha": "b" * 40,
                        "subject": "feat(operant): later accepted work",
                        "release_type": "minor",
                    }
                ]
            },
            "0.3.0",
            previous_versions=["0.2.1"],
        )
        self.assertIn("## 0.3.0 - ", refreshed)
        self.assertIn("feat(operant): later accepted work (`bbbbbbbb`)", refreshed)
        self.assertNotIn("## 0.2.1 - ", refreshed)
        self.assertIn("## 0.2.0 - 2026-09-01", refreshed)
        self.assertIn("- Cutover release.", refreshed)

    def test_stale_release_candidate_version_is_rejected(self) -> None:
        self.assertEqual(
            operant_version.validate_release_candidate(base="HEAD", head="HEAD"),
            [],
        )
        with mock.patch.object(
            operant_version,
            "_run_git",
            side_effect=["a" * 40, "b" * 40],
        ):
            with mock.patch.object(
                operant_version,
                "_version_at_ref",
                return_value=operant_version.SemVer.parse("0.2.0"),
            ):
                with mock.patch.object(
                    operant_version,
                    "current_version",
                    return_value=operant_version.SemVer.parse("9.9.9"),
                ):
                    with mock.patch.object(
                        operant_version,
                        "plan",
                        return_value={
                            "schema_version": "operant-version-plan/v1",
                            "current_version": "0.2.0",
                            "release_type": "patch",
                            "next_version": "0.2.1",
                            "relevant_commits": [
                                {
                                    "sha": "c" * 40,
                                    "subject": "fix(operant): example",
                                    "release_type": "patch",
                                }
                            ],
                        },
                    ):
                        with mock.patch.object(
                            operant_version.subprocess,
                            "run",
                            return_value=mock.Mock(returncode=0),
                        ):
                            stale = operant_version.validate_release_candidate(
                                base="origin/main", head="HEAD"
                            )
        self.assertTrue(
            any("stale Operant release candidate version" in item for item in stale)
        )

    def test_workflow_refreshes_open_release_pr_and_pins_dispatch_to_main(self) -> None:
        workflow = (
            ROOT / ".github/workflows/operant-versioning.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("ref: main", workflow)
        self.assertIn("Refreshing open Operant release PR branch in place", workflow)
        self.assertIn("validate-release-candidate", workflow)
        self.assertIn("docs/prompts.json", workflow)
        self.assertIn("docs/reference.json", workflow)
        self.assertNotIn(
            'echo "An Operant release PR already owns the pending release boundary',
            workflow,
        )

    def test_ambiguous_relevant_commit_fails_closed(self) -> None:
        with self.assertRaises(operant_version.VersioningError):
            operant_version.classify_message(
                "made operant better", operant_version.SemVer.parse("0.2.0")
            )
        with self.assertRaises(operant_version.VersioningError):
            operant_version.classify_message(
                "banana(operant): mystery behavior", operant_version.SemVer.parse("0.2.0")
            )

    def test_released_version_reuse_is_rejected(self) -> None:
        with self.assertRaises(operant_version.VersioningError):
            operant_version.assert_version_not_released(
                "0.2.1", tags=["operant-v0.2.0", "operant-v0.2.1"]
            )
        operant_version.assert_version_not_released(
            "0.2.2", tags=["operant-v0.2.0", "operant-v0.2.1"]
        )

    def test_missing_generated_site_is_version_drift(self) -> None:
        with mock.patch.object(
            operant_version,
            "GENERATED_SITE",
            ROOT / "web/prompt-kit/definitely-missing-operant-site.html",
        ):
            self.assertIn("generated Operant site is missing", operant_version.validate())

    def test_multi_file_version_write_rolls_back_on_replace_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "first.txt"
            second = root / "second.txt"
            first.write_text("old-first\n", encoding="utf-8")
            second.write_text("old-second\n", encoding="utf-8")
            real_replace = os.replace
            failed = False

            def fail_second_once(source: os.PathLike[str] | str, destination: os.PathLike[str] | str) -> None:
                nonlocal failed
                if Path(destination) == second and not failed:
                    failed = True
                    raise OSError("simulated second replace failure")
                real_replace(source, destination)

            with mock.patch.object(operant_version.os, "replace", side_effect=fail_second_once):
                with self.assertRaises(operant_version.VersioningError):
                    operant_version._atomic_write_many(
                        {first: "new-first\n", second: "new-second\n"}
                    )

            self.assertEqual(first.read_text(encoding="utf-8"), "old-first\n")
            self.assertEqual(second.read_text(encoding="utf-8"), "old-second\n")

    def test_validator_has_no_version_drift(self) -> None:
        self.assertEqual(operant_version.validate(), [])


if __name__ == "__main__":
    unittest.main()
