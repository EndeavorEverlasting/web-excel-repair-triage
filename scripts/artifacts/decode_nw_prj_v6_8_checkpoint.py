#!/usr/bin/env python3
"""Decode the NW PRJ v6.8 checkpoint artifact archive.

Run from repo root:
    python scripts/artifacts/decode_nw_prj_v6_8_checkpoint.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "artifacts" / "nw_prj_dashboard_v6_8"
B64_PATH = ARTIFACT_DIR / "NW_PRJ_v6_8_checkpoint_artifacts_2026-05-28.zip.b64"
MANIFEST_PATH = ARTIFACT_DIR / "manifest.json"
OUT_DIR = ROOT / "RecoveredArtifacts" / "NW_PRJ_v6_8_checkpoint_artifacts_2026-05-28"
ZIP_PATH = OUT_DIR / "NW_PRJ_v6_8_checkpoint_artifacts_2026-05-28.zip"


def main() -> int:
    if not B64_PATH.exists():
        raise FileNotFoundError(f"Missing base64 archive: {B64_PATH}")
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Missing manifest: {MANIFEST_PATH}")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    expected = manifest["archive_sha256"]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    archive_bytes = base64.b64decode(B64_PATH.read_text(encoding="ascii"))
    actual = hashlib.sha256(archive_bytes).hexdigest()
    if actual != expected:
        raise RuntimeError(f"Checksum mismatch: expected {expected}, got {actual}")

    ZIP_PATH.write_bytes(archive_bytes)
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        zf.extractall(OUT_DIR)

    print(f"Decoded archive: {ZIP_PATH}")
    print(f"Extracted files to: {OUT_DIR}")
    print(f"SHA-256 verified: {actual}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
