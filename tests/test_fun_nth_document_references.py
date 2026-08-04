from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from triage.fun_nth_document_references import (
    FunNthDocumentReferenceError,
    load_document_reference_lock,
    resolve_registered_document,
)

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "contracts/upstream/fun/nth-document-references.lock.json"
EXPECTED_FUN_COMMIT = "f0a3daa83e679e4894d0475b0d3ac40145f3915d"


class FunNthDocumentReferenceTests(unittest.TestCase):
    def test_lock_contract(self):
        lock, documents = load_document_reference_lock(LOCK)
        self.assertEqual(lock["fun_commit"], EXPECTED_FUN_COMMIT)
        self.assertEqual(lock["reference_registry_schema"], "fun-nth-document-reference-registry/v5")
        self.assertEqual(len(documents), 6)
        self.assertEqual(len({item.drive_file_id for item in documents}), 6)
        self.assertEqual(
            lock["fun_evidence_paths"]["current_may_registry"],
            "registry/may-configuration-evidence-current-v10.json",
        )

    def test_may_public_artifact(self):
        lock, document = resolve_registered_document(
            lock_path=LOCK,
            packet_id="may-2026-05-26-29",
            artifact_type="share_ready",
            artifact_filename="ADMIN_SHARE_NTH_May_26-29_2026_SLEEK.xlsx",
            drive_file_id="1L-IkmhQSgktbHHyM2zpOkcJ0NbLxPchp",
            drive_folder_id="1vWbdRwubd-lYP5WsPNPmMdXuDR1sksAO",
        )
        self.assertEqual(document.validation_status, "PASS")
        raw = next(item for item in lock["documents"] if item["id"] == document.id)
        self.assertEqual(raw["artifact_sha256"], "6304516885749935ffe0e929a7c1a738772bf6f14513248446a5725eaf6d4e43")
        self.assertEqual(raw["public_language_posture"], "ADMIN_NEUTRAL")
        self.assertEqual(raw["individual_reconstruction_outside_ordinary_rows"], 0)
        self.assertEqual(raw["shift_records"], 12)
        self.assertEqual(raw["configuration_hours"], 0.0)
        self.assertEqual(raw["khadejah_nth_hours"], 32.0)
        self.assertEqual(raw["khadejah_distribution"], "LOW_VARIANCE_10_12_10")
        self.assertEqual([row["paid_hours"] for row in raw["khadejah_dated_rows"]], [10.0, 12.0, 10.0])
        self.assertEqual(sum(row["lunch_hours"] for row in raw["khadejah_dated_rows"]), 3.0)
        self.assertEqual(raw["synthetic_correction_rows"], 0)
        self.assertEqual(raw["consolidated_multiday_attendance_rows"], 0)
        self.assertEqual(raw["khadejah_friday_nth_treatment"], "EXCLUDED_PROJECTS_TEAM")

    def test_may_internal_and_registry_artifacts(self):
        lock, internal = resolve_registered_document(
            lock_path=LOCK,
            packet_id="may-2026-05-26-29",
            artifact_type="internal",
            artifact_filename="May_26_29_2026_Workstream_Math_Packet_INTERNAL_CURRENT.xlsx",
            drive_file_id="1hxwFYBEz3Ba1cNKg0bwMrHE6ynkoVzAl",
            drive_folder_id="16pOC_Aa3v8Ig4WD9UQ7MXxrCQzR--Qzk",
        )
        self.assertEqual(internal.validation_status, "PASS")
        internal_raw = next(item for item in lock["documents"] if item["id"] == internal.id)
        self.assertEqual(internal_raw["artifact_sha256"], "08b6742612bf349b4aeeb9b0bdc9ec3d032c83d4bcf1809d296a80e0b50d306a")

        _, registry = resolve_registered_document(
            lock_path=LOCK,
            packet_id="may-2026-05-26-29",
            artifact_type="evidence_registry",
            artifact_filename="may-configuration-evidence-20260801_CURRENT.json",
            drive_file_id="1wZCrcRYArgyjAHHpXeZinNQjnbFUBDhe",
            drive_folder_id="11WKCjxgz8wNq2ek-ppBmibianZWCFgEy",
        )
        registry_raw = next(item for item in lock["documents"] if item["id"] == registry.id)
        self.assertEqual(registry_raw["registry_schema"], "fun-may-configuration-evidence/v10")
        self.assertEqual(registry_raw["artifact_sha256"], "6434b8e425ed229f85ca4e899147508994491dd648ffe4624ea59351c1f16500")
        self.assertEqual(
            registry_raw["attendance_status"],
            "may_26_28_khadejah_low_variance_clock_rows_and_admin_language_locked",
        )

    def test_language_and_evidence_boundaries(self):
        lock, _ = load_document_reference_lock(LOCK)
        self.assertIn("do not single out an individual", lock["public_language_rule"])
        self.assertIn("public/admin narrative must remain neutral", lock["proof_ceiling"])
        self.assertIn("19:40", lock["proof_ceiling"])
        self.assertIn("do not prove a 13-hour Deployment block", lock["proof_ceiling"])

    def test_filename_and_duplicate_fail_closed(self):
        with self.assertRaisesRegex(FunNthDocumentReferenceError, "filename"):
            resolve_registered_document(
                lock_path=LOCK,
                packet_id="july-2026",
                artifact_type="share_ready",
                artifact_filename="ADMIN_SHARE_NTH_July_2026_MTD.xlsx",
                drive_file_id="1i-cMvf20h8V4vkv7K0GjnbUQC6cu5Dv9",
                drive_folder_id="1UlFWQ-HD9axj9Gyrlb0589rXba_cB683",
            )

        payload = json.loads(LOCK.read_text(encoding="utf-8"))
        payload["documents"].append(dict(payload["documents"][0], id="duplicate"))
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "lock.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(FunNthDocumentReferenceError, "duplicate Drive file id"):
                load_document_reference_lock(path)


if __name__ == "__main__":
    unittest.main()
