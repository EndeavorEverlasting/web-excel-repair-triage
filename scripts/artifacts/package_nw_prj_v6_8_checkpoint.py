#!/usr/bin/env python3
"""Package NW PRJ v6.8 generator-critical workbooks into an AES-encrypted zip.

Run from repo root:
    python scripts/artifacts/package_nw_prj_v6_8_checkpoint.py

Password via environment (non-interactive):
    $env:NW_PRJ_CHECKPOINT_PASSWORD = "your-secret"
    python scripts/artifacts/package_nw_prj_v6_8_checkpoint.py

Never commit the password.
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
PAYLOAD_DIR = ARTIFACT_DIR / "payload"
SOURCE_DIR = ROOT / "Workbook Payload Artifacts"
MANIFEST_PATH = ARTIFACT_DIR / "manifest.json"
ARCHIVE_NAME = "NW_PRJ_v6_8_checkpoint_payload_2026-05-28.zip"
ARCHIVE_PATH = PAYLOAD_DIR / ARCHIVE_NAME
CHECKSUMS_PATH = ARTIFACT_DIR / "payload_checksums.sha256"

EXPECTED_XLSX = [
    "NW_PRJ_Tech_Roster_Dashboard_v6_8_RESOLUTION_LEDGER_WEBSAFE.xlsx",
    "NW PRJ Tech hours 5-27-2026 - Khadejah and Alejandro Updates - Manually Updated 5x.xlsx",
    "INTERNAL_May_Billing_Active_Roster_Log_2026-05-28-update so that partial hours are flagged before submission.xlsx",
]


def _require_pyzipper():
    try:
        import pyzipper
    except ImportError as e:
        raise RuntimeError("pyzipper is required: pip install pyzipper") from e
    return pyzipper


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _password() -> bytes:
    env = os.environ.get("NW_PRJ_CHECKPOINT_PASSWORD", "").strip()
    if env:
        return env.encode("utf-8")
    pw = getpass.getpass("Archive password (not stored in repo): ")
    if not pw:
        raise RuntimeError("Password required")
    confirm = getpass.getpass("Confirm password: ")
    if pw != confirm:
        raise RuntimeError("Passwords do not match")
    return pw.encode("utf-8")


def _verify_sources(manifest: dict) -> list[Path]:
    if not SOURCE_DIR.is_dir():
        raise FileNotFoundError(f"Missing source folder: {SOURCE_DIR}")

    by_name = {e["filename"]: e for e in manifest.get("contents", []) if e["filename"].endswith(".xlsx")}
    paths: list[Path] = []
    for name in EXPECTED_XLSX:
        path = SOURCE_DIR / name
        if not path.is_file():
            raise FileNotFoundError(f"Missing workbook: {path}")
        actual = _sha256_file(path)
        entry = by_name.get(name)
        if entry and actual.lower() != entry["sha256"].lower():
            raise RuntimeError(f"Checksum mismatch for {name}: expected {entry['sha256']}, got {actual}")
        if entry and path.stat().st_size != entry["size_bytes"]:
            raise RuntimeError(f"Size mismatch for {name}: expected {entry['size_bytes']}, got {path.stat().st_size}")
        paths.append(path)
    return paths


def main() -> int:
    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError(f"Missing manifest: {MANIFEST_PATH}")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    sources = _verify_sources(manifest)
    password = _password()
    pyzipper = _require_pyzipper()

    PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with pyzipper.AESZipFile(
        ARCHIVE_PATH,
        "w",
        compression=pyzipper.ZIP_DEFLATED,
        encryption=pyzipper.WZ_AES,
    ) as zf:
        zf.setpassword(password)
        for path in sources:
            zf.write(path, arcname=path.name)

    archive_sha = hashlib.sha256(ARCHIVE_PATH.read_bytes()).hexdigest()
    lines = [f"{archive_sha}  {ARCHIVE_NAME}"]
    for path in sources:
        lines.append(f"{_sha256_file(path)}  {path.name}")
    CHECKSUMS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Created encrypted archive: {ARCHIVE_PATH}")
    print(f"Archive SHA-256: {archive_sha}")
    print(f"Wrote checksums: {CHECKSUMS_PATH}")
    print(f"Files packaged: {len(sources)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
