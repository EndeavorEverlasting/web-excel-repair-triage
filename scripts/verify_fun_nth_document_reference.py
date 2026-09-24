#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from triage.fun_nth_document_references import (
    FunNthDocumentReferenceError,
    resolve_registered_document,
)

DEFAULT_LOCK = ROOT / "contracts/upstream/fun/nth-document-references.lock.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify that an NTH artifact resolves to a pinned FUN Drive document reference."
    )
    parser.add_argument("--packet-id", required=True)
    parser.add_argument("--artifact-type", required=True, choices=("share_ready", "internal", "validation"))
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--drive-file-id", required=True)
    parser.add_argument("--drive-folder-id")
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument(
        "--allow-nonpass",
        action="store_true",
        help="Resolve identity for diagnosis while preserving the non-PASS status.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        lock, document = resolve_registered_document(
            lock_path=args.lock,
            packet_id=args.packet_id,
            artifact_type=args.artifact_type,
            artifact_filename=args.artifact.name,
            drive_file_id=args.drive_file_id,
            drive_folder_id=args.drive_folder_id,
            require_validation_pass=not args.allow_nonpass,
        )
    except FunNthDocumentReferenceError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({
        "status": "PASS" if document.validation_status == "PASS" else document.validation_status,
        "fun_commit": lock["fun_commit"],
        "source_path": lock["source_path"],
        "document": {
            "id": document.id,
            "packet_id": document.packet_id,
            "artifact_type": document.artifact_type,
            "drive_file_id": document.drive_file_id,
            "drive_folder_id": document.drive_folder_id,
            "title": document.title,
            "registry_status": document.status,
            "validation_status": document.validation_status,
        },
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
