from __future__ import annotations

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

    def write(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def dump(self, relative: str, payload: dict) -> None:
        self.write(relative, json.dumps(payload, indent=2) + "\n")

    def _seed_fixture(self) -> None:
        contract = json.loads((ROOT / validator.CONTRACT_REL).read_text(encoding="utf-8"))
        self.dump(validator.CONTRACT_REL.as_posix(), contract)
        self.dump(
            validator.ARTIFACTS_REL.as_posix(),
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
            validator.PORTABILITY_CONTRACT_REL.as_posix(),
            {
                "integration": {"canonical_site": validator.CANONICAL_ARTIFACT},
                "artifact_rules": {"portable_runtime_artifact": {"source": validator.CANONICAL_ARTIFACT}},
            },
        )
        self.dump(
            validator.FRESHNESS_CONTRACT_REL.as_posix(),
            {
                "freshness_routes": {"browser-use": f"Open {validator.CANONICAL_PUBLIC_URL} and use it."},
                "anti_patterns": ["Assuming a version label is current without checking the canonical latest route."],
            },
        )
        self.write(
            validator.PAGES_WORKFLOW_REL.as_posix(),
            'python scripts/build_prompt_kit_registry.py --output "$SITE_ROOT/prompt-kit/index.html"\n'
            'cmp "$SITE_ROOT/prompt-kit/index.html" web/prompt-kit/index.html\n',
        )
        self.write(
            validator.PORTABLE_BUILDER_REL.as_posix(),
            'parser.add_argument("--source", default="web/prompt-kit/index.html")\n'
            'receipt = {"sha256": sha256_bytes(source_bytes), "canonical_site_untouched": True}\n',
        )
        self.write(validator.CANONICAL_ARTIFACT, "<!doctype html><title>Prompt Kit</title>\n")

    def assertPasses(self) -> None:
        report = validator.build_report(self.root)
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(report["failure_count"], 0)
        self.assertTrue(report["canonical_artifact_sha256"])

    def test_fixture_passes(self) -> None:
        self.assertPasses()

    def test_artifact_registry_cannot_name_a_second_canonical_site(self) -> None:
        payload = json.loads((self.root / validator.ARTIFACTS_REL).read_text(encoding="utf-8"))
        payload["artifacts"][0]["canonical_path"] = "web/local/index.html"
        self.dump(validator.ARTIFACTS_REL.as_posix(), payload)
        report = validator.build_report(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("canonical path drifted", json.dumps(report))

    def test_pages_must_compare_published_prompt_kit_to_canonical_artifact(self) -> None:
        self.write(
            validator.PAGES_WORKFLOW_REL.as_posix(),
            'python scripts/build_prompt_kit_registry.py --output "$SITE_ROOT/prompt-kit/index.html"\n',
        )
        report = validator.build_report(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("Pages workflow lost canonical parity marker", json.dumps(report))

    def test_portable_runtime_must_source_canonical_site(self) -> None:
        payload = json.loads((self.root / validator.PORTABILITY_CONTRACT_REL).read_text(encoding="utf-8"))
        payload["artifact_rules"]["portable_runtime_artifact"]["source"] = "web/prompt-kit-local/index.html"
        self.dump(validator.PORTABILITY_CONTRACT_REL.as_posix(), payload)
        report = validator.build_report(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("portable runtime source", json.dumps(report))

    def test_version_label_cannot_be_currentness_authority(self) -> None:
        payload = json.loads((self.root / validator.FRESHNESS_CONTRACT_REL).read_text(encoding="utf-8"))
        payload["anti_patterns"] = []
        self.dump(validator.FRESHNESS_CONTRACT_REL.as_posix(), payload)
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


if __name__ == "__main__":
    unittest.main()
