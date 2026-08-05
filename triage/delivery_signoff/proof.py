"""Render and package-proof helpers for delivery sign-offs."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .schema import HEX64_RE, SignoffValidationError, sha256


def render_docx(docx_path: Path, preview_dir: Path) -> tuple[Path, tuple[Path, ...]]:
    libreoffice = shutil.which("libreoffice") or shutil.which("soffice")
    pdftoppm = shutil.which("pdftoppm")
    if not libreoffice:
        raise SignoffValidationError("LibreOffice is required to render the DOCX preview")
    if not pdftoppm:
        raise SignoffValidationError("pdftoppm is required to rasterize preview pages")
    preview_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="triage-lo-") as profile_dir:
        env = os.environ.copy()
        env.setdefault("HOME", profile_dir)
        completed = subprocess.run(
            [
                libreoffice,
                "--headless",
                f"-env:UserInstallation=file://{profile_dir}",
                "--convert-to",
                "pdf",
                "--outdir",
                str(preview_dir),
                str(docx_path),
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
            check=False,
        )
        if completed.returncode != 0:
            raise SignoffValidationError(
                "LibreOffice render failed: " + (completed.stderr.strip() or completed.stdout.strip())
            )
    pdf_path = preview_dir / f"{docx_path.stem}.pdf"
    if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        raise SignoffValidationError("LibreOffice did not produce a non-empty PDF preview")
    completed = subprocess.run(
        [pdftoppm, "-png", "-r", "150", str(pdf_path), str(preview_dir / "page")],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if completed.returncode != 0:
        raise SignoffValidationError("PDF page rasterization failed: " + completed.stderr.strip())
    page_paths = tuple(sorted(preview_dir.glob("page-*.png")))
    if not page_paths:
        raise SignoffValidationError("no page preview images were produced")
    if len(page_paths) > 2:
        raise SignoffValidationError(f"rendered sign-off exceeds two-page maximum: {len(page_paths)}")
    return pdf_path, page_paths


def extract_pdf_text(pdf_path: Path) -> str:
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        raise SignoffValidationError("pdftotext is required to verify rendered identifiers")
    completed = subprocess.run(
        [pdftotext, "-raw", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if completed.returncode != 0:
        raise SignoffValidationError("PDF text extraction failed: " + completed.stderr.strip())
    return completed.stdout


def relative_entry(path: Path, package_dir: Path) -> dict[str, str]:
    return {"path": path.relative_to(package_dir).as_posix(), "sha256": sha256(path)}


def validate_path_hash_object(item: Any, package_dir: Path, label: str) -> Path:
    if not isinstance(item, dict):
        raise SignoffValidationError(f"{label} must be an object")
    raw_path = item.get("path")
    expected_hash = item.get("sha256")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise SignoffValidationError(f"{label}.path must be non-empty")
    if Path(raw_path).is_absolute():
        raise SignoffValidationError(f"{label}.path must be relative")
    if not isinstance(expected_hash, str) or not HEX64_RE.fullmatch(expected_hash.lower()):
        raise SignoffValidationError(f"{label}.sha256 must be a 64-character hex digest")
    root = package_dir.resolve()
    candidate = (root / raw_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SignoffValidationError(f"{label}.path escapes the manifest package") from exc
    if not candidate.is_file():
        raise SignoffValidationError(f"{label}.path does not exist: {candidate}")
    if sha256(candidate) != expected_hash.lower():
        raise SignoffValidationError(f"{label}.sha256 mismatch")
    return candidate
