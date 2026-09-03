from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_prompt_kit_release_identity as validator


class PromptKitReleaseIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self._seed_fixture()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, relative: str | Path, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def write_bytes(self, relative: str | Path, payload: bytes) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    def copy(self, relative: str | Path) -> None:
        relative = Path(relative)
        destination = self.root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)

    def dump(self, relative: str | Path, payload: dict) -> None:
        self.write(relative, json.dumps(payload, indent=2) + "\n")

    def _seed_fixture(self) -> None:
        contract = json.loads((ROOT / validator.CONTRACT_REL).read_text(encoding="utf-8"))
        self.dump(validator.CONTRACT_REL, contract)
        self.dump(
            validator.ARTIFACTS_REL,
            {
                "artifacts": [
                    {
                        "id": "prompt-kit-website",
                        "canonical_path": validator.CANONICAL_ARTIFACT,
                        "tracking_policy": "Tracked deterministic output; delivery surfaces may expose this same canonical release without creating a second editable Prompt Kit.",
                        "delivery_surfaces": [
                            validator.CANONICAL_PUBLIC_URL,
                            "https://endeavoreverlasting.github.io/web-excel-repair-triage/",
                            "Open-Latest-PromptKit.cmd",
                        ],
                    }
                ]
            },
        )
        self.dump(
            validator.PORTABILITY_CONTRACT_REL,
            {
                "integration": {"canonical_site": validator.CANONICAL_ARTIFACT},
                "artifact_rules": {"portable_runtime_artifact": {"source": validator.CANONICAL_ARTIFACT}},
            },
        )
        self.dump(
            validator.FRESHNESS_CONTRACT_REL,
            {
                "freshness_routes": {"browser-use": f"Open {validator.CANONICAL_PUBLIC_URL} and use it."},
                "anti_patterns": ["Assuming a version label is current without checking the canonical latest route."],
            },
        )
        self.copy(validator.PAGES_WORKFLOW_REL)
        self.copy(validator.PORTABLE_BUILDER_REL)
        self.copy(Path("web/prompt-kit/resources.v1.json"))
        self.write(validator.PORTABLE_RUNTIME_REL, "// prompt-kit-favorites/v1\n")
        self.write(validator.CANONICAL_ARTIFACT, "<!doctype html><body><title>Prompt Kit</title></body>\n")

    def assertPasses(self) -> None:
        report = validator.build_report(self.root)
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(report["failure_count"], 0)
        self.assertTrue(report["canonical_artifact_sha256"])
        self.assertTrue(report["canonical_worktree_sha256"])

    def test_fixture_passes(self) -> None:
        self.assertPasses()

    def test_missing_canonical_artifact_fails_closed(self) -> None:
        (self.root / validator.CANONICAL_ARTIFACT).unlink()
        report = validator.build_report(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertIsNone(report["canonical_artifact_sha256"])
        self.assertIsNone(report["canonical_worktree_sha256"])
        self.assertIn("canonical artifact is missing", json.dumps(report))

    def test_artifact_registry_cannot_name_a_second_canonical_site(self) -> None:
        payload = json.loads((self.root / validator.ARTIFACTS_REL).read_text(encoding="utf-8"))
        payload["artifacts"][0]["canonical_path"] = "web/local/index.html"
        self.dump(validator.ARTIFACTS_REL, payload)
        report = validator.build_report(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("canonical path drifted", json.dumps(report))

    def test_pages_must_execute_published_to_canonical_comparison(self) -> None:
        path = self.root / validator.PAGES_WORKFLOW_REL
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            '          cmp "$SITE_ROOT/prompt-kit/index.html" web/prompt-kit/index.html',
            '          # cmp "$SITE_ROOT/prompt-kit/index.html" web/prompt-kit/index.html',
        )
        path.write_text(text, encoding="utf-8")
        report = validator.build_report(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("executable canonical parity", json.dumps(report))

    def test_pages_markers_outside_build_step_do_not_satisfy_gate(self) -> None:
        path = self.root / validator.PAGES_WORKFLOW_REL
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            '          cmp "$SITE_ROOT/prompt-kit/index.html" web/prompt-kit/index.html',
            '          echo "preview only"',
        )
        text += '\n# cmp "$SITE_ROOT/prompt-kit/index.html" web/prompt-kit/index.html\n'
        path.write_text(text, encoding="utf-8")
        report = validator.build_report(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("executable canonical parity", json.dumps(report))

    def test_portable_runtime_must_source_canonical_site(self) -> None:
        payload = json.loads((self.root / validator.PORTABILITY_CONTRACT_REL).read_text(encoding="utf-8"))
        payload["artifact_rules"]["portable_runtime_artifact"]["source"] = "web/prompt-kit-local/index.html"
        self.dump(validator.PORTABILITY_CONTRACT_REL, payload)
        report = validator.build_report(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("portable runtime source", json.dumps(report))

    def test_portable_builder_default_source_must_be_canonical(self) -> None:
        path = self.root / validator.PORTABLE_BUILDER_REL
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            'parser.add_argument("--source", default="web/prompt-kit/index.html")',
            'parser.add_argument("--source", default="web/other/index.html")',
        )
        path.write_text(text, encoding="utf-8")
        report = validator.build_report(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("default source", json.dumps(report))

    def test_windows_style_receipt_path_is_normalized(self) -> None:
        path = self.root / validator.PORTABLE_BUILDER_REL
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            '"path": str(source_path.relative_to(repo_root)),',
            '"path": str(source_path.relative_to(repo_root)).replace("/", "\\\\"),',
        )
        path.write_text(text, encoding="utf-8")
        report = validator.build_report(self.root)
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(
            validator.normalize_repo_relative(r"web\prompt-kit\index.html"),
            validator.CANONICAL_ARTIFACT,
        )

    def test_crlf_checkout_keeps_platform_stable_content_identity(self) -> None:
        path = self.root / validator.CANONICAL_ARTIFACT
        lf_bytes = path.read_bytes().replace(b"\r\n", b"\n")
        expected_content_sha = hashlib.sha256(lf_bytes).hexdigest()
        crlf_bytes = lf_bytes.replace(b"\n", b"\r\n")
        self.assertNotEqual(lf_bytes, crlf_bytes)
        self.write_bytes(validator.CANONICAL_ARTIFACT, crlf_bytes)

        report = validator.build_report(self.root)
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(report["canonical_artifact_sha256"], expected_content_sha)
        self.assertEqual(report["canonical_content_sha256"], expected_content_sha)
        self.assertEqual(
            report["canonical_worktree_sha256"],
            hashlib.sha256(crlf_bytes).hexdigest(),
        )
        self.assertNotEqual(report["canonical_worktree_sha256"], expected_content_sha)

    def test_version_label_cannot_be_currentness_authority(self) -> None:
        payload = json.loads((self.root / validator.FRESHNESS_CONTRACT_REL).read_text(encoding="utf-8"))
        payload["anti_patterns"] = []
        self.dump(validator.FRESHNESS_CONTRACT_REL, payload)
        report = validator.build_report(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("version-label-only", json.dumps(report))

    def test_cli_writes_machine_report(self) -> None:
        output = self.root / "Outputs" / "prompt-kit-release-identity.json"
        self.assertEqual(
            validator.main(["--root", str(self.root), "--output", str(output), "--summary"]),
            0,
        )
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["schema_version"], "prompt-kit-release-identity-report/v1")
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["canonical_artifact_sha256"], report["canonical_content_sha256"])
        self.assertTrue(report["canonical_worktree_sha256"])


if __name__ == "__main__":
    unittest.main()
