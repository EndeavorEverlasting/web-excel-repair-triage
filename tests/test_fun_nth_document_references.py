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
EXPECTED_FUN_COMMIT = "bf5470ab55c127fa9fe4769975357940ae40b82c"
MAY_LOGISTICS_EVIDENCE_ID = "MAY-0526-ALEJANDRO-LOGISTICS-TEAMS"
MAY_KHADEJAH_ATTENDANCE_ID = "MAY-0526-0528-KHADEJAH-ATTENDANCE"
MAY_LOGISTICS_SHA256 = "7fb6378e9af8a2d545852e960eea4c92d5ebb2ff6e60e60a957f571e693bb62e"


class FunNthDocumentReferenceTests(unittest.TestCase):
    def test_lock_is_well_formed_and_drive_ids_are_unique(self):
        lock, documents = load_document_reference_lock(LOCK)
        self.assertEqual(lock["fun_commit"], EXPECTED_FUN_COMMIT)
        self.assertEqual(lock["reference_registry_schema"], "fun-nth-document-reference-registry/v3")
        self.assertEqual(len(documents), 6)
        self.assertEqual(len({document.drive_file_id for document in documents}), 6)
        self.assertEqual(
            lock["navigation"]["source_evidence_folder_id"],
            "1gDVO5RuoBHu1w-gPEE55Oy3hhK8MgdHW",
        )

    def test_july_public_sleek_reference_passes(self):
        _, document = resolve_registered_document(
            lock_path=LOCK,
            packet_id="july-2026",
            artifact_type="share_ready",
            artifact_filename="ADMIN_SHARE_NTH_July_2026_MTD_SLEEK.xlsx",
            drive_file_id="1i-cMvf20h8V4vkv7K0GjnbUQC6cu5Dv9",
            drive_folder_id="1UlFWQ-HD9axj9Gyrlb0589rXba_cB683",
        )
        self.assertEqual(document.validation_status, "PASS")

    def test_may_public_sleek_reference_passes(self):
        lock, document = resolve_registered_document(
            lock_path=LOCK,
            packet_id="may-2026-05-26-29",
            artifact_type="share_ready",
            artifact_filename="ADMIN_SHARE_NTH_May_26-29_2026_SLEEK.xlsx",
            drive_file_id="1L-IkmhQSgktbHHyM2zpOkcJ0NbLxPchp",
            drive_folder_id="1vWbdRwubd-lYP5WsPNPmMdXuDR1sksAO",
        )
        self.assertEqual(document.validation_status, "PASS")
        self.assertEqual(document.status, "current")
        raw = next(item for item in lock["documents"] if item["id"] == document.id)
        self.assertEqual(raw["evidence_id"], MAY_LOGISTICS_EVIDENCE_ID)
        self.assertEqual(raw["may_27_boundary_status"], "CURRENT / BOUNDED")
        self.assertEqual(raw["shift_records"], 12)
        self.assertEqual(raw["configuration_hours"], 0.0)
        self.assertEqual(raw["khadejah_attendance_evidence_id"], MAY_KHADEJAH_ATTENDANCE_ID)
        self.assertEqual(raw["khadejah_nth_hours"], 32.0)
        self.assertEqual(raw["synthetic_correction_rows"], 0)
        self.assertEqual(raw["consolidated_multiday_attendance_rows"], 0)
        self.assertEqual(raw["khadejah_friday_nth_treatment"], "EXCLUDED_PROJECTS_TEAM")

        rows = raw["khadejah_dated_rows"]
        self.assertEqual(
            rows,
            [
                {
                    "date": "2026-05-26",
                    "clock_in": "09:00",
                    "clock_out": "22:00",
                    "lunch_hours": 1.0,
                    "paid_hours": 12.0,
                },
                {
                    "date": "2026-05-27",
                    "clock_in": "09:00",
                    "clock_out": "22:00",
                    "lunch_hours": 1.0,
                    "paid_hours": 12.0,
                },
                {
                    "date": "2026-05-28",
                    "clock_in": "09:00",
                    "clock_out": "18:00",
                    "lunch_hours": 1.0,
                    "paid_hours": 8.0,
                },
            ],
        )
        self.assertEqual(sum(row["paid_hours"] for row in rows), 32.0)
        self.assertEqual(sum(row["lunch_hours"] for row in rows), 3.0)

    def test_may_internal_packet_passes(self):
        lock, document = resolve_registered_document(
            lock_path=LOCK,
            packet_id="may-2026-05-26-29",
            artifact_type="internal",
            artifact_filename="May_26_29_2026_Workstream_Math_Packet_INTERNAL_CURRENT.xlsx",
            drive_file_id="1hxwFYBEz3Ba1cNKg0bwMrHE6ynkoVzAl",
            drive_folder_id="16pOC_Aa3v8Ig4WD9UQ7MXxrCQzR--Qzk",
        )
        self.assertEqual(document.validation_status, "PASS")
        raw = next(item for item in lock["documents"] if item["id"] == document.id)
        self.assertIn(MAY_LOGISTICS_EVIDENCE_ID, raw["evidence_matrix_contains"])
        self.assertIn(MAY_KHADEJAH_ATTENDANCE_ID, raw["evidence_matrix_contains"])
        self.assertEqual(raw["khadejah_clock_rows_status"], "CURRENT / LOCKED")

    def test_may_direct_logistics_source_resolves(self):
        lock, document = resolve_registered_document(
            lock_path=LOCK,
            packet_id="may-2026-05-26-29",
            artifact_type="source_evidence",
            artifact_filename="2026-05-26_Alejandro_Tim_Logistics_Text_Message_Evidence.png",
            drive_file_id="1d_GePGN4HquXgx_WhOVQ7Z4Rx0MSvdxe",
            drive_folder_id="1gDVO5RuoBHu1w-gPEE55Oy3hhK8MgdHW",
        )
        self.assertEqual(document.validation_status, "PASS")
        self.assertEqual(document.status, "current")
        raw = next(item for item in lock["documents"] if item["id"] == document.id)
        self.assertEqual(raw["evidence_id"], MAY_LOGISTICS_EVIDENCE_ID)
        self.assertEqual(raw["visible_time_range"], "18:31/19:40")
        self.assertEqual(raw["attendance_clock_out"], "20:00")
        self.assertEqual(raw["artifact_sha256"], MAY_LOGISTICS_SHA256)
        self.assertEqual(raw["artifact_size_bytes"], 114744)

    def test_may_drive_registry_resolves(self):
        lock, document = resolve_registered_document(
            lock_path=LOCK,
            packet_id="may-2026-05-26-29",
            artifact_type="evidence_registry",
            artifact_filename="may-configuration-evidence-20260801_CURRENT.json",
            drive_file_id="1wZCrcRYArgyjAHHpXeZinNQjnbFUBDhe",
            drive_folder_id="11WKCjxgz8wNq2ek-ppBmibianZWCFgEy",
        )
        self.assertEqual(document.validation_status, "PASS")
        raw = next(item for item in lock["documents"] if item["id"] == document.id)
        self.assertEqual(raw["attendance_status"], "may_26_28_khadejah_dated_clock_rows_locked")

    def test_proof_ceiling_preserves_evidence_boundaries(self):
        lock, _ = load_document_reference_lock(LOCK)
        proof_ceiling = lock["proof_ceiling"]
        self.assertIn("19:40", proof_ceiling)
        self.assertIn("20:00", proof_ceiling)
        self.assertIn("does not independently prove the exact five-hour split", proof_ceiling)
        self.assertIn("do not prove a 13-hour Deployment block", proof_ceiling)
        self.assertIn("05/26 09:00-22:00 less one-hour lunch = 12h", proof_ceiling)
        self.assertIn("05/27 09:00-22:00 less one-hour lunch = 12h", proof_ceiling)
        self.assertIn("05/28 09:00-18:00 less one-hour lunch = 8h", proof_ceiling)
        self.assertIn("Friday projects-team go-live work is excluded from NTH", proof_ceiling)
        self.assertEqual(
            lock["fun_evidence_paths"]["direct_may_26_source"],
            "registry/may-0526-alejandro-logistics-text-evidence.json",
        )
        self.assertEqual(
            lock["fun_evidence_paths"]["correction_overlay"],
            "registry/may-evidence-correction-overlay-20260803.json",
        )
        self.assertEqual(
            lock["fun_evidence_paths"]["khadejah_attendance_correction"],
            "registry/may-0526-0528-khadejah-attendance-correction.json",
        )

    def test_filename_and_packet_mismatches_fail(self):
        with self.assertRaisesRegex(FunNthDocumentReferenceError, "filename"):
            resolve_registered_document(
                lock_path=LOCK,
                packet_id="july-2026",
                artifact_type="share_ready",
                artifact_filename="ADMIN_SHARE_NTH_July_2026_MTD.xlsx",
                drive_file_id="1i-cMvf20h8V4vkv7K0GjnbUQC6cu5Dv9",
                drive_folder_id="1UlFWQ-HD9axj9Gyrlb0589rXba_cB683",
            )
        with self.assertRaisesRegex(FunNthDocumentReferenceError, "packet mismatch"):
            resolve_registered_document(
                lock_path=LOCK,
                packet_id="may-2026-05-26-29",
                artifact_type="share_ready",
                artifact_filename="ADMIN_SHARE_NTH_July_2026_MTD_SLEEK.xlsx",
                drive_file_id="1i-cMvf20h8V4vkv7K0GjnbUQC6cu5Dv9",
                drive_folder_id="1UlFWQ-HD9axj9Gyrlb0589rXba_cB683",
            )

    def test_duplicate_drive_id_lock_fails(self):
        payload = json.loads(LOCK.read_text(encoding="utf-8"))
        payload["documents"].append(dict(payload["documents"][0], id="duplicate"))
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "lock.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(FunNthDocumentReferenceError, "duplicate Drive file id"):
                load_document_reference_lock(path)


if __name__ == "__main__":
    unittest.main()
