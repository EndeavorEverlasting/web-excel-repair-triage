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


class FunNthDocumentReferenceTests(unittest.TestCase):
    def test_lock_is_well_formed_and_drive_ids_are_unique(self):
        lock, documents = load_document_reference_lock(LOCK)
        self.assertEqual(lock["fun_commit"], "dc4de367967c0dc168208dff886b611e7eaf8386")
        self.assertEqual(len(documents), 4)
        self.assertEqual(len({document.drive_file_id for document in documents}), 4)

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

    def test_may_public_reference_fails_closed_until_summary_sync(self):
        with self.assertRaisesRegex(
            FunNthDocumentReferenceError, "not accepted for final manifest production"
        ):
            resolve_registered_document(
                lock_path=LOCK,
                packet_id="may-2026-05-26-29",
                artifact_type="share_ready",
                artifact_filename="ADMIN_SHARE_NTH_May_26-29_2026_SLEEK.xlsx",
                drive_file_id="1L-IkmhQSgktbHHyM2zpOkcJ0NbLxPchp",
                drive_folder_id="1vWbdRwubd-lYP5WsPNPmMdXuDR1sksAO",
            )

    def test_may_identity_can_be_resolved_for_diagnosis_without_upgrading_status(self):
        _, document = resolve_registered_document(
            lock_path=LOCK,
            packet_id="may-2026-05-26-29",
            artifact_type="share_ready",
            artifact_filename="ADMIN_SHARE_NTH_May_26-29_2026_SLEEK.xlsx",
            drive_file_id="1L-IkmhQSgktbHHyM2zpOkcJ0NbLxPchp",
            drive_folder_id="1vWbdRwubd-lYP5WsPNPmMdXuDR1sksAO",
            require_validation_pass=False,
        )
        self.assertEqual(document.validation_status, "FAIL_CLOSED_PENDING_SUMMARY_SYNC")

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
