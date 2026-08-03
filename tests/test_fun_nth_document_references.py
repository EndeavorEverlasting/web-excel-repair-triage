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
EXPECTED_FUN_COMMIT = "125dcee2b96694dcde316038653a250ad8307e39"
MAY_LOGISTICS_EVIDENCE_ID = "MAY-0526-ALEJANDRO-LOGISTICS-TEAMS"


class FunNthDocumentReferenceTests(unittest.TestCase):
    def test_lock_is_well_formed_and_drive_ids_are_unique(self):
        lock, documents = load_document_reference_lock(LOCK)
        self.assertEqual(lock["fun_commit"], EXPECTED_FUN_COMMIT)
        self.assertEqual(lock["reference_registry_schema"], "fun-nth-document-reference-registry/v2")
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
        self.assertEqual(raw["evidence_matrix_contains"], MAY_LOGISTICS_EVIDENCE_ID)

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

    def test_may_drive_registry_resolves(self):
        _, document = resolve_registered_document(
            lock_path=LOCK,
            packet_id="may-2026-05-26-29",
            artifact_type="evidence_registry",
            artifact_filename="may-configuration-evidence-20260801_CURRENT.json",
            drive_file_id="1wZCrcRYArgyjAHHpXeZinNQjnbFUBDhe",
            drive_folder_id="11WKCjxgz8wNq2ek-ppBmibianZWCFgEy",
        )
        self.assertEqual(document.validation_status, "PASS")

    def test_proof_ceiling_preserves_evidence_boundaries(self):
        lock, _ = load_document_reference_lock(LOCK)
        proof_ceiling = lock["proof_ceiling"]
        self.assertIn("19:40", proof_ceiling)
        self.assertIn("20:00", proof_ceiling)
        self.assertIn("does not independently prove the exact five-hour split", proof_ceiling)
        self.assertIn("do not prove a 13-hour Deployment block", proof_ceiling)
        self.assertEqual(
            lock["fun_evidence_paths"]["direct_may_26_source"],
            "registry/may-0526-alejandro-logistics-text-evidence.json",
        )
        self.assertEqual(
            lock["fun_evidence_paths"]["correction_overlay"],
            "registry/may-evidence-correction-overlay-20260803.json",
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
