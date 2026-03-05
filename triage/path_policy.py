"""triage/path_policy.py
----------------------
Folder semantics / safety policy.

This repo uses a strict lifecycle:
  - Deprecated/: work here (mutation allowed)
  - Active/: golden standards (read-only; analysis only)

This module provides small helpers so mutation code can refuse to read/write
in ways that violate that policy.
"""

from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    """Return the workspace root.

    Test hook: set TRIAGE_REPO_ROOT to force a fake repo root.
    """
    env = os.getenv("TRIAGE_REPO_ROOT")
    if env:
        return Path(env).resolve(strict=False)
    # triage/ is one level under repo root
    return Path(__file__).resolve().parents[1]


def _resolve(p: str | Path) -> Path:
    pp = Path(p).expanduser()
    # Treat relative paths as relative to repo root (not CWD) so policy is stable
    # across callers.
    if not pp.is_absolute():
        pp = repo_root() / pp
    return pp.resolve(strict=False)


def _folder_path(name: str) -> Path:
    return _resolve(repo_root() / name)


def is_under_folder(path: str | Path, folder_name: str) -> bool:
    """True if *path* is within <repo_root>/<folder_name>/ (case-insensitive on Windows)."""
    p = _resolve(path)
    root = _folder_path(folder_name)
    try:
        return p.is_relative_to(root)
    except AttributeError:
        # Python <3.9 fallback (kept for safety)
        return str(p).lower().startswith(str(root).lower().rstrip("\\/") + os.sep)


def is_active_path(path: str | Path) -> bool:
    return is_under_folder(path, "Active")


def is_deprecated_path(path: str | Path) -> bool:
    return is_under_folder(path, "Deprecated")
