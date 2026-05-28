#!/usr/bin/env python3
"""Extract the NW PRJ v6.8 AES-encrypted checkpoint payload.

Run from repo root:
    python scripts/artifacts/decode_nw_prj_v6_8_checkpoint.py

Password via environment (non-interactive):
    $env:NW_PRJ_CHECKPOINT_PASSWORD = "your-secret"
    python scripts/artifacts/decode_nw_prj_v6_8_checkpoint.py
"""
from __future__ import annotations

import getpass
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "artifacts" / "nw_prj_dashboard_v6_8"
MANIFEST_PATH = ARTIFACT_DIR / "manifest.json"
OUT_DIR = ROOT / "RecoveredArtifacts" / "NW_PRJ_v6_8_checkpoint_artifacts_2026-05-28"


def _require_pyzipper():
    try:
        import pyzipper
    except ImportError as e:
        raise RuntimeError("pyzipper is required: pip install pyzipper") from e
    return pyzipper


def _password() -> bytes:
    env = os.environ.get("NW_PRJ_CHECKPOINT_PASSWORD", "").strip()
    if env:
        return env.encode("utf-8")
    pw = getpass.getpass("Archive password: ")
    if not pw:
        raise RuntimeError("Password required")
    return pw.encode("utf-8")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_extracted(manifest: dict, out_dir: Path) -> None:
    expected = {
        e["filename"]: e
        for e in manifest.get("contents", [])
        if e["filename"].endswith(".xlsx")
    }
    for name, entry in expected.items():
        path = out_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"Missing extracted file: {path}")
        actual = _sha256_file(path)
        if actual.lower() != entry["sha256"].lower():
            raise RuntimeError(f"Checksum mismatch for {name}: expected {entry['sha256']}, got {actual}")


def main() -> int:
    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError(f"Missing manifest: {MANIFEST_PATH}")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    rel = manifest.get("payload_path", "")
    archive_path = ROOT / rel.replace("/", os.sep)
    if not archive_path.is_file():
        raise FileNotFoundError(f"Missing encrypted archive: {archive_path}")

    expected_archive_sha = manifest.get("archive_sha256", "")
    actual_archive_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    if expected_archive_sha and actual_archive_sha.lower() != expected_archive_sha.lower():
        raise RuntimeError(
            f"Archive checksum mismatch: expected {expected_archive_sha}, got {actual_archive_sha}"
        )

    pyzipper = _require_pyzipper()
    password = _password()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with pyzipper.AESZipFile(archive_path, "r") as zf:
        zf.setpassword(password)
        zf.extractall(OUT_DIR)

    _verify_extracted(manifest, OUT_DIR)

    print(f"Extracted files to: {OUT_DIR}")
    print(f"Archive SHA-256 verified: {actual_archive_sha}")
    for entry in manifest.get("contents", []):
        if entry["filename"].endswith(".xlsx"):
            print(f"  OK  {entry['filename']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
