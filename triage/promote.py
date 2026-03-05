"""triage/promote.py
------------------
Controlled promotion of a workbook into Active/.

Policy:
  - Work happens in Deprecated/
  - Active/ is the golden standards folder (read-only except for deliberate promotion)

Promotion is *copy-only* and is logged under Outputs/promotions/.
"""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from triage.path_policy import is_active_path, is_deprecated_path, repo_root


class PromotionError(RuntimeError):
    """Raised when a promotion would violate folder semantics or safety policy."""


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class PromotionResult:
    origin_deprecated_path: str
    source_path: str
    dest_path: str
    report_path: str
    src_sha256: str
    dest_sha256: str
    copied_bytes: int


def promote_to_active(
    *,
    origin_deprecated_path: str | Path,
    source_path: str | Path,
    active_dir: str | Path = "Active",
    outputs_dir: str | Path = "Outputs/promotions",
    allow_overwrite: bool = False,
    purpose: str | None = None,
    extra: Optional[dict[str, Any]] = None,
) -> PromotionResult:
    """Copy *source_path* into Active/ using the *origin_deprecated_path* filename.

    - Refuses promotion unless origin is under Deprecated/.
    - Refuses to promote a source that is already under Active/.
    - Refuses overwriting an existing Active/ file unless allow_overwrite=True.
    - Always writes a JSON report under Outputs/promotions/.
    """

    origin = Path(origin_deprecated_path)
    src = Path(source_path)

    if not is_deprecated_path(origin):
        raise PromotionError(
            "ENDEAVOR: Promote to Active — refused. "
            "Only workbooks originating from Deprecated/ may be promoted. "
            f"origin={origin}"
        )

    if is_active_path(src):
        raise PromotionError(
            "ENDEAVOR: Promote to Active — refused. "
            "Source is already under Active/ (golden standards). "
            f"source={src}"
        )

    if not src.exists() or not src.is_file():
        raise PromotionError(
            "ENDEAVOR: Promote to Active — refused. "
            f"Source path does not exist or is not a file. source={src}"
        )

    active_dir_path = Path(active_dir)
    if not active_dir_path.is_absolute():
        active_dir_path = repo_root() / active_dir_path
    active_dir_path = active_dir_path.resolve(strict=False)
    active_dir_path.mkdir(parents=True, exist_ok=True)

    dest = (active_dir_path / origin.name).resolve(strict=False)
    if dest.exists() and not allow_overwrite:
        raise PromotionError(
            "ENDEAVOR: Promote to Active — refused. "
            "A golden standard with this name already exists in Active/. "
            f"dest={dest}"
        )

    out_dir = Path(outputs_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root() / out_dir
    out_dir = out_dir.resolve(strict=False)
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_stem = "".join(c if c.isalnum() or c in "._-" else "_" for c in origin.stem)[:80] or "workbook"
    report_path = out_dir / f"promotion_{ts}_{safe_stem}.json"

    src_sha = _sha256_file(src)

    # Copy via temp file then atomic replace/move.
    with tempfile.NamedTemporaryFile(delete=False, dir=str(active_dir_path), suffix=".tmp") as tmp:
        tmp_path = Path(tmp.name)
    try:
        shutil.copy2(src, tmp_path)
        if dest.exists() and allow_overwrite:
            os.replace(tmp_path, dest)
        else:
            tmp_path.replace(dest)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass

    dest_sha = _sha256_file(dest)
    copied_bytes = int(dest.stat().st_size)

    payload: dict[str, Any] = {
        "endeavor": "PROMOTE_TO_ACTIVE",
        "purpose": purpose
        or "ENDEAVOR: Promote to Active — copy a validated Deprecated workbook into Active/ (golden standards).",
        "timestamp": ts,
        "origin_deprecated_path": str(origin),
        "source_path": str(src),
        "dest_path": str(dest),
        "allow_overwrite": bool(allow_overwrite),
        "src_sha256": src_sha,
        "dest_sha256": dest_sha,
        "copied_bytes": copied_bytes,
        "sha_match": (src_sha == dest_sha),
    }
    if extra:
        payload["extra"] = extra

    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return PromotionResult(
        origin_deprecated_path=str(origin),
        source_path=str(src),
        dest_path=str(dest),
        report_path=str(report_path),
        src_sha256=src_sha,
        dest_sha256=dest_sha,
        copied_bytes=copied_bytes,
    )
