from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from triage.fun_nth_artifact_export import (
    FunNthExportError,
    build_fun_nth_export,
    verify_contract_lock,
    write_export_result,
)

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "contracts/upstream/fun/nth-artifact-contract.lock.json"
COMMIT = "1" * 40


def write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def make_xlsx(path: Path) -> Path:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", "<workbook/>")
        archive.writestr("xl/worksheets/sheet1.xml", "<worksheet/>")
    return path


def packet() -> dict:
    return {
        "schema": "fun-nth-packet-spec/v1",
        "packet_id": "fixture.packet",
        "period": {"label": "Fixture", "start": "2026-08-01", "end": "2026-08-01"},
        "controls": {"hours": 8.0, "shift_records": 1, "control_kind": "operational"},
        "workstreams": [
            {
                "id": "configuration",
                "label": "Configuration",
                "hours": 8.0,
                "color": "#D9EAF7",
                "allocation_basis": [{"kind": "fixture"}],
                "included_activities": ["Synthetic fixture"],
                "evidence_authority": [{"kind": "fixture"}],
                "defense_boundaries": ["No production claim"],
                "share_safe_claim": "Synthetic fixture only",
            }
        ],
        "palette": {"configuration": "#D9EAF7"},
        "share_surface": {
            "artifact_name": "sanitized_nth.xlsx",
            "approved_tabs": ["NTH", "Task Summary"],
            "forbidden_content": ["Evidence References", "Source Notes"],
        },
        "proof_boundaries": ["Synthetic fixture only"],
    }


def profile() -> dict:
    return {
        "schema": "web-excel-fun-nth-export-profile/v1",
        "packet_id": "fixture.packet",
        "sheet_contract": {
            "allowed_sheets": ["NTH", "Task Summary"],
            "hidden_sheets_forbidden": True,
            "forbidden_sheet_patterns": ["(?i)evidence"],
            "forbidden_text": ["Evidence References", "Source Notes"],
        },
        "cell_assertions": [{"sheet": "NTH", "cell": "A1", "value": "Fixture"}],
        "reconciliations": [
            {
                "label": "fixture total",
                "terms": [{"sheet": "Task Summary", "cell": "B2"}],
                "expected": 8.0,
                "tolerance": 0.0,
            }
        ],
        "required_text": [{"sheet": "NTH", "text": "Fixture"}],
        "row_color_contracts": [
            {
                "sheet": "NTH",
                "key_column": "B",
                "start_row": 2,
                "end_row": 2,
                "apply_columns": "A:D",
                "palette": {"Configuration": "#D9EAF7"},
            }
        ],
    }


class FunNthArtifactExportTests(unittest.TestCase):
    def test_contract_lock_pins_exact_fun_schema_bytes(self):
        lock = verify_contract_lock(LOCK, ROOT)
        self.assertEqual(lock["fun_commit"], "9ba432808f823e52c6ba80ffd05ec673d2e15acf")
        self.assertEqual(len(lock["contracts"]), 3)

    def test_builds_fun_manifest_and_producer_receipt_from_actual_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = make_xlsx(root / "sanitized_nth.xlsx")
            packet_path = write_json(root / "packet.json", packet())
            profile_path = write_json(root / "profile.json", profile())
            result = build_fun_nth_export(
                artifact_path=artifact,
                packet_spec_path=packet_path,
                export_profile_path=profile_path,
                lock_path=LOCK,
                repository_root=ROOT,
                artifact_type="fixture",
                builder_version="test-builder/1",
                producer_commit=COMMIT,
                publication_posture="sanitized_fixture",
                generation_mode="generated",
            )
            self.assertEqual(result.manifest["schema"], "fun-nth-artifact-manifest/v1")
            self.assertEqual(result.manifest["packet_id"], "fixture.packet")
            self.assertEqual(result.manifest["artifact"]["filename"], artifact.name)
            self.assertEqual(result.manifest["artifact"]["size"], artifact.stat().st_size)
            self.assertEqual(
                result.manifest["artifact"]["sha256"],
                hashlib.sha256(artifact.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                result.receipt["upstream_contract"]["commit"],
                "9ba432808f823e52c6ba80ffd05ec673d2e15acf",
            )
            self.assertEqual(result.receipt["publication_posture"], "sanitized_fixture")
            manifest_out = root / "manifest.json"
            receipt_out = root / "receipt.json"
            write_export_result(result, manifest_path=manifest_out, receipt_path=receipt_out)
            self.assertTrue(manifest_out.is_file())
            self.assertTrue(receipt_out.is_file())

    def test_share_ready_sheets_must_match_fun_approved_tabs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = make_xlsx(root / "share.xlsx")
            packet_path = write_json(root / "packet.json", packet())
            broken = profile()
            broken["sheet_contract"]["allowed_sheets"] = ["NTH"]
            profile_path = write_json(root / "profile.json", broken)
            with self.assertRaisesRegex(FunNthExportError, "exactly match"):
                build_fun_nth_export(
                    artifact_path=artifact,
                    packet_spec_path=packet_path,
                    export_profile_path=profile_path,
                    lock_path=LOCK,
                    repository_root=ROOT,
                    artifact_type="share_ready",
                    builder_version="test-builder/1",
                    producer_commit=COMMIT,
                    publication_posture="protected_runtime",
                    generation_mode="generated",
                )

    def test_testing_or_evidence_claim_fields_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = make_xlsx(root / "sanitized_nth.xlsx")
            packet_path = write_json(root / "packet.json", packet())
            broken = profile()
            broken["evidence_claims"] = ["38 devices"]
            profile_path = write_json(root / "profile.json", broken)
            with self.assertRaisesRegex(FunNthExportError, "unsupported fields"):
                build_fun_nth_export(
                    artifact_path=artifact,
                    packet_spec_path=packet_path,
                    export_profile_path=profile_path,
                    lock_path=LOCK,
                    repository_root=ROOT,
                    artifact_type="fixture",
                    builder_version="test-builder/1",
                    producer_commit=COMMIT,
                    publication_posture="sanitized_fixture",
                    generation_mode="generated",
                )

    def test_schema_snapshot_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contracts = root / "contracts/upstream/fun/schemas"
            contracts.mkdir(parents=True)
            lock = json.loads(LOCK.read_text(encoding="utf-8"))
            for record in lock["contracts"]:
                source = ROOT / record["snapshot_path"]
                target = root / record["snapshot_path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
            lock_path = write_json(root / "contracts/upstream/fun/lock.json", lock)
            first = root / lock["contracts"][0]["snapshot_path"]
            first.write_text(first.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(FunNthExportError, "drift"):
                verify_contract_lock(lock_path, root)

    def test_fixture_cannot_claim_private_or_protected_runtime_posture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = make_xlsx(root / "sanitized_nth.xlsx")
            packet_path = write_json(root / "packet.json", packet())
            profile_path = write_json(root / "profile.json", profile())
            with self.assertRaisesRegex(FunNthExportError, "sanitized_fixture"):
                build_fun_nth_export(
                    artifact_path=artifact,
                    packet_spec_path=packet_path,
                    export_profile_path=profile_path,
                    lock_path=LOCK,
                    repository_root=ROOT,
                    artifact_type="fixture",
                    builder_version="test-builder/1",
                    producer_commit=COMMIT,
                    publication_posture="protected_runtime",
                    generation_mode="generated",
                )


if __name__ == "__main__":
    unittest.main()
