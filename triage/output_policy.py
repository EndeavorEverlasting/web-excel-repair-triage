"""Repo-wide output path policy — emulator inputs stay read-only.

Artifact engines read from lifecycle/emulator folders and write only under
``Outputs/`` or ``artifacts/`` (both gitignored). See
``docs/OPERATOR_SOURCE_IMMUTABILITY.md``.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

from triage.artifact_fingerprint import raw_sha256
from triage.path_policy import is_under_folder, repo_root

READONLY_INPUT_ROOTS = (
    "Candidates",
    "Active",
    "ArtifactIntake",
    "References",
    "Repaired",
    "Workbook Payload Artifacts",
    "RecoveredArtifacts",
)
WRITABLE_OUTPUT_ROOTS = ("Outputs", "artifacts")
OUTPUT_LAYOUT_VERSION = 1


class SourcePathWriteForbiddenError(ValueError):
    """Raised when an engine would write into read-only emulator/input zones."""


def _resolve(path: str | Path) -> Path:
    pp = Path(path).expanduser()
    if pp.is_absolute():
        return pp.resolve(strict=False)
    return (repo_root() / pp).resolve(strict=False)


def _writable_root_index(parts: tuple[str, ...]) -> Optional[int]:
    for folder in WRITABLE_OUTPUT_ROOTS:
        if folder in parts:
            return parts.index(folder)
    return None


def assert_not_overwriting_emulator(path: str | Path) -> None:
    """Fail closed if *path* targets a read-only emulator/input root."""
    p = _resolve(path)
    parts = p.parts
    widx = _writable_root_index(parts)
    for folder in READONLY_INPUT_ROOTS:
        if folder not in parts:
            if is_under_folder(p, folder):
                raise SourcePathWriteForbiddenError(
                    f"write target must not be under {folder}/; "
                    f"{folder}/ is a read-only operator input zone"
                )
            continue
        ro_idx = parts.index(folder)
        if widx is None or ro_idx < widx:
            raise SourcePathWriteForbiddenError(
                f"write target must not be under {folder}/; "
                f"{folder}/ is a read-only operator input zone"
            )


def assert_output_path_allowed(
    *input_paths: str | Path,
    output_path: str | Path,
) -> None:
    """Fail closed if output equals any input or targets a readonly root."""
    out = _resolve(output_path)
    assert_not_overwriting_emulator(out)

    for raw_inp in input_paths:
        if raw_inp is None:
            continue
        inp = _resolve(raw_inp)
        if inp == out:
            raise SourcePathWriteForbiddenError(
                "output path must not equal input path; "
                "write delivery artifacts under Outputs/ or artifacts/"
            )


def assert_out_dir_allowed(out_dir: str | Path) -> Path:
    """Require *out_dir* to live under Outputs/ or artifacts/."""
    p = _resolve(out_dir)
    parts = p.parts
    idx = _writable_root_index(parts)
    if idx is None:
        for folder in WRITABLE_OUTPUT_ROOTS:
            if is_under_folder(p, folder):
                return p
        raise SourcePathWriteForbiddenError(
            f"output directory must be under one of {WRITABLE_OUTPUT_ROOTS}; got {p}"
        )
    for ro in READONLY_INPUT_ROOTS:
        if ro in parts[:idx]:
            raise SourcePathWriteForbiddenError(
                f"output directory must not be under {ro}/ before writable root; got {p}"
            )
    return p


def allocate_run_dir(
    engine: str,
    slug: str,
    *,
    root: Optional[Path] = None,
    writable_root: str = "Outputs",
) -> Path:
    """Create ``<writable_root>/<engine>/<YYYY-MM-DD>_<slug>/`` for one operator batch."""
    if writable_root not in WRITABLE_OUTPUT_ROOTS:
        raise ValueError(f"writable_root must be one of {WRITABLE_OUTPUT_ROOTS}")
    base = root or repo_root()
    today = date.today().isoformat()
    safe_slug = re.sub(r"[^\w\-]+", "_", slug).strip("_") or "run"
    run_dir = base / writable_root / engine / f"{today}_{safe_slug}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def run_id_from_dir(run_dir: Path) -> str:
    return run_dir.name


def source_manifest_fields(*source_paths: str | Path) -> dict:
    """Standard manifest provenance for the primary emulator input."""
    primary: Optional[Path] = None
    for sp in source_paths:
        if sp is None:
            continue
        p = Path(sp)
        if not p.is_absolute():
            p = _resolve(p)
        if p.is_file():
            primary = p
            break

    if primary is None:
        first = str(source_paths[0]) if source_paths else ""
        return {
            "source_emulator_path": first,
            "source_raw_sha256": "",
            "output_layout_version": OUTPUT_LAYOUT_VERSION,
        }

    return {
        "source_emulator_path": str(primary.resolve()),
        "source_raw_sha256": raw_sha256(primary),
        "output_layout_version": OUTPUT_LAYOUT_VERSION,
    }


def ensure_run_subdirs(run_dir: Path, names: Iterable[str] = ()) -> None:
    """Optionally create standard layout folders under a run directory."""
    defaults = ("delivery", "internal", "sidecars", "compare", "forensics")
    for name in names or defaults:
        (run_dir / name).mkdir(parents=True, exist_ok=True)
