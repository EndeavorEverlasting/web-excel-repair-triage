#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from triage.fun_nth_artifact_export import (
    FunNthExportError,
    build_fun_nth_export,
    write_export_result,
)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Emit a FUN-compatible NTH artifact manifest and producer receipt."
    )
    p.add_argument("--artifact", required=True, type=Path)
    p.add_argument("--packet-spec", required=True, type=Path)
    p.add_argument("--export-profile", required=True, type=Path)
    p.add_argument(
        "--contract-lock",
        type=Path,
        default=ROOT / "contracts/upstream/fun/nth-artifact-contract.lock.json",
    )
    p.add_argument("--artifact-type", choices=("share_ready", "internal", "fixture"), required=True)
    p.add_argument("--builder-version", required=True)
    p.add_argument("--producer-commit", required=True)
    p.add_argument("--publication-posture", choices=("sanitized_fixture", "private_runtime", "protected_runtime"), required=True)
    p.add_argument("--generation-mode", choices=("generated", "repaired", "validated_copy"), required=True)
    p.add_argument("--manifest-out", required=True, type=Path)
    p.add_argument("--receipt-out", required=True, type=Path)
    p.add_argument("--drive-file-id")
    p.add_argument("--drive-folder-id")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = build_fun_nth_export(
            artifact_path=args.artifact,
            packet_spec_path=args.packet_spec,
            export_profile_path=args.export_profile,
            lock_path=args.contract_lock,
            repository_root=ROOT,
            artifact_type=args.artifact_type,
            builder_version=args.builder_version,
            producer_commit=args.producer_commit,
            publication_posture=args.publication_posture,
            generation_mode=args.generation_mode,
            drive_file_id=args.drive_file_id,
            drive_folder_id=args.drive_folder_id,
        )
        write_export_result(
            result, manifest_path=args.manifest_out, receipt_path=args.receipt_out
        )
    except FunNthExportError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    print(f"PASS manifest: {args.manifest_out}")
    print(f"PASS receipt: {args.receipt_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
